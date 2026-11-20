"""Focused acceptance tests for the original, headless chess rules domain."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from chess_and_chains.chess import (
    ChessGame,
    ChessRules,
    Color,
    DrawClaim,
    FenError,
    GameStatus,
    IllegalMoveError,
    Move,
    PieceType,
    export_pgn,
    parse_fen,
    parse_pgn,
    parse_square,
    to_fen,
)
from chess_and_chains.chess.notation import parse_san, to_san

RULES = ChessRules()


class ChessCoreTests(unittest.TestCase):
    def test_initial_position_perft(self):
        state = parse_fen(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        self.assertEqual([RULES.perft(state, depth) for depth in range(5)], [1, 20, 400, 8902, 197281])

    def test_reference_perft_positions(self):
        positions = (
            (
                "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
                97862,
            ),
            ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 2812),
            ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 9467),
            ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 62379),
            ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 89890),
        )
        for fen, expected in positions:
            with self.subTest(fen=fen):
                self.assertEqual(RULES.perft(parse_fen(fen), 3), expected)

    def test_fen_round_trip_and_validation(self):
        fen = "r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 7 12"
        self.assertEqual(to_fen(parse_fen(fen)), fen)
        with self.assertRaises(FenError):
            parse_fen("8/8/8/8/8/8/8/4K3 w - - 0 1")
        with self.assertRaises(FenError):
            parse_fen("4k3/8/8/8/8/8/8/P3K3 w - - 0 1")

    def test_castling_requires_clear_unattacked_path_and_updates_rook(self):
        state = parse_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        game = ChessGame(state)
        self.assertIn(Move.from_uci("e1g1"), RULES.legal_moves(state))
        after = game.play_uci("e1g1")
        self.assertEqual(after.board[parse_square("f1")].kind, PieceType.ROOK)
        self.assertEqual(after.board[parse_square("h1")], None)
        self.assertEqual(to_fen(after), "r3k2r/8/8/8/8/8/8/R4RK1 b kq - 1 1")
        attacked = parse_fen("r3k2r/8/8/8/8/5r2/8/R3K2R w KQkq - 0 1")
        self.assertNotIn(Move.from_uci("e1g1"), RULES.legal_moves(attacked))

    def test_en_passant_and_discovered_check(self):
        state = parse_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2")
        game = ChessGame(state)
        after = game.play_uci("e5d6")
        self.assertEqual(after.board[parse_square("d5")], None)
        self.assertEqual(after.board[parse_square("d6")].kind, PieceType.PAWN)
        pinned = parse_fen("k7/8/8/4KPpr/8/8/8/8 w - g6 0 1")
        self.assertNotIn(Move.from_uci("f5g6"), RULES.legal_moves(pinned))

    def test_all_promotions_and_king_safety(self):
        state = parse_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        promotions = [move for move in RULES.legal_moves(state) if move.from_square == parse_square("a7")]
        self.assertEqual({move.promotion for move in promotions}, {
            PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT
        })
        self.assertEqual(to_san(state, Move.from_uci("a7a8q")), "a8=Q+")
        self.assertEqual(parse_san(state, "a8=Q+"), Move.from_uci("a7a8q"))

    def test_checkmate_stalemate_and_insufficient_material(self):
        game = ChessGame()
        for move in ("f2f3", "e7e5", "g2g4", "d8h4"):
            game.play_uci(move)
        self.assertEqual(game.outcome().status, GameStatus.CHECKMATE)
        self.assertEqual(game.outcome().winner, Color.BLACK)
        self.assertEqual(
            ChessGame(parse_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")).outcome().status,
            GameStatus.STALEMATE,
        )
        for fen in (
            "7k/8/8/8/8/8/8/4K3 w - - 0 1",
            "7k/8/8/8/8/8/8/2N1K3 w - - 0 1",
            "5b1k/8/8/8/8/8/8/2B1K3 w - - 0 1",
        ):
            with self.subTest(fen=fen):
                self.assertEqual(
                    ChessGame(parse_fen(fen)).outcome().status,
                    GameStatus.DRAW_INSUFFICIENT_MATERIAL,
                )
        self.assertNotEqual(
            ChessGame(parse_fen("7k/8/8/8/8/8/8/1NN1K3 w - - 0 1")).outcome().status,
            GameStatus.DRAW_INSUFFICIENT_MATERIAL,
        )

    def test_repetition_claim_and_automatic_fivefold(self):
        cycle = ("g1f3", "g8f6", "f3g1", "f6g8")
        claimable = ChessGame()
        for move in cycle * 2:
            claimable.play_uci(move)
        self.assertIn(DrawClaim.THREEFOLD_REPETITION, claimable.outcome().claimable_draws)
        claimable.claim_draw(DrawClaim.THREEFOLD_REPETITION)
        self.assertEqual(claimable.outcome().status, GameStatus.DRAW_CLAIMED)
        automatic = ChessGame()
        for move in cycle * 4:
            automatic.play_uci(move)
        self.assertEqual(automatic.outcome().status, GameStatus.DRAW_FIVEFOLD_REPETITION)

    def test_repetition_key_uses_only_legally_available_en_passant(self):
        no_capture_ep = parse_fen(
            "rnbqkbnr/pppp1ppp/8/4p3/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 2"
        )
        no_ep = parse_fen(
            "rnbqkbnr/pppp1ppp/8/4p3/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 2"
        )
        self.assertEqual(RULES.position_key(no_capture_ep), RULES.position_key(no_ep))
        capture_ep = parse_fen("4k3/8/8/3Pp3/8/8/8/4K3 w - e6 0 2")
        capture_without_ep = parse_fen("4k3/8/8/3Pp3/8/8/8/4K3 w - - 0 2")
        self.assertNotEqual(RULES.position_key(capture_ep), RULES.position_key(capture_without_ep))
        pinned_ep = parse_fen("k7/8/8/4KPpr/8/8/8/8 w - g6 0 1")
        pinned_without_ep = parse_fen("k7/8/8/4KPpr/8/8/8/8 w - - 0 1")
        self.assertEqual(RULES.position_key(pinned_ep), RULES.position_key(pinned_without_ep))

    def test_fifty_move_claim_and_seventy_five_move_automatic_draw(self):
        fen = "4k2r/8/8/8/8/8/8/R3K3 w - - 99 1"
        game = ChessGame(parse_fen(fen))
        game.play_uci("a1a2")
        self.assertIn(DrawClaim.FIFTY_MOVE_RULE, game.outcome().claimable_draws)
        game.claim_draw(DrawClaim.FIFTY_MOVE_RULE)
        self.assertEqual(game.outcome().status, GameStatus.DRAW_CLAIMED)

        prospective = ChessGame(parse_fen(fen))
        before = prospective.state
        prospective.claim_draw(DrawClaim.FIFTY_MOVE_RULE, Move.from_uci("a1a2"))
        self.assertEqual(prospective.state, before)
        self.assertEqual(prospective.outcome().status, GameStatus.DRAW_CLAIMED)

        seventy_five = ChessGame(parse_fen("4k2r/8/8/8/8/8/8/R3K3 w - - 149 75"))
        seventy_five.play_uci("a1a2")
        self.assertEqual(seventy_five.outcome().status, GameStatus.DRAW_SEVENTY_FIVE_MOVE)

        mate_at_seventy_five = ChessGame(
            parse_fen("7k/8/5KQ1/8/8/8/8/8 w - - 149 76")
        )
        mate_at_seventy_five.play_uci("g6g7")
        self.assertEqual(mate_at_seventy_five.outcome().status, GameStatus.CHECKMATE)

    def test_undo_redo_restores_full_state_and_branches_clear_redo(self):
        game = ChessGame()
        start = game.state
        game.play_uci("e2e4")
        after = game.state
        game.play_uci("e7e5")
        game.undo()
        self.assertEqual(game.state, after)
        self.assertEqual(game.moves, [Move.from_uci("e2e4")])
        game.redo()
        self.assertEqual(len(game.moves), 2)
        game.undo()
        game.play_uci("c7c5")
        with self.assertRaisesRegex(ValueError, "no action to redo"):
            game.redo()
        while game.moves:
            game.undo()
        self.assertEqual(game.state, start)

    def test_san_pgn_round_trip_and_ignores_comments_variations(self):
        source = '1. e4{King pawn}e5 (1... c5 $1) 2. Nf3 Nc6 3. Bb5 a6 *'
        document = parse_pgn(source)
        game = document.new_game()
        exported = export_pgn(game)
        imported = parse_pgn(exported)
        self.assertEqual(imported.moves, document.moves)
        self.assertEqual(to_fen(imported.new_game().state), to_fen(game.state))
        self.assertIn("3. Bb5 a6 *", exported)
        custom = ChessGame(parse_fen("4k2r/8/8/8/8/8/8/R3K3 w - - 0 1"))
        custom.play_uci("a1a2")
        custom_pgn = export_pgn(custom)
        self.assertEqual(parse_pgn(custom_pgn).moves, tuple(custom.moves))

    def test_resignation_is_undoable(self):
        game = ChessGame()
        game.resign(Color.WHITE)
        self.assertEqual(game.outcome().status, GameStatus.RESIGNED)
        self.assertEqual(game.outcome().winner, Color.BLACK)
        game.undo()
        self.assertEqual(game.outcome().status, GameStatus.ACTIVE)
        game.redo()
        self.assertEqual(game.outcome().status, GameStatus.RESIGNED)

    def test_san_disambiguation_and_illegal_move_rejection(self):
        state = parse_fen("4k3/8/8/8/8/8/8/1N2KN2 w - - 0 1")
        self.assertEqual(to_san(state, Move.from_uci("b1d2")), "Nbd2")
        self.assertEqual(to_san(state, Move.from_uci("f1d2")), "Nfd2")
        pawn_state = parse_fen("4k3/8/8/8/2p5/1P1P4/8/4K3 w - - 0 1")
        self.assertEqual(to_san(pawn_state, Move.from_uci("b3c4")), "bxc4")
        with self.assertRaises(IllegalMoveError):
            ChessGame().play_uci("e2e5")
        with self.assertRaises(IllegalMoveError):
            Move.from_uci("e2e4x")


if __name__ == "__main__":
    unittest.main()
