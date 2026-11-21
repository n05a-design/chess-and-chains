# Eigene Schachbretter liefern

Ein Verzeichnis je Brettdesign, z. B. `mein-brett/`. Die editierbaren SVGs sind die Masterdateien. Für die Übergabe genügt eines dieser Formate.

| Motiv | Lieferung |
| --- | --- |
| Zwei wiederkehrende Feldmotive | `light.svg` und `dark.svg`. Jedes Feld hat einen quadratischen `viewBox`, empfohlen `0 0 256 256`. |
| Einzelne Akzentfelder | Die beiden Grundmotive plus benannte Ausnahmen wie `e4.svg` oder `d5.svg`. Alle Dateien haben denselben Feldmaßstab. |
| 64 frei gestaltete Felder | `a1.svg` bis `h8.svg`. Der Dateiname ist die Schachkoordinate. Das Motiv bleibt beim Drehen dem benannten Feld zugeordnet. |
| Feldübergreifende Komposition | Eine editierbare `board.svg` mit dem ganzen 8×8-Raster, empfohlen `viewBox="0 0 2048 2048"`. Feldobjekte oder Gruppen können wie in der [Brettvorlage](board-template.svg) nach ihren Koordinaten benannt werden. |

Die Vorlage zeigt die Sicht mit Weiß unten. `a8` liegt oben links, `h1` unten rechts und `a1` ist ein dunkles Grundfeld. Pro Feld sind 256 Einheiten vorgesehen. Die App setzt Koordinaten, Figuren, Zugmarkierungen und Tastaturfokus darüber. Ein Rahmen oder eine Randgrafik kann als eigene Gruppe mitgeliefert werden. Für richtungsabhängige Motive bitte vermerken, ob das Motiv beim Perspektivwechsel aufrecht bleiben oder mit dem Brett rotieren soll.

## Lokale Vorschau

Nach dem Entwicklerstart aus der [README](../../../README.de.md) kann Tk mit SVG-Unterstützung (Tk 9) die Vorlage direkt anzeigen.

```powershell
python -m chess_and_chains --board-design assets/boards/source/board-template.svg
```

Als Argument funktioniert auch ein Ordner mit `board.svg`, mit `light.svg` und `dark.svg` samt optionalen Sonderfeldern oder mit allen 64 benannten Feldern. Eine `board.svg` im Ordner hat Vorrang. Beim Drehen dreht sich ein Gesamtbrett um 180 Grad. Einzelne Feldmotive bleiben aufrecht und folgen ihrer Schachkoordinate. Figuren, Auswahl und Zugmarkierungen bleiben darüber sichtbar.

Die Vorschau hält beide Perspektiven der aktuellen Brettgröße für
erneutes Drehen vor. Bei Feld-SVGs verwendet sie bereits gerenderte
Feldbilder für die andere Ansicht. Eine neue Brettgröße baut den Cache
neu auf. [W06-Prüfbericht](../../../docs/reports/2026-11-21_W06-svg-brettcache.md)

Die Vorschau gilt für den Programmaufruf. Die App liest die SVG-Dateien vor Ort und lässt die Masterdateien unverändert. Der Standardstart bleibt bei der bisherigen Brettdarstellung.

Komplexe Muster und Ebenen können in der editierbaren Masterdatei bleiben. Der Vorschau-Export unterstützt grundlegende Vektorformen, Gruppen, Transformationen und lokale Farbverläufe. Schrift, eingebettete Bilder, externe Quellen, Filter und eigenständige Stylesheets benötigen für diese Vorschau einen entsprechend aufbereiteten Export. `--headless-check --board-design <Pfad>` prüft das Format, ohne ein Fenster zu öffnen.
