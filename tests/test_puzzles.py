"""Puzzle model, streaming importer, packs and solving session.

Fixtures are project-authored positions in Lichess CSV layout; no Lichess
data is stored in the repository.
"""
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.chess import Color, Move, parse_fen, to_fen  # noqa: E402
from chess_and_chains.puzzles import (  # noqa: E402
    ImportReport,
    PackError,
    PuzzleImportError,
    PuzzleSession,
    ValidationStatus,
    Verdict,
    import_lichess_file,
    iter_lichess_csv,
    load_demo_pack,
    read_pack,
    write_pack,
)

FIXTURE = ROOT / "tests" / "fixtures" / "puzzles_sample.csv"
HEADER = "PuzzleId,FEN,Moves,Rating,RatingDeviation,Popularity,NbPlays,Themes,GameUrl,OpeningTags\n"


def parse(text: str, **kwargs):
    report = ImportReport("inline", kwargs.pop("min_rating", 1000), kwargs.pop("max_rating", None))
    puzzles = list(iter_lichess_csv(io.BytesIO(text.encode()), report, **kwargs))
    return puzzles, report


class ImporterTests(unittest.TestCase):
    def test_fixture_import_accepts_valid_and_reports_each_rejection(self):
        puzzles, report = import_lichess_file(FIXTURE)
        ids = [p.puzzle_id for p in puzzles]
        self.assertEqual(ids, ["ccBR01", "ccSC01", "ccFM01", "ccQB01", "ccSM02", "quote1"])
        self.assertEqual(report.rows_read, 15)
        self.assertEqual(report.accepted, 6)
        self.assertEqual(dict(report.rejected), {
            "below_min_rating": 1, "duplicate_id": 1, "bad_fen": 1, "bad_uci": 1,
            "illegal_move": 1, "bad_move_count": 1, "bad_number": 1, "column_count": 1,
            "number_out_of_range": 1,
        })
        self.assertTrue(report.complete)
        self.assertEqual(report.input_sha256, hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertTrue(all(p.validation is ValidationStatus.VALID for p in puzzles))
        self.assertEqual(puzzles[-1].opening_tags, ("Some_Opening",))

    def test_rating_minimum_1000_is_enforced(self):
        puzzles, _ = import_lichess_file(FIXTURE)
        self.assertTrue(all(p.rating >= 1000 for p in puzzles))
        with self.assertRaises(PuzzleImportError):
            import_lichess_file(FIXTURE, min_rating=999)
        puzzles, report = import_lichess_file(FIXTURE, min_rating=1200)
        self.assertEqual([p.puzzle_id for p in puzzles], ["ccSM02", "quote1"])
        # Regression: a duplicate id stays a duplicate even if its first row was filtered.
        self.assertEqual(report.rejected["duplicate_id"], 1)

    def test_max_rating_and_limit_stop_streaming_early(self):
        _, report = import_lichess_file(FIXTURE, max_rating=1000)
        self.assertEqual(report.accepted, 3)
        puzzles, report = import_lichess_file(FIXTURE, limit=2)
        self.assertEqual(len(puzzles), 2)
        self.assertFalse(report.complete)
        self.assertIsNone(report.to_dict()["input_sha256"])

    def test_streaming_does_not_require_full_file(self):
        """A generator consumer can stop after the first puzzle of a huge stream."""
        body = HEADER + "ccBR01,6k1/p4ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1,a7a6 d1d8,1000,0,0,0,mate,,\n"

        class Endless(io.RawIOBase):
            def __init__(self):
                self.head = body.encode()
                self.served = 0

            def readable(self):
                return True

            def readinto(self, buf):
                chunk = self.head if self.served == 0 else b"x" * len(buf)
                n = min(len(buf), len(chunk))
                buf[:n] = chunk[:n]
                self.served += n
                return n

        stream = Endless()
        report = ImportReport("endless", 1000, None)
        first = next(iter_lichess_csv(stream, report))
        self.assertEqual(first.puzzle_id, "ccBR01")
        self.assertLess(stream.served, 1 << 20)

    def test_bad_header_and_encoding(self):
        with self.assertRaises(PuzzleImportError):
            parse("a,b,c\n")
        with self.assertRaises(PuzzleImportError):
            parse("")
        report = ImportReport("bin", 1000, None)
        with self.assertRaises(PuzzleImportError):
            list(iter_lichess_csv(io.BytesIO(b"\xff\xfe\x00bad"), report))

    def test_bom_header_is_accepted(self):
        text = "﻿" + HEADER + "ccBR01,6k1/p4ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1,a7a6 d1d8,1000,0,0,0,mate,,\n"
        puzzles, _ = parse(text)
        self.assertEqual(len(puzzles), 1)


class LichessSemanticsRegressionTests(unittest.TestCase):
    def test_first_uci_move_is_opponent_setup_and_applied_before_solving(self):
        puzzle = load_demo_pack().puzzles[0]  # ccBR01: FEN has Black to move
        self.assertEqual(puzzle.initial_state().turn, Color.BLACK)
        self.assertEqual(puzzle.setup_move, Move.from_uci("a7a6"))
        self.assertEqual(puzzle.player_color, Color.WHITE)
        session = PuzzleSession(puzzle)
        self.assertEqual(session.state.turn, Color.WHITE)
        self.assertEqual(session.last_move, Move.from_uci("a7a6"))
        self.assertIsNone(parse_fen(to_fen(session.state)).piece_at(48))  # a7 empty
        self.assertEqual(session.expected_move, Move.from_uci("d1d8"))

    def test_presenting_raw_fen_would_be_wrong(self):
        puzzle = load_demo_pack().puzzles[0]
        self.assertNotEqual(to_fen(puzzle.start_state()), puzzle.fen)
        self.assertNotIn(puzzle.solution[0], PuzzleSession(puzzle).game.rules.legal_moves(puzzle.initial_state()))


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.pack = load_demo_pack()
        self.by_id = {p.puzzle_id: p for p in self.pack.puzzles}

    def test_mate_in_two_flow_with_scripted_reply(self):
        session = PuzzleSession(self.by_id["ccSM02"])
        self.assertEqual(session.submit(Move.from_uci("a1a2")).verdict, Verdict.ILLEGAL)
        self.assertEqual(session.submit(Move.from_uci("c4c8")).verdict, Verdict.WRONG)
        self.assertEqual(session.mistakes, 1)
        feedback = session.submit(Move.from_uci("c4g8"))
        self.assertEqual(feedback.verdict, Verdict.CORRECT)
        self.assertEqual(feedback.reply, Move.from_uci("f8g8"))
        feedback = session.submit(Move.from_uci("h6f7"))
        self.assertEqual(feedback.verdict, Verdict.SOLVED)
        self.assertTrue(session.solved)
        self.assertFalse(session.clean_solve)
        self.assertIsNotNone(session.duration_ms)
        with self.assertRaises(Exception):
            session.submit(Move.from_uci("g1f1"))

    def test_alternative_mate_on_final_move_is_accepted(self):
        from chess_and_chains.puzzles.model import Puzzle

        # Two different back-rank mates: Rb8# (listed) and Rc8# (alternative).
        puzzle = Puzzle("alt001", "6k1/p4ppp/8/8/8/8/5PPP/1RR3K1 b - - 0 1", Move.from_uci("a7a6"),
                        (Move.from_uci("b1b8"),), 1200, 0, 0, 0, ("mateIn1",), "test",
                        validation=ValidationStatus.VALID)
        session = PuzzleSession(puzzle)
        feedback = session.submit(Move.from_uci("c1c7"))  # legal, not mate
        self.assertEqual(feedback.verdict, Verdict.WRONG)
        feedback = PuzzleSession(puzzle).submit(Move.from_uci("c1c8"))
        self.assertEqual(feedback.verdict, Verdict.SOLVED)
        self.assertTrue(feedback.alternative)

    def test_hint_and_reveal(self):
        session = PuzzleSession(self.by_id["ccSC01"])
        self.assertEqual(session.hint(), Move.from_uci("h5f7").from_square)
        self.assertEqual(session.reveal(), (Move.from_uci("h5f7"),))
        self.assertTrue(session.finished)
        self.assertFalse(session.solved)
        self.assertEqual(session.legal_moves(), ())

    def test_black_to_solve(self):
        session = PuzzleSession(self.by_id["ccFM01"])
        self.assertEqual(session.player_color, Color.BLACK)
        self.assertEqual(session.submit(Move.from_uci("d8h4")).verdict, Verdict.SOLVED)
        self.assertTrue(session.clean_solve)


class PackTests(unittest.TestCase):
    def test_demo_pack_is_marked_demo_and_valid(self):
        pack = load_demo_pack()
        self.assertTrue(pack.manifest.demo)
        self.assertEqual(pack.manifest.count, 5)
        self.assertIn("not measured", pack.manifest.license_note)
        self.assertGreaterEqual(pack.manifest.min_rating, 1000)

    def test_round_trip_and_tamper_detection(self):
        puzzles, report = import_lichess_file(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "pack"
            manifest = write_pack(directory, puzzles, pack_id="test-pack", version="1",
                                  source="fixture", license_note="test", report=report)
            pack = read_pack(directory)
            self.assertEqual([p.puzzle_id for p in pack.puzzles], [p.puzzle_id for p in puzzles])
            self.assertEqual(pack.manifest.sha256, manifest.sha256)
            self.assertTrue((directory / "import_report.json").is_file())
            self.assertEqual(json.loads((directory / "import_report.json").read_text())["accepted"], 6)
            body = (directory / "puzzles.jsonl").read_text().replace('"rating": 1000', '"rating": 1001', 1)
            (directory / "puzzles.jsonl").write_text(body)
            with self.assertRaises(PackError):
                read_pack(directory)

    def test_pack_contract_rejects_bad_input(self):
        puzzles, _ = import_lichess_file(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PackError):
                write_pack(Path(tmp), puzzles + puzzles[:1], pack_id="dup", version="1", source="s", license_note="l")
            with self.assertRaises(PackError):
                write_pack(Path(tmp), puzzles, pack_id="Bad Id", version="1", source="s", license_note="l")
            from dataclasses import replace
            low = replace(puzzles[0], rating=900)
            with self.assertRaises(PackError):
                write_pack(Path(tmp), [low], pack_id="low", version="1", source="s", license_note="l")
            with self.assertRaises(PackError):
                read_pack(Path(tmp) / "missing")


if __name__ == "__main__":
    unittest.main()
