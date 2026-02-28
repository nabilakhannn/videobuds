"""
Google AI Studio provider — image generation (Nano Banana / Nano Banana Pro)
and video generation (Veo 3.1) via the Gemini API.

Image generation is SYNCHRONOUS (response contains base64 image data).
Video generation is ASYNCHRONOUS (returns operation ID, needs polling).

Generated assets are uploaded to Kie.ai hosting to get URLs for Airtable.
"""

import base64
import json
import os
import shutil
import time
import tempfile
import uuid
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .. import config
from ..utils import print_status
from ..upload_to_kie import upload_reference

# Provider sync flags
image_IS_SYNC = True      # Images return immediately (no polling)
video_IS_SYNC = False     # Videos need polling

# --- Google model IDs ---
_IMAGE_MODELS = {
    "nano-banana": "gemini-2.5-flash-image",
    "nano-banana-pro": "gemini-3-pro-image-preview",
}

_VIDEO_MODELS = {
    "veo-3.1": "veo-3.1-generate-preview",
}

# --- API URLs ---
_GENERATE_CONTENT_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_PREDICT_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:predictLongRunning"
_POLL_URL = "https://generativelanguage.googleapis.com/v1beta/{operation_name}"


def _headers():
    """Auth headers for Google AI Studio."""
    return {
        "x-goog-api-key": config.GOOGLE_API_KEY,
        "Content-Type": "application/json",
    }


def _encode_image_base64(file_path):
    """Read a local image file and return (base64_data, mime_type)."""
    path = Path(file_path)
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(path.suffix.lower(), "image/png")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, mime_type


def _upload_base64_to_host(base64_data, filename="generated.png"):
    """
    Decode base64 image data. If Kie.ai hosting is available, upload there.
    Otherwise, save locally to references/outputs/ and return the local path.
    """
    # Try Kie.ai upload if API key is configured
    if config.KIE_API_KEY:
        tmp_path = os.path.join(tempfile.gettempdir(), filename)
        with open(tmp_path, "wb") as f:
            f.write(base64.b64decode(base64_data))
        try:
            return upload_reference(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Fallback: save locally to references/outputs/ and return a web URL
    output_dir = os.path.join(config.PROJECT_ROOT, "references", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    local_path = os.path.join(output_dir, unique_name)
    with open(local_path, "wb") as f:
        f.write(base64.b64decode(base64_data))
    print_status(f"Saved locally (no Kie key): {local_path}", "OK")
    # Return a Flask-routable URL (served by /api/outputs/<filename>)
    return f"/api/outputs/{unique_name}"


# ---------------------------------------------------------------------------
# Image Generation (Synchronous)
# ---------------------------------------------------------------------------

def submit_image(prompt, reference_paths=None, aspect_ratio="9:16",
                 resolution="1K", model="nano-banana-pro", **kwargs):
    """
    Generate an image synchronously via Google AI Studio.

    Unlike Kie AI, this returns the final GenerationResult directly
    (no task_id, no polling needed).

    Args:
        prompt: Image generation prompt
        reference_paths: List of LOCAL file paths (base64-encoded inline)
        aspect_ratio: Standard ratio string (e.g., "9:16")
        resolution: "1K", "2K", or "4K"
        model: "nano-banana" or "nano-banana-pro"

    Returns:
        dict: GenerationResult with status, result_url, task_id=None
    """
    google_model = _IMAGE_MODELS.get(model)
    if not google_model:
        raise ValueError(f"Google doesn't support image model: '{model}'")

    # Build parts: text prompt + optional reference images as inline base64
    parts = [{"text": prompt}]
    if reference_paths:
        for ref_path in reference_paths:
            b64_data, mime_type = _encode_image_base64(ref_path)
            parts.append({
                "inline_data": {"mime_type": mime_type, "data": b64_data}
            })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }

    url = _GENERATE_CONTENT_URL.format(model=google_model)
    response = requests.post(url, headers=_headers(), json=payload, timeout=120)

    if response.status_code != 200:
        raise Exception(f"Google AI error {response.status_code}: {response.text[:500]}")

    result = response.json()

    # Extract base64 image from response candidates
    candidates = result.get("candidates", [])
    if not candidates:
        raise Exception(f"No candidates in Google AI response: {result}")

    resp_parts = candidates[0].get("content", {}).get("parts", [])
    for part in resp_parts:
        if "inlineData" in part:
            b64_data = part["inlineData"]["data"]
            mime = part["inlineData"].get("mimeType", "image/png")
            ext = ".png" if "png" in mime else ".jpg"
            hosted_url = _upload_base64_to_host(b64_data, f"google_gen{ext}")
            return {
                "status": "success",
                "result_url": hosted_url,
                "task_id": None,
            }

    raise Exception(f"No image data in Google AI response parts: {[list(p.keys()) for p in resp_parts]}")


def poll_image(task_id, **kwargs):
    """No-op — Google image generation is synchronous."""
    raise NotImplementedError("Google image generation is synchronous, no polling needed")


# ---------------------------------------------------------------------------
# Video Generation (Asynchronous — Veo 3.1)
# ---------------------------------------------------------------------------

def submit_video(prompt, image_url=None, model="veo-3.1",
                 duration="8", aspect_ratio="9:16", resolution="720p",
                 image_path=None, **kwargs):
    """
    Submit a video generation task to Google Veo 3.1.

    Args:
        prompt: Video prompt text
        image_url: URL of source image (will be downloaded + base64-encoded)
        model: "veo-3.1"
        duration: "4", "6", or "8" seconds
        aspect_ratio: "9:16" or "16:9"
        resolution: "720p", "1080p", or "4k"
        image_path: Local path to source image (alternative to image_url)

    Returns:
        str: operation_name for polling
    """
    google_model = _VIDEO_MODELS.get(model)
    if not google_model:
        raise ValueError(f"Google doesn't support video model: '{model}'")

    # Build instance
    instance = {"prompt": prompt}

    # Attach source image for image-to-video
    if image_path:
        b64_data, mime_type = _encode_image_base64(image_path)
        instance["image"] = {"bytesBase64Encoded": b64_data, "mimeType": mime_type}
    elif image_url:
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()
        b64_data = base64.b64encode(img_response.content).decode("utf-8")
        content_type = img_response.headers.get("content-type", "image/png")
        instance["image"] = {"bytesBase64Encoded": b64_data, "mimeType": content_type}

    # Veo 3.1 only accepts 4, 6, or 8 seconds — snap to nearest valid value
    valid_durations = [4, 6, 8]
    dur = int(duration)
    dur = min(valid_durations, key=lambda v: abs(v - dur))

    payload = {
        "instances": [instance],
        "parameters": {
            "aspectRatio": aspect_ratio,
            "durationSeconds": dur,
            "sampleCount": 1,
            "personGeneration": "allow_adult",
        },
    }

    url = _PREDICT_URL.format(model=google_model)
    response = requests.post(url, headers=_headers(), json=payload, timeout=120)

    if response.status_code != 200:
        raise Exception(f"Google Veo error {response.status_code}: {response.text[:500]}")

    result = response.json()
    operation_name = result.get("name")
    if not operation_name:
        raise Exception(f"No operation name in Veo response: {result}")

    return operation_name


def _dump_debug_response(operation_name, result):
    """Write the full Veo response to a debug file for troubleshooting."""
    try:
        debug_dir = os.path.join(config.PROJECT_ROOT, "references", "outputs")
        os.makedirs(debug_dir, exist_ok=True)
        short_id = operation_name.split("/")[-1][:12] if "/" in operation_name else "unknown"
        debug_path = os.path.join(debug_dir, f"veo_debug_{short_id}.json")
        with open(debug_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print_status(f"Debug response saved to: {debug_path}", "..")
    except Exception:
        pass  # Never fail on debug logging


def poll_video(operation_name, max_wait=600, poll_interval=10, quiet=False):
    """
    Poll a Google Veo operation until completion.
    Downloads the result video and uploads to Kie.ai for hosting.

    Args:
        operation_name: The operation name from submit_video
        max_wait: Maximum seconds to wait
        poll_interval: Seconds between checks
        quiet: Suppress status messages

    Returns:
        dict: GenerationResult with status, result_url, task_id
    """
    start_time = time.time()

    while time.time() - start_time < max_wait:
        url = _POLL_URL.format(operation_name=operation_name)
        response = requests.get(url, headers=_headers(), timeout=30)

        if response.status_code != 200:
            elapsed = int(time.time() - start_time)
            if not quiet:
                print_status(f"Poll returned {response.status_code}, retrying... ({elapsed}s)", "!!")
            time.sleep(poll_interval)
            continue

        result = response.json()

        if result.get("done"):
            # Debug: dump the full response for troubleshooting
            if not quiet:
                _dump_debug_response(operation_name, result)

            # Check for error
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                raise Exception(f"Veo task failed: {error_msg}")

            # Check for RAI (Responsible AI) filtering
            rai_reason = (
                result.get("response", {})
                .get("raiMediaFilteredReasons", [])
            )
            if rai_reason:
                raise Exception(
                    f"Veo safety filter blocked this video. "
                    f"Reasons: {rai_reason}. "
                    f"Try a different prompt or add personGeneration='allow_adult'."
                )

            # Extract video URI — try multiple response paths because
            # the API structure can vary between versions / edge cases.
            resp_body = result.get("response", {})

            # Also check 'result' key (some LRO APIs use this instead)
            if not resp_body:
                resp_body = result.get("result", {})

            # Path 1 (REST/predictLongRunning — official docs):
            #   response.generateVideoResponse.generatedSamples[0].video.uri
            samples = (
                resp_body
                .get("generateVideoResponse", {})
                .get("generatedSamples", [])
            )

            # Path 2 (SDK-style / newer camelCase responses):
            #   response.generatedVideos[0].video.uri
            if not samples:
                samples = resp_body.get("generatedVideos", [])

            # Path 3 (snake_case variant from some API versions):
            #   response.generated_videos[0].video.uri
            if not samples:
                samples = resp_body.get("generated_videos", [])

            # Path 4: response directly contains generatedSamples
            if not samples:
                samples = resp_body.get("generatedSamples", [])

            # Path 5: top-level result (no response wrapper)
            if not samples:
                samples = (
                    result
                    .get("generateVideoResponse", {})
                    .get("generatedSamples", [])
                )

            if not samples:
                # Provide a helpful error with the actual response keys
                resp_keys = list(resp_body.keys()) if resp_body else []
                top_keys = list(result.keys())
                raise Exception(
                    f"No generated video in Veo response. "
                    f"Top-level keys: {top_keys}. "
                    f"Response keys: {resp_keys}. "
                    f"This usually means Veo's safety filter blocked the "
                    f"generated content. Try a different prompt or subject. "
                    f"Full response (truncated): {str(result)[:800]}"
                )

            # The video URI can be in sample.video.uri or sample.video.name
            sample = samples[0]
            video_obj = sample.get("video", sample)  # some paths nest under .video
            video_uri = (
                video_obj.get("uri")
                or video_obj.get("url")
                or video_obj.get("name")
            )
            if not video_uri:
                raise Exception(
                    f"No video URI in Veo sample. Sample keys: {list(sample.keys())}. "
                    f"Sample (truncated): {str(sample)[:500]}"
                )

            # Download video (requires API key auth) and host
            if not quiet:
                print_status(f"Video URI obtained, downloading...", "..")
            hosted_url = _download_and_host_video(video_uri)

            if not quiet:
                print_status("Veo task completed successfully!", "OK")

            return {
                "status": "success",
                "result_url": hosted_url,
                "task_id": operation_name,
            }

        # Still processing
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        if not quiet:
            print_status(f"Veo status: processing ({mins}m {secs}s elapsed)", "..")
        time.sleep(poll_interval)

    raise Exception(f"Veo timeout after {max_wait}s for operation: {operation_name}")


def _faststart(src_path):
    """Move the moov atom to the beginning of the MP4 file for progressive
    web playback.  Uses ``ffmpeg -movflags +faststart`` if available;
    silently returns the original path if ffmpeg is missing or fails."""
    import subprocess

    dst_path = src_path + ".tmp.mp4"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-i", src_path,
                "-c", "copy",
                "-movflags", "+faststart",
                dst_path,
            ],
            check=True,
            timeout=30,
            capture_output=True,
        )
        # Replace original with faststarted version
        os.replace(dst_path, src_path)
        print_status("Applied faststart (moov atom moved to front)", "OK")
    except FileNotFoundError:
        print_status("ffmpeg not found — skipping faststart", "!!")
    except Exception as exc:
        print_status(f"faststart failed ({exc}) — using original", "!!")
        # Clean up partial output
        if os.path.exists(dst_path):
            os.remove(dst_path)

    return src_path


def _download_and_host_video(video_uri):
    """Download a Veo video and host it (Kie.ai if available, else local)."""
    tmp_path = os.path.join(tempfile.gettempdir(), f"veo_video_{uuid.uuid4().hex[:8]}.mp4")

    response = requests.get(video_uri, headers=_headers(), stream=True, timeout=120)
    response.raise_for_status()

    with open(tmp_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    # Move moov atom to the front for smooth browser playback
    _faststart(tmp_path)

    # Try Kie.ai upload if API key is configured
    if config.KIE_API_KEY:
        try:
            return upload_reference(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Fallback: save locally to references/outputs/ and return a web URL
    output_dir = os.path.join(config.PROJECT_ROOT, "references", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    local_name = f"{uuid.uuid4().hex[:8]}_veo_video.mp4"
    local_path = os.path.join(output_dir, local_name)
    os.rename(tmp_path, local_path)
    print_status(f"Saved video locally (no Kie key): {local_path}", "OK")
    # Return a Flask-routable URL (served by /api/outputs/<filename>)
    return f"/api/outputs/{local_name}"


def poll_tasks_parallel(operation_names, max_wait=600, poll_interval=10):
    """
    Poll multiple Google Veo operations concurrently.

    Args:
        operation_names: List of operation name strings
        max_wait: Max seconds to wait per operation
        poll_interval: Seconds between checks

    Returns:
        dict: operation_name → GenerationResult
    """
    if not operation_names:
        return {}

    total = len(operation_names)
    completed = []
    results = {}

    def _poll_one(op_name):
        result = poll_video(op_name, max_wait=max_wait,
                            poll_interval=poll_interval, quiet=True)
        completed.append(op_name)
        short = op_name.split("/")[-1][:12] if "/" in op_name else op_name[:12]
        print_status(f"Veo {short}... done ({len(completed)}/{total})", "OK")
        return result

    max_workers = min(total, 20)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_poll_one, name): name
            for name in operation_names
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                completed.append(name)
                short = name.split("/")[-1][:12] if "/" in name else name[:12]
                print_status(f"Veo {short}... failed: {e}", "XX")
                results[name] = {
                    "status": "error",
                    "task_id": name,
                    "error": str(e),
                }

    return results
