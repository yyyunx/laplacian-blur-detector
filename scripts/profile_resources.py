"""Opt-in resource experiment; no accuracy claims and no production dependencies.

Run after installing .[server]: python scripts/profile_resources.py --output outputs/resources.json
Each case runs in a fresh process. The parent enforces memory/time safety limits.
"""

from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import gc
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time

MIB = 1024**2
SIZES = {"1080p": (1920, 1080), "4k": (3840, 2160), "12mp": (4000, 3000), "20mp": (5000, 4000)}


def memory(pid: int) -> tuple[int, int]:
    """Return current/peak resident bytes, without psutil (Windows or Linux)."""
    if sys.platform == "win32":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ("peak", "rss", "pp", "p", "pn", "n", "page", "peakpage")
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        query = ctypes.WinDLL("psapi").GetProcessMemoryInfo
        query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        handle = kernel.OpenProcess(0x410, False, pid)
        if not handle:
            raise OSError(ctypes.get_last_error(), "Cannot read child memory")
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            if not query(handle, ctypes.byref(counters), counters.cb):
                raise OSError("GetProcessMemoryInfo failed")
            return counters.rss, counters.peak
        finally:
            kernel.CloseHandle(handle)
    values = {}
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, value, _ = line.split()
            values[key] = int(value) * 1024
    return values["VmRSS:"], values["VmHWM:"]


def available_memory() -> int:
    if sys.platform == "win32":
        # MEMORYSTATUSEX: two DWORDs, then seven DWORDLONGs.
        buffer = ctypes.create_string_buffer(64)
        ctypes.c_uint32.from_buffer(buffer).value = 64
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(buffer):
            raise OSError("GlobalMemoryStatusEx failed")
        return ctypes.c_uint64.from_buffer(buffer, 16).value
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise OSError("MemAvailable is unavailable")


def worker(path: Path, mode: str, repeats: int) -> dict:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    import cv2
    import numpy as np

    from laplacian_blur_detector import api
    from laplacian_blur_detector.diagnostics import DiagnosticPolicy

    data = path.read_bytes()
    baseline = memory(os.getpid())[0]

    def analyze(kind):
        if kind == "quality":
            return api._analyze_quality_bytes(data, path.name, DiagnosticPolicy())
        return api._analyze_local_bytes(data, path.name, kind, 8, 8, 5.0)

    timings = []
    rss_samples = []
    for _ in range(repeats):
        gc.collect()
        started = time.perf_counter()
        if mode == "recovery":
            # Failure paths and a valid large analysis must share/release slots.
            from laplacian_blur_detector.upload_validation import UploadValidationError
            for _ in range(20):
                try:
                    api._analyze_quality_bytes(b"invalid", "invalid.png", DiagnosticPolicy())
                except UploadValidationError:
                    pass
                else:
                    raise AssertionError("Invalid image was accepted")
            results = [analyze("quality")]
        elif mode == "concurrent":
            barrier = Barrier(2)

            def paired(kind):
                barrier.wait(timeout=5)
                return analyze(kind)

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(paired, kind) for kind in ("tenengrad", "quality")]
                results = [future.result() for future in futures]
        else:
            results = [analyze(mode)]
        timings.append((time.perf_counter() - started) * 1000)
        assert all(result["success"] for result in results)
        del results
        rss_samples.append(memory(os.getpid())[0] / MIB)
    return {"status": "completed", "latency_ms": timings, "median_ms": statistics.median(timings),
            "baseline_rss_mib": baseline / MIB, "peak_rss_mib": memory(os.getpid())[1] / MIB,
            "opencv": cv2.__version__, "numpy": np.__version__, "opencv_threads": cv2.getNumThreads(),
            "rss_after_each_mib": rss_samples}


def fixture(path: Path, width: int, height: int) -> None:
    import cv2
    import numpy as np

    # Own generated RGB stripes with flat/edge regions. Never a private photo.
    row = ((np.arange(width) // 8 % 2) * 160 + 40).astype(np.uint8)
    image = np.empty((height, width, 3), dtype=np.uint8)
    for y in range(height):
        image[y, :, :] = row[:, None] if y % 32 < 16 else 128
    assert cv2.imwrite(str(path), image)


def guarded(command: list[str], reserve_mib: int, max_rss_mib: int, timeout: float) -> dict:
    if available_memory() < (reserve_mib + 64) * MIB:
        return {"status": "skipped", "reason": "insufficient available memory before launch"}
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as child:
        deadline = time.monotonic() + timeout
        sampled_peak = 0
        reason = None
        while child.poll() is None:
            try:
                sampled_peak = max(sampled_peak, memory(child.pid)[0])
            except (OSError, KeyError):
                if child.poll() is None:
                    child.terminate()
                    child.communicate()
                    raise
            if sampled_peak > max_rss_mib * MIB:
                reason = "child RSS safety budget exceeded"
            elif available_memory() < reserve_mib * MIB:
                reason = "available-memory reserve reached"
            elif time.monotonic() > deadline:
                reason = "experiment timeout"
            if reason:
                child.terminate()
                break
            time.sleep(0.02)
        stdout, stderr = child.communicate(timeout=10)
        if reason:
            return {"status": "stopped", "reason": reason, "sampled_peak_rss_mib": sampled_peak / MIB}
        if child.returncode:
            return {"status": "failed", "reason": stderr[-3000:], "returncode": child.returncode}
        return json.loads(stdout) if stdout.strip() else {"status": "completed"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sizes", nargs="+", choices=SIZES, default=list(SIZES))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--reserve-mib", type=int, default=1536)
    parser.add_argument("--max-rss-mib", type=int, default=1536)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--worker", choices=("laplacian", "tenengrad", "quality", "concurrent", "recovery"), help=argparse.SUPPRESS)
    parser.add_argument("--fixture", nargs=2, type=int, help=argparse.SUPPRESS)
    parser.add_argument("--input", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.repeats < 1 or args.reserve_mib < 256 or args.max_rss_mib < 64 or args.timeout <= 0:
        parser.error("Use positive repeats/timeout, reserve >=256 MiB and RSS budget >=64 MiB.")
    if args.fixture:
        fixture(args.input, *args.fixture)
        return
    if args.worker:
        print(json.dumps(worker(args.input, args.worker, args.repeats)))
        return
    if args.output is None:
        parser.error("--output is required")
    if args.output.exists():
        parser.error("Refusing to overwrite existing output")
    script = str(Path(__file__).resolve())
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(script).parent.parent, capture_output=True, text=True)
    report = {"recorded_utc": datetime.now(timezone.utc).isoformat(), "source_revision": revision.stdout.strip(),
              "platform": platform.platform(), "python": platform.python_version(),
              "scope": "validated API workers including decode and EXIF; no HTTP transfer; concurrent=Tenengrad+quality wall time",
              "repeats": args.repeats, "reserve_mib": args.reserve_mib, "max_rss_mib": args.max_rss_mib,
              "timeout_seconds": args.timeout, "available_mib_at_start": available_memory() / MIB, "cases": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sharpness-profile-") as directory:
        for size in args.sizes:
            width, height = SIZES[size]
            image = Path(directory) / (size + ".png")
            built = guarded([sys.executable, script, "--fixture", str(width), str(height), "--input", str(image)],
                            args.reserve_mib, args.max_rss_mib, args.timeout)
            for mode in ("laplacian", "tenengrad", "quality", "concurrent"):
                result = guarded([sys.executable, script, "--worker", mode, "--input", str(image), "--repeats", str(args.repeats)],
                                 args.reserve_mib, args.max_rss_mib, args.timeout) if built["status"] == "completed" else built.copy()
                record = {"size": size, "width": width, "height": height, "mode": mode, **result}
                report["cases"].append(record)
                args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
