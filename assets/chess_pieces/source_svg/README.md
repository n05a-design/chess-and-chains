# SVG-Schachfiguren

Die editierbare [SVG-Übersicht des Inhabers](masters/Schachfiguren.svg) ist als Master mit [Herkunft und Freigabe](masters/PROVENANCE.md) registriert. Aus den sechs Figurentypen sind **24 Einzel-SVGs** abgeleitet, je zwölf in [Vorderansicht](../../../src/chess_and_chains/ui/piece_assets/PROVENANCE.md) und [Draufsicht](../../../src/chess_and_chains/ui/piece_assets/top/PROVENANCE.md). Ihre Namen kombinieren `w` oder `b` mit `K`, `Q`, `R`, `B`, `N` oder `P`.

**Verbindliches Figurenmaß.** Innerhalb jeder Ansicht haben alle sechs Figurentypen dieselbe sichtbare Breite und Höhe. Das Außenmaß schließt die Kontur ein. Vorderansicht **39 × 54 Einheiten**, von `(12,5 | 5)` bis `(51,5 | 59)` mit der gemeinsamen Grundlinie `y=59`. Draufsicht **52 × 52 Einheiten** mit Mittelpunkt `(32 | 32)`. Beide Ansichten verwenden eine **64 × 64 SVG-Fläche**, ein Raster von 0,5 Einheiten und eine Kontur von 2 Einheiten. Helle und dunkle Varianten verwenden dieselbe Geometrie.

Die App nutzt die Vorderansicht standardmäßig in Partie und Rätselmodus. `python -m chess_and_chains --piece-view top` lädt für diese Sitzung die Draufsicht. Nach Änderungen an den Vektoren mit Tk 9 und Display `python scripts/build_piece_fallback.py` ausführen, um beide PNG-Fallbacks zu aktualisieren.

Der [editierbare SVG-Prüfbogen](../../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Masspruefung.svg) zeigt beide Farben mit Maßlinien und einer 32-Pixel-Vorschau.
