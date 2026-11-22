"""Offline upload-pipeline integration: advisory measurements, no universal gate."""

import argparse
import json

from laplacian_blur_detector import DiagnosticPolicy, diagnose_image_quality
from laplacian_blur_detector.image_utils import load_image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--min-width", type=int)
    parser.add_argument("--min-height", type=int)
    args = parser.parse_args()
    # Image loading is for trusted local files; HTTP upload limits do not apply.
    image = load_image(args.image)
    policy = DiagnosticPolicy(min_width=args.min_width, min_height=args.min_height)
    report = diagnose_image_quality(image, policy)
    print(json.dumps({"measurements": report["measurements"],
                      "attention": {name: check for name, check in report["checks"].items()
                                    if check["status"] in ("warning", "insufficient_evidence")}}, indent=2))


if __name__ == "__main__":
    main()
