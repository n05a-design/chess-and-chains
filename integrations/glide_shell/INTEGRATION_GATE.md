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
