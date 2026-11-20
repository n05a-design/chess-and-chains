# Glide Shell Integration Gate – RESERVED / NOT APPROVED

Dieser Ordner ist ein vorgesehener **Integrationspunkt** und **enthält absichtlich keinen Glide-Quellcode**.

**Referenzquellen**
- https://github.com/n05a-design/glide-to-do/blob/main/01_Repository/Glide/docs/GLIDE_SHELL_FRAMEWORK_KONZEPT.md
- https://github.com/n05a-design/glide-to-do/blob/main/01_Repository/Glide/src/glide/README.md
- https://github.com/n05a-design/steps/blob/main/docs/architecture/REUSE_AND_MIGRATION_MATRIX.md

## Voraussetzungen pro übernommener Komponente

- Quelle (`repo`, `branch`, SHA, Pfad, Datei-Hash), kopier-/importierbar laut Lizenz.
- Dependency-Graph inkl. indirekter Fonts/Vendorfiles/Tk-APIs und Herkunft.
- Nachweis, dass kein Aufgaben-/Musik-Fachmodell importiert wird.
- API-Contract plus Mock-bare Headless-Tests und native UI-Regressionstests.
- Release-/Versionierungsstrategie, Eigentümer, update/rollback, dokumentiertes Dependency-Management.

## Reuse-Kandidaten (nur Kandidaten)

`appearance`, `ui_design`, `custom_controls`, `desktop_adapter`, `modal_session`, `runtime_config`, lokalisierte Menüs, brand-/svg-Helfer, settings/storage-adapter. Keine großen Komplettdateien oder `ListApp` kopieren.

## Migrationsmanifest

Erst nach Approval eine Zeile pro Datei in `REUSE_REGISTER.csv` mit `candidate -> isolated -> ported -> reviewed`; `reviewed` setzt unabhängige Tests voraus.

## Quellenstand N02 (2026-11-20, nur lesend via `git ls-remote`/GitHub-Tree)

- `n05a-design/glide-to-do` HEAD `4b6bce086a6dcb8984b8d2ee95e0a267f7a91adb`
- `n05a-design/steps` HEAD `47af95372bf07002d61d88911774119ce1708644`
- Befund: weiterhin **kein eigenständiges Glide-Shell-Paket** (kein `pyproject`/Paket „glide_shell“); neu ist nur
  `01_Repository/Glide/docs/FABLE_GLIDE_SHELL_MIGRATION_PROMPT.md` (Migrationsauftrag, kein Code). Chess & Chains bleibt
  unabhängig; Andockpunkte sind `ui/theme.py` (Tokens), `i18n/`, `storage/settings.py` und `ui/pieces.py` (Renderer-Protokoll).

## Quellenstand W03 (2026-11-20)

Der aktuelle, ausschließlich lesende Audit ist in
`docs/reports/2026-11-20_W03_glide-audit.md` dokumentiert:

- Glide-Referenz: `n05a-design/glide-to-do`,
  `a53e779026295d315983c421bfbc9f42124037f5`.
- Steps-Referenz: `n05a-design/steps`,
  `5c66183bc9833d2fa6cbdeb1be54ebc307ed6f3d`.
- Die Konzeptdatei und das Glide-Systemregister bestätigen kein eigenständig
  freigegebenes Shell-Paket. Die Steps-Migrationsmatrix weist selbst auf ihren
  historischen Basisteil hin.

Dies ist eine Quellenaktualisierung und keine Übernahmefreigabe. Das Register
bleibt bis zu Owner-Approval leer; es wurde kein Glide-Code importiert oder
kopiert.

## Nachprüfung am 20.11.2026

| Repository | GitHub HEAD | Lokaler Stand | Befund |
| --- | --- | --- | --- |
| `n05a-design/glide-to-do` | `55ad7e95e5824820098fb0a1d5d5cab66c0a9947` | `4b6bce086a6dcb8984b8d2ee95e0a267f7a91adb`, Arbeitsbaum mit unversionierten Dateien | Der aktuelle GitHub-Tree enthält flache Glide-Module. Das Shell-Konzept beschreibt das unabhängige Paket als ausstehend. |
| `n05a-design/steps` | `e6baf69d41305be6c499c249d7668c17ea823b7c` | Entwicklungsbranch bei `b05d164733ba0282a14a4a5638d5206d2cfa3bd6` | `pyproject.toml` paketiert `steps-music`. Der Tk-Host importiert Musikmodelle und eigene Dialoge. Die Glide-Migration ist im Architektur-Handover als Ziel beschrieben. |

Die zehn Glide-Blob-SHAs im [W03-Audit](../../docs/reports/2026-11-20_W03_glide-audit.md)
stimmen mit dem aktuellen GitHub-Tree überein. Die dort beschriebene
API-, Lizenz-, Test- und Kopplungslage bleibt die Grundlage für
Themes, Dialoge, Desktopadapter, i18n, Storage und SVG/Branding.

| Kandidat am obigen GitHub-Commit | Git-Blob-SHA | API und Abhängigkeiten | Lizenz, Tests und Übernahmerisiko |
| --- | --- | --- | --- |
| Glide `window_lifetime.py` | `8e5cf1fca73135253cd139b3709f9723a5ffefd0` | `AfterScope` verwaltet Tk-Zeitgeber, `tkinter`, `weakref` | MPL-2.0 im Dateikopf. `test_shell_importregel.py` prüft statisch. Fensterabbau und verbliebene Host-Callbacks brauchen eigene Integrationstests. |
| Glide `action_menu.py` | `6bac9c892c504e14c217b9a13c55272903243b65` | `Entry`, `entries`, `search`, `grouped`. `dataclasses` und internes `content_search` | MPL-2.0 im Dateikopf. `test_action_menu.py` vorhanden. Die transitive Suche und Menüsemantik müssten isoliert werden. |
| Steps `app/ui/main_window.py` | `37a1c522ad19f7b04f49207233ebd86590a10bce` | `StepsMainWindow`, Tk, `LocaleManager`, `ThemeManager`, Musikcontroller und Modelle | Projektlizenz MPL-2.0 laut Paketmanifest. Fassade ist fachlich gekoppelt. Keine Wiederverwendung des Hosts. |
| Steps `design/tokens/tokens.json` | `f4dd9d85b626c6f34750d7010b0aa9417eea03d6` | JSON für den Steps-Theme-Manager, projektspezifische Werte | Projektlizenz laut Paketmanifest. `tests/test_theme_tokens.py` vorhanden. Eignung des Schemas getrennt von Markenwerten und Accessibility prüfen. |

Quellen für das Zielbild und den Ist-Stand stehen in den gepinnten
[Glide-Shell-Unterlagen](https://github.com/n05a-design/glide-to-do/blob/55ad7e95e5824820098fb0a1d5d5cab66c0a9947/01_Repository/Glide/docs/GLIDE_SHELL_FRAMEWORK_KONZEPT.md)
und [Steps-Unterlagen](https://github.com/n05a-design/steps/blob/e6baf69d41305be6c499c249d7668c17ea823b7c/docs/architecture/APP_SHELL_HANDOVER_AND_GLIDE_ROADMAP.md).
Die Upstream-Tests wurden für diese Nachprüfung nur inventarisiert. Der
Integrationsstatus lautet weiterhin RESERVED / NOT APPROVED.
