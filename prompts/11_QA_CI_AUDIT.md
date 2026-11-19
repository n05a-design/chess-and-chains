# PROMPT 11 – Integritätsaudit, CI und Plattformnachweise

W11 ab funktionalen Verticals. Implementiere unabhängige Verifikation der tatsächlichen Anwendung, keine selbstreferenziellen „Tests grün = App fertig“-Aussagen.

**Matrix:** Schachregel-Perft/Golden-Test, UI-nativ Win/macOS, Linux-Xvfb/realer Tk-Start, UCI Absturz und Crash Recovery, Puzzle-Daten-Provenienz/Rating >=1000, PGN-FEN Roundtrips, Save Restore, i18n DE/EN, Asset-Herkunft, installierte Abhängigkeiten, statische Security-Checks, Netzwerk-Isolation. Frozen SHA pro Build; Quell- und Lieferartefakte vergleichen.

**CI:** kein Push mit Secrets, least privileges, Cache- und Dependency-Provenienz, Versions-/Dokumentations-/Broken-Link-Prüfung, `unittest`, später native UI-Pipeline. Paketbuild nicht als Plattformrelease ausgeben, bevor isolierter Installationsnachweis vorliegt. Absicherung von Logpfaden und personensensiblen Daten.

**Audit:** Quelle-Dokumentations-Matrix mit IMPLEMENTED/TESTED/RELEASED, jedes Feature muss konkrete Tests und Lücken nennen. PR-/Branch-/Remote-Divergenzen erfassen, kein Force Merge. Veröffentlichungsblocker priorisieren.

**Gate:** Bericht mit tatsächlicher Matrix, Umgebung, Exitcodes, Ausschlüssen, ungetesteten Flows, Abnahmevorschlag (nicht selbst freigeben), W11-Dokumentation.
