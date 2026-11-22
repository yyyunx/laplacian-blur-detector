"""Bounded Linux container triage, not a proof that every decoder path is safe.

Feed to `docker exec -i ... python -` after the existing service smoke. Uses only
installed runtime dependencies and benign generated metadata; no vulnerability
exploit, fuzzing, external-entity resolution or outbound-network fixture is used.
"""

from io import BytesIO
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen


def status(pid):
    fields = {}
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        key, _, value = line.partition(":")
        if key in ("Uid", "NoNewPrivs", "CapEff", "CapPrm", "CapBnd"):
            fields[key] = value.strip()
    return fields


def libraries(pid):
    return sorted({line.split()[-1] for line in Path(f"/proc/{pid}/maps").read_text().splitlines()
                   if "/" in line and ".so" in line})


def main():
    if not Path("/proc/self/maps").exists():
        raise SystemExit("This diagnostic requires the actual Linux service container.")
    report = {"scope": "bounded observations; absence from samples is not universal non-reachability",
              "pid1_status": status(1), "probe_status": status("self"),
              "server_libraries_before": libraries(1), "fixture_results": []}
    for fields in (report["pid1_status"], report["probe_status"]):
        assert fields["NoNewPrivs"] == "1", "no-new-privileges must apply to server and probe"
        assert all(int(fields[key], 16) == 0 for key in ("CapEff", "CapPrm", "CapBnd"))
        assert set(fields["Uid"].split()) == {"10001"}

    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, PngImagePlugin
    from laplacian_blur_detector import api

    report["versions"] = {"opencv": cv2.__version__, "pillow": Image.__version__, "numpy": np.__version__}
    report["opencv_build"] = cv2.getBuildInformation()
    report["probe_libraries_imported"] = libraries("self")
    image = Image.new("RGB", (160, 128), (128, 128, 128))
    ImageDraw.Draw(image).rectangle((0, 0, 63, 127), fill=(10, 180, 80))
    # Finite benign DTD/metadata: no external identifiers or expansion stress.
    xmp = ('<!DOCTYPE x:xmpmeta [<!ENTITY note "triage">]>'
           '<x:xmpmeta xmlns:x="adobe:ns:meta/" xmlns:tiff="http://ns.adobe.com/tiff/1.0/" '
           'tiff:Orientation="6"><note>&note;</note></x:xmpmeta>')
    fixtures = []
    for name, fmt, options in (
        ("png-plain", "PNG", {}),
        ("png-xmp", "PNG", {"pnginfo": PngImagePlugin.PngInfo()}),
        ("jpeg-xmp", "JPEG", {"xmp": xmp.encode()}),
    ):
        if "pnginfo" in options:
            options["pnginfo"].add_itxt("XML:com.adobe.xmp", xmp, zip=True)
        stream = BytesIO()
        image.save(stream, format=fmt, **options)
        fixtures.append((name, fmt, stream.getvalue()))

    getxmp_calls = []
    original_getxmp = Image.Image.getxmp

    def unexpected_getxmp(*args, **kwargs):
        getxmp_calls.append(True)
        raise AssertionError("Selected worker unexpectedly called Pillow.getxmp")

    Image.Image.getxmp = unexpected_getxmp
    try:
        for name, fmt, data in fixtures:
            filename = name + (".png" if fmt == "PNG" else ".jpg")
            with Image.open(BytesIO(data)) as header:
                metadata_present = bool(header.info.get("xmp") or header.info.get("XML:com.adobe.xmp"))
            assert metadata_present == name.endswith("-xmp")
            # Guard the direct worker calls as well as checking the real HTTP service.
            assert api._analyze_local_bytes(data, filename, "tenengrad", 8, 8, 5.0)["success"]
            assert api._analyze_quality_bytes(data, filename, api.DiagnosticPolicy())["success"]
            results = []
            for route in ("/api/blur/check", "/api/sharpness/local", "/api/quality/diagnose"):
                boundary = "bounded-container-triage"
                body = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{filename}"\r\n'
                        f'Content-Type: image/{"png" if fmt == "PNG" else "jpeg"}\r\n\r\n').encode() + data + f"\r\n--{boundary}--\r\n".encode()
                request = Request("http://127.0.0.1:8000" + route, data=body,
                                  headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
                with urlopen(request, timeout=10) as response:
                    payload = json.load(response)
                    assert response.status == 200 and payload["success"]
                    results.append({"route": route, "width": payload["width"], "height": payload["height"]})
            report["fixture_results"].append({"fixture": name, "metadata_present": metadata_present, "http": results,
                                               "server_libraries_after": libraries(1)})
    finally:
        Image.Image.getxmp = original_getxmp
    report["pillow_getxmp_worker_calls"] = len(getxmp_calls)
    report["probe_libraries_after_workers"] = libraries("self")
    report["environment"] = {key: os.environ.get(key) for key in ("DISPLAY", "WAYLAND_DISPLAY")}
    report["optional_modules_present"] = {name: importlib.util.find_spec(name) is not None
                                          for name in ("libxml2", "lxml", "defusedxml", "aioquic")}
    report["installed_sensitive_executables"] = {}
    for name in ("/usr/lib/systemd/systemd-homed", "/usr/bin/mount", "/usr/bin/nsenter"):
        path = Path(name)
        report["installed_sensitive_executables"][name] = {"exists": path.exists(),
                                                           "mode": oct(path.stat().st_mode) if path.exists() else None}
    import pip
    vendor = Path(pip.__file__).parent / "_vendor"
    report["pip_vendor_executable_components"] = {name: (vendor / name).exists()
                                                   for name in ("setuptools", "pkg_resources", "setuptools/package_index.py")}
    report["process1_command"] = Path("/proc/1/cmdline").read_bytes().replace(b"\0", b" ").decode()
    subprocess_env = {key: value for key, value in os.environ.items() if key != "LD_DEBUG"}
    for label, command in (
        ("package_versions_and_depends", ["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Depends}\n",
                                          "libgl1", "libglx0", "libglx-mesa0", "mesa-libgallium", "libllvm19", "libxml2", "libexpat1", "libx11-6"]),
    ):
        result = subprocess.run(command, capture_output=True, text=True, timeout=10, env=subprocess_env)
        assert result.returncode == 0
        report[label] = {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    report["elf_dependencies"] = []
    for directory, pattern in ((Path(cv2.__file__).parent, "cv2*.so"), (Path(Image.__file__).parent, "_imaging*.so")):
        for path in sorted(directory.glob(pattern)):
            result = subprocess.run(["ldd", str(path)], capture_output=True, text=True, timeout=10, env=subprocess_env)
            assert result.returncode == 0
            report["elf_dependencies"].append({"path": str(path), "ldd": result.stdout})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
