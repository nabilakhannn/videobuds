"""
Higgsfield AI provider — image & video generation via the Higgsfield REST API.

Image models: Nano Banana, Nano Banana Pro
Video models: Seedance (ByteDance), Minimax
Talking Head: Speak v2 (Platform API), talking_photo (legacy Diffusion API)

All generation is ASYNCHRONOUS (submit → poll).

API docs: https://cloud.higgsfield.ai/
"""

import logging
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from .. import config
from ..utils import print_status

logger = logging.getLogger(__name__)

# Provider sync flags — Higgsfield is always async
image_IS_SYNC = False
video_IS_SYNC = False

# --- Higgsfield model IDs ---
_IMAGE_MODELS = {
    "nano-banana": "nano-banana",
    "nano-banana-pro": "nano-banana-pro",
}

# --- Video model IDs (Higgsfield API model paths) ---
_VIDEO_MODELS = {
    # Seedance by ByteDance — high quality, affordable
    "seedance": "bytedance/seedance/2-0",
    "seedance-i2v": "bytedance/seedance/v1/pro/image-to-video",
    # Minimax — fast, good quality, affordable
    "minimax": "minimax-ai/video-01-director/general",
}

# --- API URLs ---
_API_BASE = "https://api.higgsfield.ai/v1"
_GENERATIONS_URL = f"{_API_BASE}/generations"
_PLATFORM_BASE = "https://platform.higgsfield.ai"


def _headers():
    """Auth headers for Higgsfield API (Key ID:SECRET format)."""
    key_id = config.HIGGSFIELD_API_KEY_ID
    key_secret = config.HIGGSFIELD_API_KEY_SECRET
    return {
        "Authorization": f"Key {key_id}:{key_secret}",
        "Content-Type": "application/json",
    }


def _aspect_to_dimensions(aspect_ratio, resolution="1K"):
    """Convert aspect ratio string to width/height pixel dimensions."""
    base_sizes = {
        "1K": {
            "9:16": (576, 1024),
            "16:9": (1024, 576),
            "1:1": (1024, 1024),
            "4:5": (896, 1120),
            "5:4": (1120, 896),
            "2:3": (768, 1152),
            "3:2": (1152, 768),
            "3:4": (768, 1024),
            "4:3": (1024, 768),
            "21:9": (1344, 576),
        },
    }
    sizes = base_sizes.get(resolution, base_sizes["1K"])
    return sizes.get(aspect_ratio, (576, 1024))


# ---------------------------------------------------------------------------
# Image Generation (Asynchronous)
# ---------------------------------------------------------------------------

def submit_image(prompt, reference_paths=None, reference_urls=None,
                 aspect_ratio="9:16", resolution="1K",
                 model="nano-banana-pro", **kwargs):
    """
    Submit an image generation task to Higgsfield.

    Args:
        prompt: Image generation prompt
        reference_paths: Local file paths (not used — Higgsfield uses URLs)
        reference_urls: Hosted reference image URLs
        aspect_ratio: Aspect ratio string (e.g., "9:16")
        resolution: "1K", "2K", or "4K"
        model: "nano-banana" or "nano-banana-pro"

    Returns:
        str: generation_id for polling
    """
    hf_model = _IMAGE_MODELS.get(model, "nano-banana-pro")
    width, height = _aspect_to_dimensions(aspect_ratio, resolution)

    payload = {
        "task": "text-to-image",
        "model": hf_model,
        "prompt": prompt,
        "width": width,
        "height": height,
    }

    # Add reference images if available
    if reference_urls:
        payload["image_urls"] = reference_urls[:3]

    response = requests.post(
        _GENERATIONS_URL,
        headers=_headers(),
        json=payload,
        timeout=60,
    )

    if response.status_code not in (200, 201, 202):
        raise Exception(
            f"Higgsfield submit error {response.status_code}: {response.text[:500]}"
        )

    result = response.json()
    generation_id = result.get("id") or result.get("generation_id")
    if not generation_id:
        raise Exception(f"No generation ID in Higgsfield response: {result}")

    return generation_id


def poll_image(generation_id, max_wait=300, poll_interval=5, quiet=False):
    """
    Poll a Higgsfield generation until completion.

    Args:
        generation_id: The generation ID from submit_image
        max_wait: Maximum seconds to wait
        poll_interval: Seconds between checks
        quiet: Suppress status messages

    Returns:
        dict: GenerationResult with status, result_url, task_id
    """
    start_time = time.time()
    url = f"{_GENERATIONS_URL}/{generation_id}"

    while time.time() - start_time < max_wait:
        response = requests.get(url, headers=_headers(), timeout=30)

        if response.status_code != 200:
            elapsed = int(time.time() - start_time)
            if not quiet:
                print_status(
                    f"Higgsfield poll returned {response.status_code}, retrying... ({elapsed}s)", "!!"
                )
            time.sleep(poll_interval)
            continue

        result = response.json()
        status = result.get("status", "").lower()

        if status == "completed":
            # Extract image URL from response
            images = result.get("images", [])
            if images:
                image_url = images[0].get("url", "")
            else:
                # Fallback: check other response formats
                image_url = result.get("result_url", "") or result.get("url", "")

            if not image_url:
                raise Exception(f"No image URL in completed Higgsfield response: {result}")

            if not quiet:
                print_status("Higgsfield generation completed!", "OK")

            return {
                "status": "success",
                "result_url": image_url,
                "task_id": generation_id,
            }

        elif status in ("failed", "error", "nsfw"):
            error_msg = result.get("error", result.get("message", f"Generation {status}"))
            raise Exception(f"Higgsfield generation {status}: {error_msg}")

        # Still processing (queued, in_progress)
        elapsed = int(time.time() - start_time)
        if not quiet:
            print_status(f"Higgsfield status: {status} ({elapsed}s elapsed)", "..")
        time.sleep(poll_interval)

    raise Exception(f"Higgsfield timeout after {max_wait}s for generation: {generation_id}")


def poll_tasks_parallel(generation_ids, max_wait=300, poll_interval=5):
    """
    Poll multiple Higgsfield generations concurrently.

    Args:
        generation_ids: List of generation ID strings
        max_wait: Max seconds to wait per generation
        poll_interval: Seconds between checks

    Returns:
        dict: generation_id -> GenerationResult
    """
    if not generation_ids:
        return {}

    total = len(generation_ids)
    completed = []
    results = {}

    def _poll_one(gen_id):
        result = poll_image(gen_id, max_wait=max_wait,
                            poll_interval=poll_interval, quiet=True)
        completed.append(gen_id)
        short = gen_id[:12]
        print_status(f"Higgsfield {short}... done ({len(completed)}/{total})", "OK")
        return result

    max_workers = min(total, 10)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_poll_one, gid): gid
            for gid in generation_ids
        }
        for future in as_completed(futures):
            gid = futures[future]
            try:
                results[gid] = future.result()
            except Exception as e:
                completed.append(gid)
                short = gid[:12]
                print_status(f"Higgsfield {short}... failed: {e}", "XX")
                results[gid] = {
                    "status": "error",
                    "task_id": gid,
                    "error": str(e),
                }

    return results  # poll_tasks_parallel


# ---------------------------------------------------------------------------
# Video Generation (Asynchronous — Seedance & Minimax)
# ---------------------------------------------------------------------------

def submit_video(prompt, image_url=None, image_path=None,
                 model="seedance", duration="5", mode="pro",
                 aspect_ratio="9:16", **kwargs):
    """
    Submit a video generation task to Higgsfield (Seedance / Minimax).

    Args:
        prompt: Text prompt describing the desired video
        image_url: Source image URL (start frame for image-to-video)
        image_path: Local file path to source image (uploaded as base64)
        model: "seedance" or "minimax"
        duration: Video duration in seconds (not all models honour this)
        mode: Quality mode (ignored for most Higgsfield video models)
        aspect_ratio: Aspect ratio string (e.g., "9:16")

    Returns:
        str: generation_id for polling
    """
    import base64

    # Determine task type and resolve model ID
    has_image = bool(image_url or image_path)

    if model in ("seedance",):
        # Seedance has separate text-to-video and image-to-video endpoints
        if has_image:
            hf_model = _VIDEO_MODELS.get("seedance-i2v",
                                          "bytedance/seedance/v1/pro/image-to-video")
            task = "image-to-video"
        else:
            hf_model = _VIDEO_MODELS.get("seedance",
                                          "bytedance/seedance/2-0")
            task = "text-to-video"
    elif model in ("minimax",):
        hf_model = _VIDEO_MODELS.get("minimax",
                                      "minimax-ai/video-01-director/general")
        task = "image-to-video" if has_image else "text-to-video"
    else:
        # Fallback — try to find in _VIDEO_MODELS
        hf_model = _VIDEO_MODELS.get(model, model)
        task = "image-to-video" if has_image else "text-to-video"

    width, height = _aspect_to_dimensions(aspect_ratio)

    payload = {
        "task": task,
        "model": hf_model,
        "prompt": prompt,
        "width": width,
        "height": height,
    }

    # Duration — pass as integer seconds
    try:
        payload["duration"] = int(duration)
    except (ValueError, TypeError):
        payload["duration"] = 5

    # Attach image for image-to-video
    if image_url:
        payload["image_urls"] = [image_url]
    elif image_path:
        # Upload local file as base64 data URI
        import mimetypes
        mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
        try:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            payload["image_urls"] = [f"data:{mime_type};base64,{b64}"]
        except (IOError, OSError) as exc:
            print_status(f"Could not read image file: {exc}", "!!")
            # Fall back to text-to-video
            payload["task"] = "text-to-video"

    response = requests.post(
        _GENERATIONS_URL,
        headers=_headers(),
        json=payload,
        timeout=90,
    )

    if response.status_code not in (200, 201, 202):
        raise Exception(
            f"Higgsfield video submit error {response.status_code}: "
            f"{response.text[:500]}"
        )

    result = response.json()
    generation_id = result.get("id") or result.get("generation_id")
    if not generation_id:
        raise Exception(f"No generation ID in Higgsfield video response: {result}")

    return generation_id


def poll_video(generation_id, max_wait=600, poll_interval=10, quiet=False):
    """
    Poll a Higgsfield video generation until completion.

    Args:
        generation_id: The generation ID from submit_video
        max_wait: Maximum seconds to wait (default 600 = 10 min)
        poll_interval: Seconds between checks
        quiet: Suppress status messages

    Returns:
        dict: GenerationResult with status, result_url, task_id
    """
    start_time = time.time()
    url = f"{_GENERATIONS_URL}/{generation_id}"

    while time.time() - start_time < max_wait:
        response = requests.get(url, headers=_headers(), timeout=30)

        if response.status_code != 200:
            elapsed = int(time.time() - start_time)
            if not quiet:
                print_status(
                    f"Higgsfield video poll returned {response.status_code}, "
                    f"retrying... ({elapsed}s)", "!!"
                )
            time.sleep(poll_interval)
            continue

        result = response.json()
        status = result.get("status", "").lower()

        if status == "completed":
            # Extract video URL — Higgsfield returns videos in a `videos` array
            videos = result.get("videos", [])
            if videos:
                video_url = videos[0].get("url", "")
            else:
                # Fallback: check `result_url` or `url` fields
                video_url = (result.get("result_url", "")
                             or result.get("url", ""))

            if not video_url:
                raise Exception(
                    f"No video URL in completed Higgsfield response: {result}"
                )

            if not quiet:
                print_status("Higgsfield video generation completed!", "OK")

            return {
                "status": "success",
                "result_url": video_url,
                "task_id": generation_id,
            }

        elif status in ("failed", "error", "nsfw"):
            error_msg = result.get("error",
                                    result.get("message",
                                               f"Video generation {status}"))
            raise Exception(f"Higgsfield video {status}: {error_msg}")

        # Still processing (queued, in_progress)
        elapsed = int(time.time() - start_time)
        if not quiet:
            print_status(
                f"Higgsfield video status: {status} ({elapsed}s elapsed)", ".."
            )
        time.sleep(poll_interval)

    raise Exception(
        f"Higgsfield video timeout after {max_wait}s for generation: "
        f"{generation_id}"
    )


def poll_video_tasks_parallel(generation_ids, max_wait=600, poll_interval=10):
    """
    Poll multiple Higgsfield video generations concurrently.

    Args:
        generation_ids: List of generation ID strings
        max_wait: Max seconds to wait per generation
        poll_interval: Seconds between checks

    Returns:
        dict: generation_id -> GenerationResult
    """
    if not generation_ids:
        return {}

    total = len(generation_ids)
    completed_list = []
    results = {}

    def _poll_one(gen_id):
        result = poll_video(gen_id, max_wait=max_wait,
                            poll_interval=poll_interval, quiet=True)
        completed_list.append(gen_id)
        short = gen_id[:12]
        print_status(
            f"Higgsfield video {short}... done "
            f"({len(completed_list)}/{total})", "OK"
        )
        return result

    max_workers = min(total, 10)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_poll_one, gid): gid
            for gid in generation_ids
        }
        for future in as_completed(futures):
            gid = futures[future]
            try:
                results[gid] = future.result()
            except Exception as e:
                completed_list.append(gid)
                short = gid[:12]
                print_status(
                    f"Higgsfield video {short}... failed: {e}", "XX"
                )
                results[gid] = {
                    "status": "error",
                    "task_id": gid,
                    "error": str(e),
                }

    return results


# ---------------------------------------------------------------------------
# Talking Head — Speak v2 (Platform API) + talking_photo (legacy Diffusion)
# ---------------------------------------------------------------------------

def _platform_headers():
    """Auth headers for Higgsfield Platform API (same Key ID:SECRET format)."""
    return _headers()  # Same auth mechanism


def submit_speak_v2(image_url, audio_url, prompt="",
                    quality="high", duration=15):
    """Submit a Speak v2 (talking head) job to Higgsfield Platform API.

    Speak v2 generates a realistic talking-head video from a still image
    and a speech audio file.

    Parameters
    ----------
    image_url : str
        Hosted URL of the headshot/character image.
    audio_url : str
        Hosted URL of the speech audio (WAV/MP3).
    prompt : str, optional
        Motion/expression guidance (e.g., "natural gestures").
    quality : str
        ``"high"`` or ``"standard"`` (default ``"high"``).
    duration : int
        Approximate duration in seconds (default 15).

    Returns
    -------
    str
        ``request_id`` for polling via ``poll_speak_v2``.

    Raises
    ------
    Exception
        If the submit request fails.
    """
    payload = {
        "params": {
            "input_image": {"type": "image_url", "image_url": image_url},
            "input_audio": {"type": "audio_url", "audio_url": audio_url},
            "prompt": prompt or "natural conversational gestures",
            "quality": quality,
            "duration": duration,
        }
    }

    resp = requests.post(
        f"{_PLATFORM_BASE}/v1/speak/higgsfield",
        headers=_platform_headers(),
        json=payload,
        timeout=90,
    )

    if resp.status_code not in (200, 201, 202):
        raise Exception(
            f"Higgsfield Speak v2 submit error {resp.status_code}: "
            f"{resp.text[:500]}"
        )

    result = resp.json()
    request_id = result.get("request_id")
    if not request_id:
        raise Exception(
            f"No request ID in Higgsfield Speak v2 response: {result}"
        )

    logger.info("Higgsfield Speak v2 submitted: %s", request_id)
    return request_id


def poll_speak_v2(request_id, max_wait=600, poll_interval=10, quiet=False):
    """Poll a Higgsfield Speak v2 request until completion.

    Parameters
    ----------
    request_id : str
        The request ID from ``submit_speak_v2``.
    max_wait : int
        Maximum seconds to wait (default 600 = 10 min).
    poll_interval : int
        Seconds between status checks.
    quiet : bool
        Suppress console status messages.

    Returns
    -------
    dict
        ``{"status": "success", "result_url": str, "task_id": str}``

    Raises
    ------
    Exception
        If the job fails or times out.
    """
    start_time = time.time()
    url = f"{_PLATFORM_BASE}/requests/{request_id}/status"

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                url, headers=_platform_headers(), timeout=30
            )
        except requests.RequestException:
            time.sleep(poll_interval)
            continue

        if response.status_code != 200:
            elapsed = int(time.time() - start_time)
            if not quiet:
                print_status(
                    f"Speak v2 poll returned {response.status_code}, "
                    f"retrying… ({elapsed}s)", "!!"
                )
            time.sleep(poll_interval)
            continue

        result = response.json()
        status = result.get("status", "").upper()

        if status == "COMPLETED":
            output = result.get("output", {})
            video_url = (
                output.get("video", {}).get("url", "")
                or output.get("url", "")
            )
            if not video_url:
                raise Exception(
                    f"No video URL in completed Speak v2 response: {result}"
                )
            if not quiet:
                print_status("Higgsfield Speak v2 completed!", "OK")
            return {
                "status": "success",
                "result_url": video_url,
                "task_id": request_id,
            }

        elif status in ("FAILED", "CANCELED", "NSFW"):
            error_msg = result.get(
                "error", result.get("message", f"Speak v2 {status}")
            )
            raise Exception(f"Higgsfield Speak v2 {status}: {error_msg}")

        elapsed = int(time.time() - start_time)
        if not quiet:
            print_status(
                f"Speak v2 status: {status} ({elapsed}s elapsed)", ".."
            )
        time.sleep(poll_interval)

    raise Exception(
        f"Higgsfield Speak v2 timeout after {max_wait}s for: {request_id}"
    )


def submit_talking_photo(image_url, audio_url, prompt=""):
    """Submit a talking_photo job to Higgsfield (legacy Diffusion API).

    This is the fallback talking head method that uses the standard
    ``/v1/generations`` endpoint.

    Parameters
    ----------
    image_url : str
        Hosted URL of the headshot/character image.
    audio_url : str
        Hosted URL of the speech audio.
    prompt : str, optional
        Motion guidance text.

    Returns
    -------
    str
        ``generation_id`` for polling via ``poll_talking_photo``.
    """
    payload = {
        "type": "talking_photo",
        "inputs": {
            "image_url": image_url,
            "audio_url": audio_url,
            "prompt": prompt or "natural head movement",
        },
    }

    response = requests.post(
        _GENERATIONS_URL,
        headers=_headers(),
        json=payload,
        timeout=60,
    )

    if response.status_code not in (200, 201, 202):
        raise Exception(
            f"Higgsfield talking_photo submit error "
            f"{response.status_code}: {response.text[:500]}"
        )

    result = response.json()
    generation_id = result.get("id") or result.get("generation_id")
    if not generation_id:
        raise Exception(
            f"No generation ID in Higgsfield talking_photo response: {result}"
        )

    logger.info("Higgsfield talking_photo submitted: %s", generation_id)
    return generation_id


def poll_talking_photo(generation_id, max_wait=300, poll_interval=5,
                       quiet=False):
    """Poll a Higgsfield talking_photo generation until completion.

    Reuses ``poll_video`` since the response format is identical.

    Returns
    -------
    dict
        ``{"status": "success", "result_url": str, "task_id": str}``
    """
    return poll_video(
        generation_id,
        max_wait=max_wait,
        poll_interval=poll_interval,
        quiet=quiet,
    )
