"""Optional development server entry point."""

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the image-sharpness API and demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    try:
        import uvicorn
        import fastapi  # noqa: F401
        import multipart  # noqa: F401
    except ImportError:
        parser.exit(1, 'Install the server dependencies: pip install ".[server]"\n')
    uvicorn.run("laplacian_blur_detector.api:app", host=args.host, port=args.port)
    return 0
