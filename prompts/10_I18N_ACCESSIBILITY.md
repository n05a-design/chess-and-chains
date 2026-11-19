# PROMPT 10 – Internationalisierung und Bedienqualität

W10 nach Board und Storage. Öffentliche Texte EN/DE konsistent, getrennt von Schachnotation/SAN/PGN; Spracheinstellungen persistiert und UI-Fokus sinnvoll wiederhergestellt.

**Prüfe:** Locale-Kataloge (keys, placeholders, fallback), DE/EN Navigation, Bot-Labels, Puzzle-Themes, Zahlen/Zeit/Ratings, Formatierung/Umbruch, Screenshots/Marketing-Faktenparität. Keyboard-only: Feldwahl, Figurenzug, Promotion, Dialoge, Undo/Restart, Puzzle. Fokusindikatoren, Kontrast, DPI, reduced-motion, Statusmeldungen. Screenreader-Unterstützung real testen und ungeprüfte Grenzen ausdrücklich kennzeichnen.

**Deliverables:** lokalisierte UI-Strings, Paritätstests, UX-Checkliste, Fehler-/Gapliste, W10-Bericht.

**Gate:** Kein automatisches „vollständig barrierefrei“ ohne Menschen- und Plattformprüfung; keine zweite inkompatible i18n-Architektur bei Shell-Reuse.
