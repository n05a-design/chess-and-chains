# Inhaberentscheidungen · Design und Vertriebsweg

**20.11.2026 · KI-unterstützt · Windows 11 Pro x64, Python 3.15.1, Tk 9.0.4.**

## Ausgangsstand

- Repository `n05a-design/chess-and-chains`. Lokaler Arbeitsbranch `codex/chess-and-chains-owner-design` mit Basis `b81cced92656521e3eb4ee699faf21964840fe5e`. Dies war der direkt mit `git ls-remote --symref origin HEAD` bestätigte `main`-Stand nach Merge von PR #5.
- Die Arbeit orientiert sich an Glide `bde7fa12ed048273f2916d21ad1e06b3a0426d0b`. Der Schriftkatalog nennt Rubik als Vorgabe sowie DM Mono, DM Serif Display und Charis SIL. Die öffentliche Installerdefinition nennt Tim von Trostorff als Publisher. [Schriftkatalog](https://github.com/n05a-design/glide-to-do/blob/bde7fa12ed048273f2916d21ad1e06b3a0426d0b/01_Repository/Glide/src/glide/font_catalog.py) · [Installerdefinition](https://github.com/n05a-design/glide-to-do/blob/bde7fa12ed048273f2916d21ad1e06b3a0426d0b/01_Repository/Glide/packaging/windows/glide_setup.iss)

## Entscheidungen und Umsetzung

- **DECIDED** · Connected System als Markenrichtung. Manufacturing Consent für die Wortmarke und prägnante große Überschriften. Der Inhaber gibt die einzelnen Entscheidungen und die spätere Veröffentlichung frei. [ADR-005](../decisions/ADR-005_BRAND_ASSETS.md)
- **DECIDED** · Die Bretter werden vom Inhaber gestaltet. SVG- und Vektormaster bleiben bearbeitbar. Der Inhaber hat alle Rechte an den Originalfiguren bestätigt und ihre App-Nutzung unter MPL-2.0 freigegeben. Die Original-SVG-Übersicht wird als bytegleicher [Master](../../assets/chess_pieces/source_svg/masters/PROVENANCE.md) geführt.
- **DECIDED** · GitHub zeigt Entwicklung und Zielbild. Die fertige, freigegebene App erscheint auf GitHub und im hauseigenen Software-Katalog als kostenloser Download. Die deutschen und englischen README-Texte wurden entsprechend überarbeitet. Launch-Materialien sind zurückgestellt. [ADR-006](../decisions/ADR-006_DISTRIBUTION.md)
- **IMPLEMENTED im lokalen Arbeitsbaum** · [SVG-Lieferanleitung](../../assets/boards/source/README.md) und [64-Felder-Vorlage](../../assets/boards/source/board-template.svg). Vier [Wortmarken-Master](../../design/source/connected-system/) verwenden editierbaren Text. Die App-Kopfzeile verwendet den [Pfadexport](../../src/chess_and_chains/ui/brand_assets/wordmark.svg) mit lokalem PNG-Fallback. Die übrigen Tk-Schriften verwenden die Systemschriftrollen.
- Das Wortbild wurde mit FontTools 4.68.0 aus `ManufacturingConsent-Regular.ttf` von Upstream `80c3d822c2459ac0d76f8cb9d7ca1ca89a068f3b` abgeleitet. Das Schriftpaket bleibt eine Arbeitsquelle. Die App-Ressourcen enthalten die SVG-Pfade und den mit Tk aus demselben Bild erzeugten transparenten PNG-Export. [Upstream-Lizenz](https://github.com/googlefonts/manufacturing-consent-font/blob/80c3d822c2459ac0d76f8cb9d7ca1ca89a068f3b/OFL.txt) · [Assetregister](../design/ASSET_REGISTER.csv)

## Nachweise

Geprüft wird die genannte Basis mit den lokalen Änderungen. Statische Befehle `python scripts/verify_document_links.py`, `python scripts/verify_starter.py`, `python scripts/check_policy.py`, `python -m compileall -q src tests` und `git diff --check` lieferten jeweils Exitcode 0. Eine zusätzliche SVG-/CSV-Prüfung bestätigte die 64 Feldkoordinaten, vier Wortmarken mit editierbarem Text, sieben SHA-256-Werte vorhandener Assets und den transparenten Wortmarken-Fallback mit 254 × 40 Pixeln. Das Tk-Fenster bei 860 × 700 wurde unter Windows mit der neuen Wortmarke geöffnet und visuell geprüft.

- `python -m pip wheel --no-build-isolation --no-deps --no-index --wheel-dir <Temp> .` · Exitcode 0. Im Wheel sind die sechs SVG-/PNG-Ressourcen für Signet, Icon und Wortmarke vorhanden. Der Build enthält keine Schriftdatei.
- Der erste Gesamtlauf mit `python -m unittest discover -s tests -v` und den Variablen `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1` und `PYTHONWARNINGS=error::ResourceWarning` lief mit Exitcode 1 (172 Tests, ein Fehler). `test_user_move_bot_reply_and_ui_update` erreichte die Bot-Antwort im Testzeitraum nicht. Im selben Lauf wurden Tk-Destruktorwarnungen aus einem Worker ausgegeben. Ein isolierter Weakref-Gegencheck zeigte, dass der rekursive Testcallback den Testfall nach dem Schließen bis zur Garbage Collection hielt. Der Testhost löst diese Referenz jetzt auf dem Tk-Thread. Der Gegencheck bestand danach mit deaktivierter Garbage Collection.
- **TESTED** · Wiederholung desselben Befehls mit denselben Variablen am korrigierten lokalen Stand auf `b81cced` (Windows 11, Python 3.15.1, Tk 9.0.4). Exitcode 0, **172 Tests in 80,489 s**, keine Skips und keine Tk-Destruktorwarnungen im Protokoll.

## Übergabe

1. Wenn der Inhaber Bretter liefert, deren SVG-Master prüfen und einen Eingabepfad für die gewählte Form spezifizieren.
2. Den freigegebenen Figurenmaster in App-Einzelexporte überführen. Rendering, Lesbarkeit und Paketprüfung durchführen. Bis dahin bleiben die bestehenden Tk-Testfiguren aktiv.
3. Vor Veröffentlichung die konkreten Markenexports und den fertigen Build zur Inhaberfreigabe vorlegen. Danach Launch-Materialien und Downloadseite beauftragen.

Der Stand liegt im lokalen Arbeitsbranch. Bei einem Rückbau bleiben die Originale in der ursprünglichen Designablage erhalten.
