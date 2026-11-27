"""Present an independent analysis job in the existing desktop shell.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from glide_shell import modal_session, window_lifetime

from ..engines.analysis import AnalysisJob, AnalysisProgress, AnalysisResult, CriticalMoment, EvaluationKind, JobStatus, ScoreBound, critical_moments
from ..i18n import Translator


class AnalysisDialog:
    def __init__(
        self, root: tk.Tk, translate: Translator, analysis: AnalysisJob | AnalysisProgress, background: str,
        save_position: Callable[[AnalysisResult], str] | None = None,
        store_report: Callable[[AnalysisProgress], str] | None = None,
    ) -> None:
        self.t = translate
        self.job = analysis if isinstance(analysis, AnalysisJob) else None
        self.store_report = store_report
        self.save_position = save_position
        self.window = modal_session.create_dialog(root, translate("analysis.title"), background=background)
        self.scope = window_lifetime.scope_for(self.window)
        content = ttk.Frame(self.window, padding=12, style="Glide.TFrame")
        content.pack(fill="both", expand=True)
        self.status = tk.StringVar(self.window)
        ttk.Label(content, textvariable=self.status, style="Glide.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w",
        )
        self.output = tk.Text(content, height=15, width=58, wrap="word", state="disabled", takefocus=True)
        scroll = ttk.Scrollbar(content, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.grid(row=1, column=0, sticky="nsew", pady=8)
        scroll.grid(row=1, column=1, sticky="ns", pady=8)
        self.cancel = ttk.Button(content, text=translate("button.cancel"), command=self._cancel)
        self.cancel.grid(row=3, column=0, sticky="e")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)
        self.window.bind("<Escape>", lambda _event: self.window.destroy())
        self.window.bind("<Destroy>", self._on_destroy, add="+")
        self.cancel.focus_set()
        if isinstance(analysis, AnalysisProgress):
            self._show_results(analysis)
        else:
            self._poll()

    def _cancel(self) -> None:
        if self.job is not None and self.job.progress().status is JobStatus.RUNNING:
            self.job.cancel()
            self.cancel.state(["disabled"])
        else:
            self.window.destroy()

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self.window and self.job is not None:
            self.job.cancel()

    def _poll(self) -> None:
        if self.job is None:
            return
        progress = self.job.progress()
        if progress.status is JobStatus.RUNNING:
            self.status.set(self.t("analysis.progress", done=len(progress.results), total=progress.total))
            self.scope.after(100, self._poll)
            return
        self._show_results(progress)
        if progress.status is JobStatus.COMPLETED and self.store_report is not None:
            self.status.set(self.store_report(progress))

    def _show_results(self, progress: AnalysisProgress) -> None:
        self.status.set(self.t("analysis.failed", error=progress.error) if progress.status is JobStatus.FAILED
                        else self.t(f"analysis.{progress.status.value}"))
        lines = []
        for result in progress.results:
            lines.append(self.t("analysis.position_number", ply=len(result.history)))
            if result.outcome != "active":
                lines.append(self.t("analysis.terminal"))
            for variant in result.lines:
                score = variant.evaluation
                display = self.t("analysis.no_score")
                if score is not None:
                    bound = {ScoreBound.EXACT: "", ScoreBound.LOWER: "≥", ScoreBound.UPPER: "≤"}[score.bound]
                    value = f"{score.value / 100:+.2f}" if score.kind is EvaluationKind.CENTIPAWNS else f"M{score.value:+d}"
                    display = f"{bound}{value}"
                lines.append(f"{variant.rank}  {display}  {' '.join(move.to_uci() for move in variant.moves)}")
            if not result.lines and result.best_move is not None:
                lines.append(self.t("analysis.best_move", move=result.best_move.to_uci()))
            lines.append("")
        moments = critical_moments(progress.results)
        if moments:
            if self.save_position is not None:
                self._add_candidate_picker(moments, progress.results)
            lines.append(self.t("analysis.critical"))
            lines.extend(
                self.t("analysis.moment", ply=item.ply, move=item.played_move.to_uci(),
                       alternative=item.alternative.to_uci(), loss=item.centipawn_loss)
                for item in moments
            )
        self.output.configure(state="normal")
        self.output.insert("1.0", "\n".join(lines))
        self.output.configure(state="disabled")
        self.cancel.configure(text=self.t("button.close"))
        self.cancel.state(["!disabled"])

    def _add_candidate_picker(
        self, moments: tuple[CriticalMoment, ...], results: tuple[AnalysisResult, ...],
    ) -> None:
        positions = {len(result.history): result for result in results}
        save_position = self.save_position
        if save_position is None:
            return
        content = self.output.master
        choices = ttk.Combobox(
            content, state="readonly",
            values=[self.t("analysis.position_number", ply=item.ply - 1) for item in moments],
        )
        choices.grid(row=2, column=0, sticky="w")
        choices.current(0)

        def save() -> None:
            index = choices.current()
            if index >= 0:
                self.status.set(save_position(positions[moments[index].ply - 1]))

        ttk.Button(content, text=self.t("analysis.save_position"), command=save).grid(row=2, column=0, sticky="e")
