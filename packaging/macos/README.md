# macOS Local App Bundle

Build a local ad-hoc signed standalone `Chess & Chains.app` (`codesign` and the local python.org framework):

```sh
python3 -B scripts/build_brand_assets.py --check
python3 packaging/macos/build_app.py
open "build/macos/Chess & Chains.app"
```

## Programmsymbol

- Quelle: Logo 03, [`design/01_Logo/svg/Logo_Chess-&-Chains-03.svg`](../../design/01_Logo/README.md).
- Bundle-Datei: `Contents/Resources/ChessAndChains.icns`, kopiert aus [`assets/branding/icons/chess-and-chains.icns`](../../assets/branding/README.md). `Info.plist` → `CFBundleIconFile = ChessAndChains.icns`.
- Das ICNS enthält 16 bis 1024 px einschließlich Retina-Varianten (`icp4` … `ic14`). Der Generator legt Logo 03 einmal in das Apple-Icon-Raster (Körper 824 von 1024 px, transparente Außenfläche). Der gelbe Außenrahmen gehört zu Logo 03 und wird nicht verkleinert oder ersetzt. Es gibt keine zweite Verkleinerung im Builder.
- Laufzeit: Das Dock-Symbol des laufenden Prozesses setzt `branding.macos_dock_icon()` aus `brand_assets/app-icon-macos.png` (dasselbe Raster).
- Bundle-ID `de.n05a.chessandchains` und Anzeigename bleiben unverändert.
- Zeigt Finder noch ein altes Symbol: zuerst Pfad des geöffneten Bundles, `Info.plist` und die SHA-256 der `.icns` prüfen. Keine pauschalen Systemcache-Löschungen.

Status: Ressourcen IMPLEMENTED und geprüft (`tests/test_brand_assets.py`). Native Sichtprüfung von Dock, Finder, Spotlight und App-Umschalter auf macOS: OPEN (Arbeitsplatz dieser Integration war Windows).

Ziel für das Release-Gate: native Mac-App (ARM64/Intel-Abnahme), Developer-ID-Signierung/Notarisierung und Homebrew Cask mit echtem Releasehash.
