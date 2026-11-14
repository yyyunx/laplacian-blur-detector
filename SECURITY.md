# Security policy

The project is an early-stage image analysis library and demo service. A packaged
release is not a claim that the HTTP service is ready for an untrusted public network.
The current service has no authentication, team isolation, upload-size limits,
decoded-pixel limits, or application-level rate limiting.

## Reporting a vulnerability

If GitHub's private vulnerability reporting is enabled, use **Security > Report a
vulnerability** in this repository. If that option is unavailable, open an issue
requesting a private reporting channel without disclosing exploit details or
affected users' data. A maintainer must establish that channel before details are sent.

Include affected versions, impact, and a minimal reproduction with synthetic or
sanitized input. Do not post secrets, private photos, or working exploits publicly.
There is no guaranteed response time or maintained LTS branch at this stage.

## Deployment boundaries

- The current API does not persist uploaded images. Adding collaboration and
  storage requires explicit retention, access control, deletion, and backup rules.
- CLI inputs must be trusted files; API deployments must enforce body-size,
  decoded-image resource, timeout, and concurrency limits before public exposure.
- Keep runtime dependencies updated and test upgrades before deployment.
- Never commit credentials, production datasets, or personal images.

These deployment controls are planned work, not features supplied by this policy.
