# W07 · Bereitschaftstest für lokale UCI-Engines

**21.11.2026 · KI-unterstützt.** Basis des lokalen Folgeschritts `5d63502` auf `codex/chess-chains-figuren-w07`.

## Änderung

- *Engine testen* verwendet den konfigurierten lokalen Prozess und wartet zuerst auf `uciok`, dann auf `readyok`. Der Dialog zeigt bei Erfolg den von der Engine gemeldeten Namen und die Anzahl ihrer UCI-Optionen. Fehlt ein Name, erscheint der konfigurierte Anzeigename.
- Der Worker gibt Ergebnisdaten per Queue an Tk zurück. Beim Schließen des Dialogs endet die Tk-Abfrage. Der Verbindungsversuch schließt seinen Prozess auch bei fehlender Bereitschaft. Der Engine-Pfad wird erst durch *Speichern* übernommen.
- Die projekteigene Mock-Engine kann einen Abbruch nach `uciok` simulieren. Die Adapter- und Tk-Tests unterscheiden diesen Fall von einer bereiten Engine und prüfen, dass ein geschlossener Dialog seinen ausstehenden Tk-Callback entfernt.

## Validierung

Alle Laufzeittests nutzten Windows 11 x64 mit Tk 9.0.4, `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`.

| Befehl | Ergebnis |
| --- | --- |
| `python -m unittest discover -s tests -v` · Python 3.15.1 | 187 Tests in 102,249 Sekunden, Exitcode 0. Der Schlusslauf umfasst die Poll-Cleanup-Regression. |
| `py -3.14 -c "import faulthandler, unittest; faulthandler.dump_traceback_later(90, exit=True); unittest.main(module=None)" tests.test_board_ui tests.test_app_integration -q` · Python 3.14.7 | 51 Tk-Tests in 22,192 Sekunden, Exitcode 0. |
| `python scripts/verify_document_links.py`, `python scripts/verify_starter.py`, `python scripts/check_policy.py`, `python -m compileall -q src app scripts tests`, `git diff --check` | Jeweils Exitcode 0. |

## Nächste Schritte

1. W07 bleibt nur mit der projekteigenen Mock-Engine nachgewiesen. Ein Test gegen eine konkrete Dritt-Engine und ihre Auslieferung unterliegen [ADR-001](../decisions/ADR-001_ENGINE_LICENSE.md).
2. Nach Freigabe die echte Engine mit Version, Binary-Hash und Plattforminventar im vollständigen lokalen Spiel prüfen. Kalibrierung und Elo-Beschriftung gehören zu [ADR-007](../decisions/ADR-007_BOT_PRESETS.md).
3. Der native macOS-Gegenlauf zur vorherigen Tk-Korrektur ist im [CI-Bericht](2026-11-21_W11-ci-nach-pr6.md) als offen dokumentiert.
