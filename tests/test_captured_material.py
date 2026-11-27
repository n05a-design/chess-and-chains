"""Unit tests for captured pieces and material advantage calculations."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.chess import (  # noqa: E402
    CapturedGroup,
    CapturedMaterial,
    ChessGame,
    Color,
    GameState,
    Move,
    Piece,
    PieceType,
    calculate_captured_material,
    parse_fen,
    parse_pgn,
)
from chess_and_chains.game import GameController, GameSetup  # noqa: E402


class CapturedMaterialTests(unittest.TestCase):
    def test_01_no_captures_initial_position(self) -> None:
        """Keine geschlagenen Figuren: keine Punktzahl und leere Gruppen."""
        game = ChessGame()
        material = game.captured_material()
        self.assertEqual(material.white_score, 0)
        self.assertEqual(material.black_score, 0)
        self.assertEqual(material.difference, 0)
        self.assertIsNone(material.white_advantage)
        self.assertIsNone(material.black_advantage)
        self.assertEqual(material.white.captures, ())
        self.assertEqual(material.black.captures, ())
        self.assertEqual(material.white.groups, ())
        self.assertEqual(material.black.groups, ())

    def test_02_white_captures_pawn(self) -> None:
        """Weiß schlägt einen Bauern: Weiß +1, Schwarz keine Punktzahl."""
        # 1. e4 d5 2. exd5
        game = ChessGame()
        game.play_uci("e2e4")
        game.play_uci("d7d5")
        game.play_uci("e4d5")

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 1)
        self.assertEqual(mat.black_score, 0)
        self.assertEqual(mat.difference, 1)
        self.assertEqual(mat.white_advantage, 1)
        self.assertIsNone(mat.black_advantage)

        self.assertEqual(len(mat.white.captures), 1)
        self.assertEqual(mat.white.captures[0], Piece(Color.BLACK, PieceType.PAWN))
        self.assertEqual(mat.white.groups, (CapturedGroup(Piece(Color.BLACK, PieceType.PAWN), 1),))
        self.assertEqual(mat.black.captures, ())
        self.assertEqual(mat.black.groups, ())

    def test_03_white_pawn_black_bishop(self) -> None:
        """Weiß schlägt einen Bauern (1), Schwarz einen Läufer (3): Schwarz +2, Weiß keine Punktzahl."""
        # FEN with pawns on a-file so position does not trigger insufficient material draw
        fen = "4k3/p7/8/3p4/4B3/5b2/P7/4K3 w - - 0 1"
        game = ChessGame(parse_fen(fen))
        game.play_uci("e4d5")  # White bishop captures Black pawn -> White: 1 pt
        game.play_uci("f3d5")  # Black bishop captures White bishop -> Black: 3 pts

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 1)
        self.assertEqual(mat.black_score, 3)
        self.assertEqual(mat.difference, -2)
        self.assertIsNone(mat.white_advantage)
        self.assertEqual(mat.black_advantage, 2)

        # White captured black pawn
        self.assertEqual(mat.white.groups, (CapturedGroup(Piece(Color.BLACK, PieceType.PAWN), 1),))
        # Black captured white bishop
        self.assertEqual(mat.black.groups, (CapturedGroup(Piece(Color.WHITE, PieceType.BISHOP), 1),))

    def test_04_equal_captures_no_advantage(self) -> None:
        """Beide Seiten schlagen gleichwertige Figuren: keine Vorteilspunktzahl."""
        # 1. e4 d5 2. exd5 Qxd5 (Both took 1 pawn)
        game = ChessGame()
        game.play_uci("e2e4")
        game.play_uci("d7d5")
        game.play_uci("e4d5")  # W: 1 (pawn)
        game.play_uci("d8d5")  # B: 1 (pawn)

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 1)
        self.assertEqual(mat.black_score, 1)
        self.assertEqual(mat.difference, 0)
        self.assertIsNone(mat.white_advantage)
        self.assertIsNone(mat.black_advantage)

    def test_05_white_queen_black_rook(self) -> None:
        """Weiß schlägt eine Dame (9), Schwarz einen Turm (5): Weiß +4."""
        # Position: White rook on e1 captures Black queen on e7 (9)
        # Black knight captures White rook on e1 (5)
        # Fen: 4k3/4q3/8/8/8/8/8/4R1K1 w - - 0 1 -> not legal directly, let's create legal FEN
        fen = "4k3/4q3/8/8/8/8/5R2/4R1K1 w - - 0 1"
        game = ChessGame(parse_fen(fen))
        # White plays Rxe7+ (captures Queen -> 9 pts)
        game.play_uci("e1e7")
        # Black plays Kxe7 (captures Rook -> 5 pts)
        game.play_uci("e8e7")

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 9)
        self.assertEqual(mat.black_score, 5)
        self.assertEqual(mat.difference, 4)
        self.assertEqual(mat.white_advantage, 4)
        self.assertIsNone(mat.black_advantage)

    def test_06_en_passant(self) -> None:
        """En passant Schlagzug erfasst den geschlagenen Bauern korrekt."""
        # 1. e4 a6 2. e5 d5 3. exd6 (e.p.)
        game = ChessGame()
        game.play_uci("e2e4")
        game.play_uci("a7a6")
        game.play_uci("e4e5")
        game.play_uci("d7d5")
        game.play_uci("e5d6")  # en passant capture of d5 pawn!

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 1)
        self.assertEqual(mat.black_score, 0)
        self.assertEqual(mat.white_advantage, 1)
        self.assertIsNone(mat.black_advantage)
        self.assertEqual(len(mat.white.captures), 1)
        self.assertEqual(mat.white.captures[0], Piece(Color.BLACK, PieceType.PAWN))

    def test_07_quiet_promotion_scores_zero_captures(self) -> None:
        """Eine Bauernumwandlung allein darf keine Punkte für geschlagene Figuren erzeugen."""
        # FEN with white pawn on a7, moving to a8=Q
        fen = "7k/P7/8/8/8/8/8/7K w - - 0 1"
        game = ChessGame(parse_fen(fen))
        game.play_uci("a7a8q")

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 0)
        self.assertEqual(mat.black_score, 0)
        self.assertEqual(mat.difference, 0)
        self.assertIsNone(mat.white_advantage)
        self.assertIsNone(mat.black_advantage)
        self.assertEqual(mat.white.captures, ())

    def test_08_capture_promotion(self) -> None:
        """Schlagumwandlung: erfasst die tatsächlich geschlagene Figur (z.B. Läufer 3 Pkt)."""
        # White pawn on a7, black bishop on b8
        fen = "1b5k/P7/8/8/8/8/8/7K w - - 0 1"
        game = ChessGame(parse_fen(fen))
        game.play_uci("a7b8q")  # captures bishop on b8 and promotes to Queen

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 3)  # Bishop = 3 pts
        self.assertEqual(mat.black_score, 0)
        self.assertEqual(mat.white_advantage, 3)
        self.assertEqual(mat.white.groups, (CapturedGroup(Piece(Color.BLACK, PieceType.BISHOP), 1),))

    def test_09_capture_of_promoted_piece(self) -> None:
        """Geschlagene zuvor umgewandelte Dame gibt dem schlagenden Spieler 9 Punkte."""
        fen = "1r5k/P7/8/8/8/8/8/7K w - - 0 1"
        game = ChessGame(parse_fen(fen))
        game.play_uci("a7a8q")  # 1. a8=Q (White promotes)
        game.play_uci("b8a8")  # Black rook captures promoted Queen on a8!

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 0)
        self.assertEqual(mat.black_score, 9)  # Captured a Queen = 9 points!
        self.assertEqual(mat.black_advantage, 9)
        self.assertIsNone(mat.white_advantage)
        self.assertEqual(mat.black.groups, (CapturedGroup(Piece(Color.WHITE, PieceType.QUEEN), 1),))

    def test_10_undo_and_redo_capture(self) -> None:
        """Undo und Redo eines Schlagzugs aktualisieren Materialanzeige präzise."""
        game = ChessGame()
        game.play_uci("e2e4")
        game.play_uci("d7d5")
        game.play_uci("e4d5")  # White captures pawn

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 1)
        self.assertEqual(mat.white_advantage, 1)

        # Undo the capture
        game.undo()
        mat_undone = game.captured_material()
        self.assertEqual(mat_undone.white_score, 0)
        self.assertEqual(mat_undone.black_score, 0)
        self.assertIsNone(mat_undone.white_advantage)
        self.assertEqual(mat_undone.white.captures, ())

        # Redo the capture
        game.redo()
        mat_redone = game.captured_material()
        self.assertEqual(mat_redone.white_score, 1)
        self.assertEqual(mat_redone.white_advantage, 1)
        self.assertEqual(len(mat_redone.white.captures), 1)

    def test_11_imported_fen_starts_empty(self) -> None:
        """FEN ohne historische Züge beginnt mit leerer Anzeige; neue Züge werden erfasst."""
        # FEN with several missing pieces
        fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 4 4"
        game = ChessGame(parse_fen(fen))

        mat = game.captured_material()
        self.assertEqual(mat.white_score, 0)
        self.assertEqual(mat.black_score, 0)
        self.assertEqual(mat.difference, 0)
        self.assertIsNone(mat.white_advantage)
        self.assertIsNone(mat.black_advantage)

        # Play Bxf7+
        game.play_uci("c4f7")
        mat_after = game.captured_material()
        self.assertEqual(mat_after.white_score, 1)
        self.assertEqual(mat_after.white_advantage, 1)

    def test_12_pgn_import(self) -> None:
        """Import einer PGN-Partie berechnet geschlagene Figuren exakt."""
        pgn_text = """[Event "Test Game"]
[Site "Local"]
[Date "2026.11.24"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "*"]

1. e4 d5 2. exd5 Qxd5 3. Nc3 *
"""
        doc = parse_pgn(pgn_text)
        game = doc.new_game()
        mat = game.captured_material()
        self.assertEqual(mat.white_score, 1)
        self.assertEqual(mat.black_score, 1)
        self.assertEqual(mat.difference, 0)
        self.assertIsNone(mat.white_advantage)
        self.assertIsNone(mat.black_advantage)

    def test_13_game_controller_new_game_reset(self) -> None:
        """Controller new_game setzt Materialstand vollständig zurück."""
        ctrl = GameController()
        ctrl.play_human(Move.from_uci("e2e4"))
        ctrl.play_human(Move.from_uci("d7d5"))
        ctrl.play_human(Move.from_uci("e4d5"))

        view = ctrl.view()
        self.assertIsNotNone(view.captured_material)
        assert view.captured_material is not None
        self.assertEqual(view.captured_material.white_score, 1)

        # New game
        ctrl.new_game(GameSetup.two_players())
        view_reset = ctrl.view()
        self.assertIsNotNone(view_reset.captured_material)
        assert view_reset.captured_material is not None
        self.assertEqual(view_reset.captured_material.white_score, 0)
        self.assertEqual(view_reset.captured_material.black_score, 0)
        self.assertIsNone(view_reset.captured_material.white_advantage)


if __name__ == "__main__":
    unittest.main()
