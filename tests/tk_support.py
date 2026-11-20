"""Shared Tk root creation: skip locally without a display, fail in CI GUI jobs."""
import os
import tkinter as tk

REQUIRE_DISPLAY = os.environ.get("CHESS_AND_CHAINS_REQUIRE_DISPLAY") == "1"


def create_root(testcase) -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        if REQUIRE_DISPLAY:
            raise AssertionError(f"Tk display required but unavailable: {error}") from error
        testcase.skipTest(f"Tk display unavailable: {error}")
    root.withdraw()
    return root
