---
name: chess-ui-engineering
description: UI engineering contract for Chess & Chains built on Glide Shell 0.6.2 (AppHost, single Tk root, window_lifetime.AfterScope, modal_session dialogs, GameController authority, runtime_paths). Use when editing src/chess_and_chains/ui/ or storage/paths.py.
---

# Chess & Chains UI Engineering

Chess & Chains uses **Glide Shell 0.6.2** (`src/glide_shell/`) as its neutral desktop host layer.

## References

- Glide Shell Guide: [KI_ANLEITUNG_NEUE_PROJEKTE.md](../../../src/glide_shell/KI_ANLEITUNG_NEUE_PROJEKTE.md)
- Application Host & UI: [app.py](../../../src/chess_and_chains/ui/app.py)
- Architecture Boundaries: [ARCHITECTURE.md](../../../docs/architecture/ARCHITECTURE.md)

## Rules

- Always launch through `glide_shell.app_host.AppHost` (`create_app_host` / `launch`) with a single `tk.Tk` root.
- Manage all UI timers through `window_lifetime.AfterScope` (`self.scope.after(...)`), never raw unowned `root.after` loops that survive destruction.
- Run all modal dialogs through `glide_shell.modal_session` (`create_dialog`, `run_modal`, `wait_modal`, `remember_focus`, `return_focus`).
- Keep `GameController` as the single authoritative source of truth for chess move undo/redo; never maintain a second conflicting move undo stack.
- Keep `chess_and_chains.chess`, `game`, `engines`, and `puzzles` completely free of `tkinter` and `glide_shell` imports.
- Never edit files inside `src/glide_shell/` manually; update only via `shell_uebernehmen.py`.
