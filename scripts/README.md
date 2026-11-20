# Prüfscripte

`verify_starter.py` prüft nur Repository-/Prompt-/Manifest-Vollständigkeit. Es testet weder Schachregeln noch GUI, Engines, Lizenzen, Installer oder Plattformkompatibilität. Ziel: Foundation F0 sauber halten. Erweiterungen erst mit neuen getrennten QA-Tools und tatsächlichen Nachweisen.

`python scripts/build_piece_fallback.py` erstellt mit Tk 9 und einem Display die lokale PNG-Grafiktafel aus den zwölf [editierbaren Figuren-SVGs](../src/chess_and_chains/ui/piece_assets/PROVENANCE.md). Diesen Befehl nach Änderungen an den Einzelgrafiken ausführen.
