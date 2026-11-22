# Resource measurements (2026-11-22)

These are synthetic resource experiments, not accuracy results or service SLOs.
Windows 11, Python 3.12.14, NumPy 2.5.3, OpenCV 5.0.0, 15.71 GiB physical RAM;
about 3.5 GiB was available. Other desktop workloads were active. OpenCV reported
20 threads in most cases and 10 in some concurrent cases; thread scheduling and
allocator retention affect these measurements. Do not interpret small latency
differences as stable improvements.

## Method

Install `.[server]`, then run from the checkout:

```bash
python scripts/profile_resources.py --output outputs/resources.json
```

The script makes its own RGB stripe PNGs. Each case uses a fresh Python process,
three sequential trials, an 8×8 grid and native default texture cutoff. Latency
is median wall time including header validation, decode, EXIF and API worker
measurements, excluding imports, fixture generation, HTTP transfer and browser
rendering. First trials are included; these are not warmed-only timings. Peak RSS
is the OS process high-water mark including imports/allocations across all trials,
not a sum of array sizes. Concurrent means one Tenengrad heatmap and one quality
request starting together through the shared two-slot worker mechanism; latency
is time until both complete, and memory is their shared process peak.

Parent monitoring samples every 20 ms, reserves 1,536 MiB available RAM, limits
child RSS to 1,536 MiB and times out each case after 60 seconds. A guard stop is
recorded rather than reported as success. Sampling cannot guarantee protection
from an instantaneous allocation spike: use a deployment memory limit too.
The tool requires Windows or Linux memory counters; unsupported hosts fail
explicitly. Output refuses overwrite and belongs under ignored `outputs/`.

## Results after reducing allocations

Each cell is **median milliseconds / peak RSS MiB**. All 16 cases completed;
no safety stop or OOM occurred. Full raw local outputs are intentionally ignored.

| Size | Local Laplacian | Local Tenengrad | Quality (both metrics) | Two concurrent workers |
| --- | --- | --- | --- | --- |
| 1920×1080 | 38.3 / 88.2 | 48.5 / 106.8 | 92.5 / 107.0 | 83.4 / 128.0 |
| 3840×2160 | 146.5 / 161.0 | 165.7 / 226.6 | 310.8 / 227.2 | 327.9 / 319.8 |
| 4000×3000 | 255.4 / 204.5 | 278.2 / 297.7 | 406.3 / 297.8 | 484.4 / 364.8 |
| 5000×4000 | 450.0 / 297.7 | 490.6 / 451.2 | 740.1 / 451.4 | 823.1 / 678.3 |

Before optimization (source `5e34a61`, same script/fixtures/repeats):

| Size | Local Laplacian | Local Tenengrad | Quality | Two concurrent workers |
| --- | --- | --- | --- | --- |
| 1920×1080 | 50.9 / 103.5 | 59.3 / 122.0 | 115.8 / 125.8 | 118.9 / 151.5 |
| 3840×2160 | 181.3 / 218.6 | 212.0 / 284.0 | 473.8 / 293.9 | 468.3 / 400.1 |
| 4000×3000 | 289.9 / 285.3 | 297.4 / 380.3 | 619.0 / 393.3 | 661.3 / 549.1 |
| 5000×4000 | 487.0 / 431.8 | 509.4 / 587.8 | 1049.4 / 608.0 | 1056.1 / 870.2 |

Integer grayscale inputs now retain uint8/uint16 storage before OpenCV produces
float64 derivative arrays. Float validation/conversion and derivative definitions
stay unchanged. Diagnostics counts bright pixels channel by channel and releases
the mask before derivative passes. Exact-reference tests cover both metrics and
irregular local grids across uint8/uint16/float32/float64; input arrays are unchanged.
Legacy blur scoring, frozen benchmark versions/labels, response fields and limits
are unchanged. The after results measure these source changes, not a different
threshold, preprocessing normalization or dataset.

## Lifecycle and recovery evidence

- API tests exercise invalid images, oversized headers/streams, busy 503 and recovery.
- Four focused tests cover local/quality coroutine cancellation and client-style
  `asyncio.wait_for` timeout. The upload closes, but an active native worker keeps
  its semaphore slot until completion; replacement work gets 503. Successful
  legacy analysis then proves the slot recovers. These are coroutine tests, not
  a real TCP-disconnect or reverse-proxy timeout test.
- A separate 12MP worker completed ten quality analyses interleaved with 200 invalid
  images: median 457.9 ms per round, peak 298.2 MiB. End-of-round RSS was
  66.06, 66.42, 66.19, 66.32, 66.59, 66.61, 66.34, 66.61, 66.48, 66.50 MiB.
  This bounded run shows recovery without sustained growth; it is not proof of
  leak freedom under every codec, workload or runtime.

Reproduce the recovery case in a fresh process (internal experiment switches):

```bash
python scripts/profile_resources.py --fixture 4000 3000 --input outputs/recovery.png
python scripts/profile_resources.py --worker recovery --input outputs/recovery.png --repeats 10
```

Use the default parent-guarded experiment for large inputs; direct `--worker` is
for controlled diagnostics and does not include parent memory guards.

## Operational implications

20MP is a pixel cap, not a promise of suitability for a small-memory container.
Two server processes can each admit two analyses and multiply memory costs.
Input dtype, EXIF rotation, PNG/JPEG codec, content, and fragmentation also matter;
this RGB8 fixture is not a worst-case bound for supported 16-bit PNGs. Provision
memory headroom, upload/temporary-disk quotas, connection limits and proxy timeouts.
There is no hard native-computation deadline: aborting a browser upload does not
kill an already accepted OpenCV operation. Do not release its slot prematurely.
See [security boundaries](../SECURITY.md) and [release gates](RELEASE_READINESS.md).
