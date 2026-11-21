# Contributing to Chess & Chains

Chess & Chains is a development prototype (V.0.0.1) and has no public release yet. Open an issue to discuss larger changes, using the [issue templates](.github/ISSUE_TEMPLATE/). Licensing, feature scope and brand or design changes need owner approval. Use focused branches from a freshly fetched `origin/main`, include tests and documentation in the same pull request, and follow [AGENTS.md](AGENTS.md). Never contribute code or art copied without permission.

## Checks

```sh
python -m unittest discover -s tests
python scripts/verify_starter.py
python scripts/verify_document_links.py
python scripts/check_policy.py
```

The [pull request template](.github/pull_request_template.md) lists the required evidence. Document tested platforms, behavior, remaining limitations, dependency provenance and new license obligations. Record work evidence under [docs/reports](docs/reports/README.md). Submitted material must not contain secrets, personal information or unlicensed chess art. No contribution implies automatic release approval.

Where to start: [START_HERE.md](START_HERE.md) (German) · [Roadmap](docs/roadmap/ROADMAP.md) · [Work packages](docs/roadmap/WORK_PACKAGES.md).
