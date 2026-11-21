# Statusmodell für Arbeitspakete (seit N02)

**Gültig ab:** 2026-11-20 · **Maschinenprüfung:** `scripts/verify_starter.py`,
`tests/test_foundation.py`

Bis N02 erzwangen Manifest und Foundation-Test, dass alle Arbeitspakete
`NOT_STARTED` bleiben. Das widersprach dem tatsächlich implementierten und
getesteten Code. Der ursprüngliche Planungszustand ist jetzt als
unveränderliche historische Baseline `foundation_baseline` in
`project-manifest.json` erhalten; die laufenden Statuswerte stehen in
`work_packages[].status`.

| Status | Bedeutung | Pflichtfelder / Nachweise |
| --- | --- | --- |
| `NOT_STARTED` | Keine belegte Arbeit | – |
| `IN_PROGRESS` | Recherche, Teilcode oder Doku vorhanden; Gate nicht erreicht | `status_evidence` (existierende Pfade) |
| `BLOCKED` | Arbeit wartet auf Owner-/Lizenz-/Asset-Entscheidung | `status_evidence`, `blocked_by` |
| `IMPLEMENTED` | Code für einen **benannten** Umfang vorhanden | `status_evidence`, `scope`, `open_gate_items` |
| `TESTED` | Automatisierte Tests für diesen Umfang bestehen lokal/CI | wie IMPLEMENTED + mind. ein `tests/`-Pfad |
| `ACCEPTED` | Owner hat das Gate abgenommen | `acceptance.by/date/reference`, leere `open_gate_items` und `blocked_by`, alle Abhängigkeiten ACCEPTED oder RELEASED |
| `RELEASED` | Öffentlich ausgeliefert | wie ACCEPTED + `release.tag` |

Weitere maschinell geprüfte Regeln:

- Ein Paket ab `IMPLEMENTED` darf keine Abhängigkeit mit `NOT_STARTED` haben.
- `ACCEPTED`/`RELEASED` werden **nie** durch einen Agenten gesetzt; sie
  verlangen einen Owner-Eintrag mit Referenzdokument.
- `license_gate` bleibt `OPEN_BLOCKS_BUNDLED_GPL_RELEASE` und
  `stockfish_binary` bleibt in `not_included`, bis ADR-001 vom Owner
  akzeptiert ist.
- `product_status` ∈ `FOUNDATION_ONLY_NOT_PLAYABLE`,
  `PROTOTYPE_LOCAL_PLAY_NOT_RELEASED`, `ALPHA_NOT_RELEASED`, `RELEASED`;
  `RELEASED` verlangt W12 `RELEASED`.

`TESTED` bedeutet ausdrücklich **nicht** native Plattformabnahme oder
Release-Reife. Native Abnahmen und offene Punkte gehören in
`open_gate_items`. Nachweiskette: lokaler Code → lokaler Test → Commit →
Push → CI → Merge → native Plattformabnahme → öffentlicher Release; jede Stufe
wird in `docs/reports/` getrennt belegt.
