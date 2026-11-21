# Texturen für die Marmoransicht in Tk

Die drei PNGs sind abgeleitete Laufzeitdateien. Die editierbaren
Originale liegen unter [Marmor-Spielsatz](../../../../design/source/marmor-3d/spielsatz/)
und sind in der [Provenienz](../../../../design/source/marmor-3d/PROVENANCE.md)
beschrieben. Die Projektion ändert die Quelldateien nicht.

Der Generator [build_marble_tk.py](../../../../scripts/build_marble_tk.py)
verwendet Chromium lokal für die SVG-Masken und feinen Farbflächen.
Zur Laufzeit benötigt die Tk-App nur die drei PNGs. Die Brettseiten,
Plattenkanten, Koordinaten und Zugmarkierungen zeichnet Tk passend
zur aktuellen Größe. Generierung aus der Repository-Wurzel:

```powershell
python scripts/build_marble_tk.py --chrome 'C:/Program Files/Google/Chrome/Application/chrome.exe'
```

| Datei | SHA-256 |
| --- | --- |
| `white.png` | `bf0a4cefc7d3aac275b3cbcf70da7c0e444eb48c059271dfe06a6ce5b7abaeba` |
| `black.png` | `8dbe129ead224c08474368b9667506dd7c0eb1b4146c09a38693ea43ffe7267f` |
| `plates.png` | `6cba2a9d53c365525bc7acc9784ae03a181c39a7c00dac3b6d568c572b2ee9e1` |
