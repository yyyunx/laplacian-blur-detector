"""Explicit post-build check: generated/private workspace files must not ship."""

import argparse
from pathlib import Path, PurePosixPath, PureWindowsPath
import tarfile
from zipfile import ZipFile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args()
    artifacts = sorted(args.dist.glob("*.whl")) + sorted(args.dist.glob("*.tar.gz"))
    assert any(path.suffix == ".whl" for path in artifacts), "Wheel missing"
    assert any(path.name.endswith(".tar.gz") for path in artifacts), "Source distribution missing"
    for path in artifacts:
        if path.suffix == ".whl":
            with ZipFile(path) as archive:
                names = archive.namelist()
        else:
            with tarfile.open(path) as archive:
                names = archive.getnames()
        for name in names:
            normalized = PurePosixPath(name.replace("\\", "/"))
            assert not normalized.is_absolute() and not PureWindowsPath(name).drive and ".." not in normalized.parts, f"Unsafe archive path: {name}"
            assert not set(normalized.parts).intersection({".git", ".venv", ".pytest_tmp", "outputs"}), f"Generated/private path: {name}"
            assert not any(part.startswith(".env") for part in normalized.parts), f"Environment file: {name}"
            assert normalized.suffix not in (".pem", ".key", ".pyc"), f"Private/temporary file: {name}"
        print(f"Distribution contents passed: {path.name} ({len(names)} members)")


if __name__ == "__main__":
    main()
