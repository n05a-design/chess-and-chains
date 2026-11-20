# README

Private/temporäre Originaldaten für den importierenden Build-Prozess. Kein Roh-Lichess-Archiv im Repository.

Einzige Ausnahme: `demo_puzzles.csv` – fünf **projekteigene** Stellungen im Lichess-CSV-Layout (MPL-2.0, Test-Wertungen, keine Lichess-Daten). Daraus erzeugt `scripts/build_puzzle_pack.py` das Demo-Paket unter `src/chess_and_chains/puzzles/data/demo/`. Echte Lichess-Exporte nur nach Owner-Opt-in lokal herunterladen und Packs außerhalb des Git-Checkouts (Nutzerdatenverzeichnis) erzeugen.
