# Contributing

Contributions to general-purpose image quality evaluation are welcome. Vehicle
photos are one example; document capture, product photography, and other domains
should be able to reuse the same core without importing product-specific rules.

## Development setup

Use Python 3.10 or newer and a virtual environment:

```bash
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -e ".[server,dev]"
python -m ruff check .
python -m pytest -q
```

With Node.js 22 or newer, run `node --test tests/web/*.test.mjs`,
`node --check web/app.js`, `node --check web/heatmap.js`, and
`node --check web/quality-diagnostics.js` for batch,
relative mapping, heatmap controller, and syntax checks.
No npm runtime dependencies are needed by the browser tool.

Run `laplacian-blur-serve` for the browser demo and `/docs` API documentation.
Changes to the root `web/` directory appear in the editable checkout. The package
build bundles those same assets for installations outside the checkout.

## Pick a contribution

- Reproduce a bug and add a focused regression test.
- Improve batch handling, actionable errors, integration examples, or measured performance.
- Improve usage instructions or add a domain example with clear limitations.
- Propose a quality metric with a written contract and evaluation evidence.
- Optionally improve developer benchmark schemas and calibration reports.

For substantial features, open a feature proposal with the user problem and
acceptance criteria before introducing new services or dependencies. Consult
[the roadmap](docs/ROADMAP.md) and [architecture](docs/ARCHITECTURE.md).

## Submit a change

Use `feature/<name>`, `fix/<name>`, `docs/<name>`, `refactor/<name>`, or
`release/<version>` for new branches. Do not use `codex/`, `ai/`, or other tool
names as prefixes. Earlier feature/release branches are retained as review history;
PR #1–#6 are merged. Do not start new development on legacy refs or delete them
without checking current PR references and maintainer approval.

1. Fork the repository and create a descriptive branch.
2. Keep the pull request focused. Explain the resulting behavior and compatibility.
3. Run lint and the tests relevant to your changes. Add tests for new behavior
   where they demonstrate a meaningful regression or contract.
4. Update documentation and add an Unreleased changelog entry for future behavior
   changes; keep published release entries historical.
5. Open a pull request using the template and respond to review feedback.

Maintainer review determines whether a change is merged. CI runs on pull requests;
branch protection and required approvals must be configured separately on GitHub.
Do not assume a committed workflow has enabled those repository settings.

## Detector and dataset changes

- Keep the core independent of HTTP, storage, user accounts, and image domains.
- Treat a score as a measurement, not a probability or a universal quality label.
- Record preprocessing, threshold, metric version, and dataset provenance when
  comparing results. Changes to preprocessing require threshold reevaluation.
- Report both false rejections and missed unusable images. Separate calibration
  and test data, including near-duplicate captures from the same session.
- Use generated fixtures for unit tests. Share real images only with permission;
  redact faces, identifiers, license plates, and other sensitive information.
- Do not silently change the meaning of existing API fields or score scales.

## Community expectations

Be respectful, explain disagreements with evidence, and credit others' work.
Harassment and publication of another person's private information are not accepted.
Use [the security policy](SECURITY.md) for vulnerability reports.

## Release checklist

Use the evidence/status in [Release readiness](docs/RELEASE_READINESS.md) and
[release notes](docs/RELEASE_NOTES.md). Passing tests does not check off pending
or unreported browser substeps or operator deployment controls. Distinguish
maintainer-reported manual QA from automation. Follow the
[completed stacked integration record](docs/INTEGRATION_PLAN.md) and
[experimental version/assets checklist](docs/PRERELEASE_PREPARATION.md).

1. Update `laplacian_blur_detector/__init__.py` and the changelog together.
2. Run `python -m ruff check .`, `python -m pytest -q`, and `python -m build`.
3. Install the built wheel in a clean environment with server dependencies, then
   run `tests/smoke_installed.py` from outside the checkout.
4. Verify the CI matrix, documented compatibility, and third-party notices.
   Also run the Node suite, clean sdist installation, and Docker/live HTTP smoke;
   perform real desktop/mobile QA and dependency/image vulnerability review.
5. Have a maintainer create the release. No workflow currently publishes to PyPI
   or deploys a hosted service automatically.
