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
from queue import Empty, SimpleQueue
from weakref import proxy
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Sequence

from ..chess import ChessError, ChessGame, Color, GameStatus, Move, export_pgn, square_name, to_san
from ..engines.bot import EngineConfig, EngineConfigError, MoveProvider, UCIBot, probe_engine, resolve_engine_config
from ..engines.presets import BotPreset, load_presets
from ..engines.uci import UCIEngineError
from ..game import BotStatus, GameController, GameSetup, GameView, PlayMode
from ..i18n import Translator
from ..puzzles import PuzzlePack, PuzzleSession, Verdict, load_demo_pack
from ..storage import Database, DataLayout, Settings, StorageError, load_settings, save_settings
from .atlas import PuzzleAtlas
from .board import BoardCanvas, Orientation
from .board_artwork import BoardArtwork, BoardArtworkError, BoardDesign
from .branding import brand_image
from .pieces import OwnerSvgPieces, PieceRenderer
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
            button.grid(row=0, column=index, sticky="ew", padx=(0, 3))
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
        if data_layout is not None:
            self.settings, self.settings_warning = load_settings(data_layout.settings)
            try:
                self.db: Database | None = Database.open(data_layout.database)
            except StorageError as error:
                # Never modify a database we cannot handle; run without persistence.
                self.db = None
                self.settings_warning = str(error)
        else:
            self.settings, self.db = Settings(), None
        self.t = Translator(locale or self.settings.locale)
        self.presets = load_presets()
        self._provider_factory = provider_factory
        self.controller = GameController()
        self._unsubscribe_view = self.controller.subscribe(self._on_view)
        self.orientation: Orientation = "white"
        self.active_panel = "play"
        self.pack = puzzle_pack or load_demo_pack()
        self._puzzle_selection = self.pack.puzzles
        self._puzzle_themes = sorted({theme for puzzle in self.pack.puzzles for theme in puzzle.themes})
        self.puzzle_index = 0
        self.puzzle: PuzzleSession | None = None
        self._puzzle_recorded = False
        self._solved_puzzle_ids: set[str] = set()
        self._provider_stale = False
        self._game_headers: dict[str, str] = {}
        self._closed = False
        self.interaction_text = tk.StringVar(root)
        self.panel_text = tk.StringVar(root)
        self.header_mode_text = tk.StringVar(root)
        self.action_state_text = tk.StringVar(root)
        self.bot_text = tk.StringVar(root)
        self.puzzle_title_text = tk.StringVar(root)
        self.puzzle_meta_text = tk.StringVar(root)
        self.puzzle_feedback_text = tk.StringVar(root)
        self.puzzle_progress_text = tk.StringVar(root)
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
        if self.settings_warning:
            self.interaction_text.set(self.settings_warning)

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
        self.root.title(t("app.window_title"))
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
        tk.Label(board_sheet, text=t("board.pieces"), background=ACETATE, foreground=INK,
                 font=("TkDefaultFont", FONT_SIZES["caption"], "bold"), anchor="w", padx=14, pady=9,
                 ).grid(row=0, column=0, sticky="ew")
        self.board = BoardCanvas(board_sheet, lambda moves: app._on_move_requested(moves),
                                 lambda detail: app._on_selection_changed(detail),
                                 artwork=self._board_artwork, renderer=piece_renderer)
        self.board.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        tk.Label(board_sheet, textvariable=self.interaction_text, background=ACETATE, foreground=MUTED_INK,
                 font=("TkDefaultFont", FONT_SIZES["caption"]), anchor="w", padx=14, pady=8,
                 ).grid(row=2, column=0, sticky="ew")

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
            for button in self.mode_buttons.values():
                button.configure(wraplength=max(1, width - 35), justify="left")

        self._bind_panel_scroll(
            canvas, panel, (*paired_buttons, *self.mode_buttons.values(), self.level_menu, self.new_game_button),
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
            font=("TkFixedFont", 11), relief="solid", borderwidth=1, highlightthickness=1,
            highlightbackground=INK, highlightcolor=INK, exportselection=False,
        )
        self.move_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.move_list.yview,
                                 background=CHROME_YELLOW, troughcolor=PAPER, activebackground=INK)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.move_list.configure(yscrollcommand=scrollbar.set)
        list_frame.grid_remove()

    def _build_puzzle_panel(self) -> None:
        t = self.t
        self.puzzle_viewport, canvas, self.puzzle_panel = self._scrollable_panel()
        panel = self.puzzle_panel
        self._label(panel, var=self.puzzle_title_text, role="body", bold=True).grid(row=0, column=0, sticky="ew")
        self._label(panel, var=self.puzzle_meta_text, role="caption", muted=True).grid(row=1, column=0, sticky="ew", pady=(2, 8))
        if self.pack.manifest.demo:
            self._label(panel, text=t("puzzle.demo_notice"), role="caption", muted=True).grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.puzzle_feedback_label = self._label(panel, var=self.puzzle_feedback_text, role="body")
        self.puzzle_feedback_label.grid(row=3, column=0, sticky="ew", pady=(4, 12))
        self.hint_button = self._button(panel, t("button.hint"), self._puzzle_hint)
        self.hint_button.grid(row=4, column=0, sticky="ew", pady=3)
        self.solution_button = self._button(panel, t("button.solution"), self._puzzle_reveal)
        self.solution_button.grid(row=5, column=0, sticky="ew", pady=3)
        self.next_puzzle_button = self._button(panel, t("button.next_puzzle"), self._next_puzzle, role="new")
        self.next_puzzle_button.grid(row=6, column=0, sticky="ew", pady=3)
        filters = tk.Frame(panel, background=ACETATE)
        filters.grid(row=7, column=0, sticky="ew", pady=(8, 0))
        filters.grid_columnconfigure(1, weight=1)
        self._label(filters, text=t("puzzle.filter_theme"), role="caption").grid(row=0, column=0, sticky="w")
        self._label(filters, text=t("puzzle.filter_rating"), role="caption").grid(row=1, column=0, sticky="w")
        rating_labels = [
            t("puzzle.rating_from", rating=lower) if upper is None else f"{lower}–{upper}"
            for lower, upper in PUZZLE_RATING_RANGES
        ]
        self.puzzle_theme_filter = ttk.Combobox(
            filters, state="readonly", values=(t("puzzle.all_themes"), *self._puzzle_themes), width=12,
        )
        self.puzzle_rating_filter = ttk.Combobox(
            filters, state="readonly", values=(t("puzzle.all_ratings"), *rating_labels), width=12,
        )
        for row, dropdown in enumerate((self.puzzle_theme_filter, self.puzzle_rating_filter)):
            dropdown.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=2)
            dropdown.current(0)
            dropdown.bind("<<ComboboxSelected>>", self._apply_puzzle_filters)
        self.atlas_section = tk.Frame(panel, background=PAPER, padx=6, pady=4)
        self.atlas_section.grid(row=8, column=0, sticky="ew", pady=(12, 0))
        tk.Label(self.atlas_section, text="Atlas of Moves", background=PAPER, foreground=INK, anchor="w",
                 font=("TkDefaultFont", FONT_SIZES["caption"], "bold"), padx=6, pady=3).pack(fill="x")
        self.puzzle_atlas = PuzzleAtlas(self.atlas_section)
        self.puzzle_atlas.pack(fill="x")
        if self.db is not None:
            self._label(panel, var=self.puzzle_progress_text, role="caption", muted=True).grid(
                row=9, column=0, sticky="ew", pady=(6, 0),
            )
        controls = (self.hint_button, self.solution_button, self.next_puzzle_button,
                    self.puzzle_theme_filter, self.puzzle_rating_filter)

        def resize_buttons(width: int) -> None:
            for button in controls[:3]:
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
        return tk.Button(
            master, text=label, command=command, background=background, foreground=foreground,
            activebackground=INK, activeforeground=ACETATE, disabledforeground=DISABLED_INK, relief="solid",
            borderwidth=1, highlightthickness=1, highlightbackground=background, highlightcolor=INK,
            padx=10, pady=7, anchor="w", font=("TkDefaultFont", FONT_SIZES["body"], "bold"),
        )

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
        actions: Sequence[tuple[str, Callable[[int | None], None], bool]] = (),
    ) -> int | None:
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        content = ttk.Frame(dialog, padding=12)
        content.grid(sticky="nsew")
        selection = ttk.Combobox(content, values=labels, state="readonly" if labels else "disabled", width=46)
        selection.grid(row=0, column=0, columnspan=len(actions) + 2, sticky="ew", pady=(0, 10))
        if labels:
            selection.current(0)
        else:
            selection.set(empty)
        chosen = None
        action = None

        def accept(callback: Callable[[int | None], None] | None = None) -> None:
            nonlocal chosen, action
            index = selection.current()
            chosen = index if index >= 0 else None
            action = callback
            dialog.destroy()

        confirm_button = ttk.Button(content, text=confirm, command=accept, state="normal" if labels else "disabled")
        confirm_button.grid(row=1, column=0, padx=4)
        for column, (label, callback, requires_selection) in enumerate(actions, 1):
            state = "disabled" if requires_selection and not labels else "normal"
            button = ttk.Button(content, text=label, command=lambda callback=callback: accept(callback), state=state)
            button.grid(row=1, column=column, padx=4)
            if not labels and not requires_selection:
                button.focus_set()
        ttk.Button(content, text=self.t("button.cancel"), command=dialog.destroy).grid(
            row=1, column=len(actions) + 1, padx=4,
        )
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        if labels:
            selection.bind("<Return>", lambda _event: accept())
            selection.focus_set()
        dialog.grab_set()
        self.root.wait_window(dialog)
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
            rows = self.db.list_games()
            labels = [self.t("library.entry", id=game_id, date=created, result=result)
                      for game_id, created, result, _mode in rows]
            chosen = self._choose_item(
                self.t("button.library"), labels, self.t("library.open"), empty=self.t("library.empty"),
                actions=(
                    (self.t("library.import"), lambda _index: self._import_pgn_file(), False),
                    (self.t("library.export"), lambda index: self._export_pgn_file(rows[index][0])
                     if index is not None else None, True),
                ),
            )
            if chosen is None:
                return
            saved = self.db.load_game(rows[chosen][0])
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

    # ----- puzzles --------------------------------------------------------
    def _apply_puzzle_filters(self, _event: tk.Event | None = None) -> None:
        theme_choice = self.puzzle_theme_filter.current()
        theme = self._puzzle_themes[theme_choice - 1] if theme_choice > 0 else None
        rating_choice = self.puzzle_rating_filter.current()
        lower, upper = PUZZLE_RATING_RANGES[rating_choice - 1] if rating_choice > 0 else (0, None)
        self._puzzle_selection = tuple(
            puzzle for puzzle in self.pack.puzzles
            if (not theme or theme in puzzle.themes)
            and puzzle.rating >= lower and (upper is None or puzzle.rating <= upper)
        )
        self._update_puzzle_progress()
        if self.puzzle is not None and self.puzzle.puzzle in self._puzzle_selection:
            self.puzzle_index = self._puzzle_selection.index(self.puzzle.puzzle)
            self._refresh()
        else:
            self._start_puzzle(0)

    def _start_puzzle(self, index: int) -> None:
        self._puzzle_recorded = False
        self.puzzle_feedback_text.set("")
        if self._puzzle_selection:
            self.puzzle_index = index % len(self._puzzle_selection)
            self.puzzle = PuzzleSession(self._puzzle_selection[self.puzzle_index])
            self.board.set_orientation("white" if self.puzzle.player_color is Color.WHITE else "black")
        else:
            self.puzzle_index = 0
            self.puzzle = None
        self._refresh()

    def _next_puzzle(self) -> None:
        self._start_puzzle(self.puzzle_index + 1)

    def _update_puzzle_progress(self) -> None:
        if self.db is None:
            return
        try:
            solved = self.db.solved_puzzle_ids(self.pack.manifest.pack_id)
        except sqlite3.Error:
            self._solved_puzzle_ids.clear()
            self.puzzle_progress_text.set(self.t("puzzle.progress_unavailable"))
            return
        self._solved_puzzle_ids = solved
        count = sum(puzzle.puzzle_id in solved for puzzle in self._puzzle_selection)
        self.puzzle_progress_text.set(
            self.t("puzzle.progress", solved=count, count=len(self._puzzle_selection)) if self._puzzle_selection else ""
        )

    def _puzzle_move(self, move: Move) -> None:
        session = self.puzzle
        if session is None or session.finished:
            return
        before = session.state
        feedback = session.submit(move)
        if feedback.verdict is Verdict.CORRECT:
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
        if self.puzzle is None:
            return
        square = self.puzzle.hint()
        if square is not None:
            self.puzzle_feedback_text.set(self.t("puzzle.hint", square=square_name(square)))
            self.board.set_hint(square)

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

    def _open_engine_dialog(self) -> None:
        EngineDialog(self)

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
        self.puzzle_atlas.update_route(self._puzzle_selection, self.puzzle_index, session, self._solved_puzzle_ids)
        if session is None:
            self.atlas_section.grid_remove()
            self.panel_text.set(self.t("puzzle.no_matches"))
            self.puzzle_title_text.set("")
            self.puzzle_meta_text.set("")
            self.board.set_position(None, (), None, False)
            self.hint_button.configure(state=tk.DISABLED)
            self.solution_button.configure(state=tk.DISABLED)
            return
        self.atlas_section.grid()
        self.panel_text.set(self.t("puzzle.title", index=self.puzzle_index + 1, count=len(self._puzzle_selection)))
        self.puzzle_title_text.set(self.t("puzzle.prompt", side=self._side(session.player_color)))
        self.puzzle_meta_text.set(self.t("puzzle.meta", id=session.puzzle.puzzle_id, rating=session.puzzle.rating,
                                         themes=", ".join(session.puzzle.themes[:3])))
        legal = session.legal_moves()
        self.board.set_position(session.state, legal, session.last_move, session.game.rules.is_in_check(session.state))
        state = tk.DISABLED if session.finished else tk.NORMAL
        self.hint_button.configure(state=state)
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
        self.interaction_text.set(message)

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
