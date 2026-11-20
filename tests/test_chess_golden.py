"""Independent reference and property tests for the chess domain (N02).

Perft reference counts are the published values from the Chess Programming
Wiki "Perft Results" page (positions 3, 4 and its mirror). No third-party
rules code is used; the mirror-symmetry and round-trip properties are
self-checking and need no external oracle.
"""
import random
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chess_and_chains.chess import (  # noqa: E402
    ChessGame,
    ChessRules,
    GameStatus,
    Move,
    PGNError,
    export_pgn,
    parse_fen,
    parse_pgn,
    parse_square,
    to_fen,
    to_san,
)
from chess_and_chains.chess.notation import parse_san  # noqa: E402

RULES = ChessRules()


def mirror_fen(fen: str) -> str:
    """Colour-flip a position: swap sides, mirror ranks; perft must be identical."""
    board, turn, castling, ep, half, full = fen.split()
    ranks = [rank.swapcase() for rank in reversed(board.split("/"))]
    castling = "-" if castling == "-" else "".join(sorted(castling.swapcase(), key="KQkq".index))
    if ep != "-":
        ep = ep[0] + {"3": "6", "6": "3"}[ep[1]]
    return " ".join(["/".join(ranks), "b" if turn == "w" else "w", castling, ep, half, full])


def random_game(seed: int, plies: int = 120) -> ChessGame:
    rng = random.Random(seed)
    game = ChessGame()
    while len(game.moves) < plies and game.outcome().status is GameStatus.ACTIVE:
        game.play(rng.choice(RULES.legal_moves(game.state)))
    return game


class PerftReferenceTests(unittest.TestCase):
    def test_position3_depth4(self):
        self.assertEqual(RULES.perft(parse_fen("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"), 4), 43238)

    def test_position4_and_mirror_depth3(self):
        for fen in (
            "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
            "r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1",
        ):
            with self.subTest(fen=fen):
                self.assertEqual([RULES.perft(parse_fen(fen), d) for d in (1, 2, 3)], [6, 264, 9467])

    def test_reference_positions_five_and_six(self):
        # Published numeric fixtures: https://www.chessprogramming.org/Perft_Results
        for fen, counts in (
            ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", [44, 1486, 62379]),
            ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", [46, 2079, 89890]),
        ):
            with self.subTest(fen=fen):
                state = parse_fen(fen)
                self.assertEqual([RULES.perft(state, depth) for depth in (1, 2, 3)], counts)

    def test_colour_mirror_symmetry(self):
        fens = (
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
            "8/2k5/8/3pP3/8/8/8/4K3 w - d6 0 2",          # en passant available
            "4k3/1P6/8/8/8/8/6p1/4K3 w - - 0 1",           # promotions both sides
            "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",        # castling both sides
            "8/8/8/2k5/2pP4/8/B7/4K3 b - d3 0 1",          # pinned en-passant capture
        )
        for fen in fens:
            with self.subTest(fen=fen):
                self.assertEqual(to_fen(parse_fen(mirror_fen(mirror_fen(fen)))), to_fen(parse_fen(fen)))
                self.assertEqual(
                    RULES.perft(parse_fen(fen), 3), RULES.perft(parse_fen(mirror_fen(fen)), 3)
                )

    def test_en_passant_that_exposes_king_is_illegal(self):
        state = parse_fen("8/8/8/KPp4r/8/8/8/4k3 w - c6 0 2")
        self.assertNotIn(Move.from_uci("b5c6"), RULES.legal_moves(state))


class NotationGoldenTests(unittest.TestCase):
    def test_san_disambiguation_file_rank_and_square(self):
        state = parse_fen("7k/8/8/8/Q1Q5/8/Q7/7K w - - 0 1")
        expected = {"a4b3": "Qa4b3", "c4b3": "Qcb3", "a2b3": "Q2b3"}
        for uci, san in expected.items():
            with self.subTest(uci=uci):
                move = Move.from_uci(uci)
                self.assertEqual(to_san(state, move), san)
                self.assertEqual(parse_san(state, san), move)
        with self.assertRaises(PGNError):
            parse_san(state, "Qb3")  # ambiguous

    def test_promotion_san_and_pgn(self):
        state = parse_fen("1n5k/P7/8/8/8/8/8/K7 w - - 0 1")
        self.assertEqual(to_san(state, Move.from_uci("a7b8n")), "axb8=N")
        self.assertEqual(to_san(state, Move.from_uci("a7a8q")), "a8=Q")  # b8 knight blocks the check
        for token in ("a8=Q+", "a8Q", "a8=Q"):
            self.assertEqual(parse_san(state, token), Move.from_uci("a7a8q"))
        doc = parse_pgn('[SetUp "1"]\n[FEN "1n5k/P7/8/8/8/8/8/K7 w - - 0 1"]\n\n1. axb8=R+ Kg7 *')
        self.assertEqual(doc.moves[0], Move.from_uci("a7b8r"))
        self.assertIn("axb8=R+", export_pgn(doc.new_game()))

    def test_capture_marker_is_required_and_checked(self):
        state = parse_fen("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1")
        self.assertEqual(parse_san(state, "exd5"), Move.from_uci("e4d5"))
        for bad in ("ed5", "xd5", "e5x", "Pe5", "exe5"):
            with self.subTest(bad=bad), self.assertRaises(PGNError):
                parse_san(state, bad)

    def test_castling_notations(self):
        state = parse_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        self.assertEqual(parse_san(state, "O-O"), Move.from_uci("e1g1"))
        self.assertEqual(parse_san(state, "0-0-0"), Move.from_uci("e1c1"))

    def test_pgn_with_comments_nags_variations_and_escaped_tags(self):
        text = (
            '[Event "Club \\"Open\\""]\n[White "A"]\n[Black "B"]\n[Result "1-0"]\n\n'
            "1. e4 $1 {best by test} e5 (1... c5 2. Nf3 (2. c3)) 2. Bc4 ; line comment\n"
            "Nc6 3. Qh5 Nf6?? 4. Qxf7# 1-0"
        )
        doc = parse_pgn(text)
        self.assertEqual(doc.result, "1-0")
        self.assertEqual(dict(doc.tags)["Event"], 'Club "Open"')
        game = doc.new_game()
        self.assertIs(game.outcome().status, GameStatus.CHECKMATE)
        exported = export_pgn(game, {"Event": 'Club "Open"'})
        self.assertIn('[Event "Club \\"Open\\""]', exported)
        self.assertEqual(parse_pgn(exported).moves, doc.moves)

    def test_malformed_pgn_is_rejected(self):
        cases = {
            "illegal move": "1. e5 *",
            "unknown token": "1. e4 banana *",
            "unterminated comment": "1. e4 { open *",
            "unmatched variation": "1. e4 ) *",
            "text after result": "1. e4 e5 1-0 2. Nf3",
            "result tag conflict": '[Result "0-1"]\n\n1. e4 1-0',
            "bad result tag": '[Result "2-0"]\n\n1. e4 *',
            "setup without fen": '[SetUp "1"]\n\n1. e4 *',
            "invalid fen": '[SetUp "1"]\n[FEN "8/8/8/8/8/8/8/8 w - - 0 1"]\n\n*',
            "duplicate tag": '[White "A"]\n[White "B"]\n\n*',
            "mate result mismatch": "1. f3 e5 2. g4 Qh4# 1-0",
            "stalemate scored as win": '[SetUp "1"]\n[FEN "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"]\n\n1-0',
        }
        for name, text in cases.items():
            with self.subTest(case=name), self.assertRaises(PGNError):
                parse_pgn(text)

    def test_result_star_is_allowed_for_finished_position(self):
        self.assertEqual(parse_pgn("1. f3 e5 2. g4 Qh4# *").result, "*")


class PropertyTests(unittest.TestCase):
    def test_random_games_round_trip_through_pgn_fen_and_undo_redo(self):
        for seed in range(6):
            with self.subTest(seed=seed):
                game = random_game(seed)
                states = [game.initial_state]
                for move in game.moves:
                    states.append(RULES.apply(states[-1], move))
                for state in states:
                    self.assertEqual(parse_fen(to_fen(state)), state)
                doc = parse_pgn(export_pgn(game))
                self.assertEqual(doc.moves, tuple(game.moves))
                outcome = game.outcome()
                count = len(game.moves)
                for _ in range(count):
                    game.undo()
                self.assertEqual(game.state, game.initial_state)
                self.assertEqual(game.moves, [])
                for _ in range(count):
                    game.redo()
                self.assertEqual(game.state, states[-1])
                self.assertEqual(game.outcome(), outcome)

    def test_pgn_import_performance_budget(self):
        game = random_game(11, plies=150)
        text = export_pgn(game)
        start = time.perf_counter()
        parse_pgn(text)
        # Was 5.7 s before the structural SAN parser (N02 measurement, macOS arm64).
        self.assertLess(time.perf_counter() - start, 3.0)


class TerminationRuleTests(unittest.TestCase):
    def test_checkmate_on_move_that_reaches_75_move_limit_counts_as_mate(self):
        game = ChessGame(parse_fen("7k/8/6K1/8/8/8/8/R7 w - - 149 120"))
        game.play(Move.from_uci("a1a8"))
        self.assertIs(game.outcome().status, GameStatus.CHECKMATE)

    def test_dead_position_bishops_same_colour_only(self):
        self.assertTrue(RULES.insufficient_material(parse_fen("4k3/8/8/2b5/8/8/5B2/4K3 w - - 0 1")))
        self.assertFalse(RULES.insufficient_material(parse_fen("4k3/8/8/3b4/8/8/5B2/4K3 w - - 0 1")))
        self.assertFalse(RULES.insufficient_material(parse_fen("4k3/8/8/3n4/8/8/5B2/4K3 w - - 0 1")))
        self.assertFalse(RULES.insufficient_material(parse_fen("4k3/8/8/8/8/8/2NN4/4K3 w - - 0 1")))

    def test_castling_rights_lost_when_rook_is_captured(self):
        game = ChessGame(parse_fen("r3k2r/8/8/8/8/8/6b1/R3K2R b KQkq - 0 1"))
        game.play(Move.from_uci("g2h1"))
        self.assertEqual(to_fen(game.state).split()[2], "Qkq")
        game.undo()
        self.assertEqual(to_fen(game.state).split()[2], "KQkq")

    def test_square_helpers(self):
        self.assertEqual(parse_square("h8"), 63)


if __name__ == "__main__":
    unittest.main()
