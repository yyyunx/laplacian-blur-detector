# Roadmap: reusable engine to team collaboration

This is a sequence of milestones with acceptance criteria, not a release-date promise.
The open-source foundation and local labeled evaluation are implemented. The shared
team workspace remains future work.

## 1. Open-source foundation — implemented

- Install a library, CLI, or optional API from the same project metadata.
- Preserve existing score behavior and checkout entry points.
- Define contribution, bug report, feature proposal, and review workflows.
- Run lint, regression tests, packaging, and installed-wheel checks in CI.

The foundation was pushed and its GitHub CI passed. Remaining maintainer operations:
configure branch protection/review requirements, enable private security reporting,
and decide when to tag or publish the first packaged release. These settings are
not enabled by local files.

## 2. Reproducible quality evaluation — local tooling implemented

User outcome: a contributor can prove that a change improves a particular use case.

- Define a labeled CSV schema: relative image path, domain, usable/retake label,
  optional reason, and capture-group identifier for preventing split leakage.
- Record rights/provenance for datasets and keep private datasets out of Git.
- Compare thresholds on calibration data and report final results on held-out data.
- Export false rejection, missed unusable image, and confusion-matrix reports.
- Version preprocessing and quality policies. Include a document/photo example
  alongside the existing vehicle use case without claiming universal thresholds.

Done when another contributor can reproduce an evaluation from a documented
dataset manifest and configuration. Synthetic images alone do not establish accuracy.

The CLI, manifest contract, calibration/test isolation checks, per-domain policies,
fingerprinted reports, and a synthetic document/product example are now implemented.
See [the guide](BENCHMARKING.md). Representative real datasets and human-reviewed
labels still need to be supplied; real-world accuracy has not been established.

## 3. Shared review workspace — first team MVP

User outcome: multiple people can inspect the same dataset and resolve disagreements.

- Sign in, create a workspace/project, and assign owner/contributor/reviewer roles.
- Upload with byte/pixel limits and private storage; define consent, retention,
  deletion, and export behavior.
- Analyze using a selected policy version, then queue images for human labeling.
- Add labels, review decisions, and disagreement handling. Record who changed what.
- Prevent concurrent edits from silently overwriting labels; allow filtering and CSV export.

Done when two authorized users can finish a shared review, unauthorized users
cannot access the images or results, concurrent edits produce a visible conflict,
and policy changes leave historical runs intact.

## 4. Reliable team operation

- Background jobs with progress, bounded concurrency, retries, and cancellation.
- Idempotent analysis requests so retries do not create duplicate work.
- API authentication, per-workspace quotas, structured errors, and audit logs.
- Document backup/restore, schema migration, deletion, and deployment procedures.
- Track queue age, analysis latency, failures, and resource usage.

Done when a failed worker can resume work safely, quotas prevent one workspace
from exhausting service resources, and a restore exercise succeeds.

## 5. Broader quality capabilities

Consider local sharpness maps, exposure, minimum resolution, and additional focus
metrics after milestone 2 provides a trustworthy comparison process. Consider
model-based subject detection only for use cases and datasets that justify it.

Every addition must report known limitations, processing cost, and domain-specific
evaluation results. A higher number of algorithms does not establish better quality.
