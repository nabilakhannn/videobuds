"""
WaveSpeed AI provider — image generation (GPT Image 1.5),
video generation (Kling 3.0, Sora 2 Pro), media upload, and
InfiniteTalk talking head generation via WaveSpeed's REST API.

All generation is ASYNCHRONOUS (submit → poll).
WaveSpeed returns a dynamic polling URL in the submit response.
"""

import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from .. import config
from ..utils import (
    print_status,
    submit_wavespeed_task,
    poll_wavespeed_task,
)

logger = logging.getLogger(__name__)

# Provider sync flags — WaveSpeed is always async
image_IS_SYNC = False
video_IS_SYNC = False

# --- WaveSpeed image model IDs ---
_IMAGE_MODELS = {
    "gpt-image-1.5": "openai/gpt-image-1.5/edit",
}

# --- WaveSpeed video model IDs ---
_VIDEO_MODELS = {
    "kling-3.0": "kwaivgi/kling-v3.0-pro/image-to-video",
    "kling-3.0-std": "kwaivgi/kling-v3.0-std/image-to-video",
    "sora-2": "openai/sora-2/image-to-video",
    "sora-2-pro": "openai/sora-2/image-to-video-pro",
}

# Module-level storage: task_id → poll_url
# Populated by submit_image/submit_video, consumed by poll_image/poll_video/poll_tasks_parallel
_task_poll_urls = {}


# --- Image helpers ---

def _map_image_size(aspect_ratio):
    """Map aspect ratio to GPT Image 1.5 size parameter."""
    return {
        "9:16": "1024*1536",
        "2:3":  "1024*1536",
        "16:9": "1536*1024",
        "3:2":  "1536*1024",
        "1:1":  "1024*1024",
    }.get(aspect_ratio, "auto")


def _map_image_quality(resolution):
    """Map resolution string to GPT Image 1.5 quality parameter."""
    if resolution in ("2K", "4K"):
        return "high"
    return "medium"


def submit_image(prompt, reference_urls=None, aspect_ratio="9:16",
                 resolution="1K", model="gpt-image-1.5", **kwargs):
    """
    Submit an image generation task to WaveSpeed AI (GPT Image 1.5).

    Args:
        prompt: Image prompt text
        reference_urls: List of reference image URLs (product references)
        aspect_ratio: Aspect ratio string (e.g., "9:16")
        resolution: "1K", "2K", or "4K"
        model: "gpt-image-1.5"

    Returns:
        str: task_id for polling
    """
    model_id = _IMAGE_MODELS.get(model)
    if not model_id:
        raise ValueError(f"WaveSpeed doesn't support image model: '{model}'. "
                         f"Available: {list(_IMAGE_MODELS.keys())}")

    payload = {
        "prompt": prompt,
        "size": _map_image_size(aspect_ratio),
        "quality": _map_image_quality(resolution),
        "input_fidelity": "high",
        "output_format": "jpeg",
    }
    if reference_urls:
        payload["images"] = list(reference_urls)

    task_info = submit_wavespeed_task(model_id, payload)
    _task_poll_urls[task_info["task_id"]] = task_info["poll_url"]
    return task_info["task_id"]


def poll_image(task_id, max_wait=300, poll_interval=5, quiet=False):
    """
    Poll a WaveSpeed image task. Returns GenerationResult dict.

    Args:
        task_id: The task ID returned by submit_image
        max_wait: Maximum seconds to wait
        poll_interval: Seconds between checks
        quiet: Suppress status messages

    Returns:
        dict: GenerationResult with status, result_url, task_id
    """
    poll_url = _task_poll_urls.get(task_id)
    if not poll_url:
        raise Exception(f"No poll URL stored for WaveSpeed task {task_id}. "
                        "Was submit_image called in this session?")
    return poll_wavespeed_task(task_id, poll_url, max_wait=max_wait,
                               poll_interval=poll_interval, quiet=quiet)


def submit_video(prompt, image_url=None, model="sora-2-pro",
                 duration="5", aspect_ratio="9:16", mode="pro", **kwargs):
    """
    Submit a video generation task to WaveSpeed AI.

    Args:
        prompt: Video prompt text
        image_url: Source image URL (start frame)
        model: "kling-3.0", "kling-3.0-std", "sora-2", or "sora-2-pro"
        duration: Video duration in seconds
        aspect_ratio: Aspect ratio string
        mode: "std" or "pro" — Kling quality mode (default: "pro")

    Returns:
        str: task_id for polling
    """
    # For Kling, select pro/std model variant based on mode
    if model == "kling-3.0" and mode == "std":
        model_id = _VIDEO_MODELS.get("kling-3.0-std")
    else:
        model_id = _VIDEO_MODELS.get(model)
    if not model_id:
        raise ValueError(f"WaveSpeed doesn't support video model: '{model}'. "
                         f"Available: {list(_VIDEO_MODELS.keys())}")

    if model.startswith("kling"):
        payload = {
            "prompt": prompt,
            "duration": int(duration),
            "cfg_scale": 0.5,
            "sound": True,
        }
        if image_url:
            payload["image"] = image_url

    elif model.startswith("sora"):
        # Map duration: WaveSpeed Sora accepts 4/8/12/16/20
        dur_int = int(duration)
        if dur_int <= 5:
            ws_duration = 4
        elif dur_int <= 10:
            ws_duration = 8
        elif dur_int <= 14:
            ws_duration = 12
        elif dur_int <= 18:
            ws_duration = 16
        else:
            ws_duration = 20

        payload = {
            "prompt": prompt,
            "duration": ws_duration,
        }
        if model == "sora-2-pro":
            payload["resolution"] = "1080p"
        if image_url:
            payload["image"] = image_url
    else:
        raise ValueError(f"No payload builder for model: {model}")

    task_info = submit_wavespeed_task(model_id, payload)

    # Store poll_url for later retrieval by poll functions
    _task_poll_urls[task_info["task_id"]] = task_info["poll_url"]

    return task_info["task_id"]


def poll_video(task_id, max_wait=600, poll_interval=10, quiet=False):
    """
    Poll a WaveSpeed video task. Returns GenerationResult dict.

    Args:
        task_id: The task ID returned by submit_video
        max_wait: Maximum seconds to wait
        poll_interval: Seconds between checks
        quiet: Suppress status messages

    Returns:
        dict: GenerationResult with status, result_url, task_id
    """
    poll_url = _task_poll_urls.get(task_id)
    if not poll_url:
        raise Exception(f"No poll URL stored for WaveSpeed task {task_id}. "
                        "Was submit_video called in this session?")

    return poll_wavespeed_task(task_id, poll_url, max_wait=max_wait,
                               poll_interval=poll_interval, quiet=quiet)


# ---------------------------------------------------------------------------
# Media Upload (for Talking Avatar — uploads audio/images to get hosted URLs)
# ---------------------------------------------------------------------------

def upload_media(data_bytes, content_type="audio/wav", api_key=None):
    """Upload media to WaveSpeed via **multipart form** and get a hosted URL.

    Used by the Talking Avatar recipe to upload TTS audio and headshot
    images so that downstream providers (Speak v2, InfiniteTalk) can
    access them via URL.

    Parameters
    ----------
    data_bytes : bytes
        Raw file bytes to upload.
    content_type : str
        MIME type of the file (e.g., ``"audio/wav"``, ``"image/jpeg"``).
    api_key : str, optional
        WaveSpeed API key.  Falls back to ``config.WAVESPEED_API_KEY``.

    Returns
    -------
    str
        The hosted URL of the uploaded file.

    Raises
    ------
    RuntimeError
        If the upload fails or no URL is returned.
    """
    api_key = api_key or config.WAVESPEED_API_KEY
    if not api_key:
        raise RuntimeError("WAVESPEED_API_KEY not configured")

    url = f"{config.WAVESPEED_API_URL}/media/upload/binary"
    headers = {
        "Authorization": f"Bearer {api_key}",
        # Do NOT set Content-Type — requests sets it automatically for
        # multipart/form-data with the correct boundary.
    }

    # Map MIME type → sensible filename for the multipart upload
    _ext_map = {
        "audio/wav": "upload.wav",
        "audio/mpeg": "upload.mp3",
        "audio/mp3": "upload.mp3",
        "image/jpeg": "upload.jpg",
        "image/png": "upload.png",
        "image/webp": "upload.webp",
    }
    filename = _ext_map.get(content_type, "upload.bin")

    try:
        resp = requests.post(
            url,
            headers=headers,
            files={"file": (filename, data_bytes, content_type)},
            timeout=120,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"WaveSpeed media upload failed: {exc}") from exc

    result = resp.json()
    # WaveSpeed may return the URL under different keys — try all known ones
    data = result.get("data", {})
    file_url = (
        data.get("download_url")
        or data.get("file_url")
        or data.get("url")
        or result.get("url", "")
    )
    if not file_url:
        raise RuntimeError(f"No URL in WaveSpeed upload response: {result}")

    logger.info("WaveSpeed upload: %s (%d bytes)", file_url, len(data_bytes))
    return file_url


# ---------------------------------------------------------------------------
# InfiniteTalk — Talking Head Video (audio + image → talking video)
# ---------------------------------------------------------------------------

def submit_infinitetalk(audio_url, image_url, prompt="",
                        resolution="480p", api_key=None):
    """Submit an InfiniteTalk job to WaveSpeed (talking head video).

    Parameters
    ----------
    audio_url : str
        Hosted URL of the speech audio (WAV/MP3).
    image_url : str
        Hosted URL of the headshot/character image.
    prompt : str, optional
        Motion/expression guidance (e.g., "natural conversational gestures").
    resolution : str
        Output resolution — ``"480p"`` or ``"720p"`` (default ``"480p"``).
    api_key : str, optional
        WaveSpeed API key.  Falls back to ``config.WAVESPEED_API_KEY``.

    Returns
    -------
    str
        Polling URL (``get_url``) for checking job status.

    Raises
    ------
    RuntimeError
        If submission fails.
    """
    api_key = api_key or config.WAVESPEED_API_KEY
    if not api_key:
        raise RuntimeError("WAVESPEED_API_KEY not configured")

    url = f"{config.WAVESPEED_API_URL}/wavespeed-ai/infinitetalk"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "audio": audio_url,
        "image": image_url,
        "resolution": resolution,
    }
    if prompt:
        payload["prompt"] = prompt

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"WaveSpeed InfiniteTalk submit failed: {exc}") from exc

    result = resp.json()
    get_url = result.get("data", {}).get("urls", {}).get("get")
    if not get_url:
        raise RuntimeError(
            f"No polling URL in WaveSpeed InfiniteTalk response: {result}"
        )

    logger.info("WaveSpeed InfiniteTalk submitted: %s", get_url)
    return get_url


def poll_infinitetalk(get_url, api_key=None, max_wait=600, interval=5):
    """Poll a WaveSpeed InfiniteTalk job until completion.

    Parameters
    ----------
    get_url : str
        The polling URL returned by ``submit_infinitetalk``.
    api_key : str, optional
        WaveSpeed API key.
    max_wait : int
        Maximum seconds to wait.
    interval : int
        Seconds between polls.

    Returns
    -------
    str
        The video URL on success.

    Raises
    ------
    RuntimeError
        If the job fails.
    TimeoutError
        If the job doesn't complete in time.
    """
    import time as _time

    api_key = api_key or config.WAVESPEED_API_KEY
    if not api_key:
        raise RuntimeError("WAVESPEED_API_KEY not configured")

    headers = {"Authorization": f"Bearer {api_key}"}
    max_polls = max_wait // interval

    for i in range(max_polls):
        _time.sleep(interval)
        try:
            resp = requests.get(get_url, headers=headers, timeout=30)
            data = resp.json().get("data", {})
        except Exception:
            continue

        status = data.get("status", "")
        logger.info("InfiniteTalk poll %d/%d: %s", i + 1, max_polls, status)

        if status == "completed":
            outputs = data.get("outputs", [])
            if outputs:
                return outputs[0] if isinstance(outputs[0], str) else outputs[0].get("url", "")
            output_url = data.get("output", {}).get("url", "")
            if output_url:
                return output_url
            raise RuntimeError(f"No video URL in completed InfiniteTalk: {data}")

        elif "fail" in status.lower() or "error" in status.lower():
            raise RuntimeError(
                f"InfiniteTalk failed: {data.get('errorMessage', status)}"
            )

    raise TimeoutError(f"InfiniteTalk timeout after {max_wait}s")


def poll_tasks_parallel(task_ids, max_wait=600, poll_interval=10):
    """
    Poll multiple WaveSpeed tasks concurrently.

    Args:
        task_ids: List of task ID strings (from submit_video)
        max_wait: Max seconds to wait per task
        poll_interval: Seconds between checks

    Returns:
        dict: task_id → GenerationResult
    """
    if not task_ids:
        return {}

    total = len(task_ids)
    completed = []
    results = {}

    def _poll_one(tid):
        result = poll_video(tid, max_wait=max_wait,
                            poll_interval=poll_interval, quiet=True)
        completed.append(tid)
        print_status(f"Task {tid[:12]}... done ({len(completed)}/{total})", "OK")
        return result

    max_workers = min(total, 20)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_poll_one, tid): tid
            for tid in task_ids
        }
        for future in as_completed(futures):
            tid = futures[future]
            try:
                results[tid] = future.result()
            except Exception as e:
                completed.append(tid)
                print_status(f"Task {tid[:12]}... failed: {e}", "XX")
                results[tid] = {
                    "status": "error",
                    "task_id": tid,
                    "error": str(e),
                }

    return results
