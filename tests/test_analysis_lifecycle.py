"""Cancellation cannot admit replacement work while a native worker is active."""

import asyncio
from io import BytesIO
from threading import BoundedSemaphore, Event
import time

from fastapi import UploadFile
import pytest

from laplacian_blur_detector import api
from laplacian_blur_detector.upload_validation import UploadValidationError


@pytest.mark.parametrize("kind", ["local", "quality"])
@pytest.mark.parametrize("timeout", [False, True])
def test_cancelled_or_timed_out_analysis_keeps_slot_until_worker_exits(monkeypatch, kind, timeout):
    data = (api.WEB_DIRECTORY / "demo.png").read_bytes()
    entered, release = Event(), Event()
    slots = BoundedSemaphore(1)
    monkeypatch.setattr(api, "_analysis_slots", slots)
    original = api.analyze_local_sharpness if kind == "local" else api.diagnose_image_quality

    def blocked(*args, **kwargs):
        entered.set()
        if not release.wait(5):
            raise RuntimeError("Test did not release the native worker")
        return original(*args, **kwargs)

    monkeypatch.setattr(api, "analyze_local_sharpness" if kind == "local" else "diagnose_image_quality", blocked)

    async def scenario():
        upload = UploadFile(file=BytesIO(data), filename="demo.png")
        operation = api.local_sharpness(upload, "tenengrad", 8, 8, 5.0) if kind == "local" else api.quality_diagnostics(upload, "{}")
        task = asyncio.create_task(operation)
        try:
            assert await asyncio.to_thread(entered.wait, 3)
            if timeout:
                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(task, 0.01)
            else:
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            assert upload.file.closed
            with pytest.raises(UploadValidationError) as error:
                api._analyze_bytes(data, "demo.png", 100)
            assert error.value.status_code == 503
        finally:
            release.set()
            if not task.done():
                await task
        deadline = time.monotonic() + 3
        while not slots.acquire(blocking=False):
            assert time.monotonic() < deadline, "Worker leaked its analysis slot"
            await asyncio.sleep(0.01)
        slots.release()
        result = await asyncio.to_thread(api._analyze_bytes, data, "demo.png", 100)
        assert result["success"]

    asyncio.run(scenario())
