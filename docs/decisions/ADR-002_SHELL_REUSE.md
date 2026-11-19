# ADR-002 – UI-Stack und Glide Shell

**Status: PROPOSED – keine Portierung freigegeben.**

Vorschlag: Python; Standardbibliothek für Headless-Core und initiale Prüfungen; Tk/Tk9 als bevorzugter UI-Stack **nach prototypischem SVG-Benchmark**. Die Glide-Shell ist laut Glide-Konzept vom 17.11.2026 noch kein unabhängig abgenommenes Paket. Kein `from glide.app ...`, kein Kopieren von `ListApp`.

Ein Wiederverwendungsmodul wird nur übernommen nach: exakter Quell-SHA, Dateien-/Lizenzinventar, Abhängigkeitsmatrix, Testisolierung, API-Vertrag, Performance/Mac-Windows-Linux-Befund, Regressionsnachweisen, Rollback. Ziel `integrations/glide_shell/` bleibt bis dahin reserviert. Alternative PySide6 nur nach UX-/Performance-Vergleich samt Lizenzcheck; Qt bringt eigene Paket- und UI-Migrationskosten.

Offen: Bridge vs. eigenständiges `glide-shell`-Package; gemeinsamer Codeowner; Versionierung, Akzeptanzkriterien.
