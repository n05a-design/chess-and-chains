# README

Ziel: Linux-Quellstart zuerst, später abgestimmtes AppImage/Flatpak inkl. Runtime-Dokumentation.

## Programmsymbol (vorbereitet)

Logo 03 ([Logo-Vertrag](../../design/01_Logo/README.md)) für Freedesktop-Starter:

- Vorlage [`chess-and-chains.desktop`](chess-and-chains.desktop) mit `Icon=chess-and-chains`.
- Symbole nach hicolor-Konvention installieren, zum Beispiel
  `assets/branding/icons/chess-and-chains.svg` → `share/icons/hicolor/scalable/apps/chess-and-chains.svg` und
  `assets/branding/icons/chess-and-chains-{16,24,32,48,64,128,256,512}.png` → `share/icons/hicolor/<N>x<N>/apps/chess-and-chains.png`.
- Fensterliste und Alt-Tab: Die Tk-App setzt Logo 03 über `branding.apply_window_icon()` (`iconphoto` mit 16 bis 256 px).

Status: Ressourcen IMPLEMENTED. Ein Linux-Paket (AppImage/Flatpak) existiert nicht; Installation der Starterdatei bleibt OPEN.
