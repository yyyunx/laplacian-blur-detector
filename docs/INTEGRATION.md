# Integration without a universal quality gate

## Trusted local upload pipeline

After installing the core package, run:

```bash
python examples/diagnose_upload.py web/demo.png --min-width 1024 --min-height 768
```

This prints reusable measurements and configured resolution hints, while leaving
sharpness/exposure warning limits disabled. A backend can show `suggestion` for
`warning`, and a separate information message for `insufficient_evidence`.
Do not turn low texture into automatic rejection. The example consumes trusted
local files; it does not implement HTTP file limits or EXIF display orientation.
Use the existing bounded service for untrusted uploads and browser coordinates.
Array inputs use OpenCV BGR/BGRA, ignore alpha, and retain native sharpness units.

## Existing bounded HTTP integration

Use multipart `image` with `/api/quality/diagnose` and a `policy` JSON string.
For instance, send `{"min_width":1024,"min_height":768}` explicitly for a capture
workflow that needs those dimensions; defaults do not impose that requirement.
Use `/api/sharpness/local` separately for Laplacian/Tenengrad region measurements.
Follow [API contracts](API.md) and [diagnostic definitions](DIAGNOSTICS.md).

Set connect/read deadlines in your HTTP client. Handle 400/413/422 by correcting
the input; show retry guidance for 503 `SERVICE_BUSY` with `Retry-After`. Never
launch unbounded automatic retries: a client timeout or abort can leave an accepted
native analysis running. Old blur check/batch responses remain unchanged.

An actual local service can be smoke-tested without a Python HTTP dependency:

```bash
laplacian-blur-serve
# In another terminal:
python tests/smoke_http.py --url http://127.0.0.1:8000
```

The smoke uploads only the owned demo image and checks installed assets, legacy
fields, both local metrics, an explicit diagnostic policy and per-file batch
failure isolation. It is not browser visual QA or a throughput/load test.

## Bounded container example

```bash
docker build -t sharpness-local .
docker run --rm --cap-drop=ALL --security-opt no-new-privileges:true --memory=1536m --cpus=2 --pids-limit=128 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m -p 127.0.0.1:8000:8000 sharpness-local
```

The image runs as UID 10001; its default command listens on port 8000 inside the
container. Bind to loopback for local use.
Drop capabilities and enable no-new-privileges in your actual deployment too;
the Dockerfile's non-root USER alone does not enforce those runtime settings.
The resource settings illustrate a bounded demo, not a capacity guarantee for
every 20MP/dtype/codec combination.
Temporary multipart files need a writable temporary filesystem. Run the HTTP smoke
after readiness; resource profiling belongs in a separate controlled experiment.

For public hosting, add your own trusted reverse proxy with authentication where
appropriate, connection/rate limits, timeouts and TLS. Budget memory across worker
processes, isolate temporary storage, update dependencies, and define monitoring
and incident ownership. See [security review](../SECURITY-REVIEW.md),
[caveats](../SECURITY-CAVEATS.md) and [resource measurements](PERFORMANCE.md).
