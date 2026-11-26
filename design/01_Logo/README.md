# Logo-Vertrag Chess & Chains

Diese Datei ist die einzige führende Übersicht aller Logo-Master, Logo-Fundorte und des Logo-Wechsels. Aufbau nach dem Grafik-Master von [Glide](https://github.com/n05a-design/glide-to-do/blob/main/20_Grafik_Master/README.md) und `design/brand/README.md` von [STEPS](https://github.com/n05a-design/steps/blob/main/design/brand/README.md). Deren Markenzeichen und Anwendungslogik sind nicht übernommen.

Stand: 26.11.2026, Master **V.2** · Status: IMPLEMENTED und lokal TESTED (Windows 11). CI- und native macOS-/Linux-Abnahme siehe [Prüfbericht](../../docs/reports/2026-11-26_logo-integration.md).

## Die drei Master

Die Master in [`svg/`](svg/) sind verbindliche Originalgestaltungen des Projektinhabers (Affinity-Export aus [`Logo_Chess-&-Chains.af`](Logo_Chess-&-Chains.af)). Aktiv ist **V.2** vom 26.11.2026 (vom Inhaber als `V.2 Logo_Chess-&-Chains.svg`, `…-02.svg`, `…-03.svg` geliefert und hier unter den festen Masternamen abgelegt). V.1 vom 25.11.2026 liegt unverändert in [`Archiv/Chess-&-Chains_V.1_2026-11-25/`](Archiv/Chess-&-Chains_V.1_2026-11-25/). Sie werden nie bearbeitet. Alle Laufzeit-, Paket- und Veröffentlichungsdateien werden daraus abgeleitet.

| Master | Rolle im Code | Funktion | Einfärbung | SHA-256 (LF-Checkout) |
| --- | --- | --- | --- | --- |
| [`Logo_Chess-&-Chains-01.svg`](svg/Logo_Chess-&-Chains-01.svg) | `in_app` | Signet in der Anwendung | dynamisch, Themenfarbe | `339851432a878ee7f8081ae734a48ca0eac62c240754af21e53b658ac5cdd394` |
| [`Logo_Chess-&-Chains-02.svg`](svg/Logo_Chess-&-Chains-02.svg) | `internal_brand` | vollfarbige interne Markendarstellung | nie | `278c85904a701df0570d78d995c285b23dd3c3c2b2a5590bb82a3f45e6990bca` |
| [`Logo_Chess-&-Chains-03.svg`](svg/Logo_Chess-&-Chains-03.svg) | `app_icon` | offizielles App-Symbol und öffentliche Identität | nie | `81026097772f53ab0dfcb7c41d1dcc0a755948e18c252fe00dea8788c721baf4` |

`.gitattributes` setzt `design/01_Logo/svg/*.svg -text`. Damit sind die Bytes auf jedem Betriebssystem gleich und die Prüfsummen stabil.

**Aufbau (geprüft am SVG):** quadratische ViewBox 842 × 842, verschachtelte `matrix()`-Transformationen, gefüllte Pfade aus `M`, `L`, `C`, `Z`, Füllregel `evenodd` (geerbt), runde Linienverbindungen.

| Fläche | 01 | 02 | 03 |
| --- | --- | --- | --- |
| Gelbes Kettenglied `#F4C400` | ✓ | ✓ | ✓ |
| Blaues Kettenglied `#2447D8` | ✓ | ✓ | ✓ |
| Weiße Trennbänder `#FFFFFF` mit schwarzer Haarlinie (0,31 / 0,30 / 0,36 px lokal) | 2 | 2 | 2 |
| Gelbe abgerundete Grundfläche `#FFDC0B` | – | ✓ (Brett bis nahe an den Rand) | ✓ (breiter gelber Außenrahmen) |
| Dunkle Schachbrettfelder `#171920` | – | 99 | 100 |
| Hintergrund | transparent | transparente Ecken | transparente Ecken |

Die Farben stehen als statische Logo-Farben in [`brand-tokens.json`](../../docs/design/brand-tokens.json) (`logo.colors`), getrennt von Theme-, Status-, Brett- und Figurenfarben.

## Logo 01 – dynamisches In-App-Signet

- Laufzeit: [`branding.py`](../../src/chess_and_chains/ui/branding.py) liest `brand_assets/signet.svg` (Bytekopie des Masters) und rastert mit dem Standardbibliotheks-Renderer [`brand_raster.py`](../../src/chess_and_chains/ui/brand_raster.py) in exakter Pixelhöhe.
- **Ableitung:** `brand_raster.signet_layers()` ordnet die vier Flächen zu. Beide Kettenglieder erhalten die Themenrolle `ThemePalette.view_title` (mit `legible_accent()` auf mindestens 4,5 : 1 gegen alle Flächen geprüft). Die weißen Trennbänder werden zu **echten transparenten Aussparungen** (Erase-Compositing in Malreihenfolge). Ihre schwarzen Haarlinien entfallen. Dadurch bleibt die Verschlingung auch einfarbig lesbar: In V.2 malt der Master blaues Glied → Trennband → gelbes Glied → Trennband; das gelbe Glied schneidet sein Trennband in das blaue. Ohne Aussparung verschmelzen beide Glieder (Test `test_separator_bands_become_transparent_cut_outs`). Ein zweiter Tonwert ist deshalb nicht nötig und nicht eingeführt. Keine Verläufe, Schatten, Umrandung oder Kachel.
- **Warum Raster statt Tk-SVG:** Tk 9 (nanosvg) kann keine Aussparung (Erase) zeichnen. Der Renderer liefert auf Tk 8.6 und Tk 9 dieselben Pixel. Für SVG-Verbraucher ohne Erase gibt es `tinted_signet_svg(color, background=…)` mit hintergrundangepassten Trennbändern.
- **Sichtbare Begrenzung:** `signet_bounding_box()` misst nur die beiden Glieder nach allen Transformationen: x 69,5 · y 177,1 · 703,2 × 466,2 Einheiten, Seitenverhältnis 1,508 (V.2). Die ViewBox-Ränder zählen nicht.
- **Kopfzeilenhöhe (Glide B05/D66/D68):** `ChessApp.header_logo_metrics()` setzt die Signethöhe gleich der Strecke von der Versalhöhe des Titels bis zur Grundlinie der Unterzeile. Gemessen am Screenshot (Windows 11): Logo y 33–76, Titel-Versal 34, Unterzeilen-Grundlinie 76; bei großer Schrift 34–82 gegenüber 35/82. Schriftgröße, Schriftgewicht und HiDPI wirken über die Fontmetrik in Pixeln. Unter 900 px Breite und im Kompaktmodus blendet der Minimalkopf das Logo aus. Klick auf das Signet öffnet weiter den Info-Dialog.
- **Themenwechsel:** `_register_theme` → `sync_header_logo()` zeichnet bei jeder Änderung von Theme, Themenfarbe, Hintergrund oder Schrift neu. Der Einstellungsdialog zeigt dasselbe Signet als Themenfarben-Vorschau und aktualisiert es live.

## Logo 02 – vollfarbiges Markenemblem

- Info-Dialog (`ChessApp.show_about_dialog`): `branding.emblem_image(dialog, 88)`. Tk 9 liest `brand_assets/brand-emblem.svg`, Tk 8.6 nutzt `brand-emblem.png` (96 px) oder `brand-emblem-192.png`.
- Nie eingefärbt. Auf hellen und dunklen Dialogflächen unverändert lesbar, weil die gelbe Grundfläche das Motiv trägt.
- Eine Start-, Willkommens- oder Onboarding-Ansicht gibt es nicht. Sie wurde für das Logo nicht neu gebaut.

## Logo 03 – App-Symbol

- Laufzeit: `branding.apply_window_icon(root)` setzt `iconphoto(True, …)` mit 256/128/64/48/32/16 px. Dialoge erben es. Windows erhält zusätzlich `iconbitmap(default=app-icon.ico)` für Taskleiste und Alt-Tab. macOS erhält `app-icon-macos.png` im Apple-Raster für das Dock.
- Vollständige Zeichenfläche einschließlich gelbem Außenrahmen und transparenter Ecken. Nie eingefärbt, kein zusätzlicher Rahmen oder Hintergrund.
- macOS-Rand: nur im ICNS und in `app-icon-macos.png`. Der Körper misst 824 von 1024 px. Die Verkleinerung erfolgt einmal im Generator, nicht zusätzlich im Builder.

## Fundortmatrix

Legende: **aktiv** = im Code oder in der Dokumentation tatsächlich verwendet · **vorbereitet** = Ressource erzeugt, Einsatzort existiert noch nicht.

| Einsatzort | Bisher | Künftig | Ableitung | Besitzende Komponente | Plattform | Status | Prüfung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Hauptfenster-Kopfzeile | orthogonales Connected-System-Signet | 01 | Laufzeit-Raster, Themenfarbe | `app.py` `sync_header_logo` → `branding.draw_signet_canvas` | alle | aktiv | `test_31_…`, `test_logo_roles_…` |
| Spiel-, Zug-, Rätselansicht, Puzzle Lab, Rätselatlas, Partiebibliothek, Partiewiedergabe | gemeinsame Kopfzeile, kein eigenes Signet | 01 über die gemeinsame Kopfzeile | – | `app.py` | alle | aktiv (keine zusätzlichen Kopien) | Sichtprüfung Screenshots |
| Themenfarben-Vorschau im Einstellungsdialog | Farbkreis | 01 | Laufzeit-Raster, 22 px | `appearance_dialog.py` `_draw_swatch` | alle | aktiv | `test_logo_roles_…` (Wechsel bei offenem Dialog) |
| Info-Dialog | Signet 48 px | 02 | `brand-emblem.svg` / `.png` | `app.py` `show_about_dialog` | alle | aktiv | `test_26_…`, `test_logo_roles_…` |
| Start-/Willkommens-/Onboarding-Ansicht | – | 02 | – | – | – | nicht vorhanden | – |
| Fenster-, Dialog-, Fensterlisten-Symbol | dunkle Kachel 64 px | 03 | `app-icon-{16…128}.png`, `app-icon.png` | `branding.apply_window_icon` | alle | aktiv | `test_logo_roles_…` |
| Taskleiste, Alt-Tab | dunkle Kachel | 03 | `brand_assets/app-icon.ico` | `branding.apply_window_icon` | Windows | Fenster/Alt-Tab aktiv; Taskleiste zeigt beim Quellstart das `python.exe`-Symbol (keine AppUserModelID) – OPEN | Smoke Windows 11 |
| Dock, App-Umschalter (laufender Prozess) | Pillow-Inset aus `app-icon.png` | 03 | `app-icon-macos.png` (Apple-Raster) | `branding.macos_dock_icon` | macOS | aktiv, native Sichtprüfung OPEN | `test_macos_dock_icon_…` |
| macOS-App-Bundle, Finder, Spotlight, „Informationen“ | ICNS per Pillow/iconutil | 03 | `assets/branding/icons/chess-and-chains.icns` | `packaging/macos/build_app.py` | macOS | aktiv, nativer Bau OPEN | `test_packaging_references_…` |
| Windows-EXE, Verknüpfungen, Installer, Deinstallation | – | 03 | `assets/branding/icons/chess-and-chains.ico` | `packaging/windows/` | Windows | vorbereitet | `test_icon_resources_complete` |
| WinGet / Homebrew | – | 03 | über Installer/Bundle | `packaging/winget/`, `packaging/homebrew/` | – | nicht vorhanden | – |
| Linux-Programmstarter, Menüs | – | 03 | `chess-and-chains.svg` + PNG-Größen, `.desktop` | `packaging/linux/` | Linux | vorbereitet | `test_packaging_references_…` |
| Root-README Englisch / Deutsch | Text-Überschrift | 03 | `icons/chess-and-chains-512.png`, angezeigt mit 96 px | `README.md`, `README.de.md` | GitHub | aktiv | `test_readmes_use_logo03_…` |
| GitHub-Social-Preview | Connected-System-Entwurf 1200 × 630 | 03 | `marketing/social/chess-and-chains-social-preview.png` | `scripts/build_marketing_images.py` | GitHub | Datei aktiv, Upload manuell OPEN | `test_social_preview_export` |
| Release-Banner, Website-Hero, Kampagne | Connected-System-Studien | – | – | `marketing/source/connected-system-*.svg` | – | historische Studien, nicht aktiv | – |
| Presskit | – | 02, 03 | `emblem/`, `icons/` | `marketing/presskit/` | – | vorbereitet | – |
| Website-Favicon, Produktwebsite, Softwarekatalog | – | 03 | `assets/branding/favicon/` | – | Web | vorbereitet, keine Website | `test_icon_resources_complete` |
| Wortmarke `wordmark.svg` | Manufacturing Consent | unverändert | – | `brand_assets/wordmark.*` | – | kein Logo-Master, derzeit nicht in der UI | – |

## Abgeleitete Dateien

Der Generator [`scripts/build_brand_assets.py`](../../scripts/build_brand_assets.py) erzeugt 41 Dateien. Das Herkunftsmanifest [`assets/branding/brand-manifest.json`](../../assets/branding/brand-manifest.json) nennt zu jeder Datei Master, SHA-256 (Kopien) oder plattformunabhängige Pixel-SHA-256 (Raster).

| Ablage | Inhalt |
| --- | --- |
| `src/chess_and_chains/ui/brand_assets/` (Python-Paket, offline) | `signet.svg/.png` (01), `brand-emblem.svg/.png/-192.png` (02), `app-icon.svg/.png/-16/-32/-48/-64/-128.png`, `app-icon-macos.png`, `app-icon.ico` (03). `wordmark.*` ist nicht generiert. |
| `assets/branding/icons/` | 03: SVG-Kopie, PNG 16, 24, 32, 48, 64, 96, 128, 192, 256, 512, 1024, ICO (16–256), ICNS (16–1024 inkl. Retina), `chess-and-chains-macos-1024.png` |
| `assets/branding/favicon/` | 03: `favicon.svg`, `favicon.ico` (16/32/48), PNG 16, 32, 64, 192, 512 |
| `assets/branding/emblem/` | 02: SVG-Kopie, PNG 512 |
| `assets/branding/signet/` | 01: SVG-Kopie, PNG 512 in Originalfarben |

Der Renderer ist reine Standardbibliothek: 8 × 8-Überabtastung, Box-Filter, Straight-Alpha-PNG. Für PNG-, ICO- und ICNS-Dateien vergleicht `--check` dekodierte Pixel, nicht zlib-Bytes. SVG-Kopien und Manifest werden byteweise verglichen. Er liest nur `svg`, `g`, `rect`, `path` mit Inline-Stil und `matrix()`. `<!ENTITY`, `href`, `<image>`, `<use>`, `<style>`, `<script>` und unbekannte Elemente brechen ab. Es gibt keinen Netzwerkzugriff.

## Logo wechseln

1. Einen der drei Master in `design/01_Logo/svg/` ersetzen (gleicher Dateiname). Abgeleitete Dateien nie von Hand ändern.
2. Neue SHA-256 in `MASTERS` von `scripts/build_brand_assets.py` und in der Tabelle oben eintragen.
3. `python3 -B scripts/build_brand_assets.py` ausführen.
4. In [`ASSET_REGISTER.csv`](../../docs/design/ASSET_REGISTER.csv) nur die betroffenen `BRAND-*`-Zeilen mit den neuen SHA-256 aktualisieren (`python3 scripts/verify_starter.py` meldet Abweichungen).
5. `python3 -B scripts/build_brand_assets.py --check` ausführen, dann `PYTHONPATH=src python3 -m unittest tests.test_brand_assets -v` und die GUI-Tests.
6. Bei Bedarf native Symbole neu bauen: `python3 packaging/macos/build_app.py`.
7. README-Kopf, Social Preview (`python3 scripts/build_marketing_images.py`) und Screenshots prüfen. Die GitHub-Social-Preview manuell unter *Repository → Settings → General → Social preview* hochladen.
8. Änderungen mit Git versionieren.

Ändert ein neuer Master die Struktur von Logo 01 (nicht mehr zwei Glieder plus zwei Trennbänder) oder nutzt er neue SVG-Funktionen, bricht der Generator mit `BLOCKED` ab. Dann muss `brand_raster.py` gezielt erweitert werden.

## Historische Logos

- Das orthogonal konstruierte Connected-System-Signet und die dunkle App-Kachel (KI-unterstützter Kandidat, 20.11.2026) sind nicht mehr aktiv. Ihre Bytes liegen in der Git-Historie vor dieser Änderung. Die Studien in [`design/source/connected-system/`](../source/connected-system/), [`design/concepts/`](../concepts/) und `marketing/source/connected-system-*.svg` bleiben als historische Studien erhalten und dürfen nicht als Programmsymbol oder aktuelles Produktlogo verwendet werden.
- Logo-Master V.1 (25.11.2026): [`Archiv/Chess-&-Chains_V.1_2026-11-25/`](Archiv/Chess-&-Chains_V.1_2026-11-25/) mit SVGs und `.af`, nicht aktiv.
- `Logo_Glide-*.svg`, `Logo_Steps-*.svg`, die übrigen Dateien in [`Archiv/`](Archiv/) und [`Exporte/`](Exporte/) gehören zu Glide und STEPS (Produktfamilie, Ablagevorlage). Sie werden von Chess & Chains nicht verwendet.

## Freigaben und Rechte

Der Projektinhaber Tim von Trostorff hat die drei Logo-Master am 26.11.2026 für die interne Verwendung in der App sowie für Pakete, README, GitHub-Präsentation, Social Preview, Presskit, Favicon und künftige Produktseiten bereitgestellt. Eine Lizenzierung der Marke für beliebige Drittverwendung ist damit nicht erteilt. Die MPL-2.0 des Quellcodes erstreckt sich nicht automatisch auf die Marke. Markenrecherche und Drittnutzung bleiben in [ADR-005](../../docs/decisions/ADR-005_BRAND_ASSETS.md) offen.
