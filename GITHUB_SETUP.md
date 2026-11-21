# Bestehendes GitHub-Repository – Chess & Chains

Das Projekt liegt auf [GitHub](https://github.com/n05a-design/chess-and-chains). `main` ist der Integrationsbranch. Für neue Arbeit Standort, Änderungen und Remote-Stand im vorhandenen Checkout prüfen und den PR-Weg verwenden. Der [Einstieg](START_HERE.md) und die [Roadmap](docs/roadmap/ROADMAP.md) gelten für die laufende Entwicklung.

Die GitHub-Kurzbeschreibung nennt das lokale Zweispieler-Spiel, Demo-Rätsel
und die eigenen SVG-Figuren des Entwicklungsprototyps. Den aktuellen
Versions- und Funktionsstand führen die READMEs.

## Aktuelle GitHub-Konfiguration (geprüft 21.11.2026)

| Einstellung | Stand | Empfehlung (Owner-Entscheidung) |
| --- | --- | --- |
| Sichtbarkeit | Öffentlich | Bestätigung offen (Q-017) |
| Beschreibung | Prototyp mit Zweispieler-Partien, Demo-Rätseln und eigenen SVG-Figuren | aktuell |
| Topics | `chess`, `offline-first`, `python`, `desktop-app`, `chess-puzzles`, `tkinter`, `uci`, `open-source` | gesetzt beim Ablageaudit |
| Branches | nur `main`; abgeschlossene Branches sind entfernt | – |
| Branch-Schutz für `main` | nicht aktiv | Pflichtprüfungen der Matrix und PR-Pflicht aktivieren |
| Branch nach Merge löschen | aus | einschalten, hält das Repository aufgeräumt |
| Private Sicherheitsmeldungen | aus | einschalten, damit `SECURITY.md` einen Meldeweg hat |
| Issue- und PR-Vorlagen | `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md` | – |
| Wiki | aktiviert, ungenutzt | deaktivieren; Dokumentation lebt im Repository |
| Releases | keine | erst nach W12-Gate |

Sicherheits- und Schutzeinstellungen ändert nur der Inhaber.

## Historische Anlageanleitung F0

Die folgenden Schritte beschreiben die ursprüngliche Neuanlage aus dem Starter-ZIP. Sie bleiben als Archiv der Einrichtung erhalten.

## Variante A – GitHub-Webseite

1. Unter dem gewünschten GitHub-Account/der Organisation `n05a-design` ein leeres Repository `chess-and-chains` erstellen.
2. **Nicht** zusätzlich „Add README“, „Add .gitignore“ oder „Choose a license“ auswählen – alle drei Dateien sind bereits im Starter enthalten.
3. Sichtbarkeit vorab selbst entscheiden (Frage Q-017; privat bis zum Rechte-Check sinnvoll).
4. ZIP entpacken und den Inhalt von `Chess-and-Chains-GitHub-Starter/` in den neuen Repo-Checkout übernehmen, einschließlich **verstecktem Ordner `.github`**.
5. Prüfen, dass `LICENSE`, `README.md`, `README.de.md`, `AGENTS.md`, `MANIFEST.md` auf der obersten Ebene liegen.

## Variante B – Terminal / Git

Voraussetzung: Ein **leeres** GitHub-Repository wurde von dir bereits angelegt. Befehle im **entpackten Projektordner** ausführen:

```sh
python scripts/verify_starter.py
python -m unittest discover -s tests -v
git init -b main
git add .
git commit -m "chore: initialize Chess & Chains Foundation F0"
git remote add origin https://github.com/n05a-design/chess-and-chains.git
git push -u origin main
```

Danach den echten Remote-Stand prüfen (`git status`, `git rev-parse HEAD`, `git ls-remote origin refs/heads/main`). Kein Force-Push nötig.

## GitHub About – Vorschlag

Description: `A planned free, offline-first desktop chess and tactical puzzle app with customizable SVG boards and local engines.`

Topics: `chess`, `offline-first`, `python`, `desktop-app`, `chess-puzzles`, `open-source`, `uci`.

Aktiviere Issues und Pull Requests; Branch-Protection, Actions-Rechte, Code-Scanning und Security-Reporting nach GitHub-Verfügbarkeit und Projektstatus konfigurieren. **Nicht** durch Copilot ohne Freigabe ändern lassen.

## Erste Copilot-Aufgabe

`prompts/00_MASTER_BOOTSTRAP.md` direkt im geöffneten Repo abarbeiten lassen. Keine neue, doppelte Struktur generieren: die Dateien existieren bereits. Erst W00/Basis-Audit, dann W01…W04 und Freigaben einholen.
