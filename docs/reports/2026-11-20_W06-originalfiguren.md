# W06 · Originale SVG-Schachfiguren im Prototyp

**20.11.2026 · KI-unterstützt · Windows 11 x64.**

## Basis und Freigabe

Lokaler Branch `codex/chess-and-chains-owner-design` auf `b81cced92656521e3eb4ee699faf21964840fe5e`, zum Start direkt gegen GitHub-`main` abgeglichen. Der Arbeitsbaum enthielt bereits die Inhaberentscheidungen, die Wortmarke und die SVG-Brettvorlage. Der [Figurenmaster](../../assets/chess_pieces/source_svg/masters/PROVENANCE.md) stammt von Tim von Trostorff und ist für die App unter MPL-2.0 freigegeben.

## Umsetzung

- **IMPLEMENTED (lokaler Arbeitsbaum)** · Zwölf [editierbare SVG-Einzelgrafiken](../../src/chess_and_chains/ui/piece_assets/) aus sechs originalen Vorderansichten in heller und dunkler Fassung. Gleicher Maßstab und gleiche Grundlinie. Der Originalmaster bleibt bytegleich.
- Das vorhandene Brett nutzt sie als Standard in Spiel und Rätselmodus. Tk 9 zeichnet direkt aus SVG. Ältere Tk-Versionen kopieren passende Größen aus der vorab erzeugten PNG-Grafiktafel. Rasterbilder werden pro Brett begrenzt zwischengespeichert. Schachregeln, Zugzustände, Modi und Datenformate bleiben unverändert.
- Die Laufzeit braucht keine weiteren Grafikbibliotheken. [Erzeugung und Herkunft](../../src/chess_and_chains/ui/piece_assets/PROVENANCE.md) · [Assetregister](../design/ASSET_REGISTER.csv)

## Prüfungen

Die Windows-Prüfungen beziehen sich auf den genannten Basiscommit plus Beschreibung des lokalen Stands.

| Stand und Befehl | Ergebnis und Exitcode |
| --- | --- |
| Ausgangsstand mit Inhaberentscheidungen · `python -m unittest discover -s tests -v`, Python 3.15.1 / Tk 9.0.4, `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` | 172 Tests in 91,548 s, Exitcode 0. |
| Nach Figureneinbau · `python -m unittest tests.test_app_integration.OwnerPieceUiTests tests.test_app_integration.PieceRendererContractTests tests.test_board_ui -v`, gleiche Umgebung | 15 Tests in 3,223 s, Exitcode 0. Partie, Drehung, Rätselmodus, Wiederverwendung und erzwungener PNG-Pfad eingeschlossen. |
| `python scripts/build_piece_fallback.py` mit Tk 9.0.4 | Bei 21 Größen wurden alle zwölf Vektordateien gerendert. Tafel 1536 × 2968 Pixel, Exitcode 0. |
| Native Tk-Sichtprüfung mit lokalem Prüfskript, Windows 11 / Python 3.15.1 / Tk 9.0.4 | Partie bei 860 × 700 und 1200 × 850, Größenwechsel und Rätselmodus. Figuren bei 45,5 px Feldgröße gesehen, Exitcode 0. |
| Gesamtlauf mit Figureneinbau · `python -m unittest discover -s tests -v`, Python 3.15.1 / Tk 9.0.4 mit denselben Umgebungsvariablen | 174 Tests in 91,050 s, keine Skips, Exitcode 0. |
| Zweite Python-Version · `py -3.14 -m unittest tests.test_board_ui tests.test_app_integration -q`, Python 3.14.7 / Tk 9.0.4, dieselben Umgebungsvariablen | 40 Tests in 14,765 s, keine Skips, Exitcode 0. |
| Wheel · `python -m pip wheel --no-build-isolation --no-deps --no-index --wheel-dir <Temp> .`, Installation mit `python -m pip install --no-index --no-deps --target <Temp> <Wheel>` und lokaler Tk-Smoke aus dem installierten Paket | Exitcode 0. 12 SVGs, PNG-Tafel, Provenienz und MPL-Lizenz im Paket. Partie und Rätsel gerendert. SHA-256 des geprüften Wheels `580e05d02346d225c4b95833a272bf56abf551e7447c2d57f2eda3d394b28877`. |
| Statische Prüfung · `python scripts/verify_document_links.py`, `python scripts/verify_starter.py`, `python scripts/check_policy.py`, `python -m compileall -q src app scripts tests`, `git diff --check` und Hashprüfung des Assetregisters | Jeweils Exitcode 0. 20 vorhandene Asset-Dateien stimmen mit den gespeicherten SHA-256-Werten überein. |

## Übergabe

1. Sichtprüfung durch den Inhaber, besonders die Unterscheidbarkeit von Turm und Läufer sowie Dame und König bei kleinen Feldern.
2. Native Plattform- und High-DPI-Abnahme ergänzen. Tests des erzwungenen Fallbacks belegen die Funktionskette, eine Ausführung auf älterem Tk ist separat zu dokumentieren.
3. Individuelle Bretter nach Eingang der SVG-Entwürfe einbinden. Die [Lieferformate](../../assets/boards/source/README.md) sind festgehalten.

Der Stand liegt im lokalen Arbeitsbranch. Ein Rückbau kann Renderer, Assets und begleitende Integration betreffen. Der freigegebene Master und bestehende Spielstände bleiben dabei erhalten.
