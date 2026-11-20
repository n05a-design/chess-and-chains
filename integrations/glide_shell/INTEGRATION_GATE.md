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
