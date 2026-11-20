"""Own each test's Tk root and clean it up on the Tk thread."""
import gc
import os
import tkinter as tk

REQUIRE_DISPLAY = os.environ.get("CHESS_AND_CHAINS_REQUIRE_DISPLAY") == "1"


def _destroy_root(root: tk.Tk) -> None:
    try:
        exists = root.winfo_exists()
    except tk.TclError:
        return  # ChessApp.close() may already have destroyed this root.
    if exists:
        root.destroy()


def create_root(testcase) -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        if REQUIRE_DISPLAY:
            raise AssertionError(f"Tk display required but unavailable: {error}") from error
        testcase.skipTest(f"Tk display unavailable: {error}")
    # Cleanups are LIFO. Close the app and destroy the root before collecting
    # widget cycles, so a later bot thread cannot finalize Tk objects from this test.
    testcase.addCleanup(gc.collect)
    testcase.addCleanup(_destroy_root, root)
    root.withdraw()
    return root
