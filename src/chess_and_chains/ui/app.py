"""Offline Tk desktop prototype: two players, bot mode (mock/user engine), puzzles.

The UI never talks to a UCI process directly: all game flow goes through
``game.GameController``; bot searches run on its worker thread and results
are applied by polling on the Tk main thread.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import sqlite3
import threading
import tkinter as tk
from functools import partial
from queue import Empty, SimpleQueue
from weakref import proxy
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Sequence

from .. import DISPLAY_VERSION
from ..chess import ChessError, ChessGame, Color, GameStatus, Move, export_pgn, square_name, to_san
from ..engines.bot import EngineConfig, EngineConfigError, MoveProvider, UCIBot, probe_engine, resolve_engine_config
from ..engines.presets import BotPreset, load_presets
from ..engines.uci import UCIEngineError
from ..game import BotStatus, GameController, GameSetup, GameView, PlayMode
from ..i18n import Translator
from ..puzzles import DEMO_PACK_ID, PackError, PackLibrary, Puzzle, PuzzlePack, PuzzleSession, Verdict, load_demo_pack
from ..storage import Database, DataLayout, Settings, SettingsError, StorageError, load_settings, save_settings
from .atlas import PuzzleAtlas
from .board import BoardCanvas, Orientation
from .board_artwork import BoardArtwork, BoardArtworkError, BoardDesign
from .branding import brand_image
from .dialogs import PositionDialog, bind_button_enter as _bind_button_enter
from .pieces import OwnerSvgPieces, PieceRenderer
from .replay import ReplayDialog
from .text_board import TextBoardDialog
from .theme import (
    ACETATE,
    BRAND_BLUE,
    BUTTON_ROLES,
    CHROME_YELLOW,
    DISABLED_INK,
    FONT_SIZES,
    INK,
    MUTED_INK,
    PAPER,
    SHADOW,
    TAB_IDLE,
    WINDOW,
)

POLL_MS = 40
PUZZLE_RATING_RANGES: tuple[tuple[int, int | None], ...] = (
    (1000, 1199), (1200, 1599), (1600, 1999), (2000, None),
)
ProviderFactory = Callable[[BotPreset, Settings], MoveProvider]


def default_provider_factory(preset: BotPreset, settings: Settings) -> MoveProvider:
    config, _warning = resolve_engine_config(settings.engine_path)
    return UCIBot(config, preset)


class TabRail(tk.Frame):
    """The three workspace views, with native keyboard-focusable controls."""

    def __init__(self, master: tk.Misc, on_change, tabs: Sequence[tuple[str, str]]) -> None:
        super().__init__(master, background=ACETATE)
        self._on_change = on_change
        self._tabs = tuple(name for name, _ in tabs)
        self._active = self._tabs[0]
        for index, (name, label) in enumerate(tabs):
            button = tk.Button(
                self, name=name, text=label, command=lambda tab=name: self.set_active(tab),
                foreground=INK, activeforeground=PAPER, activebackground=INK,
                relief="flat", borderwidth=0, highlightthickness=2, highlightcolor=INK,
                highlightbackground=ACETATE, padx=2, pady=8, takefocus=True,
            )
            self.grid_columnconfigure(index, weight=1)
            button.grid(row=0, column=index, sticky="ew", padx=(0, 3 if index < len(tabs) - 1 else 0))
            button.bind("<Return>", lambda _event, tab=name: self._activate(tab))
            for key, step in (("Left", -1), ("Right", 1), ("Up", -1), ("Down", 1)):
                target = self._tabs[(index + step) % len(self._tabs)]
                button.bind(f"<{key}>", lambda _event, tab=target: self._activate(tab))
        self._paint()

    @property
    def active(self) -> str:
        return self._active

    def _paint(self) -> None:
        for name, button in self.children.items():
            selected = name == self._active
            button.configure(
                background=CHROME_YELLOW if selected else TAB_IDLE,
                font=("TkDefaultFont", FONT_SIZES["caption"], "bold underline" if selected else "normal"),
            )

    def set_active(self, tab: str) -> None:
        if tab not in self._tabs:
            raise ValueError(f"Unknown game panel: {tab}")
        self._active = tab
        self._paint()
        self._on_change(tab)

    def _activate(self, tab: str) -> str:
        self.children[tab].focus_set()
        self.set_active(tab)
        return "break"


class ChessApp:
    def __init__(
        self,
        root: tk.Tk,
        *,
        data_layout: DataLayout | None = None,
        provider_factory: ProviderFactory = default_provider_factory,
        locale: str | None = None,
        puzzle_pack: PuzzlePack | None = None,
        board_artwork: BoardArtwork | None = None,
        piece_renderer: PieceRenderer | None = None,
    ) -> None:
        self.root = root
        self._board_artwork = board_artwork
        self.layout = data_layout
        self.settings_warning: str | None = None
        database_warning: str | None = None
        if data_layout is not None:
            self.settings, self.settings_warning = load_settings(data_layout.settings)
            try:
                self.db: Database | None = Database.open(data_layout.database)
            except StorageError as error:
                # Never modify a database we cannot handle; run without persistence.
                self.db = None
                database_warning = str(error)
        else:
            self.settings, self.db = Settings(), None
        self.t = Translator(locale or self.settings.locale)
        self.presets = load_presets()
        self._provider_factory = provider_factory
        self.controller = GameController()
        self._unsubscribe_view = self.controller.subscribe(self._on_view)
        self.orientation: Orientation = "white"
        self.active_panel = "play"
        self._pack_library = PackLibrary(data_layout.packs) if data_layout is not None else None
        self._pack_results: SimpleQueue[PuzzlePack | str] = SimpleQueue()
        self._pack_loading = False
        self.pack = puzzle_pack or load_demo_pack()
        self._puzzle_selection = self.pack.puzzles
        self._puzzle_themes = sorted({theme for puzzle in self.pack.puzzles for theme in puzzle.themes})
        self.puzzle_index = 0
        self.puzzle: PuzzleSession | None = None
        self._puzzle_recorded = False
        self._puzzle_hint_stage = 0
        self._solved_puzzle_ids: set[str] = set()
        self._review_puzzle_ids: set[str] = set()
        self._provider_stale = False
        self._game_headers: dict[str, str] = {}
        self._closed = False
        self._text_board: TextBoardDialog | None = None
        self.interaction_text = tk.StringVar(root)
        self._board_feedback = ""
        self.panel_text = tk.StringVar(root)
        self.header_mode_text = tk.StringVar(root)
        self.action_state_text = tk.StringVar(root)
        self.bot_text = tk.StringVar(root)
        self.puzzle_title_text = tk.StringVar(root)
        self.puzzle_meta_text = tk.StringVar(root)
        self.puzzle_feedback_text = tk.StringVar(root)
        self.puzzle_progress_text = tk.StringVar(root)
        self.puzzle_history_text = tk.StringVar(root)
        self.puzzle_pack_text = tk.StringVar(root)
        self.puzzle_pack_feedback = tk.StringVar(root)
        self.mode_var = tk.StringVar(root, value=self.settings.play_mode)
        preset_ids = [p.id for p in self.presets]
        initial_preset = self.settings.bot_preset_id if self.settings.bot_preset_id in preset_ids else preset_ids[2]
        self.preset_var = tk.StringVar(root, value=self._preset_label(initial_preset))
        self._wrap_labels: list[tk.Label] = []
        self._build(piece_renderer)
        self._bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._refresh()
        self._poll_job = self.root.after(POLL_MS, self._poll)
        if self.db is not None and self.db.recovered_from is not None:
            database_warning = self.t("library.recovered", file=self.db.recovered_from.name)
        startup_messages = (database_warning, self.settings_warning)
        self.interaction_text.set("\n".join(message for message in startup_messages if message))
        saved_pack = self.settings.last_pack_id
        if puzzle_pack is None and self._pack_library is not None and saved_pack not in (None, DEMO_PACK_ID):
            self._start_pack_task(partial(self._pack_library.load, saved_pack))

    # ----- compatibility with W06 API ---------------------------------
    @property
    def game(self) -> ChessGame:
        return self.controller.game

    @property
    def redo_count(self) -> int:
        return int(self.controller.view().can_redo)

    # ----- construction ------------------------------------------------
    def _build(self, piece_renderer: PieceRenderer | None) -> None:
        t = self.t
        # Child widgets can outlive the window while a worker is winding down.
        app = proxy(self)
        self.root.title(f'{t("app.window_title")} · {DISPLAY_VERSION}')
        self._window_icon = brand_image(self.root, "app-icon")
        self.root.iconphoto(True, self._window_icon)
        self.root.configure(background=WINDOW)
        self.root.geometry("1180x820")
        self.root.minsize(860, 700)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        masthead = tk.Frame(self.root, background=BRAND_BLUE, pady=0)
        masthead.grid(row=0, column=0, sticky="ew")
        header = tk.Frame(masthead, background=PAPER, padx=22, pady=12)
        header.pack(fill="x", pady=(4, 0))
        header.grid_columnconfigure(1, weight=1)
        self._header_signet = brand_image(self.root, "signet", scale=40 / 64)
        self._header_wordmark = brand_image(self.root, "wordmark")
        tk.Label(header, image=self._header_signet, background=PAPER, borderwidth=0).grid(row=0, column=0, sticky="w")
        tk.Label(header, text=t("app.title"), image=self._header_wordmark,
                 background=PAPER, borderwidth=0).grid(row=0, column=1, sticky="w", padx=(10, 0))
        tk.Label(header, textvariable=self.header_mode_text, background=PAPER, foreground=MUTED_INK,
                 font=("TkFixedFont", FONT_SIZES["caption"], "bold"), justify="right", wraplength=350,
                 ).grid(row=0, column=2, sticky="e", padx=(12, 0))

        body = tk.Frame(self.root, background=WINDOW, padx=18)
        body.grid(row=1, column=0, sticky="nsew", pady=(4, 12))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=7, minsize=450)
        body.grid_columnconfigure(1, weight=3, minsize=328)

        board_sheet = self._sheet(body, 0, padx=(0, 14))
        board_sheet.grid_rowconfigure(1, weight=1)
        board_sheet.grid_columnconfigure(0, weight=1)
        board_header = tk.Frame(board_sheet, background=ACETATE)
        board_header.grid(row=0, column=0, sticky="ew")
        board_header.columnconfigure(0, weight=1)
        board_title = tk.Label(board_header, text=t("board.pieces"), background=ACETATE, foreground=INK,
                 font=("TkDefaultFont", FONT_SIZES["caption"], "bold"), anchor="w", justify="left", padx=14, pady=9,
                 )
        board_title.grid(row=0, column=0, sticky="ew")
        self.text_board_button = self._button(board_header, t("text_board.button"), self._open_text_board)
        self.text_board_button.grid(row=0, column=1, padx=(0, 12), pady=4)
        board_title.bind("<Configure>", lambda event: board_title.configure(wraplength=max(1, event.width - 28)))
        self.board = BoardCanvas(board_sheet, lambda moves: app._on_move_requested(moves),
                                 lambda detail: app._on_selection_changed(detail),
                                 artwork=self._board_artwork, renderer=piece_renderer, translator=t)
        self.board.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        board_status = tk.Label(
            board_sheet, textvariable=self.interaction_text, background=ACETATE, foreground=MUTED_INK,
            font=("TkDefaultFont", FONT_SIZES["caption"]), anchor="w", justify="left", padx=14, pady=8,
        )
        board_status.grid(row=2, column=0, sticky="ew")
        board_sheet.bind("<Configure>", lambda event: board_status.configure(wraplength=max(1, event.width - 28)))

        side_sheet = self._sheet(body, 1)
        side_sheet.grid_rowconfigure(2, weight=1)
        side_sheet.grid_columnconfigure(0, weight=1)
        self.tab_rail = TabRail(
            side_sheet, lambda name: app._show_panel(name),
            (("play", t("tab.play")), ("moves", t("tab.moves")), ("puzzles", t("tab.puzzles"))),
        )
        self.tab_rail.grid(row=0, column=0, sticky="ew", padx=(12, 9), pady=(12, 0))
        status = tk.Label(side_sheet, textvariable=self.panel_text, background=ACETATE, foreground=INK,
                          font=("TkDefaultFont", FONT_SIZES["section"], "bold"), anchor="w", justify="left",
                          padx=16, pady=15, wraplength=200)
        status.grid(row=1, column=0, sticky="ew")
        side_sheet.bind("<Configure>", lambda event: status.configure(wraplength=max(1, event.width - 32)))
        self.panel = tk.Frame(side_sheet, background=ACETATE, padx=14, pady=10)
        self.panel.grid(row=2, column=0, sticky="nsew")
        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_rowconfigure(0, weight=1)
        self._build_play_panel()
        self._build_moves_panel()
        self._build_puzzle_panel()
        self.panel.bind("<Configure>", self._update_panel_wraplengths)
        self._show_panel("play")

    def _sheet(self, master: tk.Misc, column: int, padx=(0, 0)) -> tk.Frame:
        slot = tk.Frame(master, background=WINDOW)
        slot.grid(row=0, column=column, sticky="nsew", padx=padx, pady=(4, 10))
        shadow = tk.Frame(slot, background=SHADOW)
        shadow.place(x=6, y=6, relwidth=1, relheight=1, width=-6, height=-6)
        sheet = tk.Frame(slot, background=ACETATE, highlightbackground=INK, highlightthickness=1)
        sheet.place(x=0, y=0, relwidth=1, relheight=1, width=-6, height=-6)
        return sheet

    def _label(self, master, *, text=None, var=None, role="body", bold=False, muted=False) -> tk.Label:
        label = tk.Label(
            master, text=text, textvariable=var, background=ACETATE,
            foreground=MUTED_INK if muted else INK,
            font=("TkDefaultFont", FONT_SIZES[role], "bold" if bold else "normal"),
            wraplength=250, justify="left", anchor="w",
        )
        self._wrap_labels.append(label)
        return label

    def _build_play_panel(self) -> None:
        t = self.t
        self.play_viewport, self.play_canvas, self.play_panel = self._scrollable_panel()
        canvas, panel = self.play_canvas, self.play_panel
        row = 0
        self._label(panel, text=t("play.mode_label"), role="caption", bold=True).grid(row=row, column=0, sticky="ew")
        row += 1
        self.mode_buttons: dict[str, tk.Radiobutton] = {}
        for value, key in (("human-vs-human", "mode.human"), ("human-vs-bot-white", "mode.bot_white"),
                           ("human-vs-bot-black", "mode.bot_black")):
            button = tk.Radiobutton(
                panel, text=t(key), value=value, variable=self.mode_var, anchor="w",
                background=ACETATE, foreground=INK, activebackground=ACETATE, selectcolor=PAPER,
                highlightthickness=1, highlightcolor=INK, font=("TkDefaultFont", FONT_SIZES["body"]),
            )
            button.grid(row=row, column=0, sticky="ew")
            self.mode_buttons[value] = button
            row += 1
        level_row = tk.Frame(panel, background=ACETATE)
        level_row.grid(row=row, column=0, sticky="ew", pady=(4, 8))
        level_row.grid_columnconfigure(1, weight=1)
        tk.Label(level_row, text=t("play.level_label"), background=ACETATE, foreground=INK,
                 font=("TkDefaultFont", FONT_SIZES["caption"], "bold")).grid(row=0, column=0, sticky="w")
        self.level_menu = tk.OptionMenu(level_row, self.preset_var, *[self._preset_label(p.id) for p in self.presets],
                                        command=lambda _v: self._on_preset_changed())
        self.level_menu.configure(background=PAPER, foreground=INK, highlightthickness=1, relief="solid", borderwidth=1)
        self.level_menu.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        row += 1
        self.new_game_button = self._button(panel, t("button.new_game"), self._new_game, role="new")
        self.new_game_button.grid(row=row, column=0, sticky="ew", pady=3)
        row += 1
        controls = tk.Frame(panel, background=ACETATE)
        controls.grid(row=row, column=0, sticky="ew")
        controls.grid_columnconfigure((0, 1), weight=1)
        self.undo_button = self._button(controls, t("button.undo"), self._undo)
        self.undo_button.grid(row=0, column=0, sticky="ew", pady=3, padx=(0, 3))
        self.redo_button = self._button(controls, t("button.redo"), self._redo)
        self.redo_button.grid(row=0, column=1, sticky="ew", pady=3, padx=(3, 0))
        self.flip_button = self._button(controls, t("button.flip"), self._flip_board)
        self.flip_button.grid(row=1, column=0, sticky="ew", pady=3, padx=(0, 3))
        self.resign_button = self._button(controls, t("button.resign"), self._resign)
        self.resign_button.grid(row=1, column=1, sticky="ew", pady=3, padx=(3, 0))
        self.save_button = self._button(controls, t("button.save_game"), self._save_game)
        self.save_button.grid(row=2, column=0, sticky="ew", pady=3, padx=(0, 3))
        self.copy_pgn_button = self._button(controls, t("button.copy_pgn"), self._copy_pgn)
        self.copy_pgn_button.grid(row=2, column=1, sticky="ew", pady=3, padx=(3, 0))
        self.claim_button = self._button(controls, t("button.claim_draw"), self._claim_draw)
        self.claim_button.grid(row=3, column=0, sticky="ew", pady=3, padx=(0, 3))
        self.library_button = self._button(controls, t("button.library"), self._open_library)
        self.library_button.grid(row=3, column=1, sticky="ew", pady=3, padx=(3, 0))
        row += 1
        self.position_button = self._button(panel, t("position.button"), self._open_position)
        self.position_button.grid(row=row, column=0, sticky="ew", pady=3)
        row += 1
        self._label(panel, var=self.action_state_text, role="caption", muted=True).grid(row=row, column=0, sticky="ew", pady=(6, 0))
        row += 1
        tk.Frame(panel, height=1, background=INK).grid(row=row, column=0, sticky="ew", pady=(12, 8))
        row += 1
        self.bot_label = self._label(panel, var=self.bot_text, role="caption", bold=True)
        self.bot_label.grid(row=row, column=0, sticky="ew")
        row += 1
        bot_controls = tk.Frame(panel, background=ACETATE)
        bot_controls.grid(row=row, column=0, sticky="ew", pady=(6, 0))
        bot_controls.grid_columnconfigure((0, 1), weight=1)
        self.retry_bot_button = self._button(bot_controls, t("button.retry_bot"), self._retry_bot)
        self.retry_bot_button.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.engine_button = self._button(bot_controls, t("button.engine"), self._open_engine_dialog)
        self.engine_button.grid(row=0, column=1, sticky="ew", padx=(3, 0))

        paired_buttons = (
            self.undo_button, self.redo_button, self.flip_button, self.resign_button, self.save_button,
            self.copy_pgn_button, self.claim_button, self.library_button, self.retry_bot_button, self.engine_button,
        )

        def resize_content(width: int) -> None:
            for button in paired_buttons:
                button.configure(wraplength=max(1, width // 2 - 32), justify="left")
            for button in (*self.mode_buttons.values(), self.position_button):
                button.configure(wraplength=max(1, width - 35), justify="left")

        self._bind_panel_scroll(
            canvas, panel,
            (*paired_buttons, *self.mode_buttons.values(), self.level_menu, self.new_game_button, self.position_button),
            resize_content,
        )

    def _scrollable_panel(self) -> tuple[tk.Frame, tk.Canvas, tk.Frame]:
        viewport = tk.Frame(self.panel, background=ACETATE)
        viewport.grid(row=0, column=0, sticky="nsew")
        viewport.grid_rowconfigure(0, weight=1)
        viewport.grid_columnconfigure(0, weight=1)
        canvas = tk.Canvas(viewport, background=ACETATE, highlightthickness=0, borderwidth=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(viewport, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        panel = tk.Frame(canvas, background=ACETATE)
        panel.grid_columnconfigure(0, weight=1)
        canvas.create_window(0, 0, window=panel, anchor="nw", tags=("panel-content",))
        panel.bind("<Configure>", lambda event: canvas.configure(scrollregion=(0, 0, event.width, event.height)))
        return viewport, canvas, panel

    @staticmethod
    def _bind_panel_scroll(
        canvas: tk.Canvas, panel: tk.Frame, controls: Sequence[tk.Widget], resize_content: Callable[[int], None],
    ) -> None:
        window, = canvas.find_withtag("panel-content")

        def resize(event: tk.Event) -> None:
            if int(canvas.itemcget(window, "width")) == event.width:
                return
            canvas.itemconfigure(window, width=event.width)
            resize_content(event.width)

        canvas.bind("<Configure>", resize)

        def scroll(event: tk.Event) -> str:
            up = event.num == 4 or event.delta > 0
            canvas.yview_scroll(-1 if up else 1, "units")
            return "break"

        def show_focus(event: tk.Event) -> None:
            widget = event.widget
            top = widget.winfo_rooty() - panel.winfo_rooty()
            bottom = top + widget.winfo_height()
            view_top = canvas.canvasy(0)
            view_height = canvas.winfo_height()
            if top < view_top:
                canvas.yview_moveto(top / panel.winfo_height())
            elif bottom > view_top + view_height:
                canvas.yview_moveto((bottom - view_height) / panel.winfo_height())

        for widget in controls:
            widget.bind("<FocusIn>", show_focus, add="+")
        remaining = [canvas]
        while remaining:
            widget = remaining.pop()
            remaining.extend(widget.winfo_children())
            for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                widget.bind(sequence, scroll)

    def _build_moves_panel(self) -> None:
        t = self.t
        panel = self.moves_panel = tk.Frame(self.panel, background=ACETATE)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        tk.Label(panel, text=t("moves.title"), background=ACETATE, foreground=INK,
                 font=("TkDefaultFont", FONT_SIZES["section"], "bold"), anchor="w").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.empty_moves_label = self._label(panel, text=t("moves.empty"), muted=True)
        self.empty_moves_label.grid(row=1, column=0, sticky="new")
        list_frame = self.move_list_frame = tk.Frame(panel, background=ACETATE)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        self.move_list = tk.Listbox(
            list_frame, background=PAPER, foreground=INK, selectbackground=CHROME_YELLOW, selectforeground=INK,
            font=("TkFixedFont", 11), relief="solid", borderwidth=1, highlightthickness=2,
            highlightbackground=PAPER, highlightcolor=BRAND_BLUE, exportselection=False,
        )
        self.move_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.move_list.yview,
                                 background=CHROME_YELLOW, troughcolor=PAPER, activebackground=INK)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.move_list.configure(yscrollcommand=scrollbar.set)
        list_frame.grid_remove()
        self.replay_button = self._button(panel, t("replay.title"), lambda: self._open_replay(self.game))
        self.replay_button.grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def _build_puzzle_panel(self) -> None:
        t = self.t
        self.puzzle_viewport, canvas, self.puzzle_panel = self._scrollable_panel()
        panel = self.puzzle_panel
        pack_section = tk.Frame(panel, background=ACETATE)
        pack_section.grid_columnconfigure(0, weight=1)
        self.puzzle_pack_button = self._button(pack_section, t("puzzle.packs"), self._open_puzzle_packs)
        if self._pack_library is not None:
            pack_section.grid(row=0, column=0, sticky="ew", pady=(0, 8))
            self.puzzle_pack_button.grid(row=0, column=0, sticky="ew")
        self.puzzle_pack_feedback_label = self._label(pack_section, var=self.puzzle_pack_feedback, role="caption")
        self.puzzle_pack_feedback_label.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.puzzle_pack_feedback_label.grid_remove()
        self.puzzle_pack_text.set(self._pack_description())
        self._label(panel, var=self.puzzle_title_text, role="body", bold=True).grid(row=1, column=0, sticky="ew")
        self._label(panel, var=self.puzzle_meta_text, role="caption", muted=True).grid(row=2, column=0, sticky="ew", pady=(2, 8))
        self.puzzle_feedback_label = self._label(panel, var=self.puzzle_feedback_text, role="body")
        self.puzzle_feedback_label.grid(row=3, column=0, sticky="ew", pady=(4, 12))
        self.hint_button = self._button(panel, t("button.hint"), self._puzzle_hint)
        self.hint_button.grid(row=4, column=0, sticky="ew", pady=3)
        self.solution_button = self._button(panel, t("button.solution"), self._puzzle_reveal)
        self.solution_button.grid(row=5, column=0, sticky="ew", pady=3)
        self.next_puzzle_button = self._button(panel, t("button.next_puzzle"), self._next_puzzle, role="new")
        self.next_puzzle_button.grid(row=6, column=0, sticky="ew", pady=3)
        self.retry_puzzle_button = self._button(panel, t("puzzle.retry"), self._retry_puzzle)
        self.retry_puzzle_button.grid(row=7, column=0, sticky="ew", pady=3)
        filters = tk.Frame(panel, background=ACETATE)
        filters.grid(row=9, column=0, sticky="ew", pady=(8, 0))
        filters.grid_columnconfigure(1, weight=1)
        self._label(filters, text=t("puzzle.filter_theme"), role="caption").grid(row=0, column=0, sticky="w")
        self._label(filters, text=t("puzzle.filter_rating"), role="caption").grid(row=1, column=0, sticky="w")
        rating_labels = [
            t("puzzle.rating_from", rating=lower) if upper is None else f"{lower}–{upper}"
            for lower, upper in PUZZLE_RATING_RANGES
        ]
        theme_labels = [t.puzzle_theme_label(theme) for theme in self._puzzle_themes]
        self.puzzle_theme_filter = ttk.Combobox(
            filters, state="readonly", values=(t("puzzle.all_themes"), *theme_labels), width=12,
        )
        self.puzzle_rating_filter = ttk.Combobox(
            filters, state="readonly", values=(t("puzzle.all_ratings"), *rating_labels), width=12,
        )
        self.puzzle_status_filter = ttk.Combobox(
            filters, state="readonly",
            values=(t("puzzle.status_all"), t("puzzle.status_open"), t("puzzle.status_review")), width=12,
        )
        dropdowns = (self.puzzle_theme_filter, self.puzzle_rating_filter)
        if self.db is not None:
            self._label(filters, text=t("puzzle.filter_status"), role="caption").grid(row=2, column=0, sticky="w")
            dropdowns += (self.puzzle_status_filter,)
        for row, dropdown in enumerate(dropdowns):
            dropdown.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=2)
            dropdown.current(0)
            dropdown.bind("<<ComboboxSelected>>", self._apply_puzzle_filters)
        self.atlas_section = tk.Frame(panel, background=PAPER, padx=6, pady=4)
        self.atlas_section.grid(row=10, column=0, sticky="ew", pady=(12, 0))
        tk.Label(self.atlas_section, text="Atlas of Moves", background=PAPER, foreground=INK, anchor="w",
                 font=("TkDefaultFont", FONT_SIZES["caption"], "bold"), padx=6, pady=3).pack(fill="x")
        self.puzzle_atlas = PuzzleAtlas(self.atlas_section)
        self.puzzle_atlas.pack(fill="x")
        if self.db is not None:
            self._label(panel, var=self.puzzle_progress_text, role="caption", muted=True).grid(
                row=11, column=0, sticky="ew", pady=(6, 0),
            )
            self.puzzle_history_label = self._label(panel, var=self.puzzle_history_text, role="caption", muted=True)
            self.puzzle_history_label.grid(row=8, column=0, sticky="ew", pady=(6, 0))
            self.puzzle_history_label.grid_remove()
        self._label(panel, var=self.puzzle_pack_text, role="caption", muted=True).grid(
            row=12, column=0, sticky="ew", pady=(8, 0),
        )
        buttons = (self.puzzle_pack_button, self.hint_button, self.solution_button,
                   self.next_puzzle_button, self.retry_puzzle_button)
        controls = (*buttons, *dropdowns)

        def resize_buttons(width: int) -> None:
            for button in buttons:
                button.configure(wraplength=max(1, width - 32), justify="left")

        self._bind_panel_scroll(canvas, panel, controls, resize_buttons)

    def _bind_shortcuts(self) -> None:
        for modifier in ("Control", "Command"):
            for sequence, action in (("z", self._undo), ("y", self._redo), ("Z", self._redo), ("n", self._new_game)):
                try:
                    self.root.bind(f"<{modifier}-{sequence}>", lambda _e, a=action: (a(), "break")[1])
                except tk.TclError:
                    pass  # Command modifier only exists on macOS

    def _update_panel_wraplengths(self, _event: tk.Event | None = None) -> None:
        wraplength = max(120, min(320, self.panel.winfo_width() - 40))
        for label in self._wrap_labels:
            label.configure(wraplength=wraplength)

    def _button(self, master: tk.Misc, label: str, command, *, role: str = "neutral") -> tk.Button:
        if role not in BUTTON_ROLES:
            raise ValueError(f"Unknown button role: {role}")
        background, foreground = BUTTON_ROLES[role]
        button = tk.Button(
            master, text=label, command=command, background=background, foreground=foreground,
            activebackground=INK, activeforeground=ACETATE, disabledforeground=DISABLED_INK, relief="solid",
            borderwidth=1, highlightthickness=2, highlightbackground=background, highlightcolor=BRAND_BLUE,
            padx=10, pady=7, anchor="w", font=("TkDefaultFont", FONT_SIZES["body"], "bold"),
        )

        _bind_button_enter(button)
        return button

    # ----- panels / modes ----------------------------------------------
    def _show_panel(self, name: str) -> None:
        panels = {"play": self.play_viewport, "moves": self.moves_panel, "puzzles": self.puzzle_viewport}
        if name not in panels:
            raise ValueError(f"Unknown game panel: {name}")
        for panel in panels.values():
            panel.grid_remove()
        panels[name].grid()
        previous, self.active_panel = getattr(self, "active_panel", "play"), name
        if name == "puzzles" and previous != "puzzles":
            if self.puzzle is None:
                self._start_puzzle(self.puzzle_index)
            self._update_puzzle_progress()
            self._refresh()
        elif previous == "puzzles" and name != "puzzles":
            self.board.set_orientation(self.orientation)
            self._refresh()

    def _preset_label(self, preset_id: str) -> str:
        preset = next(p for p in self.presets if p.id == preset_id)
        return self.t(preset.label_key)

    def _selected_preset(self) -> BotPreset:
        label = self.preset_var.get()
        return next((p for p in self.presets if self.t(p.label_key) == label), self.presets[2])

    def _on_preset_changed(self) -> None:
        preset = self._selected_preset()
        provider = self.controller.provider
        if isinstance(provider, UCIBot):
            provider.set_preset(preset)
        self._store_settings(bot_preset_id=preset.id)

    def _store_settings(self, **changes) -> None:
        self.settings = replace(self.settings, **changes)
        if self.layout is not None:
            save_settings(self.layout.settings, self.settings)

    def _setup_for_mode(self, mode: str) -> GameSetup:
        if mode == "human-vs-bot-white":
            return GameSetup.against_bot(Color.WHITE)
        if mode == "human-vs-bot-black":
            return GameSetup.against_bot(Color.BLACK)
        return GameSetup.two_players()

    # ----- game commands ------------------------------------------------
    def _new_game(self) -> None:
        if self.active_panel == "puzzles":
            self.tab_rail.set_active("play")
        view = self.controller.view()
        if (self.game.moves or view.can_redo) and not messagebox.askyesno(
            self.t("new_game.confirm_title"), self.t("new_game.confirm_body"), parent=self.root,
        ):
            return
        self.start_game(self.mode_var.get())

    def start_game(self, mode: str) -> None:
        """Start a game in ``mode`` without confirmation (used by tests and New game)."""
        setup = self._setup_for_mode(mode)
        if setup.mode is PlayMode.HUMAN_VS_BOT:
            preset = self._selected_preset()
            provider = self.controller.provider
            if provider is None or self._provider_stale:
                self.controller.set_provider(self._provider_factory(preset, self.settings))
                self._provider_stale = False
            elif isinstance(provider, UCIBot):
                provider.set_preset(preset)
            human = Color.WHITE if mode == "human-vs-bot-white" else Color.BLACK
            self.orientation = "white" if human is Color.WHITE else "black"
            self.board.set_orientation(self.orientation)
        self.mode_var.set(mode)
        self._store_settings(play_mode=mode)
        self._game_headers.clear()
        self.controller.new_game(setup)

    def _on_move_requested(self, candidates: tuple[Move, ...]) -> None:
        if len(candidates) == 1:
            self._play_move(candidates[0])
            return
        self._choose_promotion(candidates)

    def _play_move(self, move: Move) -> None:
        if self.active_panel == "puzzles":
            self._puzzle_move(move)
            return
        try:
            self.controller.play_human(move)
        except ChessError as error:
            self.interaction_text.set(self.t("move.rejected", error=error))
            self._refresh()

    def _choose_promotion(self, candidates: Sequence[Move]) -> None:
        promotions = tuple(move for move in candidates if move.promotion is not None)
        if not promotions:
            self.interaction_text.set(self.t("move.ambiguous"))
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("promotion.title"))
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.configure(background=ACETATE)
        tk.Label(dialog, text=self.t("promotion.prompt"), background=ACETATE, foreground=INK,
                 font=("TkDefaultFont", FONT_SIZES["body"], "bold"), padx=18, pady=14,
                 ).grid(row=0, column=0, columnspan=len(promotions), sticky="ew")
        chosen: list[Move] = []
        for column, move in enumerate(promotions):
            label = self.t(f"piece.{move.promotion.name.lower()}") if move.promotion else "?"
            button = self._button(dialog, label, lambda candidate=move: (chosen.append(candidate), dialog.destroy()))
            button.grid(row=1, column=column, padx=6, pady=(0, 14))
            if column == 0:
                button.focus_set()
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        try:
            dialog.grab_set()
            self.root.wait_window(dialog)
        finally:
            try:
                dialog.grab_release()
            except tk.TclError:
                pass
        if chosen:
            self._play_move(chosen[0])

    def _undo(self) -> None:
        if self.active_panel == "puzzles":
            return
        try:
            self.controller.undo()
        except ChessError as error:
            self.interaction_text.set(str(error))

    def _redo(self) -> None:
        if self.active_panel == "puzzles":
            return
        try:
            self.controller.redo()
        except ChessError as error:
            self.interaction_text.set(str(error))

    def _resign(self) -> None:
        try:
            self.controller.resign()
        except ChessError as error:
            self.interaction_text.set(str(error))

    def _choose_item(
        self,
        title: str,
        labels: Sequence[str],
        confirm: str,
        *,
        empty: str = "",
        initial_index: int = 0,
        actions: Sequence[tuple[str, Callable[[int | None], None], bool]] = (),
        searchable: bool = False,
    ) -> int | None:
        previous_focus = self.root.focus_lastfor()
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        content = ttk.Frame(dialog, padding=12)
        content.grid(sticky="nsew")
        columns = 3 if len(actions) >= 3 else len(actions) + 2
        selection = ttk.Combobox(content, values=labels, state="readonly" if labels else "disabled", width=46)
        selection.grid(row=0, column=0, columnspan=columns, sticky="ew", pady=(0, 10))
        if labels:
            selection.current(initial_index)
        else:
            selection.set(empty)
        chosen = None
        action = None
        visible = list(range(len(labels)))

        def close(_event: tk.Event | None = None) -> None:
            # Return focus while the dialog still owns it. Tk also remembers the
            # target in the parent if the window manager has deactivated the app.
            if previous_focus is not None and previous_focus.winfo_exists() and previous_focus.winfo_viewable():
                previous_focus.focus_set()
            dialog.destroy()

        def accept(callback: Callable[[int | None], None] | None = None) -> None:
            nonlocal chosen, action
            index = selection.current()
            chosen = visible[index] if index >= 0 else None
            action = callback
            close()

        confirm_button = ttk.Button(content, text=confirm, command=accept, state="normal" if labels else "disabled")
        confirm_button.grid(row=1, column=0, padx=4)
        _bind_button_enter(confirm_button)
        initial_focus: tk.Widget | None = selection if labels else None
        selection_actions = [confirm_button]
        for index, (label, callback, requires_selection) in enumerate(actions, 1):
            state = "disabled" if requires_selection and not labels else "normal"
            button = ttk.Button(content, text=label, command=lambda callback=callback: accept(callback), state=state)
            button.grid(row=1 + index // columns, column=index % columns, padx=4, pady=2)
            _bind_button_enter(button)
            if requires_selection:
                selection_actions.append(button)
            if initial_focus is None and state == "normal":
                initial_focus = button
        cancel_button = ttk.Button(content, text=self.t("button.cancel"), command=close)
        index = len(actions) + 1
        cancel_button.grid(row=1 + index // columns, column=index % columns, padx=4, pady=2)
        _bind_button_enter(cancel_button)
        dialog.bind("<Escape>", close)
        dialog.protocol("WM_DELETE_WINDOW", close)
        if labels:
            selection.bind("<Return>", lambda _event: accept())
            selection.bind("<KP_Enter>", lambda _event: accept())
        query = None
        trace = None
        if searchable and labels:
            ttk.Label(content, text=self.t("library.search")).grid(row=0, column=0, columnspan=columns,
                                                                   sticky="w")
            query = tk.StringVar(dialog)
            search = ttk.Entry(content, textvariable=query)
            search.grid(row=1, column=0, columnspan=columns, sticky="ew", pady=(4, 8))
            selection.grid_configure(row=2)
            for child in content.winfo_children():
                if isinstance(child, ttk.Button):
                    child.grid_configure(row=int(child.grid_info()["row"]) + 2)
            normalized = tuple(label.casefold() for label in labels)

            def filter_games(*_trace: str) -> None:
                terms = query.get().casefold().split()
                current = selection.current()
                previous = visible[current] if current >= 0 else None
                visible[:] = [index for index, label in enumerate(normalized)
                              if all(term in label for term in terms)]
                selection.configure(values=[labels[index] for index in visible],
                                    state="readonly" if visible else "disabled")
                if visible:
                    selection.current(visible.index(previous) if previous in visible else 0)
                else:
                    selection.set(self.t("library.no_matches"))
                for button in selection_actions:
                    button.configure(state="normal" if visible else "disabled")

            def focus_matches(_event: tk.Event) -> str:
                if visible:
                    selection.focus_set()
                return "break"

            trace = query.trace_add("write", filter_games)
            search.bind("<Down>", focus_matches)
            search.bind("<Return>", focus_matches)
            search.bind("<KP_Enter>", focus_matches)
            initial_focus = search
        (initial_focus or cancel_button).focus_set()
        dialog.grab_set()
        try:
            self.root.wait_window(dialog)
        finally:
            if query is not None:
                query.trace_remove("write", trace)
        if action is not None:
            action(chosen)
            return None
        return chosen

    def _claim_draw(self) -> None:
        view = self.controller.view()
        if not view.human_to_move:
            return
        options = self.game.draw_claim_options()
        if not options:
            return
        labels = []
        for reason, move in options:
            label = self.t(f"claim.{reason.name.lower()}")
            if move is not None:
                label = self.t("claim.by_move", rule=label, move=to_san(view.state, move))
            labels.append(label)
        chosen = self._choose_item(self.t("button.claim_draw"), labels, self.t("button.claim_draw"))
        if chosen is None or self.controller.view().state is not view.state:
            return
        try:
            self.controller.claim_draw(*options[chosen])
        except ChessError as error:
            self.interaction_text.set(str(error))

    def _retry_bot(self) -> None:
        self.controller.retry_bot()

    def _flip_board(self) -> None:
        self.orientation = "black" if self.orientation == "white" else "white"
        self.board.set_orientation(self.orientation)
        self.interaction_text.set(self.t("board.black_bottom" if self.orientation == "black" else "board.white_bottom"))

    def _pgn_headers(self) -> dict[str, str]:
        view = self.controller.view()
        headers = {"Event": "Chess & Chains local game", **self._game_headers}
        if view.setup.mode is PlayMode.HUMAN_VS_BOT and view.bot_name:
            if view.setup.bot_color is Color.WHITE:
                headers.update(White=view.bot_name, Black="Human")
            else:
                headers.update(White="Human", Black=view.bot_name)
        return headers

    def _save_game(self) -> int | None:
        if self.db is None:
            self.interaction_text.set(self.t("save.unavailable"))
            return None
        view = self.controller.view()
        provider = self.controller.provider
        mode = view.setup.mode.value
        if view.setup.bot_color is not None:
            mode += f"-{view.setup.bot_color.opposite.name.lower()}"
        try:
            game_id = self.db.save_game(
                self.game,
                mode=mode,
                bot_color=view.setup.bot_color.value if view.setup.bot_color else None,
                bot_name=view.bot_name if view.setup.mode is PlayMode.HUMAN_VS_BOT else None,
                bot_preset=provider.preset.id if view.setup.bot_color and isinstance(provider, UCIBot) else None,
                headers=self._pgn_headers(),
            )
        except (StorageError, sqlite3.Error, ChessError) as error:
            self.interaction_text.set(self.t("library.error", error=error))
            return None
        self.interaction_text.set(self.t("save.done", id=game_id))
        return game_id

    def _open_library(self) -> None:
        if self.db is None:
            return
        try:
            rows = self.db.game_summaries()
            labels = []
            for game in rows:
                label = self.t("library.entry", id=game.id, date=game.created_utc[:10], result=game.result)
                if game.white and game.black:
                    label += "  ·  " + self.t("library.players", white=game.white, black=game.black)
                if game.event and game.event not in ("*", "?"):
                    label += "  ·  " + game.event
                labels.append(label)
            chosen = self._choose_item(
                self.t("button.library"), labels, self.t("library.open"), empty=self.t("library.empty"), searchable=True,
                actions=(
                    (self.t("library.import"), lambda _index: self._import_pgn_file(), False),
                    (self.t("library.export"), lambda index: self._export_pgn_file(rows[index].id)
                     if index is not None else None, True),
                    (self.t("replay.title"), lambda index: self._open_replay(self.db.load_game(rows[index].id).to_game())
                     if index is not None else None, True),
                ),
            )
            if chosen is None:
                return
            saved = self.db.load_game(rows[chosen].id)
            game = saved.to_game()
            if (self.game.can_undo or self.game.can_redo) and not messagebox.askyesno(
                self.t("library.open"), self.t("library.replace"), parent=self.root,
            ):
                return
            self._game_headers = dict(saved.pgn_tags)
            self.mode_var.set("human-vs-human")
            self.controller.load_game(game)
            self.interaction_text.set(self.t("library.loaded", id=saved.id))
        except (StorageError, sqlite3.Error, ChessError) as error:
            self.interaction_text.set(self.t("library.error", error=error))

    def _import_pgn_file(self) -> None:
        if self.db is None:
            return
        title = self.t("library.import")
        names = [(self.t("library.pgn_files"), "*.pgn")]
        source = filedialog.askopenfilename(parent=self.root, title=title, filetypes=names)
        if not source:
            return
        try:
            game_id = self.db.import_pgn_file(Path(source))
        except (OSError, ValueError, StorageError, sqlite3.Error) as error:
            messagebox.showerror(title, self.t("library.error", error=error), parent=self.root)
            return
        self.interaction_text.set(self.t("library.imported", id=game_id))

    def _export_pgn_file(self, game_id: int) -> None:
        if self.db is None:
            return
        title = self.t("library.export")
        names = [(self.t("library.pgn_files"), "*.pgn")]
        target = filedialog.asksaveasfilename(
            parent=self.root, title=title, filetypes=names, defaultextension=".pgn",
            initialfile=f"chess-and-chains-{game_id}.pgn",
        )
        if not target:
            return
        try:
            self.db.export_pgn_file(game_id, Path(target))
        except (OSError, ValueError, StorageError, sqlite3.Error) as error:
            messagebox.showerror(title, self.t("library.error", error=error), parent=self.root)
            return
        self.interaction_text.set(self.t("library.exported", id=game_id))

    def _current_pgn(self) -> str:
        return export_pgn(self.game, self._pgn_headers())

    def _copy_pgn(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(self._current_pgn())
        self.interaction_text.set(self.t("pgn.copied"))

    def _open_position(self) -> None:
        def confirm_replacement(parent: tk.Misc) -> bool:
            if not (self.game.can_undo or self.game.can_redo):
                return True
            return messagebox.askyesno(
                self.t("position.play"), self.t("position.replace"), parent=parent, default=messagebox.NO,
            )

        dialog = PositionDialog(self.root, self.t, self.controller.view().state, confirm_replacement)
        self.root.wait_window(dialog)
        if dialog.result is None or self._closed:
            return
        self._game_headers.clear()
        self.mode_var.set("human-vs-human")
        self.controller.load_game(ChessGame(dialog.result))
        self.interaction_text.set(self.t("position.playing"))

    # ----- puzzles --------------------------------------------------------
    def _pack_description(self) -> str:
        manifest = self.pack.manifest
        if manifest.pack_id == DEMO_PACK_ID:
            return self.t("puzzle.demo_notice")
        return self.t("puzzle.pack_info", version=manifest.version, source=manifest.source)

    def _set_pack_feedback(self, message: str) -> None:
        self.puzzle_pack_feedback.set(message)
        if message:
            self.puzzle_pack_feedback_label.grid()
        else:
            self.puzzle_pack_feedback_label.grid_remove()

    def _open_puzzle_packs(self) -> None:
        library = self._pack_library
        if library is None or self._pack_loading:
            return
        try:
            pack_ids = (DEMO_PACK_ID, *library.ids())
        except PackError as error:
            self._set_pack_feedback(self.t("puzzle.pack_error", error=error))
            return
        current = self.pack.manifest.pack_id
        chosen = self._choose_item(
            self.t("puzzle.packs"),
            (self.t("puzzle.demo_name"), *pack_ids[1:]),
            self.t("puzzle.pack_open"),
            initial_index=pack_ids.index(current) if current in pack_ids else 0,
            actions=((self.t("puzzle.pack_install"), lambda _index: self._pick_pack_folder(), False),),
        )
        if chosen is None or pack_ids[chosen] == current:
            return
        if pack_ids[chosen] == DEMO_PACK_ID:
            self._activate_pack(load_demo_pack())
        else:
            self._start_pack_task(partial(library.load, pack_ids[chosen]))

    def _pick_pack_folder(self) -> None:
        library = self._pack_library
        if library is None:
            return
        folder = filedialog.askdirectory(parent=self.root, title=self.t("puzzle.pack_install"), mustexist=True)
        if folder:
            self._start_pack_task(partial(library.install, Path(folder)))

    def _start_pack_task(self, task: Callable[[], PuzzlePack]) -> None:
        worker = threading.Thread(target=_read_local_pack, args=(task, self._pack_results),
                                  name="puzzle-pack", daemon=True)
        try:
            worker.start()
        except RuntimeError as error:
            self._set_pack_feedback(self.t("puzzle.pack_error", error=error))
            return
        self._pack_loading = True
        self.puzzle_pack_button.configure(state=tk.DISABLED)
        self._set_pack_feedback(self.t("puzzle.pack_loading"))

    def _poll_pack_task(self) -> None:
        try:
            result = self._pack_results.get_nowait()
        except Empty:
            return
        self._pack_loading = False
        self.puzzle_pack_button.configure(state=tk.NORMAL)
        if isinstance(result, str):
            self._set_pack_feedback(self.t("puzzle.pack_error", error=result))
        else:
            self._activate_pack(result)

    def _activate_pack(self, pack: PuzzlePack) -> None:
        self.pack = pack
        self._puzzle_selection = pack.puzzles
        self._puzzle_themes = sorted({theme for puzzle in pack.puzzles for theme in puzzle.themes})
        labels = [self.t.puzzle_theme_label(theme) for theme in self._puzzle_themes]
        self.puzzle_theme_filter.configure(values=(self.t("puzzle.all_themes"), *labels))
        self.puzzle_theme_filter.current(0)
        self.puzzle_rating_filter.current(0)
        self.puzzle_status_filter.current(0)
        self._solved_puzzle_ids.clear()
        self._review_puzzle_ids.clear()
        self.puzzle = None
        self.puzzle_index = 0
        self.puzzle_pack_text.set(self._pack_description())
        self._set_pack_feedback("")
        self._update_puzzle_history()
        self._update_puzzle_progress()
        if self.active_panel == "puzzles":
            self._start_puzzle(0)
        if self.settings.last_pack_id != pack.manifest.pack_id:
            try:
                self._store_settings(last_pack_id=pack.manifest.pack_id)
            except (OSError, SettingsError):
                self._set_pack_feedback(self.t("puzzle.pack_preference_error"))

    def _matching_puzzles(self) -> tuple[Puzzle, ...]:
        theme_choice = self.puzzle_theme_filter.current()
        theme = self._puzzle_themes[theme_choice - 1] if theme_choice > 0 else None
        rating_choice = self.puzzle_rating_filter.current()
        lower, upper = PUZZLE_RATING_RANGES[rating_choice - 1] if rating_choice > 0 else (0, None)
        status_choice = self.puzzle_status_filter.current()
        return tuple(
            puzzle for puzzle in self.pack.puzzles
            if (not theme or theme in puzzle.themes)
            and puzzle.rating >= lower and (upper is None or puzzle.rating <= upper)
            and (status_choice != 1 or puzzle.puzzle_id not in self._solved_puzzle_ids)
            and (status_choice != 2 or puzzle.puzzle_id in self._review_puzzle_ids)
        )

    def _apply_puzzle_filters(self, _event: tk.Event | None = None) -> None:
        self._puzzle_selection = self._matching_puzzles()
        self._update_puzzle_progress()
        if self.puzzle is not None and self.puzzle.puzzle in self._puzzle_selection:
            self.puzzle_index = self._puzzle_selection.index(self.puzzle.puzzle)
            self._refresh()
        else:
            self._start_puzzle(0)

    def _start_puzzle(self, index: int) -> None:
        self._puzzle_recorded = False
        self._puzzle_hint_stage = 0
        self.puzzle_feedback_text.set("")
        if self._puzzle_selection:
            self.puzzle_index = index % len(self._puzzle_selection)
            self.puzzle = PuzzleSession(self._puzzle_selection[self.puzzle_index])
            self.board.set_orientation("white" if self.puzzle.player_color is Color.WHITE else "black")
        else:
            self.puzzle_index = 0
            self.puzzle = None
        self._update_puzzle_history()
        self._refresh()

    def _next_puzzle(self) -> None:
        following = self.puzzle_index + 1
        if self.puzzle_status_filter.current() > 0 and self.puzzle_status_filter.instate(("!disabled",)):
            previous = self._puzzle_selection
            self._puzzle_selection = self._matching_puzzles()
            indexes = {puzzle.puzzle_id: index for index, puzzle in enumerate(self._puzzle_selection)}
            following = next((indexes[puzzle.puzzle_id] for puzzle in previous[following:] + previous[:following]
                              if puzzle.puzzle_id in indexes), 0)
            self._update_puzzle_progress()
        self._start_puzzle(following)

    def _retry_puzzle(self) -> None:
        session = self.puzzle
        if session is None:
            return
        has_work = session.mistakes or session.hints_used or len(session.game.moves) > 1
        if not session.finished and has_work and not messagebox.askyesno(
            self.t("puzzle.retry"), self.t("puzzle.retry_confirm"), parent=self.root, default=messagebox.NO,
        ):
            return
        self._start_puzzle(self.puzzle_index)

    def _update_puzzle_progress(self) -> None:
        if self.db is None:
            return
        try:
            solved, review = self.db.puzzle_training_ids(self.pack.manifest.pack_id)
        except sqlite3.Error:
            self.puzzle_status_filter.configure(state="disabled")
            self.puzzle_progress_text.set(self.t("puzzle.progress_unavailable"))
            return
        self._solved_puzzle_ids = solved
        self._review_puzzle_ids = review
        self.puzzle_status_filter.configure(state="readonly")
        count = sum(puzzle.puzzle_id in solved for puzzle in self._puzzle_selection)
        self.puzzle_progress_text.set(
            self.t("puzzle.progress", solved=count, count=len(self._puzzle_selection)) if self._puzzle_selection else ""
        )

    def _update_puzzle_history(self) -> None:
        if self.db is None:
            return
        self.puzzle_history_text.set("")
        self.puzzle_history_label.grid_remove()
        if self.puzzle is None:
            return
        pack_id, puzzle_id = self.pack.manifest.pack_id, self.puzzle.puzzle.puzzle_id
        try:
            progress = self.db.puzzle_progress(pack_id, puzzle_id)
            last = self.db.latest_puzzle_attempt(pack_id, puzzle_id)
        except sqlite3.Error:
            return
        if progress is None or last is None:
            return

        def duration(milliseconds: int | None) -> str:
            if milliseconds is None:
                return "–"
            minutes, seconds = divmod(milliseconds // 1000, 60)
            return f"{minutes}:{seconds:02d}"

        outcome = self.t("puzzle.attempt_solved" if last.solved else "puzzle.attempt_unsolved")
        self.puzzle_history_text.set(self.t(
            "puzzle.history", count=progress.attempts, best=duration(progress.best_duration_ms),
            outcome=outcome, mistakes=last.mistakes, hints=last.hints_used, time=duration(last.duration_ms),
        ))
        self.puzzle_history_label.grid()

    def _puzzle_move(self, move: Move) -> None:
        session = self.puzzle
        if session is None or session.finished:
            return
        before = session.state
        feedback = session.submit(move)
        if feedback.verdict is Verdict.CORRECT:
            self._puzzle_hint_stage = 0
            after_player = session.game.rules.apply(before, move)
            reply = to_san(after_player, feedback.reply, session.game.rules)
            self.puzzle_feedback_text.set(self.t("puzzle.correct", reply=reply))
        elif feedback.verdict is Verdict.SOLVED:
            self.puzzle_feedback_text.set(self.t("puzzle.solved_alternative" if feedback.alternative else "puzzle.solved"))
            self._record_puzzle()
        elif feedback.verdict is Verdict.WRONG:
            self.puzzle_feedback_text.set(self.t("puzzle.wrong"))
        else:
            self.puzzle_feedback_text.set(self.t("puzzle.illegal"))
        self._refresh()

    def _puzzle_hint(self) -> None:
        if self.puzzle is None or self._puzzle_hint_stage >= 2:
            return
        move = self.puzzle.expected_move
        if move is None:
            return
        destination = self._puzzle_hint_stage == 1
        self.puzzle.hint(destination=destination)
        self._puzzle_hint_stage += 1
        if destination:
            key = "puzzle.hint_promotion" if move.promotion is not None else "puzzle.hint_destination"
            detail = {"source": square_name(move.from_square), "target": square_name(move.to_square)}
            if move.promotion is not None:
                detail["piece"] = self.t(f"piece.{move.promotion.name.lower()}")
            self.puzzle_feedback_text.set(self.t(key, **detail))
        else:
            self.puzzle_feedback_text.set(self.t("puzzle.hint", square=square_name(move.from_square)))
        self._refresh()

    def _puzzle_reveal(self) -> None:
        session = self.puzzle
        if session is None or session.finished:
            return
        state = session.state
        sans = []
        for move in session.puzzle.solution[len(session.game.moves) - 1:]:
            sans.append(to_san(state, move, session.game.rules))
            state = session.game.rules.apply(state, move)
        session.reveal()
        self.puzzle_feedback_text.set(self.t("puzzle.revealed", line=" ".join(sans)))
        self._record_puzzle()
        self._refresh()

    def _record_puzzle(self) -> None:
        session = self.puzzle
        if session is None or self._puzzle_recorded or self.db is None:
            return
        try:
            self.db.record_puzzle_attempt(
                self.pack.manifest.pack_id, session.puzzle.puzzle_id, solved=session.solved,
                mistakes=session.mistakes, hints_used=session.hints_used, duration_ms=session.duration_ms,
            )
        except sqlite3.Error:
            self.puzzle_progress_text.set(self.t("puzzle.progress_unavailable"))
            return
        self._puzzle_recorded = True
        self._update_puzzle_progress()
        self._update_puzzle_history()

    def _open_engine_dialog(self) -> None:
        EngineDialog(self)

    def _open_replay(self, game: ChessGame) -> None:
        dialog = ReplayDialog(self.root, game, self.t, self._board_artwork, self.board.renderer, self.orientation)
        self.root.wait_window(dialog)

    def _open_text_board(self) -> None:
        dialog = TextBoardDialog(self.root, self.t, self._play_move)
        self._text_board = dialog
        try:
            self._refresh()
            self.root.wait_window(dialog)
        finally:
            self._text_board = None

    # ----- rendering ------------------------------------------------------
    def _side(self, color: Color) -> str:
        return self.t("side.white" if color is Color.WHITE else "side.black")

    def _on_view(self, _view: GameView) -> None:
        if not self._closed:
            self._refresh()

    def _poll(self) -> None:
        if self._closed:
            return
        self.controller.poll()
        if self._pack_loading:
            self._poll_pack_task()
        self._poll_job = self.root.after(POLL_MS, self._poll)

    def _refresh(self) -> None:
        if self.active_panel == "puzzles":
            self._refresh_puzzle()
        else:
            self._refresh_game(self.controller.view())

    def _refresh_puzzle(self) -> None:
        session = self.puzzle
        self.header_mode_text.set(self.t("header.mode.puzzle", pack=self.pack.manifest.pack_id.upper()))
        self.next_puzzle_button.configure(state=tk.NORMAL if session is not None else tk.DISABLED)
        self.retry_puzzle_button.configure(state=tk.NORMAL if session is not None else tk.DISABLED)
        self.puzzle_atlas.update_route(self._puzzle_selection, self.puzzle_index, session, self._solved_puzzle_ids)
        if session is None:
            self.atlas_section.grid_remove()
            self.panel_text.set(self.t("puzzle.no_matches"))
            self.puzzle_title_text.set("")
            self.puzzle_meta_text.set("")
            self.board.set_position(None, (), None, False)
            if self._text_board is not None:
                self._text_board.show_position(None, (), self.panel_text.get())
            self.hint_button.configure(state=tk.DISABLED)
            self.solution_button.configure(state=tk.DISABLED)
            return
        self.atlas_section.grid()
        self.panel_text.set(self.t("puzzle.title", index=self.puzzle_index + 1, count=len(self._puzzle_selection)))
        self.puzzle_title_text.set(self.t("puzzle.prompt", side=self._side(session.player_color)))
        theme_labels = [self.t.puzzle_theme_label(theme) for theme in session.puzzle.themes[:3]]
        self.puzzle_meta_text.set(self.t("puzzle.meta", id=session.puzzle.puzzle_id, rating=session.puzzle.rating,
                                         themes=", ".join(theme_labels)))
        legal = session.legal_moves()
        self.board.set_position(session.state, legal, session.last_move, session.game.rules.is_in_check(session.state))
        move = session.expected_move
        if move is not None and self._puzzle_hint_stage:
            self.board.set_hint(move.to_square if self._puzzle_hint_stage == 2 else move.from_square)
        if self._text_board is not None:
            self._text_board.show_position(session.state, legal, self.puzzle_title_text.get(),
                                           self.puzzle_feedback_text.get())
        state = tk.DISABLED if session.finished else tk.NORMAL
        hint_label = self.t("puzzle.hint_target_button" if self._puzzle_hint_stage else "button.hint")
        self.hint_button.configure(text=hint_label, state=state if self._puzzle_hint_stage < 2 else tk.DISABLED)
        self.solution_button.configure(state=state)

    def _refresh_game(self, view: GameView) -> None:
        t = self.t
        self.board.set_position(view.state, view.legal_moves, view.last_move, view.outcome.in_check)
        self.panel_text.set(self._status_label(view))
        bot = view.bot_name or ""
        if view.setup.mode is PlayMode.HUMAN_VS_BOT:
            key = "header.mode.bot_black" if view.setup.bot_color is Color.WHITE else "header.mode.bot_white"
            self.header_mode_text.set(t(key, bot=bot.upper()))
        else:
            self.header_mode_text.set(t("header.mode.human"))
        if view.bot_status is BotStatus.NONE:
            self.bot_text.set(t("bot.none"))
        elif view.bot_status is BotStatus.THINKING:
            self.bot_text.set(t("bot.thinking", bot=bot))
        elif view.bot_status is BotStatus.ERROR:
            self.bot_text.set(t("bot.error", error=view.bot_error))
        else:
            notice = f"\n{t('bot.mock_notice')}" if view.bot_is_mock else ""
            self.bot_text.set(t("bot.idle", bot=bot) + notice)
        if self._text_board is not None:
            feedback = ""
            if view.bot_status in (BotStatus.THINKING, BotStatus.ERROR):
                feedback = self.bot_text.get()
            elif view.san_moves:
                feedback = t("text_board.last", move=view.san_moves[-1])
            self._text_board.show_position(view.state, view.legal_moves, self.panel_text.get(), feedback)
        self.retry_bot_button.configure(state=tk.NORMAL if view.bot_status is BotStatus.ERROR else tk.DISABLED)
        if not self.game.moves and view.can_redo:
            action_state = t("action.redo_only")
        elif not view.can_undo:
            action_state = t("action.undo_unavailable")
        elif not view.can_redo:
            action_state = t("action.redo_unavailable")
        else:
            action_state = ""
        self.action_state_text.set(action_state)
        self._update_move_list(view.san_moves)
        self.replay_button.configure(state=tk.NORMAL if view.san_moves else tk.DISABLED)
        self.undo_button.configure(state=tk.NORMAL if view.can_undo else tk.DISABLED)
        self.redo_button.configure(state=tk.NORMAL if view.can_redo else tk.DISABLED)
        can_claim = view.human_to_move and bool(self.game.draw_claim_options())
        self.claim_button.configure(state=tk.NORMAL if can_claim else tk.DISABLED)
        active = view.outcome.status is GameStatus.ACTIVE
        self.resign_button.configure(state=tk.NORMAL if active and self.game.moves else tk.DISABLED)
        can_save = self.db is not None and (self.game.moves or not active)
        self.save_button.configure(state=tk.NORMAL if can_save else tk.DISABLED)
        self.library_button.configure(state=tk.NORMAL if self.db is not None else tk.DISABLED)

    def _status_label(self, view: GameView) -> str:
        t = self.t
        status, winner = view.outcome.status, view.outcome.winner
        if status is GameStatus.ACTIVE:
            key = "status.check_to_move" if view.outcome.in_check else "status.to_move"
            return t(key, side=self._side(view.state.turn))
        if status is GameStatus.CHECKMATE and winner:
            return t("status.checkmate", side=self._side(winner))
        if status is GameStatus.RESIGNED:
            return t("status.resigned", side=self._side(winner)) if winner else t("status.resigned_draw")
        if status is GameStatus.DRAW_CLAIMED and view.outcome.claimed_draw:
            reason = t(f"claim.{view.outcome.claimed_draw.name.lower()}")
            if view.outcome.declared_move is not None:
                reason = t("claim.by_move", rule=reason, move=to_san(view.state, view.outcome.declared_move))
            return t("status.claimed_reason", reason=reason)
        if status is GameStatus.RECORDED_RESULT:
            return t("status.recorded_win", side=self._side(winner)) if winner else t("status.recorded_draw")
        return t({
            GameStatus.STALEMATE: "status.stalemate",
            GameStatus.DRAW_INSUFFICIENT_MATERIAL: "status.insufficient",
            GameStatus.DRAW_DEAD_POSITION: "status.dead_position",
            GameStatus.DRAW_FIVEFOLD_REPETITION: "status.fivefold",
            GameStatus.DRAW_SEVENTY_FIVE_MOVE: "status.seventyfive",
            GameStatus.DRAW_CLAIMED: "status.claimed",
        }.get(status, "status.finished"))

    def _update_move_list(self, san_moves: Sequence[str]) -> None:
        offset = 1 if self.game.initial_state.turn is Color.BLACK else 0
        padded = [""] * offset + list(san_moves)
        rows = []
        first = self.game.initial_state.fullmove_number
        for index in range(0, len(padded), 2):
            white = padded[index] or "…"
            black = padded[index + 1] if index + 1 < len(padded) else ""
            rows.append(f"{first + index // 2:>3}. {white:<8} {black}")
        self.move_list.delete(0, tk.END)
        for row in rows:
            self.move_list.insert(tk.END, row)
        if rows:
            self.empty_moves_label.grid_remove()
            self.move_list_frame.grid()
            self.move_list.selection_clear(0, tk.END)
            self.move_list.selection_set(len(rows) - 1)
            self.move_list.see(len(rows) - 1)
        else:
            self.move_list_frame.grid_remove()
            self.empty_moves_label.grid()

    def _on_selection_changed(self, message: str) -> None:
        if message or self.interaction_text.get() == self._board_feedback:
            self.interaction_text.set(message)
        self._board_feedback = message

    # ----- lifecycle --------------------------------------------------------
    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._unsubscribe_view()
        del self._unsubscribe_view
        try:
            self.root.after_cancel(self._poll_job)
        except (tk.TclError, ValueError):
            pass
        self.controller.shutdown()
        if self.db is not None:
            self.db.close()
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def _read_local_pack(task: Callable[[], PuzzlePack], results: SimpleQueue[PuzzlePack | str]) -> None:
    try:
        results.put(task())
    except (PackError, OSError) as error:
        results.put(str(error))


def _probe_connection(config: EngineConfig, results: SimpleQueue[tuple[str, int] | str]) -> None:
    try:
        results.put(probe_engine(config))
    except (UCIEngineError, ValueError) as error:
        results.put(str(error))


class EngineDialog:
    """Configure a locally installed UCI engine; tests run on a worker thread."""

    def __init__(self, app: ChessApp) -> None:
        self.app = app
        t = app.t
        self.window = tk.Toplevel(app.root)
        self.window.title(t("engine.title"))
        self.window.transient(app.root)
        self.window.configure(background=ACETATE, padx=16, pady=14)
        self.path_var = tk.StringVar(self.window, value=app.settings.engine_path or "")
        self.status_var = tk.StringVar(self.window, value="" if app.settings.engine_path else t("engine.missing"))
        self._results: SimpleQueue[tuple[str, int] | str] = SimpleQueue()
        self._probe_job: str | None = None
        tk.Label(self.window, text=t("engine.explain"), background=ACETATE, foreground=INK, wraplength=420,
                 justify="left", font=("TkDefaultFont", FONT_SIZES["body"])).grid(row=0, column=0, columnspan=3, sticky="ew")
        tk.Label(self.window, text=t("engine.path_label"), background=ACETATE, foreground=INK,
                 font=("TkDefaultFont", FONT_SIZES["caption"], "bold")).grid(row=1, column=0, sticky="w", pady=(12, 2))
        self.entry = tk.Entry(self.window, textvariable=self.path_var, width=48)
        self.entry.grid(row=2, column=0, columnspan=2, sticky="ew")
        app._button(self.window, t("button.browse"), self._browse).grid(row=2, column=2, padx=(6, 0))
        tk.Label(self.window, textvariable=self.status_var, background=ACETATE, foreground=MUTED_INK, wraplength=420,
                 justify="left", font=("TkDefaultFont", FONT_SIZES["caption"])).grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)
        buttons = tk.Frame(self.window, background=ACETATE)
        buttons.grid(row=4, column=0, columnspan=3, sticky="e")
        self.test_button = app._button(buttons, t("button.test_engine"), self.test)
        self.test_button.grid(row=0, column=0, padx=3)
        app._button(buttons, t("button.use_mock"), self.use_mock).grid(row=0, column=1, padx=3)
        app._button(buttons, t("button.save"), self.save, role="new").grid(row=0, column=2, padx=3)
        app._button(buttons, t("button.cancel"), self.window.destroy).grid(row=0, column=3, padx=3)
        self.window.bind("<Escape>", lambda _e: self.window.destroy())
        self.window.bind("<Destroy>", self._cancel_probe_poll)
        self.entry.focus_set()

    def _browse(self) -> None:
        path = filedialog.askopenfilename(parent=self.window, title=self.app.t("engine.path_label"))
        if path:
            self.path_var.set(path)

    def test(self) -> None:
        try:
            config = EngineConfig.from_path(self.path_var.get().strip())
        except EngineConfigError as error:
            self.status_var.set(self.app.t("engine.test_failed", error=error))
            return
        self.status_var.set(self.app.t("engine.testing"))
        self.test_button.configure(state=tk.DISABLED)

        threading.Thread(target=_probe_connection, args=(config, self._results),
                         name="engine-test", daemon=True).start()
        self._probe_job = self.window.after(50, self._check)

    def _check(self) -> None:
        self._probe_job = None
        try:
            result = self._results.get_nowait()
        except Empty:
            self._probe_job = self.window.after(50, self._check)
            return
        self.test_button.configure(state=tk.NORMAL)
        if isinstance(result, str):
            self.status_var.set(self.app.t("engine.test_failed", error=result))
        else:
            name, count = result
            self.status_var.set(self.app.t("engine.test_ok", name=name, count=count))

    def _cancel_probe_poll(self, event: tk.Event) -> None:
        if event.widget is self.window and self._probe_job is not None:
            self.window.after_cancel(self._probe_job)
            self._probe_job = None

    def use_mock(self) -> None:
        self.path_var.set("")
        self.save()

    def save(self) -> None:
        path = self.path_var.get().strip() or None
        if path is not None:
            try:
                EngineConfig.from_path(path)
            except EngineConfigError as error:
                self.status_var.set(self.app.t("engine.test_failed", error=error))
                return
        self.app._store_settings(engine_path=path)
        self.app._provider_stale = True  # the next bot game builds a provider from the new setting
        self.app.interaction_text.set(self.app.t("engine.saved"))
        self.window.destroy()


def launch(*, board_design: BoardDesign | None = None, top_pieces: bool = False) -> None:
    root = tk.Tk()
    artwork = None
    if board_design is not None:
        artwork = BoardArtwork(board_design)
        try:
            artwork.image(root, 8, flipped=False)
        except tk.TclError as error:
            root.destroy()
            raise BoardArtworkError(f"SVG board preview needs an SVG-capable Tk renderer: {error}") from error
    renderer = OwnerSvgPieces(top_view=True) if top_pieces else None
    ChessApp(root, data_layout=DataLayout.default(), board_artwork=artwork, piece_renderer=renderer)
    root.mainloop()
