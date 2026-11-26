# Markenressourcen

Alle Dateien in `icons/`, `favicon/`, `emblem/` und `signet/` sowie [`brand-manifest.json`](brand-manifest.json) erzeugt [`scripts/build_brand_assets.py`](../../scripts/build_brand_assets.py) aus den drei Logo-Mastern. Nicht von Hand bearbeiten. Master, Rollen, Fundorte und den Wechselablauf beschreibt der [Logo-Vertrag](../../design/01_Logo/README.md).

| Ordner | Master | Inhalt | Verwendung |
| --- | --- | --- | --- |
| `icons/` | Logo 03 | SVG, PNG 16–1024 px, `chess-and-chains.ico` (16–256), `chess-and-chains.icns` (16–1024 inkl. Retina), `chess-and-chains-macos-1024.png` | README-Kopf (`chess-and-chains-512.png`), macOS-Bundle, künftiger Windows-Installer, Linux-hicolor |
| `favicon/` | Logo 03 | `favicon.svg`, `favicon.ico` (16/32/48), PNG 16, 32, 64, 192, 512 | vorbereitet für eine künftige Produktwebsite oder den Softwarekatalog; eine Website existiert nicht |
| `emblem/` | Logo 02 | SVG, PNG 512 | Presskit, Produktinformationen |
| `signet/` | Logo 01 | SVG, PNG 512 in Originalfarben | Dokumentation; in der App wird Logo 01 zur Laufzeit eingefärbt |

Die Laufzeitkopien für die App liegen im Python-Paket unter [`src/chess_and_chains/ui/brand_assets/`](../../src/chess_and_chains/ui/brand_assets/), damit die App ohne dieses Verzeichnis offline installierbar bleibt.

Prüfung: `python3 -B scripts/build_brand_assets.py --check`.
