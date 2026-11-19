# PROMPT 03 – Unabhängiger Glide Shell Reuse & Migration Audit

W03 nach W00. Ziel: Chess & Chains für die zukünftige Glide-Shell vorbereiten, **ohne** sie fälschlich als fertige Library zu behandeln.

**Inputs:** aktuelle GitHub-Stände `n05a-design/glide-to-do` und `n05a-design/steps`, Glide `GLIDE_SHELL_FRAMEWORK_KONZEPT.md`, `src/glide/README.md`, Steps `REUSE_AND_MIGRATION_MATRIX.md`. Erfasse Git SHAs (Remote) und bei verfügbaren lokalen Checkouts getrennte Arbeitsstands-SHAs. Berechtigungen und Source-of-Truth prüfen; kein blindes Kopieren aus OneDrive oder GitHub.

**Audit:** Für `appearance`, `ui_design`, `custom_controls`, `desktop_adapter`, `modal_session`, `runtime_config`, `i18n`, `svg_geometry`, `brand`, `storage` prüfen: Quelle/Hash/Status, direkter und transitiver Importgraph, `ListApp`-Kopplung, Lizenz und Drittassets, Tk-Version/OS, vorhandene Tests, Multi-DPI-/UI-Performance. Kategorisiere `candidate`, `isolated`, `ported`, `reviewed`, `rejected`. Reuse-IDs in `integrations/glide_shell/REUSE_REGISTER.csv`.

**Ergebnis:** Drei Integrationsoptionen: A externe eigenständige Shell-Package-Abhängigkeit, B selektive modulare Übernahme inkl. Attribution und Upgradeweg, C temporär neutrales Tk-Board ohne Reuse. Erstelle einen **messbaren** Proof-of-Concept-Plan für SVG-Board und Modalfenster mit Rollback.

**Gate:** Keine Komplettkopie von `app.pyw`, keine Domain-Imports, keine ungeprüfte Portierung oder Mutation fremder Repos. `INTEGRATION_GATE.md` und ADR-002 bleiben ausdrücklich vorläufig ohne Owner-Abnahme. Bericht mit aktuellen Quellreferenzen und Tests.
