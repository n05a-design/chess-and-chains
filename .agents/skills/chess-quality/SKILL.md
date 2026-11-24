---
name: chess-quality
description: Verification and quality assurance checklist for Chess & Chains and Glide Shell 0.6.2. Use before committing or opening a PR to run selftest, unit/GUI tests, manifest checks, policy checks, and agent bootstrap validation.
---

# Chess & Chains Quality Assurance

Every code or documentation change must be verified with actual command execution using isolated test data directories (`CHESS_AND_CHAINS_DATA_DIR`).

## Required Checks

1. Glide Shell Self-Test (expected: `13/13 checks passed`):
   - `cd src && python3 -m glide_shell.selftest`
   - `cd src && python3 -O -m glide_shell.selftest`
2. Full Test Suite (unit + GUI integration + Glide Shell integration):
   - `PYTHONPATH=src CHESS_AND_CHAINS_REQUIRE_DISPLAY=1 python3 -m unittest discover -s tests -v`
3. Repository Structure, Links & Policy Checks:
   - `python3 scripts/verify_starter.py`
   - `python3 scripts/verify_document_links.py`
   - `python3 scripts/check_policy.py`
   - `python3 -m compileall -q src app scripts tests`
4. CLI & Packaging Checks (using isolated `CHESS_AND_CHAINS_DATA_DIR`):
   - `PYTHONPATH=src python3 -m chess_and_chains --version`
   - `PYTHONPATH=src python3 -m chess_and_chains --headless-check`

## References

- Agent Rules: [AGENTS.md](../../../AGENTS.md)
- Test Plan: [TEST_PLAN.md](../../../docs/qa/TEST_PLAN.md)
- Foundation Verifier: [verify_starter.py](../../../scripts/verify_starter.py)
