"""Exercise Tk's actual macOS FEN file panels and their Cancel actions."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import ctypes as c
import faulthandler
import tkinter as tk

from chess_and_chains.chess import INITIAL_FEN, parse_fen
from chess_and_chains.i18n import Translator
from chess_and_chains.ui.dialogs import PositionDialog


class MacPanels:
    """Send Cancel to the expected AppKit panel on the runner's main thread."""

    def __init__(self) -> None:
        self.appkit = c.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
        self.cf = c.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self.objc = c.CDLL("/usr/lib/libobjc.A.dylib")
        self.get_class = self.objc.objc_getClass
        self.get_class.argtypes, self.get_class.restype = [c.c_char_p], c.c_void_p
        self.selector = self.objc.sel_registerName
        self.selector.argtypes, self.selector.restype = [c.c_char_p], c.c_void_p
        send = c.cast(self.objc.objc_msgSend, c.c_void_p).value
        self.object = c.CFUNCTYPE(c.c_void_p, c.c_void_p, c.c_void_p)(send)
        self.is_kind = c.CFUNCTYPE(c.c_bool, c.c_void_p, c.c_void_p, c.c_void_p)(send)
        self.command = c.CFUNCTYPE(None, c.c_void_p, c.c_void_p, c.c_void_p)(send)

        self.callback_type = c.CFUNCTYPE(None, c.c_void_p, c.c_void_p)
        self.cf.CFAbsoluteTimeGetCurrent.restype = c.c_double
        self.cf.CFRunLoopGetCurrent.restype = c.c_void_p
        self.cf.CFRunLoopTimerCreate.argtypes = [
            c.c_void_p, c.c_double, c.c_double, c.c_ulong, c.c_long, self.callback_type, c.c_void_p,
        ]
        self.cf.CFRunLoopTimerCreate.restype = c.c_void_p
        self.cf.CFRunLoopAddTimer.argtypes = [c.c_void_p, c.c_void_p, c.c_void_p]
        self.cf.CFRunLoopAddTimer.restype = None
        self.cf.CFRunLoopTimerInvalidate.argtypes = [c.c_void_p]
        self.cf.CFRunLoopTimerInvalidate.restype = None
        self.cf.CFRelease.argtypes = [c.c_void_p]
        self.cf.CFRelease.restype = None

    def cancel(self, action, panel_class: bytes) -> None:
        canceled = False
        app = self.object(self.get_class(b"NSApplication"), self.selector(b"sharedApplication"))
        expected = self.get_class(panel_class)

        @self.callback_type
        def close_panel(timer, _context):
            nonlocal canceled
            panel = self.object(app, self.selector(b"modalWindow"))
            if panel and self.is_kind(panel, self.selector(b"isKindOfClass:"), expected):
                self.cf.CFRunLoopTimerInvalidate(timer)
                canceled = True
                self.command(panel, self.selector(b"cancel:"), None)

        start = self.cf.CFAbsoluteTimeGetCurrent() + 0.25
        timer = self.cf.CFRunLoopTimerCreate(None, start, 0.1, 0, 0, close_panel, None)
        if not timer:
            raise RuntimeError("CoreFoundation could not create the file panel timer.")
        try:
            mode = c.c_void_p.in_dll(self.appkit, "NSModalPanelRunLoopMode")
            self.cf.CFRunLoopAddTimer(self.cf.CFRunLoopGetCurrent(), timer, mode)
            action()
        finally:
            self.cf.CFRunLoopTimerInvalidate(timer)
            self.cf.CFRelease(timer)
        if not canceled:
            raise AssertionError(f"{panel_class.decode()} did not open as an AppKit modal.")


def main() -> None:
    faulthandler.dump_traceback_later(25, exit=True)
    root = tk.Tk()
    try:
        if root.tk.call("tk", "windowingsystem") != "aqua":
            raise RuntimeError("Native file-panel probe requires Aqua Tk.")
        print(f"Aqua Tk {root.tk.call('package', 'provide', 'Tk')}", flush=True)
        root.update()
        panels = MacPanels()
        dialog = PositionDialog(root, Translator("en"), parse_fen(INITIAL_FEN), lambda _parent: True)
        root.update()
        for action, panel_class in ((dialog._open, b"NSOpenPanel"), (dialog._save, b"NSSavePanel")):
            panels.cancel(action, panel_class)
            root.update()
            if dialog.draft.get() != INITIAL_FEN or dialog.result is not None:
                raise AssertionError("Cancel changed the FEN draft or accepted a position.")
            if root.grab_current() is not dialog:
                raise AssertionError("Cancel did not return the Tk grab to the FEN dialog.")
            print(f"{panel_class.decode()}: opened and canceled; FEN draft and dialog grab preserved", flush=True)
        dialog.destroy()
    finally:
        root.destroy()
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
