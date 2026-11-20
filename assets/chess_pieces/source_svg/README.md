# SVG-Schachfiguren

Die editierbare [SVG-Übersicht des Inhabers](masters/Schachfiguren.svg) ist als Master mit [Herkunft und Freigabe](masters/PROVENANCE.md) registriert. Aus den sechs Figurentypen sind **24 Einzel-SVGs** abgeleitet, je zwölf in [Vorderansicht](../../../src/chess_and_chains/ui/piece_assets/PROVENANCE.md) und [Draufsicht](../../../src/chess_and_chains/ui/piece_assets/top/PROVENANCE.md). Ihre Namen kombinieren `w` oder `b` mit `K`, `Q`, `R`, `B`, `N` oder `P`.

**Figurenmaß.** Innerhalb jeder Ansicht haben alle sechs Figurentypen dieselbe Breite und Höhe. Beide Ansichten nutzen eine **64 × 64 SVG-Fläche**. Die Vorderansichten übernehmen die Pfade und die 1,14 Einheiten breite Kontur der überarbeiteten Inhaberfassung. Bei doppelter Auflösung belegen sie durchgängig **78 × 108 Rasterpixel**. Die Draufsicht misst **52 × 52 Einheiten** inklusive Kontur und ist um `(32 | 32)` zentriert. Helle und dunkle Varianten verwenden dieselbe Geometrie.

Die App nutzt die Vorderansicht standardmäßig in Partie und Rätselmodus. `python -m chess_and_chains --piece-view top` lädt für diese Sitzung die Draufsicht. Nach Änderungen an den Vektoren mit Tk 9 und Display `python scripts/build_piece_fallback.py` ausführen, um beide PNG-Fallbacks zu aktualisieren.

Der [editierbare Schatten-Prüfbogen](../../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Schatten.svg) zeigt beide Farben und eine Kleinansicht auf 40-Pixel-Feldern. Die [überarbeitete Inhaberfassung](../../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Inhaberfassung.svg) liegt separat. Der [frühere Maßprüfbogen](../../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Masspruefung.svg) dokumentiert das ursprüngliche Raster.
