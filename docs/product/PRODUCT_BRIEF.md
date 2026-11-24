# Product Brief – Chess & Chains

Status der Produktvision: **VORGESCHLAGEN** · F0 vom 19.11.2026, Iststand geprüft für V.0.2.0.

Der [aktuelle Prototyp](../../README.de.md#was-bereits-vorhanden-ist) enthält
lokales Zweispieler-Spiel, Mock-UCI, fünf eigene Demo-Rätsel und die lokale
Partiebibliothek. Die folgenden Abläufe beschreiben den Zielzustand.

## Vision

Ein hochwertig gestalteter, individuell anpassbarer, dauerhaft kostenfrei angebotener Open-Source-Desktop-Schachraum. Lokal statt Cloud: gegen einen Bot spielen, anspruchsvolle Rätsel lösen, Partien nachvollziehen und die Umgebung visuell selbst konfigurieren.

## Primäre Zielgruppe

- Offline-Trainer, die Taktikaufgaben und Partien ohne Konto, Cloud oder
  Pflichtverbindung nutzen möchten.
- Bot-Spieler, die lokal gegen eine nachvollziehbar abgestufte Engine spielen
  und ihre Partien analysieren möchten.
- Designaffine Desktop-Nutzer, denen konventionelle Oberflächen zu dicht oder
  austauschbar erscheinen und die eigene Figuren/Bretter verwenden möchten.
- Datenschutzorientierte Nutzer, die lokale Spiel- und Trainingsdaten
  kontrollieren und portabel exportieren möchten.

Die genannten Gruppen sind Produkthypothesen. Die Schwelle für Rätsel bezieht
sich auf das Puzzle-Rating der Datenquelle (mindestens 1000), nicht auf eine
persönliche Spielstärke.

## Jobs-to-be-done

1. Ich möchte ohne Internet und ohne Konto gegen einen angemessenen Computergegner spielen.
2. Ich möchte anspruchsvolle Taktikaufgaben nach Schwierigkeit und Thema auswählen können.
3. Ich möchte eine eigenständige, angenehm ruhige Schachoberfläche statt eines überladenen Portals.
4. Ich möchte Partien/Training lokal behalten und portabel exportieren können.

## Erste Nutzerabläufe

Diese Abläufe beschreiben geplante Erfahrungen, nicht implementierte Funktionen.

1. **Erster Offline-Start:** Nutzer startet die App ohne Konto oder
   Netzwerkzugriff, sieht den Projekt-/Setup-Status und landet in einer lokalen
   Hauptansicht. Ist keine freigegebene Engine vorhanden, wird kein Bot-Spiel
   vorgetäuscht; der Zustand und die lokale Engine-Auswahl werden verständlich
   erklärt. Ein Engine-Installationsweg bleibt bis ADR-001 offen.
2. **Partie gegen Bot:** Nutzer wählt eine verfügbare lokale Engine und ein
   Bot-Preset, startet eine Standardpartie, macht ausschließlich legale Züge
   und kann nach der Partie pausieren, speichern oder exportieren. Engine-Fehler
   blockieren die UI nicht und werden sichtbar gemeldet. Engine-Verteilung
   bleibt durch ADR-001 gesperrt.
3. **Puzzle ab Rating 1000:** Nutzer wählt ein lokal verfügbares, rechtlich
   freigegebenes Puzzle-Pack und Filter. Die App richtet die Position vor dem
   ersten Gegnerzug ein, spielt diesen Zug zuerst ab und fragt anschließend
   nach der Lösung. Ungültige Züge werden abgewiesen; Ergebnis und Verlauf
   bleiben lokal. Der Prototyp bringt fünf projekteigene Demos mit. Ein
   veröffentlichter Lichess-Katalog steht aus.

## Kernprinzipien

**Offline by design**, **Rule correctness before effects**, **Own your visuals**, **Modular over monolithic**, **License clarity before packaging**, **Proof before release**.

## Nicht-Ziele im ersten Release

Online-Multiplayer, Cloud-Synchronisation, Benutzerkonten, Social Feed, KI-Abos, Echtzeit-Coaching durch bezahlte APIs, mobile Apps, eigene neuronale Engine, beliebig viele Schachvarianten und ein vollwertiger Datenbank-Manager.

## Designidentität

Arbeitsname **Chess & Chains**. „Chains“ steht für Zug- und Denkketten,
Taktikfolgen und Fortschritt. Der Inhaber bestätigte Connected System und
Manufacturing Consent für Wortmarke und große Überschriften. Die App enthält
eigene Vorderansichten V.02 und einen Draufsichtssatz unter MPL-2.0.
Finale Brettmotive und weitere Freigaben behandelt [ADR-005](../decisions/ADR-005_BRAND_ASSETS.md).

## Erfolgskriterien des MVP

1. Vollständige, regelkorrekte lokale Standardpartie mit freigegebener Engine;
   UI bleibt während Engine-Arbeit bedienbar.
2. Mindestens sechs reproduzierbare Bot-Konfigurationen; Stärke wird gemessen,
   nicht als ungeprüfte Elo-Garantie behauptet.
3. Lokal lösbare Rätsel mit Mindest-Puzzle-Rating 1000 und dokumentierter
   Datenherkunft; Lieferkatalog erst nach Rechte- und Qualitätsgate.
4. Nachgewiesenes Speichern/Wiederöffnen und keine ungefragte
   Netzwerkkommunikation.
5. Tastaturbedienung, DE/EN-Parität und dokumentierte Asset-/Lizenzherkunft.
6. Geprüfter Paketbau für Windows/macOS und Linux-Quellstart mit expliziten
   Plattformgrenzen.

Die Kriterien bleiben Vorschläge für die Produktabnahme. Den belegten Stand
automatisierter Plattformprüfungen und offene Gates führt die [QA-Matrix](../qa/TEST_PLAN.md).
