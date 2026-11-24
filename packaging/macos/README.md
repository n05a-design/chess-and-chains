# macOS Local App Bundle

Build a local ad-hoc signed standalone `Chess & Chains.app` (using macOS built-in `sips`, `iconutil`, `codesign` and the local python.org framework):

```sh
python3 packaging/macos/build_app.py
open "build/macos/Chess & Chains.app"
```

Ziel für das Release-Gate: native Mac-App (ARM64/Intel-Abnahme), Developer-ID-Signierung/Notarisierung und Homebrew Cask mit echtem Releasehash.
