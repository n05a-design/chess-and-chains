---
name: glide-shell
description: Anleitung und Regeln für die Nutzung der Glide Shell in diesem Projekt. Verwenden bei UI-Entwicklung mit Tkinter, Dialogen, Tastaturkürzeln oder beim Aktualisieren der Shell.
---

# Glide Shell – Projektnutzung

Dieses Projekt verwendet die **Glide Shell** als UI-Fundament.

## Wichtige Referenzen

- Anleitung: [KI_ANLEITUNG_NEUE_PROJEKTE.md](../../../src/glide_shell/KI_ANLEITUNG_NEUE_PROJEKTE.md)
- Startprompt: [STARTPROMPT_KI.md](../../../src/glide_shell/STARTPROMPT_KI.md)
- Portabler Designvertrag: [DESIGN_RICHTLINIEN.md](../../../src/glide_shell/DESIGN_RICHTLINIEN.md)
- Manifest: [SHELL_MANIFEST.json](../../../src/glide_shell/SHELL_MANIFEST.json)

## Regeln

- Dateien in `src/glide_shell/` nicht manuell ändern.
- Vor und nach UI-Arbeiten: `cd src && python3 -m glide_shell.selftest` (Windows: `Set-Location -LiteralPath 'src' -ErrorAction Stop; python -m glide_shell.selftest`).
- Designvertrag (P1–P6, B15, B11, Kontrast, Fokus) beachten.
