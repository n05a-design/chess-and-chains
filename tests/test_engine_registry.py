"""Registry coverage with the project-owned UCI mock and temporary files.

SPDX-License-Identifier: MPL-2.0
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

from chess_and_chains.engines.bot import EngineConfig, EngineConfigError, UCIBot
from chess_and_chains.engines.uci import EngineLaunchError
from chess_and_chains.engines.mock_engine import ENGINE_NAME, OPTIONS
from chess_and_chains.engines.registry import (
    EngineAvailability,
    EngineProfile,
    EngineRegistry,
    inspect_engine,
)


class EngineRegistryTests(unittest.TestCase):
    def test_registration_and_approval_survive_restart_and_removal_revokes_launch(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "registry.sqlite3"
            config = EngineConfig.mock()
            registry = EngineRegistry(path)
            profile = registry.register(config.command[0], arguments=config.command[1:],
                                        options=(("Threads", 1),))
            approval = registry.probe(profile.engine_id)
            self.assertIs(approval.status, EngineAvailability.READY)
            self.assertIn("Chess & Chains", approval.advertised_author)
            self.assertIsNone(approval.advertised_version)
            reopened = EngineRegistry(path)
            self.assertEqual(reopened.profiles(), (profile,))
            self.assertEqual(reopened.last_success(profile.engine_id), approval)
            selected = reopened.launch_configuration(profile.engine_id)
            self.assertEqual(selected.session_reference(), approval.reference())
            bot = UCIBot(selected)
            try:
                self.assertEqual(bot.ensure_started().name, ENGINE_NAME)
            finally:
                bot.close()
            registry.remove(profile.engine_id)
            with patch("chess_and_chains.engines.uci.subprocess.Popen") as spawn:
                with self.assertRaisesRegex(EngineLaunchError, "approval changed"):
                    bot.ensure_started()
                spawn.assert_not_called()
            self.assertTrue(Path(config.command[0]).exists())
            self.assertEqual(EngineRegistry(path).profiles(), ())

    def test_guard_blocks_same_size_binary_replacement_and_changed_resource(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            engine = folder / "fixture.exe"
            resource = folder / "model.dat"
            engine.write_bytes(b"original")
            engine.chmod(0o700)
            resource.write_bytes(b"original")
            registry = EngineRegistry(folder / "registry.sqlite3")
            profile = registry.register(engine, resources=(resource,))
            with patch("chess_and_chains.engines.registry.UCIEngine"):
                registry.probe(profile.engine_id)
            choice = registry.launch_configuration(profile.engine_id)
            bot = UCIBot(choice)
            with patch("chess_and_chains.engines.uci.subprocess.Popen") as spawn:
                resource.write_bytes(b"modified")
                with self.assertRaisesRegex(EngineLaunchError, "resources changed"):
                    bot.ensure_started()
                resource.write_bytes(b"original")
                previous = engine.stat()
                engine.write_bytes(b"modified")
                os.utime(engine, ns=(previous.st_atime_ns, previous.st_mtime_ns))
                with self.assertRaisesRegex(EngineLaunchError, "executable"):
                    bot.ensure_started()
                spawn.assert_not_called()

    def test_benchmark_smoke_keeps_color_pairs_and_ply_limits_unrated(self):
        runner = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_engines.py"
        with TemporaryDirectory() as directory:
            output = Path(directory) / "results.json"
            completed = subprocess.run(
                [sys.executable, str(runner), "--smoke", "--max-plies", "2", "--nodes", "32", "--output", str(output)],
                capture_output=True, text=True, timeout=25,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual([(item["white"], item["black"]) for item in saved["games"]], [(0, 1), (1, 0)])
            self.assertTrue(all(item["kind"] == "ply-limit" and item["result"] == "*" for item in saved["games"]))
            self.assertEqual(output.with_suffix(".pgn").read_text(encoding="utf-8").count('[Result "*"]'), 2)

    def test_registration_is_explicit_and_does_not_launch_programs(self):
        config = EngineConfig.mock()
        registry = EngineRegistry()
        with patch("chess_and_chains.engines.registry.UCIEngine") as engine:
            first = registry.register(Path(config.command[0]), display_name="First", license_id="MPL-2.0")
            second = registry.register(Path(config.command[0]), display_name="Second", declared_version="dev")
        engine.assert_not_called()
        self.assertNotEqual(first.engine_id, second.engine_id)
        self.assertEqual(registry.profiles(), (first, second))
        self.assertEqual(first.license_id, "MPL-2.0")
        self.assertEqual(second.declared_version, "dev")
        self.assertIs(registry.availability(first.engine_id), EngineAvailability.UNTESTED)
        self.assertIsNone(registry.last_success(first.engine_id))
        with self.assertRaises(EngineConfigError):
            registry.verified_configuration(first.engine_id)
        with self.assertRaises(EngineConfigError):
            registry.register("just-a-command")

    def test_explicit_worker_probe_identifies_actual_file_and_options(self):
        config = EngineConfig.mock()
        path, *arguments = config.command
        registry = EngineRegistry()
        profile = registry.register(path, arguments=tuple(arguments), display_name="Probe fixture")
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(registry.probe, profile.engine_id).result(timeout=10)
        self.assertIs(result.status, EngineAvailability.READY)
        self.assertEqual(result.resolved_executable, Path(path).resolve())
        self.assertIsNotNone(result.checked_at.utcoffset())
        self.assertEqual(result.advertised_name, ENGINE_NAME)
        self.assertEqual(len(result.options), len(OPTIONS))
        self.assertEqual(result.option("threads").kind, "spin")
        self.assertIsNone(result.option("unsupported"))
        with Path(path).open("rb") as binary:
            self.assertEqual(result.binary_sha256, hashlib.file_digest(binary, "sha256").hexdigest())
        self.assertEqual(registry.last_success(profile.engine_id), result)
        engine = registry.verified_configuration(profile.engine_id)
        self.assertEqual(engine.command, (str(result.resolved_executable), *arguments))

    def test_missing_file_and_crash_have_explicit_status(self):
        registry = EngineRegistry()
        with TemporaryDirectory() as directory:
            profile = registry.register(Path(directory) / "missing.exe")
            result = registry.probe(profile.engine_id)
        self.assertIs(result.status, EngineAvailability.UNAVAILABLE)
        self.assertIsNone(result.binary_sha256)
        self.assertIsNotNone(result.error)
        crash = inspect_engine(EngineProfile.from_config(EngineConfig.mock("crash-on-ready")))
        self.assertIs(crash.status, EngineAvailability.ERROR)
        self.assertIsNotNone(crash.binary_sha256)
        self.assertIsNotNone(crash.error)

    def test_changed_executable_requires_another_probe(self):
        registry = EngineRegistry()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.exe"
            path.write_bytes(b"first version")
            path.chmod(0o700)
            profile = registry.register(path)
            with patch("chess_and_chains.engines.registry.UCIEngine"):
                initial = registry.probe(profile.engine_id)
                self.assertIs(initial.status, EngineAvailability.READY)
                self.assertEqual(registry.verified_configuration(profile.engine_id).command, (str(path.resolve()),))
                path.write_bytes(b"second version")
                with self.assertRaisesRegex(EngineConfigError, "changed"):
                    registry.verified_configuration(profile.engine_id)
                path.unlink()
                self.assertIs(registry.probe(profile.engine_id).status, EngineAvailability.UNAVAILABLE)
        self.assertEqual(registry.last_success(profile.engine_id), initial)

    def test_change_during_handshake_is_not_recorded_as_success(self):
        registry = EngineRegistry()
        with TemporaryDirectory() as directory, patch("chess_and_chains.engines.registry.UCIEngine") as engine:
            path = Path(directory) / "fixture.exe"
            path.write_bytes(b"first version")
            path.chmod(0o700)
            profile = registry.register(path)
            engine.return_value.__enter__.return_value.is_ready.side_effect = lambda: path.write_bytes(b"changed")
            result = registry.probe(profile.engine_id)
        self.assertIs(result.status, EngineAvailability.CHANGED)
        self.assertIsNone(registry.last_success(profile.engine_id))

    def test_only_one_check_per_profile_runs_at_a_time(self):
        config = EngineConfig.mock()
        registry = EngineRegistry()
        profile = registry.register(config.command[0], arguments=config.command[1:])
        active = threading.Event()
        release = threading.Event()

        def block(profile, *, timeout):
            active.set()
            self.assertTrue(release.wait(timeout))
            return inspect_engine(profile, timeout=timeout)

        with patch("chess_and_chains.engines.registry.inspect_engine", side_effect=block):
            with ThreadPoolExecutor(max_workers=1) as pool:
                task = pool.submit(registry.probe, profile.engine_id)
                try:
                    self.assertTrue(active.wait(5))
                    self.assertIs(registry.availability(profile.engine_id), EngineAvailability.BUSY)
                    with self.assertRaisesRegex(EngineConfigError, "in progress"):
                        registry.probe(profile.engine_id)
                finally:
                    release.set()
                self.assertIs(task.result(timeout=10).status, EngineAvailability.READY)
