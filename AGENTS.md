# Repository working instructions

Use the user's branch naming convention for all new work:

- `feature/<name>` for features
- `fix/<name>` for bug fixes
- `docs/<name>` for documentation
- `refactor/<name>` for refactoring
- `release/<version>` for release preparation

Do not create branches with `codex/`, `ai/`, or other tool-name prefixes.
Phase 5 work uses the explicitly requested `feature/release-readiness` branch.
Legacy branches backing open draft PRs may remain as frozen review references;
do not rename/delete them in a way that closes an existing PR. Check PR bases,
heads, commit SHAs and CI before changing review references. Do not force push,
merge, publish, or modify main without explicit user authorization.
