"""Regression tests for the local marble-board bridge and vector artwork."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pathlib import Path
import json
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.marble_3d.build_art import NS, board_svg, invert  # noqa: E402
from app.marble_3d.server import DEFAULT_ASSETS, LocalGame, MarbleServer, StalePosition  # noqa: E402
from chess_and_chains.chess import ChessError, parse_pgn  # noqa: E402
from chess_and_chains.ui.piece_contract import validate_svg_piece_set  # noqa: E402


class MarbleGameTests(unittest.TestCase):
    def test_file_import_preserves_record_metadata_and_is_atomic(self):
        game = LocalGame()
        game.apply({"revision": 0, "action": "move", "move": "d2d4"})
        initial = game.snapshot()
        for kind, data in (("pgn", b"1. e5 *"), ("fen", b"bad position"), ("pgn", b"\xff")):
            with self.subTest(kind=kind, data=data), self.assertRaises(ValueError):
                game.import_file(kind, data, 1)
            self.assertEqual(game.snapshot(), initial)
        with self.assertRaises(StalePosition):
            game.import_file("pgn", b"1. e4 *", 0)
        self.assertEqual(game.snapshot(), initial)

        pgn = '[Event "Clubtest"]\n[White "Éva"]\n\n1. e4 e5 1/2-1/2'
        state = game.import_file("pgn", pgn.encode("utf-8-sig"), 1)
        self.assertEqual((state["revision"], state["status"]), (2, "RECORDED_RESULT"))
        exported = parse_pgn(game.pgn())
        self.assertEqual(exported.result, "1/2-1/2")
        self.assertEqual(dict(exported.tags)["White"], "Éva")
        self.assertEqual(dict(exported.tags)["Event"], "Clubtest")

        fen = "r3k2r/8/8/8/3pP3/8/8/R3K2R b KQkq e3 0 17"
        state = game.import_file("fen", fen.encode("ascii"), 2)
        self.assertEqual((state["firstMove"], state["turn"], state["san"]), (17, "b", ()))
        self.assertIn("d4e3", state["moves"])
        self.assertNotIn("Clubtest", game.pgn())

    def test_game_revision_and_full_undo_and_redo(self):
        game = LocalGame()
        original = game.snapshot()
        move = game.apply({"revision": 0, "action": "move", "move": "e2e4"})
        self.assertEqual(move["san"], ("e4",))
        self.assertEqual(move["last"], "e2e4")
        with self.assertRaises(StalePosition):
            game.apply({"revision": 0, "action": "move", "move": "e7e5"})
        with self.assertRaises(ChessError):
            game.apply({"revision": 1, "action": "move", "move": "e7e4"})
        self.assertEqual(game.snapshot(), move)
        undone = game.apply({"revision": 1, "action": "undo"})
        self.assertEqual(undone["board"], original["board"])
        self.assertEqual(undone["moves"], original["moves"])
        replayed = game.apply({"revision": 2, "action": "redo"})
        self.assertEqual(replayed["board"], move["board"])
        self.assertEqual(replayed["last"], "e2e4")

    def test_underpromotion_and_game_outcome(self):
        game = LocalGame("7k/P7/8/8/8/8/8/7K w - - 0 1")
        options = {move for move in game.snapshot()["moves"] if move.startswith("a7a8")}
        self.assertEqual(options, {"a7a8" + kind for kind in "qrbn"})
        result = game.apply({"revision": 0, "action": "move", "move": "a7a8n"})
        self.assertEqual(result["board"][56], "wN")
        self.assertEqual(result["status"], "DRAW_INSUFFICIENT_MATERIAL")
        self.assertEqual(result["moves"], [])
        exported = parse_pgn(game.pgn())
        self.assertEqual(exported.result, "1/2-1/2")
        self.assertEqual([move.to_uci() for move in exported.moves], ["a7a8n"])

    def test_draw_by_declared_move_preserves_position_and_can_be_undone(self):
        game = LocalGame("7k/8/8/8/8/8/6R1/7K w - - 99 1")
        state = game.snapshot()
        option = next(claim for claim in state["claims"] if claim["move"])
        outcome = game.apply({"revision": 0, "action": "claim", **option})
        self.assertEqual(outcome["status"], "DRAW_CLAIMED")
        self.assertEqual(outcome["board"], state["board"])
        self.assertEqual(game.apply({"revision": 1, "action": "undo"})["status"], "ACTIVE")

    def test_pawn_barrier_from_current_core_ends_3d_game_and_exports_draw(self):
        game = LocalGame("7k/8/1p1p1p1p/pPpPpPp1/P1P1P1PP/8/8/K7 w - - 0 1")
        result = game.apply({"revision": 0, "action": "move", "move": "h4h5"})
        self.assertEqual(result["status"], "DRAW_DEAD_POSITION")
        self.assertEqual(result["moves"], [])
        exported = parse_pgn(game.pgn())
        self.assertEqual(exported.result, "1/2-1/2")
        self.assertEqual(exported.new_game().outcome().status.name, "DRAW_DEAD_POSITION")


class MarbleRequestTests(unittest.TestCase):
    def test_file_routes_enforce_origin_limits_and_follow_the_current_position(self):
        with tempfile.TemporaryDirectory() as directory:
            with MarbleServer(0, Path(directory), LocalGame()) as server:
                worker = Thread(target=server.serve_forever, daemon=True)
                worker.start()
                try:
                    fen = b"r3k2r/8/8/8/3pP3/8/8/R3K2R b KQkq e3 0 17"
                    for origin, revision, data, code in (
                        ("https://example.invalid", 0, fen, 403),
                        (server.origin, 0, b"x" * 4097, 400),
                        (server.origin, 1, fen, 409),
                        (server.origin, 0, fen, 200),
                    ):
                        request = Request(server.origin + "/api/import", data=data, headers={
                            "Origin": origin, "Content-Type": "application/x-chess-fen",
                            "X-Board-Revision": str(revision),
                        })
                        with self.subTest(code=code):
                            if code == 200:
                                with urlopen(request, timeout=4) as response:
                                    self.assertEqual(json.load(response)["revision"], 1)
                            else:
                                with self.assertRaises(HTTPError) as invalid:
                                    urlopen(request, timeout=4)
                                with invalid.exception as response:
                                    self.assertEqual(response.code, code)
                    with urlopen(server.origin + "/api/stellung.fen", timeout=4) as response:
                        self.assertEqual(response.headers.get_filename(), "chess-and-chains.fen")
                        self.assertEqual(response.read(), fen + b"\n")
                finally:
                    server.shutdown()
                    worker.join(timeout=4)

    def test_local_origin_and_revision_guard_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            with MarbleServer(0, Path(directory), LocalGame()) as server:
                worker = Thread(target=server.serve_forever, daemon=True)
                worker.start()
                try:
                    endpoint = server.origin + "/api/game"
                    move = json.dumps({"revision": 0, "action": "move", "move": "e2e4"}).encode()
                    def request(origin):
                        return Request(endpoint, data=move, headers={
                            "Origin": origin, "Content-Type": "application/json",
                        })

                    with self.assertRaises(HTTPError) as invalid:
                        urlopen(request("https://example.invalid"), timeout=4)
                    self.assertEqual(invalid.exception.code, 403)
                    invalid.exception.close()
                    with urlopen(request(server.origin), timeout=4) as response:
                        self.assertEqual(json.load(response)["san"], ["e4"])
                    with urlopen(server.origin + "/api/partie.pgn", timeout=4) as response:
                        self.assertEqual(response.headers.get_filename(), "chess-and-chains.pgn")
                        pgn = parse_pgn(response.read().decode("utf-8"))
                        self.assertEqual([move.to_uci() for move in pgn.moves], ["e2e4"])
                    with self.assertRaises(HTTPError) as stale:
                        urlopen(request(server.origin), timeout=4)
                    self.assertEqual(stale.exception.code, 409)
                    with stale.exception as response:
                        self.assertEqual(json.load(response)["state"]["san"], ["e4"])
                finally:
                    server.shutdown()
                    worker.join(timeout=4)


class MarbleArtworkTests(unittest.TestCase):
    def test_checkout_contains_complete_editable_game_art(self):
        result = validate_svg_piece_set(DEFAULT_ASSETS / "Figuren")
        self.assertTrue(result.ok, result.problems)
        board = ET.parse(DEFAULT_ASSETS / "Brett.svg").getroot()
        self.assertEqual(board.get("viewBox"), "0 0 864 864")
        self.assertEqual(len(board.find(f'{NS}g[@id="brettfelder"]')), 64)
        self.assertFalse(list(board.iter(NS + "image")))

    def test_inverted_motif_keeps_geometry_and_board_has_64_tiles(self):
        svg = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg"><path id="marmor" '
            'fill="#f0f0ee" d="M 0 0 L 1 1 Z"/></svg>'
        )
        light = svg[0]
        dark = invert(svg)[0]
        self.assertEqual(light.get("d"), dark.get("d"))
        self.assertNotEqual(light.get("fill"), dark.get("fill"))
        board = board_svg()
        tiles = board.find(f'{NS}g[@id="brettfelder"]')
        self.assertEqual(len(tiles), 64)
        self.assertEqual(tiles[0].get("id"), "feld-a8")
        self.assertGreater(int(tiles[0].find(f"{NS}g/{NS}rect").get("fill")[1:3], 16), 200)
        self.assertLess(int(tiles[1].find(f"{NS}g/{NS}rect").get("fill")[1:3], 16), 55)
        self.assertEqual(tiles[-1].get("id"), "feld-h1")
        first_veins = {tile.find(f"{NS}g/{NS}g[@id='adern-{tile.get('id')[5:]}']/{NS}path").get("d")
                       for tile in tiles}
        self.assertEqual(len(first_veins), 64)
        self.assertFalse(list(board.iter(NS + "use")))
        ids = [node.get("id") for node in board.iter() if "id" in node.attrib]
        self.assertEqual(len(ids), len(set(ids)))
