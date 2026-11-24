# ADR-002 – UI-Stack und Glide Shell

**Status: DECIDED (23.11.2026) – Technische Integration von Glide Shell 0.6.2 (Glide `v1.0.2`) freigegeben; CairoSVG-Runtime weiterhin gesperrt.**

Entscheidung des Inhabers (23.11.2026, Argon Master-Prompt / Q-006):
- **UI-Fundament:** Chess & Chains übernimmt die anwendungsneutrale **Glide Shell `0.6.2`** aus `n05a-design/glide-to-do` Release `1.0.2`, Git-Tag `v1.0.2`, Commit `7dcd8dc04366f88943fa17827882cef4d81421b8` (Lizenz `MPL-2.0`).
- **Übernahmeweg:** Reproduzierbare Paketkopie nach `src/glide_shell/` mittels `01_Repository/Glide/scripts/pflege/shell_uebernehmen.py --commit 7dcd8dc04366f88943fa17827882cef4d81421b8 --agenten-bootstrap` mit SHA-256-Integritätsanker (`src/glide_shell/SHELL_MANIFEST.json`).
- **Architekturgrenze:** Kein Import von `glide.app` oder Glide-To-do-Fachmodellen; keine manuelle Bearbeitung von `src/glide_shell/`; `chess_and_chains.chess`, `game`, `engines` und `puzzles` bleiben frei von Tk- und Shell-Imports.
- **Abgrenzung:** Die Freigabe betrifft die technische Framework-Migration, nicht automatisch eine Produktveröffentlichung (W12) oder die Aufnahme zusätzlicher Drittkomponenten (z. B. CairoSVG oder GPL-Engines).

Vorschlag (historischer Ausgangsstand vor Freigabe): Python; Standardbibliothek für Headless-Core und initiale Prüfungen; Tk/Tk9 als bevorzugter UI-Stack **nach prototypischem SVG-Benchmark**. Alternative PySide6 wurde vom Inhaber nicht ausgewählt.

## W06-SVG-Prototypvergleich (2026-11-20; Tk-Richtung beibehalten)

Der Owner beauftragte einen isolierten Vergleich von Tk/CairoSVG und
Qt/PySide6/QtSvg. Der Messlauf mit einem selbst erstellten 64×64-Pawn-SVG
ergab bei 48/72/96 Pixeln (100 Wiederholungen, macOS 27.2.1, Python 3.14.5,
Tk 9.0, CairoSVG 2.9.1, Qt 6.12.0) folgende p95-Zeiten für Parse+Rasterize+
Widget-Übergabe:

| Größe | Tk/CairoSVG | QtSvg, Renderer neu | QtSvg, Renderer wiederverwendet |
| --- | ---: | ---: | ---: |
| 48 px | 0,611 ms | 0,074 ms | 0,052 ms |
| 72 px | 1,226 ms | 0,101 ms | 0,054 ms |
| 96 px | 1,100 ms | 0,083 ms | 0,065 ms |

Beide Rasterbilder waren visuell ähnlich; die mittlere Kanalabweichung lag
unter 0,55/255. Das ist ein Einzel-SVG-/Ein-Mac-PoC, kein echter DPI-,
Ressourcen-, Interaktions- oder Plattformbenchmark. Mit einem Cache war die
Widget-Übergabe in beiden Varianten unter 0,02 ms. Die Renderer-Laufzeiten
allein belegen daher keinen nötigen Stackwechsel.

Die Tk/CairoSVG-Ausführung benötigte installierte native Cairo-/libffi-
Bibliotheken und ein gesetztes `DYLD_FALLBACK_LIBRARY_PATH`; ohne diesen
Bibliothekspfad scheiterte der isolierte Import. CairoSVG ist laut PyPI
LGPL-3.0-or-later und führt mehrere Python-Abhängigkeiten auf. Die
PySide6-Essentials-Installation enthält QtSvg, war im Evaluations-venv rund
350 MiB groß und weist laut PyPI LGPL-3.0-only OR GPL-2.0-only OR
GPL-3.0-only aus; konkrete Qt-Lieferdateien und LGPL-/GPL-Pflichten sind
nicht abschließend geprüft. Diese Größen sind Messwerte der Installationen,
keine garantierten Endartefaktgrößen.

**Owner-Richtung (2026-11-20):** Tk für W06 beibehalten und die
CairoSVG-Plattform-/Offline-Paketierung prüfen; Qt wurde nicht ausgewählt.
Damit ist Q-005 für die W06-Stackrichtung geschlossen. Das ist keine
Freigabe, CairoSVG als Runtime-Abhängigkeit aufzunehmen.

Der nachfolgende PyInstaller-Einordner-PoC konnte das Cairo-Backend und seine
17 nativen Bibliotheken in ein 37-MiB-Verzeichnis übernehmen. Der frische
Prozess fand die gebündelte Cairo-Datei aber erst nach einer zusätzlichen
`libcairo.2.dylib`-Aliasdatei und einem Startsuchpfad auf das gebündelte
Verzeichnis; die Sandbox-Ausführung ohne Netzwerk war damit erfolgreich.
Diese lokale Lösung ist noch kein produktiver `.app`-Launcher und wurde
ausschließlich auf macOS ARM64 geprüft.

Vor einer CairoSVG-Produktintegration bleiben native Bibliotheks- und
Launcherbehandlung, exakte LGPL-/Drittkomponenten-Inventarisierung sowie
Windows-/macOS-x64/Linux-Verhalten zu prüfen. Kein Renderer wurde als
Laufzeitabhängigkeit hinzugefügt; der ADR-Status bleibt PROPOSED. Siehe
`docs/reports/2026-11-20_W06_board-ui.md` und `docs/research/SOURCES.md`.

### Weitere Plattformen – Metadaten-/Wheel-Audit (2026-11-20)

`pip download --only-binary=:all:` fand passende Python-Wheels für
CairoSVG 2.9.1 samt Python-Abhängigkeiten für `win_amd64`, `macosx_10_13_x86_64`
und `manylinux` x86_64 mit CPython 3.14. Diese Wheels enthalten **nicht**
die native Cairo-Laufzeit. Die CairoSVG-/cairocffi-Dokumentation verlangt
weiterhin native Cairo-/FFI-Bibliotheken; unter Windows insbesondere
`libcairo-2.dll` und einen Suchpfad, unter Linux native Shared Libraries,
unter macOS Cairo und libffi. PyInstaller baut laut Dokumentation pro
aktivem Betriebssystem/Python/Wortbreite und nimmt Standard-Systembibliotheken
nicht mit.

Nur der macOS-ARM64-Smoke wurde tatsächlich gebaut und im
Netzwerk-deny-Sandboxprofil ausgeführt. Windows, macOS x64 und Linux sind
**nicht getestet**; Wheel-Verfügbarkeit ist kein ABI-, Paketierungs- oder
Offline-Nachweis. Für eine belastbare Abnahme braucht es echte Builds und
Smoke-Tests auf den jeweiligen Zielsystemen.
