"""FEN, SAN, and mainline PGN notation for the chess domain."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from .model import (
    CastlingRights,
    ChessError,
    Color,
    FenError,
    GameState,
    GameStatus,
    IllegalMoveError,
    Move,
    PGNError,
    Piece,
    PieceType,
    parse_square,
    square_name,
)
from .rules import INITIAL_FEN, ChessRules

if TYPE_CHECKING:
    from .game import ChessGame

_PIECES = {piece.value.lower(): piece for piece in PieceType}
_CASTLING = {
    "K": CastlingRights.WHITE_KINGSIDE,
    "Q": CastlingRights.WHITE_QUEENSIDE,
    "k": CastlingRights.BLACK_KINGSIDE,
    "q": CastlingRights.BLACK_QUEENSIDE,
}
_RESULTS = {"1-0", "0-1", "1/2-1/2", "*"}
_HEADER = re.compile(r'^\[([A-Za-z0-9_]+)\s+"((?:\\.|[^"\\])*)"\]\s*$')


@dataclass(frozen=True, slots=True)
class PGNDocument:
    tags: tuple[tuple[str, str], ...]
    initial_state: GameState
    moves: tuple[Move, ...]
    result: str

    def new_game(self, rules: ChessRules | None = None) -> ChessGame:
        from .game import ChessGame

        game = ChessGame(self.initial_state, rules=rules)
        with game.replay_record():
            for move in self.moves:
                game.play(move)
        game.record_result(self.result, historical=True)
        return game


def parse_fen(fen: str) -> GameState:
    fields = fen.strip().split()
    if len(fields) != 6:
        raise FenError("FEN must contain six fields.")
    placement, active, castling, ep_field, halfmove_text, fullmove_text = fields
    ranks = placement.split("/")
    if len(ranks) != 8:
        raise FenError("FEN piece placement must contain eight ranks.")
    board: list[Piece | None] = [None] * 64
    for fen_rank, rank_text in enumerate(ranks):
        file_pos = 0
        rank = 7 - fen_rank
        for symbol in rank_text:
            if symbol in "12345678":
                file_pos += int(symbol)
            else:
                kind = _PIECES.get(symbol.lower())
                if kind is None or file_pos >= 8:
                    raise FenError(f"Invalid FEN piece placement: {placement!r}")
                color = Color.WHITE if symbol.isupper() else Color.BLACK
                board[rank * 8 + file_pos] = Piece(color, kind)
                file_pos += 1
            if file_pos > 8:
                raise FenError(f"FEN rank expands beyond eight squares: {rank_text!r}")
        if file_pos != 8:
            raise FenError(f"FEN rank does not expand to eight squares: {rank_text!r}")
    try:
        turn = Color(active)
        rights = CastlingRights.NONE
        if castling != "-":
            for symbol in castling:
                if symbol not in _CASTLING or rights & _CASTLING[symbol]:
                    raise FenError(f"Invalid FEN castling rights: {castling!r}")
                rights |= _CASTLING[symbol]
        ep = None if ep_field == "-" else parse_square(ep_field)
        halfmove_clock = int(halfmove_text)
        fullmove_number = int(fullmove_text)
    except (ValueError, ChessError) as exc:
        if isinstance(exc, FenError):
            raise
        raise FenError("Invalid FEN active color, castling, en-passant, or counters.") from exc
    if halfmove_clock < 0 or fullmove_number < 1:
        raise FenError("FEN counters must be non-negative and fullmove number positive.")
    state = GameState(tuple(board), turn, rights, ep, halfmove_clock, fullmove_number)
    _validate_position(state)
    return state


def _validate_position(state: GameState) -> None:
    kings = {color: [] for color in Color}
    for square, piece in enumerate(state.board):
        if piece is None:
            continue
        if piece.kind is PieceType.KING:
            kings[piece.color].append(square)
        if piece.kind is PieceType.PAWN and square // 8 in (0, 7):
            raise FenError("Pawns cannot occupy the first or eighth rank.")
    if any(len(squares) != 1 for squares in kings.values()):
        raise FenError("FEN must contain exactly one king of each color.")
    white_king, black_king = kings[Color.WHITE][0], kings[Color.BLACK][0]
    if max(abs(white_king % 8 - black_king % 8), abs(white_king // 8 - black_king // 8)) <= 1:
        raise FenError("Kings cannot be adjacent.")

    for right, king_square, rook_square in (
        (CastlingRights.WHITE_KINGSIDE, 4, 7),
        (CastlingRights.WHITE_QUEENSIDE, 4, 0),
        (CastlingRights.BLACK_KINGSIDE, 60, 63),
        (CastlingRights.BLACK_QUEENSIDE, 60, 56),
    ):
        if state.castling_rights & right:
            color = Color.WHITE if right in (
                CastlingRights.WHITE_KINGSIDE,
                CastlingRights.WHITE_QUEENSIDE,
            ) else Color.BLACK
            if state.board[king_square] != Piece(color, PieceType.KING):
                raise FenError("Castling right requires the king on its original square.")
            if state.board[rook_square] != Piece(color, PieceType.ROOK):
                raise FenError("Castling right requires the corresponding rook.")

    if state.en_passant is not None:
        expected_rank = 5 if state.turn is Color.WHITE else 2
        if state.en_passant // 8 != expected_rank or state.board[state.en_passant] is not None:
            raise FenError("Invalid en-passant target square.")
        captured_square = state.en_passant - 8 if state.turn is Color.WHITE else state.en_passant + 8
        source_square = state.en_passant + 8 if state.turn is Color.WHITE else state.en_passant - 8
        moved_color = state.turn.opposite
        if state.board[captured_square] != Piece(moved_color, PieceType.PAWN):
            raise FenError("En-passant target has no pawn that just advanced two squares.")
        if state.board[source_square] is not None:
            raise FenError("En-passant pawn's source square must be empty.")

    rules = ChessRules()
    if rules.is_in_check(state, state.turn.opposite):
        raise FenError("The side that just moved cannot still be in check.")


def to_fen(state: GameState) -> str:
    ranks: list[str] = []
    for rank in range(7, -1, -1):
        empty = 0
        text = ""
        for file_pos in range(8):
            piece = state.board[rank * 8 + file_pos]
            if piece is None:
                empty += 1
            else:
                if empty:
                    text += str(empty)
                    empty = 0
                text += piece.fen_symbol
        if empty:
            text += str(empty)
        ranks.append(text)
    castling = "".join(
        symbol for symbol, right in _CASTLING.items() if state.castling_rights & right
    ) or "-"
    ep = square_name(state.en_passant) if state.en_passant is not None else "-"
    return (
        f"{'/'.join(ranks)} {state.turn.value} {castling} {ep} "
        f"{state.halfmove_clock} {state.fullmove_number}"
    )


def to_san(state: GameState, move: Move, rules: ChessRules | None = None) -> str:
    chess_rules = rules or ChessRules()
    legal = chess_rules.legal_moves(state)
    if move not in legal:
        raise IllegalMoveError(f"Illegal move {move.to_uci()} in this position.")
    piece = state.board[move.from_square]
    if piece is None:
        raise IllegalMoveError("Cannot format a move from an empty square.")
    if piece.kind is PieceType.KING and abs(move.to_square - move.from_square) == 2:
        san = "O-O" if move.to_square % 8 == 6 else "O-O-O"
    else:
        capture = (
            state.board[move.to_square] is not None
            or (
                piece.kind is PieceType.PAWN
                and move.to_square == state.en_passant
                and move.from_square % 8 != move.to_square % 8
            )
        )
        san = "" if piece.kind is PieceType.PAWN else piece.kind.value.upper()
        alternatives = [
            candidate
            for candidate in legal
            if candidate != move
            and candidate.from_square != move.from_square
            and candidate.to_square == move.to_square
            and state.board[candidate.from_square] == piece
        ] if piece.kind is not PieceType.PAWN else []
        if alternatives:
            same_file = any(candidate.from_square % 8 == move.from_square % 8 for candidate in alternatives)
            same_rank = any(candidate.from_square // 8 == move.from_square // 8 for candidate in alternatives)
            if not same_file:
                san += chr(ord("a") + move.from_square % 8)
            elif not same_rank:
                san += str(move.from_square // 8 + 1)
            else:
                san += square_name(move.from_square)
        if piece.kind is PieceType.PAWN and capture:
            san += chr(ord("a") + move.from_square % 8)
        if capture:
            san += "x"
        san += square_name(move.to_square)
        if move.promotion is not None:
            san += f"={move.promotion.value.upper()}"
    next_state = chess_rules.apply(state, move)
    if chess_rules.is_in_check(next_state):
        san += "#" if not chess_rules.legal_moves(next_state) else "+"
    return san


_SAN = re.compile(
    r"^(?P<piece>[KQRBN])?(?P<file>[a-h])?(?P<rank>[1-8])?(?P<capture>x)?"
    r"(?P<to>[a-h][1-8])(?:=?(?P<promotion>[QRBN]))?$"
)


def parse_san(state: GameState, text: str, rules: ChessRules | None = None) -> Move:
    """Parse one SAN token structurally against the legal moves of ``state``.

    Accepts check/annotation suffixes, ``0-0`` castling, ``e.p.`` and
    promotion without ``=`` (``e8Q``). Captures must be marked with ``x``.
    """
    chess_rules = rules or ChessRules()
    token = text.strip()
    token = re.sub(r"[!?]+$", "", token)
    token = re.sub(r"[+#]+$", "", token)
    token = re.sub(r"\s*e\.p\.$", "", token)
    legal = chess_rules.legal_moves(state)
    castle = token.replace("0", "O")
    if castle in ("O-O", "O-O-O"):
        king = state.king_square(state.turn)
        target_file = 6 if castle == "O-O" else 2
        matches = [
            move for move in legal
            if move.from_square == king
            and abs(move.to_square - move.from_square) == 2
            and move.to_square % 8 == target_file
        ]
    else:
        parsed = _SAN.match(token)
        if parsed is None:
            raise PGNError(f"Invalid or ambiguous SAN move: {text!r}")
        kind = _PIECES[parsed["piece"].lower()] if parsed["piece"] else PieceType.PAWN
        to_square = parse_square(parsed["to"])
        promotion = _PIECES[parsed["promotion"].lower()] if parsed["promotion"] else None
        wants_capture = parsed["capture"] is not None
        matches = []
        for move in legal:
            piece = state.board[move.from_square]
            if piece is None or piece.kind is not kind or move.to_square != to_square:
                continue
            if move.promotion is not promotion:
                continue
            if parsed["file"] and move.from_square % 8 != ord(parsed["file"]) - ord("a"):
                continue
            if parsed["rank"] and move.from_square // 8 != int(parsed["rank"]) - 1:
                continue
            is_capture = state.board[to_square] is not None or (
                kind is PieceType.PAWN and move.from_square % 8 != to_square % 8
            )
            if is_capture != wants_capture:
                continue
            if kind is PieceType.PAWN and is_capture and not parsed["file"]:
                continue
            matches.append(move)
    if len(matches) != 1:
        raise PGNError(f"Invalid or ambiguous SAN move: {text!r}")
    return matches[0]


def parse_pgn(text: str, rules: ChessRules | None = None, *, max_plies: int | None = None) -> PGNDocument:
    chess_rules = rules or ChessRules()
    tag_map: dict[str, str] = {}
    lines = text.splitlines()
    movetext_lines: list[str] = []
    in_movetext = False
    for line in lines:
        stripped = line.strip()
        if not in_movetext and not stripped:
            continue
        if not in_movetext:
            match = _HEADER.match(stripped)
            if match:
                key, raw_value = match.groups()
                value = re.sub(r'\\(["\\])', r"\1", raw_value)
                if key in tag_map:
                    raise PGNError(f"Duplicate PGN tag: {key}")
                tag_map[key] = value
                continue
            in_movetext = True
        movetext_lines.append(line)
    if "SetUp" in tag_map and tag_map["SetUp"] != "1":
        raise PGNError("PGN SetUp tag must be 1 when present.")
    if tag_map.get("SetUp") == "1" and "FEN" not in tag_map:
        raise PGNError("PGN SetUp=1 requires a FEN tag.")
    try:
        initial = parse_fen(tag_map["FEN"]) if tag_map.get("SetUp") == "1" else parse_fen(INITIAL_FEN)
    except FenError as exc:
        raise PGNError(f"Invalid PGN starting position: {exc}") from exc

    movetext = _remove_comments_and_variations("\n".join(movetext_lines))
    tokens = re.sub(r"(\S)(\$\d+)", r"\1 \2", movetext).split()
    from .game import ChessGame

    game = ChessGame(initial, rules=chess_rules)
    result_token: str | None = None
    with game.replay_record():
        for token_index, raw_token in enumerate(tokens):
            token = re.sub(r"^\d+\.(?:\.\.)?", "", raw_token)
            if not token or token == "...":
                continue
            if token.startswith("$") and token[1:].isdigit():
                continue
            if token in _RESULTS:
                result_token = token
                if any(re.sub(r"^\d+\.(?:\.\.)?", "", trailing) for trailing in tokens[token_index + 1 :]):
                    raise PGNError("Unexpected movetext after the game result.")
                break
            if max_plies is not None and len(game.moves) >= max_plies:
                raise PGNError(f"PGN exceeds the limit of {max_plies} half-moves.")
            try:
                game.play(parse_san(game.state, token, chess_rules))
            except ChessError as exc:
                raise PGNError(f"Invalid PGN move {token!r}: {exc}") from exc
        tag_result = tag_map.get("Result")
        if tag_result is not None and tag_result not in _RESULTS:
            raise PGNError(f"Invalid PGN Result tag: {tag_result!r}")
        if result_token is not None and tag_result not in (None, "*", result_token):
            raise PGNError("PGN movetext result conflicts with the Result tag.")
        result = result_token or tag_result or "*"
        final = game.outcome()
        if result != "*" and final.status is not GameStatus.ACTIVE and final.status not in (
            GameStatus.DRAW_CLAIMED,
            GameStatus.RESIGNED,
        ):
            expected = _game_result(game)
            if result != expected:
                raise PGNError(
                    f"PGN result {result} contradicts the final position ({final.status.name.lower()})."
                )
    return PGNDocument(tuple(tag_map.items()), initial, tuple(game.moves), result)


def export_pgn(
    game: ChessGame,
    headers: Mapping[str, str] | None = None,
    result: str | None = None,
    rules: ChessRules | None = None,
) -> str:
    chess_rules = rules or game.rules
    tag_map = {
        "Event": "*",
        "Site": "?",
        "Date": "????.??.??",
        "Round": "?",
        "White": "White",
        "Black": "Black",
    }
    if headers:
        tag_map.update(headers)
    final_result = result if result is not None else _game_result(game)
    if final_result not in _RESULTS:
        raise PGNError(f"Invalid PGN result: {final_result!r}")
    tag_map["Result"] = final_result
    if game.initial_state != chess_rules.initial_state():
        tag_map["SetUp"] = "1"
        tag_map["FEN"] = to_fen(game.initial_state)
    else:
        tag_map.pop("SetUp", None)
        tag_map.pop("FEN", None)
    header_lines: list[str] = []
    for key, value in tag_map.items():
        if not re.fullmatch(r"[A-Za-z0-9_]+", key) or "\n" in value or "\r" in value:
            raise PGNError(f"Invalid PGN tag: {key!r}")
        escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
        header_lines.append(f'[{key} "{escaped_value}"]')
    header_text = "\n".join(header_lines)
    state = game.initial_state
    san_tokens: list[str] = []
    for move in game.moves:
        if state.turn is Color.WHITE:
            san_tokens.append(f"{state.fullmove_number}.")
        elif not san_tokens:
            san_tokens.append(f"{state.fullmove_number}...")
        san_tokens.append(to_san(state, move, chess_rules))
        state = chess_rules.apply(state, move)
    san_tokens.append(final_result)
    return f"{header_text}\n\n{' '.join(san_tokens)}"


def _remove_comments_and_variations(text: str) -> str:
    output: list[str] = []
    variation_depth = 0
    brace_comment = False
    line_comment = False
    for character in text:
        if line_comment:
            if character == "\n":
                line_comment = False
                if variation_depth == 0 and not brace_comment:
                    output.append(character)
            continue
        if brace_comment:
            if character == "}":
                brace_comment = False
                if variation_depth == 0:
                    output.append(" ")
            continue
        if character == ";":
            line_comment = True
            if variation_depth == 0:
                output.append(" ")
        elif character == "{":
            brace_comment = True
            if variation_depth == 0:
                output.append(" ")
        elif character == "}":
            raise PGNError("Unmatched PGN comment terminator.")
        elif character == "(":
            if variation_depth == 0:
                output.append(" ")
            variation_depth += 1
        elif character == ")":
            if variation_depth == 0:
                raise PGNError("Unmatched PGN variation terminator.")
            variation_depth -= 1
            if variation_depth == 0:
                output.append(" ")
        elif variation_depth == 0:
            output.append(character)
    if brace_comment:
        raise PGNError("Unterminated PGN brace comment.")
    if variation_depth:
        raise PGNError("Unterminated PGN variation.")
    return "".join(output)


def _game_result(game: ChessGame) -> str:
    outcome = game.outcome()
    if outcome.status is GameStatus.ACTIVE:
        return "*"
    if outcome.winner is Color.WHITE:
        return "1-0"
    if outcome.winner is Color.BLACK:
        return "0-1"
    return "1/2-1/2"
