# W03 – Glide Shell Reuse Audit

**Stand:** 2026-11-20 · **Work Package:** W03 · **Status:** statische
Recherche; keine Portierung, kein Owner-Approval

## Quellen und Beweisgrenzen

- Glide `main`: `a53e779026295d315983c421bfbc9f42124037f5`.
  Das Konzept ist vom 17.11.2026; das Systemregister ist V1.54 vom 19.11.2026.
- Steps `main`: `5c66183bc9833d2fa6cbdeb1be54ebc307ed6f3d`. Die aktuelle
  `REUSE_AND_MIGRATION_MATRIX.md` kennzeichnet ihren größeren Grundlagenteil
  ausdrücklich als historisch; ihre älteren SHA-/Versionsaussagen werden nicht
  als aktuelle Upstream-Fakten ausgegeben.
- Die vorgesehenen Glide- und Steps-Arbeitsverzeichnisse liegen nicht in diesem
  geöffneten Worktree. Die Quellen wurden nur lesend per GitHub API/raw Dateien
  geprüft. Es gab keinen lokalen Datei-/Plattform-/Performance-Test und keine
  Änderung eines anderen Repositories.

Das Glide-Konzept sagt ausdrücklich, dass ein eigenständig nutzbares
Shell-Paket und die skizzierten Schnittstellen **noch nicht abgenommen** sind.
Glide-`app.pyw` ist ein großer Host mit `ListApp`, der viele Fach- und
Shell-Module importiert. Die modulare Ablage allein bedeutet weder
unabhängige Paketierbarkeit noch einen stabilen API-Vertrag.

## Kandidatenübersicht

Die Moduldateien führen `SPDX-License-Identifier: MPL-2.0`. Das gilt nicht
automatisch für Fonts, Marken, Bilder, andere Assets oder transitive
Abhängigkeiten. Die `blob`-Werte unten sind Git-Blob-SHAs am genannten
Glide-Commit, keine SHA-256-Prüfsummen.

| Bereich / Upstream-Datei | Blob SHA | Direkte Imports aus statischer Sicht | Kopplung, Testdatei, vorläufige Einordnung |
| --- | --- | --- | --- |
| `appearance.py` | `562e27d07bd733d20a4738e91f052b936a357d98` | keine Datei-Imports; Register beschreibt Tk-freie Designpaar-/Systemmodusfunktionen | Designwerte sind Glide-geprägt; `tests/unit/test_appearance.py`. **candidate**, noch nicht isoliert oder plattformgeprüft |
| `ui_design.py` | `1fdcaac97ab52d0891bd9dfc2a69c09e5085ac72` | `types.MappingProxyType` | Register trennt neutrale Maße von taskbezogenen Titeln/Layouts; `tests/unit/test_ui_design.py`. **candidate** für ausgewählte Funktionen, nicht das vollständige Modul |
| `custom_controls.py` | `9680b55164c7841e71bf3fa25248078a47df6ad4` | `sys`, `tkinter`, `tkinter.font` | Widgets erhalten Host-Provider für Schrift/Tinte/Hintergrund; Glide-Klassennamen bleiben Kompatibilitätsoberfläche. `tests/integration/test_custom_controls.py`. **candidate**, Tk-/DPI-/Accessibility-Tests auf Ziel-OS fehlen hier |
| `desktop_adapter.py` | `b98845afa77fbfae8df4b6a4ef04a95f62e79568` | `os`, `subprocess`, `sys`, `tkinter` | Enthält plattformspezifische Menü-/Öffnen-/Zwischenablagefunktionen; Host liefert Aktionskennungen und Beschriftungen. `tests/unit/test_desktop_adapter.py`. **candidate**, Prozessstart und OS-Verhalten erfordern separate Prüfung |
| `modal_session.py` | `fca895cd1cb5b932cea39c3ce305b5fc9aed9d20` | `contextlib`, `tkinter` | Generische Modal-/Fokusfunktion; Glide-Kompatibilitätsattribute und `ListApp.run_modal`-Fassade bleiben. `tests/unit/test_modal_session.py`. **candidate**, echter Grab-/Fokus-/Abbauvertrag muss in eigener App geprüft werden |
| `runtime_config.py` | `dc32aac04459b21491433e313ba7c20c9cc56c0f` | `dataclasses`, `json`, `os`, `sys` | Auflösung ist teilweise zustandslos; Namen, Umgebungsvariablen und Speicherpfade sind produktbezogen. `tests/unit/test_runtime_config.py`. **candidate** nur für ein neu entworfenes Chess-&-Chains-Vertragsmodul |
| `i18n.py` | `5f95e8e4fd563152fcd7f2f0ef84dcc0eefc1243` | `json`, `locale`, `os`, `pathlib`, `typing` | Generische Katalogauflösung ist denkbar; Glide-Kataloge, Schlüssel und Startsprache nicht übernehmen. `tests/unit/test_i18n.py`. **candidate** für Schnittstellenmuster, nicht für Produktdaten |
| `svg_geometry.py` | `4b5dd79d14ac97974433d42ab1edad6a414e6121` | `re`, `math`, `xml.etree.ElementTree`, `brand` | Der direkte `brand`-Import und Logo-/Symbolkonventionen verhindern eine unbesehene Übernahme. `tests/unit/test_svg_geometry.py`. **candidate** erst nach Entkopplung von `brand` und eigenen SVG-Fixtures |
| `brand.py` | `cb1c860e8e1eef6a00708b042e97069e620d8e83` | keine Datei-Imports im Modulkopf | Glide-Farben/Logo/Markenwerte sind keine neutrale Shell; fremde Markenassets scheiden aus. Im gezielten Testinventar kein passender `test_brand.py` gefunden. **rejected** als Marken-/Assetübernahme; generische Farbkontrakt-Idee separat neu prüfen |
| `storage_health.py` (Storage-Teilbereich) | `c072b0451553834776aca76aa2af09dfd83d0f97` | `json`, `os` | Speicherbudget, Dateipfade und Sicherungsreserve sind an Glide-Daten-/Ablageverträge gebunden. `tests/unit/test_storage_health.py`. **candidate** nur für ein neu formuliertes Interface; keine Übernahme von Glide-Pfaden oder Datenformaten |

Die Code-Imports sind nur direkte statische Imports der Kandidaten; sie sind
kein vollständiger transitiver Laufzeitgraph. Der Host `app.pyw` importiert
zahlreiche Module und stellt Fassade/Provider bereit. Indirekte GUI-Aufrufe,
Assets, Fonts, Tcl/Tk-Versionen, Modulaufbau und Paketlieferung müssen durch
separate Tests belegt werden. Die oben genannten Upstream-Tests wurden nicht
ausgeführt; ein vorhandener Test ist kein Plattform-Abnahmebeleg.

## Integrationsoptionen

| Option | Plan | Vorteile | Risiken / Gate |
| --- | --- | --- | --- |
| **A – separates Shell-Paket** | Warten, bis Glide eine unabhängig paketierte, versionierte Bibliothek mit API-/Abhängigkeits-/Lizenzvertrag ausweist | Upgrade und Verantwortlichkeit klarer | Ein solches Paket ist am geprüften Stand nicht abgenommen; Versionierung, License-/Asset-BOM, Support und Plattformmatrix fehlen |
| **B – selektive Modulübernahme** | Nur nach Einzelprüfung eigene, isolierte Adapter/Module übernehmen und nötige MPL-Notices, Tests und Update-/Rollbackweg dokumentieren | kleine, messbare Schnittmenge | entkoppelte Teile enthalten teils Hostwerte; höheres Fork-/Wartungsrisiko; Rechte an Drittassets bleiben getrennt |
| **C – neutrales Tk-Board** | Zunächst Chess-&-Chains-eigene Tk-Oberfläche und Adapter entwickeln | unabhängige Produkt-/Datenverträge, kein Glide-Code | eigene Arbeit für Modalität, Accessibility und Rendering |

**Vorschlag, keine Freigabe:** C als Prototyp-Baseline; A erneut prüfen, wenn
Glide ein unabhängiges Release und Vertrag vorlegt. B nur für klar eingegrenzte
Einzelfunktionen nach explizitem Owner-Approval. Keine Komplettkopie von
`app.pyw`/`ListApp`.

## Messbarer PoC- und Rollback-Plan

1. Eigenständige Chess-&-Chains-Test-App mit leerem Tk-Fenster und 8×8-Canvas
   anlegen; keine Glide-Dateien im Importpfad. Für SVG nur testinterne,
   selbst erzeugte Geometrie-Fixtures verwenden, keine unfreigegebenen
   Marken-/Figurenassets.
2. Gegen einen neutralen Tk-Baseline-PoC drei Dinge messen: Zeit bis zum
   stabilen Erstlayout, korrektes Layout bei 100/150/200 % Skalierung und
   Tastatur-/Fokuszugänglichkeit; für Modalität Grab-Freigabe, Escape/Abbruch,
   Fokus-Rückgabe und Fensterabbau automatisiert prüfen.
3. Kandidaten jeweils isoliert und unter genau einem Adapter testen; Importtests
   verbieten `glide`, `ListApp`, Glide-Pfade und Glide-Kataloge im Chess-&-Chains
   Prozess. Alle Messwerte samt Python/Tk-/OS-Version protokollieren.
4. Vor Freigabe keine Übernahme. Bei Regression oder fehlendem Rechtebeleg den
   Adapter entfernen und zum neutralen Tk-PoC zurückkehren; Quellen-SHA und
   Rollback-Commit dokumentieren.

## Status

`integrations/glide_shell/REUSE_REGISTER.csv` bleibt leer (nur Kopfzeile), wie
das Approval-Gate verlangt. ADR-002 bleibt PROPOSED; die Shell bleibt
RESERVED/NOT APPROVED. LOCAL: dieser Auditbericht und Quellenhinweise.
COMMITTED/PUSHED/MERGED/RELEASED: nein.
