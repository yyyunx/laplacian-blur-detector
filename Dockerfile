FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# OpenCV's regular wheel needs these shared libraries on the slim base image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md LICENSE THIRD_PARTY_NOTICES.md ./
COPY laplacian_blur_detector ./laplacian_blur_detector
COPY web ./web
RUN pip install --no-cache-dir ".[server]"
RUN useradd --system --uid 10001 --create-home sharpness
USER 10001
EXPOSE 8000
CMD ["laplacian-blur-serve", "--host", "0.0.0.0", "--port", "8000"]
