# Security policy

The project is an early-stage image analysis library and bounded HTTP tool. A
packaged release is not a claim that every public deployment requirement is met.

## Reporting a vulnerability

If GitHub private vulnerability reporting is enabled, use **Security > Report a
vulnerability**. Otherwise open an issue requesting a private reporting channel
without posting exploit details or user data. A maintainer must establish that
channel before details are sent.

Include affected versions, impact, and a minimal reproduction using synthetic or
sanitized inputs. Do not post credentials, private photos, or working exploits.
There is no guaranteed response time or maintained LTS branch at this stage.

## Implemented HTTP boundaries

- 10 MiB per encoded file; 20 files and 50 MiB of image bytes per batch API call.
- Streaming request limits include 1 MiB of multipart overhead and apply without
  Content-Length. Upload handles are closed on completion and validation failures.
- Pillow checks supported content and a 20-million-pixel limit before OpenCV decode.
- Worker-thread processing admits two active analyses per server process; busy
  requests receive a retryable 503. A batch is processed serially within its request.
- Local sharpness uses the same upload/header/decode/worker controls, with at most
  32×32 cells and a minimum cell size of 16×16 pixels to bound response size.
  These spatial bounds do not replace process memory limits for derivative arrays.
- Quality diagnostics shares the same image/worker controls. JSON policy is capped
  at 8 KiB and rejects duplicate/unknown fields and invalid numeric values before
  decoding. Diagnostic hints do not alter the existing upload acceptance decisions.
- No persistent image/result storage. Multipart parsing can temporarily spool
  uploads to local disk; deployment operators control that temporary filesystem.

Defaults live in `laplacian_blur_detector/config.py`. CLI and direct Python calls
remain offline tools for trusted files and do not inherit the HTTP upload limits.

## Deployment responsibilities

Authentication, per-client rate limiting, connection/request timeouts, overall
process memory/CPU limits, and temporary-disk quotas are deployment concerns that
are not provided by these upload checks. Multiple server processes each have their
own analysis limit. Keep runtime dependencies updated and test upgrades.

Do not commit secrets, production datasets, or personal images. Review the data
handling contract before adding any future persistence or external processing.
