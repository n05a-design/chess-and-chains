# README

Ziel: getesteter Windows-x64-Installer, uninstall/upgrade, UCI-Engine-Bundling nur nach Lizenzentscheidung, WinGet-Manifest danach.

## Programmsymbol (vorbereitet)

Logo 03 ([Logo-Vertrag](../../design/01_Logo/README.md)) liegt als Mehrfachauflösungs-ICO vor:

| Datei | Inhalt | Verwendung |
| --- | --- | --- |
| [`assets/branding/icons/chess-and-chains.ico`](../../assets/branding/icons/chess-and-chains.ico) | 16, 24, 32, 48, 64, 128, 256 px (32-Bit-Alpha, 256 px als PNG) | künftige EXE-Ressource, Installer, Deinstallation, Desktop- und Startmenü-Verknüpfung |
| `src/chess_and_chains/ui/brand_assets/app-icon.ico` | dieselben Bilder im Python-Paket | Laufzeit: `root.iconbitmap(default=…)` für Taskleiste und Alt-Tab |

Die laufende Tk-App setzt Logo 03 bereits über `branding.apply_window_icon()` als Fenster-, Dialog-, Taskleisten- und Alt-Tab-Symbol. Befund 26.11.2026 (Windows 11, Quellstart): Titelleiste und Alt-Tab zeigen Logo 03, die Taskleiste gruppiert das Fenster aber unter `python.exe` und zeigt dessen Symbol, weil keine AppUserModelID gesetzt ist. Lösung nach Inhaberentscheidung: eine eigene ID (z. B. per `SetCurrentProcessExplicitAppUserModelID` vor dem ersten Fenster) oder die künftige EXE mit ICO-Ressource. Systembenachrichtigungen gibt es nicht.

Status: ICO IMPLEMENTED. EXE-Ressource, Installer und Verknüpfungen: OPEN, weil noch kein Windows-Build-System existiert.
