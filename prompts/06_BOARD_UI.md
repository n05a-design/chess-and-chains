# PROMPT 06 – Original Board UI, SVG-Rendering und Accessibility

**Start nur nach W03+W05 (oder mit ausdrücklich freigegebener neutraler Tk-Spike-Ausnahme).** Keine Board-Interaktion ohne legal move service.

**Arbeite:** GUI-Prototyp auf Python/Tk mit korrekt orientiertem 8x8-Brett, variabler Größe, Koordinaten, SVG-to-render-Cache und einem austauschbaren Figurensatz-Contract. Verwende bis zur Lieferung der Eigentümer-SVGs nur **selbst erzeugte, ausdrücklich als Test-Provisorium benannte** Shapes; nicht in Marketing oder Release ausgeben. Selektions-/Ziel-/Schach-/letzter-Zug-Indikatoren klar und barrierearm; Klick/Klick und Drag/Drop; Promotion-Dialog; White/Black board orientation; Fokus/Navigationskeys; reduced motion. Keine Netzabhängigkeit.

**Benchmarks:** Windows/macOS Ziel-DPI (1x/1.5x/2x), native Fensterneuzeichnung, Eingabe während Größenwechsel, Farbkontrast, Ressourcen-Leaks; Tk UI thread muss frei bleiben. Dokumentiere Entscheidung Tk/SVG vs Qt als ADR-002-Vorschlag, keinen Stackwechsel ohne Owner.

**Deliverables:** Board-Vertical-Slice, UI-Tests, Branding-Asset-Schnittstellen und Design-/QA-Bericht, keine echte Nutzer-SVG ohne gesicherte Rechte.

**Gate:** Alle visuellen Ebenen entkoppelt von Regeln, alle schachrechtlich relevanten Interaktionen von Domäne validiert. Keine irreführende Grafik im README als fertiges Produkt.
