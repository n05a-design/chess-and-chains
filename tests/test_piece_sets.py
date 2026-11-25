"""Comprehensive tests for Chess & Chains piece set registry, assets, and live switching.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from chess_and_chains.__main__ import main as cli_main
from chess_and_chains.chess import Color, Move, Piece, PieceType, to_fen
from chess_and_chains.game import GameController, GameSetup
from chess_and_chains.storage.settings import DEFAULT_PIECE_SET, PIECE_SET_CHOICES, Settings, load_settings, save_settings
from chess_and_chains.ui.piece_contract import validate_svg_piece_set
from chess_and_chains.ui.pieces import (
    PIECE_FILE_NAMES,
    PIECE_SETS,
    OwnerSvgPieces,
    get_piece_set,
    list_piece_sets,
)


class TestPieceSetRegistry:
    """Tests for central piece set registry."""

    def test_list_piece_sets_contains_all_three(self) -> None:
        sets = list_piece_sets()
        set_ids = [s.set_id for s in sets]
        assert set_ids == ["original", "top", "classic"]

    def test_registered_metadata(self) -> None:
        orig = get_piece_set("original")
        assert orig.set_id == "original"
        assert orig.asset_version == "V.06"
        assert orig.display_name("de") == "Original"
        assert orig.display_name("en") == "Original"
        assert orig.perspective == "front"

        top = get_piece_set("top")
        assert top.set_id == "top"
        assert top.asset_version == "V.04.2"
        assert top.display_name("de") == "Draufsicht"
        assert top.display_name("en") == "Top view"
        assert top.perspective == "top"

        classic = get_piece_set("classic")
        assert classic.set_id == "classic"
        assert classic.asset_version == "V.05.1"
        assert classic.display_name("de") == "Klassisch"
        assert classic.display_name("en") == "Classic"
        assert classic.perspective == "front"

    def test_get_piece_set_fallbacks(self) -> None:
        assert get_piece_set(None).set_id == "original"
        assert get_piece_set("unknown_set_xyz").set_id == "original"
        assert get_piece_set("front").set_id == "original"
        assert get_piece_set("top").set_id == "top"


class TestAssetContract:
    """Tests for SVG asset compliance and provenance."""

    def test_all_sets_pass_svg_contract(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / "src" / "chess_and_chains" / "ui" / "piece_assets"

        for subdir in ["", "original", "top", "classic"]:
            target_dir = root_dir / subdir if subdir else root_dir
            report = validate_svg_piece_set(target_dir)
            assert report.ok, f"Contract validation failed for {subdir}: {report.problems}"

    def test_fallback_png_atlases_exist(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / "src" / "chess_and_chains" / "ui" / "piece_assets"

        for subdir in ["", "original", "top", "classic"]:
            target_file = (root_dir / subdir / "fallback.png") if subdir else (root_dir / "fallback.png")
            assert target_file.exists(), f"Missing fallback.png in {subdir}"
            assert target_file.stat().st_size > 50000

    def test_provenance_files_exist(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / "src" / "chess_and_chains" / "ui" / "piece_assets"

        for subdir in ["original", "top", "classic"]:
            prov_file = root_dir / subdir / "PROVENANCE.md"
            assert prov_file.exists(), f"Missing PROVENANCE.md in {subdir}"
            content = prov_file.read_text(encoding="utf-8")
            assert "MPL-2.0" in content or "Owner" in content


class TestSettingsMigration:
    """Tests for settings persistence and backward compatibility."""

    def test_settings_validation(self) -> None:
        settings = Settings()
        assert settings.piece_set == "original"
        assert settings.piece_view == "front"

        s2 = Settings(piece_set="classic", piece_view="front")
        s2.validate()

        s3 = Settings(piece_set="top", piece_view="top")
        s3.validate()

        with pytest.raises(ValueError):
            bad = Settings(piece_set="nonexistent")
            bad.validate()

    def test_migration_from_legacy_piece_view(self, tmp_path: Path) -> None:
        # 1. Legacy file with only piece_view="top"
        legacy_top = tmp_path / "top_settings.json"
        legacy_top.write_text(json.dumps({"piece_view": "top"}), encoding="utf-8")
        s_top, warn_top = load_settings(legacy_top)
        assert s_top.piece_set == "top"
        assert s_top.piece_view == "top"

        # 2. Legacy file with only piece_view="front"
        legacy_front = tmp_path / "front_settings.json"
        legacy_front.write_text(json.dumps({"piece_view": "front"}), encoding="utf-8")
        s_front, warn_front = load_settings(legacy_front)
        assert s_front.piece_set == "original"
        assert s_front.piece_view == "front"

        # 3. New file with piece_set="classic"
        new_classic = tmp_path / "classic_settings.json"
        save_settings(new_classic, Settings(piece_set="classic", piece_view="front"))
        s_classic, _ = load_settings(new_classic)
        assert s_classic.piece_set == "classic"


class TestCLIArguments:
    """Tests for CLI options."""

    def test_headless_check_with_piece_set(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = cli_main(["--headless-check", "--piece-set", "classic"])
        assert code == 0
        captured = capsys.readouterr().out
        assert "Chess & Chains" in captured

    def test_headless_check_with_legacy_piece_view(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = cli_main(["--headless-check", "--piece-view", "top"])
        assert code == 0


class TestLiveSwitchingInvariance:
    """Verify that switching piece set does not alter game state."""

    def test_game_controller_invariance(self) -> None:
        gc = GameController()
        gc.new_game(GameSetup.two_players())
        gc.play_human(Move.from_uci("e2e4"))
        view_before = gc.view()
        fen_before = to_fen(view_before.state)
        san_before = view_before.san_moves

        # Simulate piece set switch
        renderer = OwnerSvgPieces(piece_set="original")
        assert renderer.piece_set == "original"

        renderer.set_piece_set("classic")
        assert renderer.piece_set == "classic"

        renderer.set_piece_set("top")
        assert renderer.piece_set == "top"

        # Check domain model invariance
        view_after = gc.view()
        assert to_fen(view_after.state) == fen_before
        assert view_after.san_moves == san_before

        # Undo / redo still authoritative
        gc.undo()
        assert len(gc.view().san_moves) == 0
        gc.redo()
        assert gc.view().san_moves == san_before
        gc.shutdown()
