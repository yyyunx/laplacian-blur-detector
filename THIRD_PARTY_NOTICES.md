# Third-Party Software Notices

This project uses third-party open-source software.

The original source code of this repository is licensed under the MIT License. Third-party dependencies are not relicensed under the MIT License of this project and remain subject to their respective license terms and copyrights.

## OpenCV / opencv-python

**Purpose:** Image processing, grayscale conversion, Laplacian filtering, and variance-based image sharpness analysis.

* OpenCV: Apache License 2.0
* opencv-python packaging scripts: MIT License
* Project: https://opencv.org/
* Python package: https://github.com/opencv/opencv-python

OpenCV 4.5.0 and later are distributed under the Apache License 2.0.

The `opencv-python` binary wheels may contain additional third-party components. Official upstream license information, including licenses for redistributed components, is available in the `opencv-python` `LICENSE-3RD-PARTY.txt` file.

Depending on the package and platform, these components may include software such as FFmpeg and Qt.

## FastAPI

**Purpose:** REST API framework.

* License: MIT License
* Project: https://github.com/fastapi/fastapi

## Pillow

**Purpose:** Reading upload headers to validate format and image dimensions before pixel decoding.

* License: MIT-CMU
* Project: https://github.com/python-pillow/Pillow
* Pillow is required by the optional HTTP server, not the core library or offline CLI.

## NumPy

**Purpose:** Numerical operations and image-array processing.

* License: BSD 3-Clause License
* Project: https://github.com/numpy/numpy

## Uvicorn

**Purpose:** ASGI server used to run the FastAPI application.

* License: BSD 3-Clause License
* Project: https://github.com/encode/uvicorn

## python-multipart

**Purpose:** Parsing multipart/form-data image uploads.

* License: Apache License 2.0
* Project: https://github.com/Kludex/python-multipart

## HTTPX

**Purpose:** HTTP client used by API tests.

* License: BSD 3-Clause License
* Project: https://github.com/encode/httpx

## pytest

**Purpose:** Automated testing.

* License: MIT License
* Project: https://github.com/pytest-dev/pytest

## Development and build tooling

These tools are used for contribution checks and package builds; they are not
required by the image analysis runtime.

* build: MIT License — https://github.com/pypa/build
* Hatchling: MIT License — https://github.com/pypa/hatch
* Ruff: MIT License — https://github.com/astral-sh/ruff

---

The licenses and copyrights of all third-party software remain with their respective authors and copyright holders.

For authoritative licensing information, refer to the upstream project and the exact dependency version installed by this project.
