"""
D-ID AI provider — talking-head video generation.

Uses the D-ID Talks API:
  POST /talks  → create a lip-sync video from image + audio
  GET  /talks/{id} → poll until done

Free trial: 20 credits at https://studio.d-id.com
API key format: base64-encoded "username:password" (shown in D-ID dashboard).
"""

import base64
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

_API_BASE = "https://api.d-id.com"
_TALKS_URL = f"{_API_BASE}/talks"


def _headers():
    """Build Authorization header from DID_API_KEY env var.

    D-ID expects:  Authorization: Basic <base64("key:")>
    The key can be used directly as the username with an empty password.
    """
    api_key = os.getenv("DID_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "DID_API_KEY is not set. "
            "Sign up at https://studio.d-id.com and add the key to your .env file."
        )
    # D-ID accepts the raw API key as Basic auth username with empty password
    encoded = base64.b64encode(f"{api_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def submit_talk(image_url: str, audio_url: str) -> str:
    """Submit a talking-head job to D-ID.

    Args:
        image_url: Publicly accessible URL of the headshot image.
        audio_url: Publicly accessible URL of the speech audio (WAV/MP3).

    Returns:
        talk_id: String ID to pass to poll_talk().

    Raises:
        RuntimeError: On API error.
    """
    payload = {
        "source_url": image_url,
        "script": {
            "type": "audio",
            "audio_url": audio_url,
        },
        "config": {
            "stitch": True,
        },
    }

    response = requests.post(_TALKS_URL, json=payload, headers=_headers(), timeout=30)
    if not response.ok:
        raise RuntimeError(
            f"D-ID submit error {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    talk_id = data.get("id")
    if not talk_id:
        raise RuntimeError(f"D-ID did not return a talk ID: {data}")

    logger.info("D-ID talk submitted: %s", talk_id)
    return talk_id


def poll_talk(talk_id: str, max_wait: int = 300, poll_interval: int = 5) -> str:
    """Poll D-ID until the talk is done.

    Args:
        talk_id: ID returned by submit_talk().
        max_wait: Maximum seconds to wait (default 300 = 5 minutes).
        poll_interval: Seconds between polls.

    Returns:
        result_url: CDN URL of the generated video.

    Raises:
        RuntimeError: On error or timeout.
    """
    url = f"{_TALKS_URL}/{talk_id}"
    deadline = time.time() + max_wait

    while time.time() < deadline:
        resp = requests.get(url, headers=_headers(), timeout=30)
        if not resp.ok:
            raise RuntimeError(
                f"D-ID poll error {resp.status_code}: {resp.text[:300]}"
            )

        data = resp.json()
        status = data.get("status", "")

        if status == "done":
            result_url = data.get("result_url", "")
            if not result_url:
                raise RuntimeError("D-ID returned 'done' but no result_url.")
            logger.info("D-ID talk done: %s", result_url[:80])
            return result_url

        if status == "error":
            error = data.get("error", {})
            raise RuntimeError(
                f"D-ID generation failed: {error.get('description', 'unknown error')}"
            )

        logger.debug("D-ID status=%s, waiting…", status)
        time.sleep(poll_interval)

    raise RuntimeError(
        f"D-ID timed out after {max_wait}s. Talk ID: {talk_id}"
    )
