# Logo-Integration der drei Inhaber-Master (W06) – Prüfbericht und Übergabe

**Datum:** 26.11.2026 · **Branch:** `claude/chess-chains-brand-integration-8d2f9b` (Worktree) · **Basis:** `9209e3d` (= `origin/main` beim Start, enthält `78507f4`) · **Umgebung:** Windows 11 Pro, Python 3.15.1, Tk 9.0.4, Pillow 13.0.0 (nur Entwicklerwerkzeuge) · **KI-Unterstützung:** umgesetzt mit Claude Code (Claude Opus 5.5); Gestaltungsfreigabe und Rechtsaussagen bleiben beim Inhaber.

**Master-Stand:** V.2 des Inhabers (26.11.2026, geliefert als `design/01_Logo/V.2 Logo_Chess-&-Chains*.svg` samt aktualisiertem `.af`), unter den festen Namen in `design/01_Logo/svg/` abgelegt. V.1 ist unverändert archiviert in `design/01_Logo/Archiv/Chess-&-Chains_V.1_2026-11-25/`. Alle Ableitungen, Screenshots, Social Preview und Assetregister-Prüfsummen beruhen auf V.2.

Status: **IMPLEMENTED**, lokal **TESTED** (Windows). CI: **OPEN** (nicht gepusht). Native macOS-/Linux-Sichtprüfung: **OPEN**.

## Ergebnis

| Abschlusskriterium | Stand |
| --- | --- |
| Drei Master vorhanden und dokumentiert | ja (V.2) – [Logo-Vertrag](../../design/01_Logo/README.md), SHA-256 im Generator, im Vertrag und im Assetregister |
| Altes In-App-Signet vollständig durch Logo 01 ersetzt | ja – Kopfzeile, Themenfarben-Vorschau; `signet.svg` ist Bytekopie von Logo 01 |
| Logo 01 reagiert dynamisch auf die Themenfarbe | ja – Rolle `view_title`, Test über alle 10 Themes × 8 Themenfarben |
| Verschlingung und Originalgeometrie erhalten | ja – Trennbänder als transparente Aussparungen, Geometrie unverändert aus dem Master |
| Sichtbare Höhe = Titel + Unterzeile | ja – gemessen: Logo y 33–76 · Versalhöhe 34 · Grundlinie 76 (Standard); 34–82 · 35 · 82 (große Schrift) |
| Logo 02 im Info-Dialog, vollfarbig | ja |
| Logo 03 als Programmsymbol | Fenster, Dialoge, Alt-Tab (PNG-Satz + ICO), Dock (Apple-Raster); Windows-Taskleiste beim Quellstart **OPEN** (s. Befund) |
| PNG, ICO, ICNS erzeugt | ja – 41 Ausgaben, Manifest mit Pixel-Prüfsummen |
| macOS-App nutzt Logo 03 | Builder kopiert das generierte ICNS; nativer Bau und Finder/Dock-Sichtprüfung **OPEN** (kein Mac) |
| Windows- und Linux-Ressourcen | ICO und `.desktop`-Vorlage vorbereitet; EXE/Installer existieren nicht (**OPEN**) |
| README EN/DE mit Logo 03 | ja – zentrierter Kopf, Claim, Badges inkl. dynamischem CI-Badge, Navigation, echte Screenshots |
| Social Preview | Datei 1280 × 640, 188 KB erzeugt; Upload in GitHub-Einstellungen **OPEN** (manuell, keine Freigabe für Repo-Einstellungen) |
| Generator funktioniert, `--check` ohne Abweichung | ja |
| Assetregister korrekt | ja – `verify_starter.py` PASS |
| Figurensätze unverändert | ja – kein Diff in `piece_assets`, `pieces.py`, Figuren-Generatoren, Figurentests, Schachkern, Glide Shell |
| Vollständige Testsuite | lokal grün bis auf fehlendes `pytest` (separat grün); CI OPEN |

## Technische Umsetzung

- **`src/chess_and_chains/ui/brand_raster.py` (neu):** Standardbibliotheks-Rasterer für genau die SVG-Teilmenge der Affinity-Master: verschachtelte `matrix()`, `rect`, Pfade `M/L/H/V/C/S/Q/T/Z`, geerbte Füllregel `evenodd`/`nonzero`, Konturen mit runden Verbindungen, Erase-Compositing, PNG/ICO/ICNS-Codec. Sicherheitsprüfung vor dem Parsen (`<!ENTITY`, `href`, `<image>`, `<use>`, `<style>`, `<script>`), kein Netzwerk. Pfadparser aus STEPS übernommen und erweitert. Die vorhandene Glide-Shell-Infrastruktur enthält keinen SVG-Renderer; Glide und STEPS nutzen ebenfalls einen eigenen Standardbibliotheks-Weg.
- **`branding.py` (neu geschrieben, Schnittstellen erhalten):** `brand_image`, `macos_dock_icon`, `read_signet_svg`, `signet_bounding_box`, `signet_aspect`, `cropped_signet_svg`, `tinted_signet_svg`, `render_signet_rgba_png`, `in_app_logo_photo`, `draw_signet_canvas`, `has_svg_support` bleiben. Neu: `LOGO_ROLES`, `emblem_image`, `window_icon_photos`, `apply_window_icon`. Pillow wird zur Laufzeit nicht mehr benötigt.
- **Ableitung Logo 01:** Die Master-Malreihenfolge ist gelbes Glied → Trennband → blaues Glied → Trennband. Glieder werden in `view_title` gemalt, Trennbänder löschen Alpha (Aussparung), Haarlinien entfallen. Ergebnis und Gegenüberstellung: [Logo-Übersicht](assets/2026-11-26-branding/logo-overview.png). Zweiter Tonwert nicht nötig: Ohne Aussparung verschmelzen die Glieder messbar (Test), mit Aussparung bleibt die Überführung lesbar.
- **`app.py`:** `apply_window_icon` statt Einzelbild, Info-Dialog mit `emblem_image(88)`. `header_logo_metrics` unverändert, weil die neue sichtbare Begrenzung die Glide-Höhenregel ohne Anpassung trifft (Messung oben).
- **`appearance_dialog.py`:** Farbkreis durch Signet in der Themenrolle ersetzt.
- **Generator `scripts/build_brand_assets.py`:** 41 Ausgaben, Manifest `assets/branding/brand-manifest.json`, `--check` ohne Schreibzugriff (Exit 0/1/2), Laufzeit ca. 11 s.
- **Paketierung:** `build_app.py` kopiert das generierte ICNS (kein `sips`/`iconutil`/Pillow mehr nötig, Bundle-ID unverändert). `pyproject.toml` packt `brand_assets/*.ico`. Windows-/Linux-READMEs, `.desktop`-Vorlage.
- **`.gitattributes`:** Master und SVG-Kopien `-text`, Raster/ICO/ICNS `binary`. Grund: Mit `core.autocrlf=true` lagen die Master im Windows-Checkout als CRLF vor und hatten andere Prüfsummen als die Git-Blobs.
- **CI:** `build_brand_assets.py --check` im Job *Foundation*, `tests.test_brand_assets` in der Headless-Matrix (Windows/macOS/Linux × Python 3.11/3.14). Neue GUI-Tests laufen in den bestehenden GUI-Jobs.

## Visuelle Abnahme

Echte Aufnahmen der laufenden App mit isolierten Temporärdaten (`scripts/capture_brand_screenshots.py`):

| Nr. | Ansicht | Datei |
| --- | --- | --- |
| 1 | Hauptfenster, Kobaltblau, Original V.06 | [main-cobalt-original.png](../../marketing/screenshots/2026-11-26/main-cobalt-original.png) |
| 2 | Hauptfenster, Türkis | [02-main-turquoise-light.png](assets/2026-11-26-branding/02-main-turquoise-light.png) |
| 3 | Hauptfenster, Bernsteingelb, dunkel | [03-main-amber-dark.png](assets/2026-11-26-branding/03-main-amber-dark.png) |
| 4 | Hellmodus, Himmelblau, Draufsicht V.04.2 | [main-sky-top.png](../../marketing/screenshots/2026-11-26/main-sky-top.png) |
| 5 | Dunkelmodus, Klassisch V.05.1 | [main-dark-classic.png](../../marketing/screenshots/2026-11-26/main-dark-classic.png) |
| 6 | Kontrast dunkel, Smaragdgrün | [06-contrast-dark.png](assets/2026-11-26-branding/06-contrast-dark.png) |
| 7 | Kompaktes Fenster (940 px) | [07-compact-window.png](assets/2026-11-26-branding/07-compact-window.png) |
| 8 | Große Schrift, Liquid Glass | [08-large-font.png](assets/2026-11-26-branding/08-large-font.png) |
| 9 | Info-Dialog mit Logo 02 | [about-dialog.png](../../marketing/screenshots/2026-11-26/about-dialog.png) |
| 10 | Einstellungsdialog mit Signet-Vorschau | [10-settings-theme-preview.png](assets/2026-11-26-branding/10-settings-theme-preview.png) |
| 16 | GitHub-Social-Preview | [chess-and-chains-social-preview.png](../../marketing/social/chess-and-chains-social-preview.png) |
| – | Technische Logo-Übersicht (Master, Laufzeit-Einfärbung, Icon-Größen, macOS-Raster) | [logo-overview.png](assets/2026-11-26-branding/logo-overview.png) |

**Nicht ausgeführt (OPEN):** 11 macOS-Dock, 12 Finder mit neu gebautem Bundle (kein Mac verfügbar), 13 Windows-Explorer-Vorschau (keine EXE), 14/15 README-Köpfe auf GitHub (nicht gepusht; Struktur durch Test geprüft). Die 16-px-Größe zeigt das Schachbrettmuster zwangsläufig als Mischton; das Kettenglied bleibt als blauer Fleck erkennbar (Test). Eine vereinfachte Kleinversion wurde bewusst nicht entworfen.

## Nachweise

Alle Befehle im Worktree auf Basis `9209e3d` plus dieser Änderung, Windows 11, Python 3.15.1, Tk 9.0.4, 26.11.2026:

| Befehl | Ergebnis |
| --- | --- |
| `python -B scripts/build_brand_assets.py --check` | Exit 0 · „OK: 41 brand outputs match the three logo masters.“ |
| `python scripts/verify_starter.py` | PASS |
| `python scripts/verify_document_links.py` | PASS |
| `python scripts/check_policy.py` · `python -m compileall -q src app scripts tests` | PASS · ohne Fehler |
| `PYTHONPATH=src python -m unittest tests.test_foundation tests.test_i18n` | 23 Tests OK |
| `PYTHONPATH=src python -m unittest tests.test_brand_assets` | 27 Tests OK |
| `PYTHONPATH=src PYTHONWARNINGS=error::ResourceWarning python -m unittest discover -s tests` (Stand V.2) | 365 Tests in drei Läufen. Logo- und Branding-Tests stets grün. Immer: 1 Ladefehler `test_piece_sets`, weil `pytest` fehlt (vorbestehend). Zeitweise: `test_tk_event_loop_keeps_running_while_bot_thinks` (Tk-Pause 0,27–0,45 s statt < 0,25 s), auf dem unveränderten Basis-Commit `9209e3d` ebenfalls in 2 von 5 Läufen rot, also vorbestehend; `test_34_promotion_dialog…` einmal rot im Gesamtlauf, bei zwei Einzelwiederholungen grün. |
| `PYTHONPATH=src python -m pytest tests/test_piece_sets.py -q` (separate Wegwerf-venv mit pytest) | 11 passed |
| `cd src && python -m glide_shell.selftest` | 13/13 checks passed, Manifest 23 Dateien |
| `python start_chess_and_chains.py --headless-check` | Exit 0 |
| App-Start und Screenshots (`scripts/capture_brand_screenshots.py`) | Hauptfenster, Info- und Einstellungsdialog öffnen fehlerfrei |

**Befund Windows-Taskleiste:** Beim Quellstart zeigt die Taskleiste das `python.exe`-Symbol, weil Windows nach Prozess gruppiert und keine AppUserModelID gesetzt ist. Titelleiste und Alt-Tab zeigen Logo 03. Behebung erfordert eine Inhaberentscheidung über eine App-ID oder die künftige EXE ([Windows-Paketierung](../../packaging/windows/README.md)). Status OPEN.

Nicht lokal ausgeführt: Tk 8.6 (PNG-Pfad nur per Patch simuliert), Python 3.11/3.14, macOS, Linux. Diese laufen in der CI-Matrix nach dem Push.

## Offene Punkte und nächste Schritte

1. Inhaber: Sichtabnahme der einfarbigen Signet-Ableitung (Aussparungen statt Haarlinien) und der Screenshots.
2. Inhaber: Social Preview unter *Repository → Settings → General → Social preview* hochladen (`marketing/social/chess-and-chains-social-preview.png`).
3. Push und PR nach Freigabe; CI-Lauf abwarten (neue Schritte: Brand-Check, `tests.test_brand_assets`).
4. Auf macOS: `python3 packaging/macos/build_app.py`, `open "build/macos/Chess & Chains.app"`, Dock/Finder/Spotlight/„Informationen“ prüfen.
5. Windows-Installer (eigenes Gate): ICO als EXE-Ressource und für Verknüpfungen verwenden.
6. Linux-Paket (eigenes Gate): hicolor-Installation und `.desktop`-Vorlage.
7. Retina auf macOS: Tk zeichnet Fotobilder in Punktgröße; ein schärferes Signet bräuchte doppelte Rasterauflösung mit Tk-Skalierung (Backlog).

## Rücknahme

Revert des Commits stellt das alte Signet, die alte Kachel und den alten Renderer wieder her. Die Master in `design/01_Logo/svg/` waren schon vorher versioniert und bleiben unberührt.
