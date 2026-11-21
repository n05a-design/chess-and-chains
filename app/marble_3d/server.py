"""Run the optional local 3D chessboard with the project's own game controller."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys
import webbrowser

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ASSETS = ROOT / "design" / "source" / "marmor-3d" / "spielsatz"
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.chess import (  # noqa: E402
    ChessError, ChessGame, DrawClaim, GameStatus, Move, export_pgn, parse_pgn, square_name, to_fen,
)
from chess_and_chains.game.controller import GameController, GameSetup  # noqa: E402
from chess_and_chains.storage.database import MAX_PGN_FILE_BYTES, MAX_PGN_FILE_PLIES  # noqa: E402
from chess_and_chains.storage.exchange import MAX_FEN_FILE_BYTES, parse_fen_text  # noqa: E402
from chess_and_chains.ui.piece_contract import PIECE_FILE_NAMES, validate_svg_piece_set  # noqa: E402


class StalePosition(ValueError):
    """A different action changed the board after the player selected a move."""


class LocalGame:
    def __init__(self, fen: str | None = None) -> None:
        self.controller = GameController()
        self._headers: dict[str, str] = {}
        if fen is not None:
            self.controller.new_game(GameSetup(initial_fen=fen))
        self.revision = 0

    def pgn(self) -> str:
        headers = {"Event": "Chess & Chains – Marmorbrett", **self._headers}
        return export_pgn(self.controller.game, headers) + "\n"

    def import_file(self, kind: str, content: bytes, revision: int) -> dict:
        if revision != self.revision:
            raise StalePosition("Die Stellung wurde inzwischen aktualisiert.")
        if kind == "fen" and 0 < len(content) <= MAX_FEN_FILE_BYTES:
            game = ChessGame(parse_fen_text(content.decode("utf-8-sig")))
            headers = {}
        elif kind == "pgn" and 0 < len(content) <= MAX_PGN_FILE_BYTES:
            text = content.decode("utf-8-sig")
            if not text.strip() or any(ord(char) < 32 and char not in "\t\n\r" for char in text):
                raise ValueError("Die PGN-Datei ist leer oder enthält ungültige Zeichen.")
            document = parse_pgn(text, max_plies=MAX_PGN_FILE_PLIES)
            game = document.new_game()
            headers = dict(document.tags)
        else:
            raise ValueError("Dateityp oder Dateigröße ist ungültig.")
        self.controller.load_game(game)
        self._headers = headers
        self.revision += 1
        return self.snapshot()

    def snapshot(self) -> dict:
        view = self.controller.view()
        state = view.state
        outcome = view.outcome
        return {
            "revision": self.revision,
            "board": [piece.color.value + piece.kind.value.upper() if piece else None
                      for piece in state.board],
            "turn": state.turn.value,
            "status": outcome.status.name,
            "winner": outcome.winner.value if outcome.winner else None,
            "check": square_name(state.king_square(state.turn)) if outcome.in_check else None,
            "moves": [move.to_uci() for move in view.legal_moves],
            "last": view.last_move.to_uci() if view.last_move else None,
            "san": view.san_moves,
            "firstMove": self.controller.game.initial_state.fullmove_number,
            "firstTurn": self.controller.game.initial_state.turn.value,
            "undo": view.can_undo,
            "redo": view.can_redo,
            "claims": [
                {"reason": reason.name, "move": move.to_uci() if move else None}
                for reason, move in self.controller.game.draw_claim_options()
            ] if outcome.status is GameStatus.ACTIVE else [],
        }

    def apply(self, data: object) -> dict:
        if not isinstance(data, dict) or type(data.get("revision")) is not int:
            raise ValueError("Ungültige Anfrage.")
        if data["revision"] != self.revision:
            raise StalePosition("Die Stellung wurde inzwischen aktualisiert.")
        action = data.get("action")
        if action == "move":
            self.controller.play_human(self.parse_move(data.get("move")))
        elif action == "undo":
            self.controller.undo()
        elif action == "redo":
            self.controller.redo()
        elif action == "new":
            self.controller.new_game()
            self._headers.clear()
        elif action == "resign":
            self.controller.resign()
        elif action == "claim":
            reason = data.get("reason")
            if not isinstance(reason, str) or reason not in DrawClaim.__members__:
                raise ValueError("Unbekannte Remisregel.")
            token = data.get("move")
            move = self.parse_move(token) if token is not None else None
            self.controller.claim_draw(DrawClaim[reason], move)
        else:
            raise ValueError("Unbekannte Aktion.")
        self.revision += 1
        return self.snapshot()

    @staticmethod
    def parse_move(token: object) -> Move:
        if not isinstance(token, str) or len(token) not in (4, 5):
            raise ValueError("Ungültige Zugnotation.")
        return Move.from_uci(token)


class MarbleServer(HTTPServer):
    # All controller calls occur serially on the server's owner thread.
    def __init__(self, port: int, assets: Path, game: LocalGame) -> None:
        self.game = game
        static = Path(__file__).resolve().parent
        self.files = {
            "/": (static / "index.html", "text/html; charset=utf-8"),
            "/board.css": (static / "board.css", "text/css; charset=utf-8"),
            "/game.js": (static / "game.js", "text/javascript; charset=utf-8"),
            "/scene.js": (static / "scene.js", "text/javascript; charset=utf-8"),
            "/art/board.svg": (assets / "Brett.svg", "image/svg+xml"),
            **{f"/art/{name}": (assets / "Figuren" / name, "image/svg+xml")
               for name in PIECE_FILE_NAMES},
        }
        super().__init__(("127.0.0.1", port), MarbleRequest)
        self.host = f"127.0.0.1:{self.server_port}"
        self.origin = f"http://{self.host}"


class MarbleRequest(BaseHTTPRequestHandler):
    server: MarbleServer
    timeout = 2

    def do_GET(self) -> None:
        if not self.check_host():
            return
        if self.path == "/api/game":
            self.reply_json(self.server.game.snapshot())
            return
        if self.path == "/api/partie.pgn":
            self.respond(
                HTTPStatus.OK, "application/x-chess-pgn; charset=utf-8",
                self.server.game.pgn().encode("utf-8"), download="chess-and-chains.pgn",
            )
            return
        if self.path == "/api/stellung.fen":
            fen = to_fen(self.server.game.controller.game.state) + "\n"
            self.respond(HTTPStatus.OK, "text/plain; charset=ascii", fen.encode("ascii"),
                         download="chess-and-chains.fen")
            return
        resource = self.server.files.get(self.path)
        if resource is None:
            self.respond(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"Not found")
            return
        file, mime = resource
        try:
            content = file.read_bytes()
        except OSError:
            self.respond(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"File unavailable")
            return
        self.respond(HTTPStatus.OK, mime, content)

    def do_POST(self) -> None:
        if not self.check_host():
            return
        if self.path not in ("/api/game", "/api/import"):
            self.reply_json({"error": "Unbekannte Adresse."}, HTTPStatus.NOT_FOUND)
            return
        if self.headers.get("Origin") != self.server.origin:
            self.reply_json({"error": "Unzulässiger Ursprung."}, HTTPStatus.FORBIDDEN)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            mime = self.headers.get_content_type()
            if self.path == "/api/import":
                limits = {"application/x-chess-pgn": ("pgn", MAX_PGN_FILE_BYTES),
                          "application/x-chess-fen": ("fen", MAX_FEN_FILE_BYTES)}
                kind, limit = limits.get(mime, ("", 0))
                if not 0 < size <= limit:
                    raise ValueError("Dateityp oder Dateigröße ist ungültig.")
                revision = int(self.headers.get("X-Board-Revision", "-1"))
                content = self.rfile.read(size)
                if len(content) != size:
                    raise ValueError("Die Datei wurde nicht vollständig übertragen.")
                result = self.server.game.import_file(kind, content, revision)
            else:
                if not 0 < size <= 4096 or mime != "application/json":
                    raise ValueError("Ungültige Anfrage.")
                data = json.loads(self.rfile.read(size))
                result = self.server.game.apply(data)
        except StalePosition as error:
            self.reply_json({"error": str(error), "state": self.server.game.snapshot()}, HTTPStatus.CONFLICT)
        except (ChessError, ValueError, RecursionError) as error:
            message = str(error) if isinstance(error, ChessError) else "Die Anfrage war ungültig."
            self.reply_json({"error": message}, HTTPStatus.BAD_REQUEST)
        else:
            self.reply_json(result)

    def check_host(self) -> bool:
        if self.headers.get("Host") == self.server.host:
            return True
        self.reply_json({"error": "Nur die lokale Startadresse ist zulässig."}, HTTPStatus.FORBIDDEN)
        return False

    def reply_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.respond(status, "application/json; charset=utf-8",
                     json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def respond(self, status: HTTPStatus, mime: str, body: bytes, *, download: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if download is not None:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' blob:; "
            "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
        )
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format: str, *args: object) -> None:
        # The local session does not need an access log.
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assets", type=Path, default=DEFAULT_ASSETS,
        help="Optionaler Ordner mit eigenem Brett.svg und Figuren/ (Standard: Marmor-Spielsatz im Checkout)",
    )
    parser.add_argument("--port", type=int, default=0, help="Lokaler Port (0 wählt einen freien Port)")
    parser.add_argument("--fen", help="Optionale Startstellung in FEN-Notation")
    parser.add_argument("--no-browser", action="store_true", help="Startadresse ausgeben und keinen Browser öffnen")
    args = parser.parse_args()
    report = validate_svg_piece_set(args.assets / "Figuren")
    if not report.ok:
        parser.error("\n".join(report.problems))
    if not (args.assets / "Brett.svg").is_file():
        parser.error("Brett.svg fehlt im Assetordner.")
    try:
        game = LocalGame(args.fen)
    except ChessError as error:
        parser.error(str(error))
    with MarbleServer(args.port, args.assets, game) as server:
        print(f"Chess & Chains 3D: {server.origin}/", flush=True)
        if not args.no_browser:
            webbrowser.open(server.origin + "/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            game.controller.shutdown()


if __name__ == "__main__":
    main()
