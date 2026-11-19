# PROMPT 02 – Rechts-/Lizenz-/Engine-Entscheidungsgrundlage

W02 nach W00; zwingend vor der Integration oder Distribution von Engine-/GPL-Paketen. Agiere als technischer Compliance-Analyst, nicht als Rechtsanwalt. Recherchiere bei Quellenbedarf die **aktuellen offiziellen Originalquellen**.

**Prüfe konkret:** Stockfish GPLv3 samt NNUE-Dateien/Binaries; python-chess GPLv3; Chessnut Unlicense + tatsächliche Regelunterstützung; MPL 2.0 Larger Work; Unterschied GPL-Gesamtbuild vs separate Prozesse/UCI vs separate Installation. Keine pauschale Behauptung, dass separate EXE automatisch GPL-Pflichten der kombinierten Distribution ausschließt. Gibt es alternative freie, kompatible Schachregel-Implementierungen? Quellen und geprüfte Versionen angeben.

**Optionsanalyse:** A GPL-konformes Gesamtprodukt, B MPL-Anwendung mit rechtlich geprüfter Engine-Trennung und kompatiblem Regelwerk, C separate Engine-Installation. Für jede Option: Benutzererlebnis (direkt offline spielbar?), Build-/Update-/Quell-/Lizenzpflichten, Risiken, Kosten, Shell-Reuse, Windows/macOS/Linux-Auswirkung. Das Ergebnis ist ein **Entscheidungsantrag** und ein Test-/Compliance-Plan, niemals automatisch ein ACCEPTED ADR.

**Deliverables:** aktualisiere `docs/legal/LICENSE_STRATEGY.md`, `docs/decisions/ADR-001_ENGINE_LICENSE.md`, `THIRD_PARTY_NOTICES.md`, Quellenregister und Q-001/Q-002/Q-015. Datei-/Binär-/Asset-Inventar-Template, klare Blocker-Matrix. Bericht `docs/reports/YYYY-MM-DD_W02_license.md`.

**Gate:** keine GPL-Laufzeitabhängigkeit, Binary oder Modell in das Repo hinzufügen; nichts signieren, verpacken oder als lizenzfreigegeben darstellen; unresolved legal gate im Manifest dokumentieren. Optional fachkundige Rechtsprüfung durch Owner anfordern.
