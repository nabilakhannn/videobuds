"""
Gemini TTS provider — text-to-speech using Google's Gemini 2.5 Flash Preview.

Converts text → WAV audio (PCM 16-bit, 24kHz mono).
Uses the free Gemini API — same GOOGLE_API_KEY as image generation.

Security: Validates input length, voice whitelist.
"""

import base64
import io
import logging
import struct
import time

import requests

from .. import config

logger = logging.getLogger(__name__)

# ── Available voices ──────────────────────────────────────────────────────
AVAILABLE_VOICES = [
    "Kore", "Charon", "Fenrir", "Aoede", "Puck",
    "Leda", "Orus", "Zephyr",
]
DEFAULT_VOICE = "Kore"

# ── API config ────────────────────────────────────────────────────────────
_TTS_MODEL = "gemini-2.5-flash-preview-tts"
_TTS_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{_TTS_MODEL}:generateContent"
)

# Maximum text length (characters) — Gemini TTS works best under 5K
MAX_TEXT_LENGTH = 8_000


def generate_speech(text, api_key=None, voice_name=None, max_retries=3):
    """Generate speech audio from text using Gemini TTS.

    Parameters
    ----------
    text : str
        The text to convert to speech (max ~8,000 chars).
    api_key : str, optional
        Google API key. Falls back to ``config.GOOGLE_API_KEY``.
    voice_name : str, optional
        Voice to use (default: "Kore"). See ``AVAILABLE_VOICES``.
    max_retries : int
        Number of retry attempts on failure.

    Returns
    -------
    bytes
        WAV file bytes (PCM 16-bit, 24kHz mono).

    Raises
    ------
    ValueError
        If text is empty or exceeds length limit.
    RuntimeError
        If speech generation fails after all retries.
    """
    # ── Input validation ──
    if not text or not text.strip():
        raise ValueError("Text cannot be empty for TTS")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(
            f"Text too long for TTS ({len(text):,} chars). "
            f"Maximum is {MAX_TEXT_LENGTH:,} characters."
        )

    api_key = api_key or config.GOOGLE_API_KEY
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured for TTS")

    voice_name = voice_name or DEFAULT_VOICE
    if voice_name not in AVAILABLE_VOICES:
        logger.warning(
            "Unknown TTS voice '%s', falling back to '%s'",
            voice_name, DEFAULT_VOICE,
        )
        voice_name = DEFAULT_VOICE

    url = f"{_TTS_URL}?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice_name}
                }
            },
        },
    }

    last_err = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, timeout=180)
            if resp.status_code >= 500:
                raise RuntimeError(f"Gemini TTS server error {resp.status_code}")
            resp.raise_for_status()

            result = resp.json()
            parts = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [])
            )
            for part in parts:
                inline_data = part.get("inlineData")
                if inline_data:
                    raw_pcm = base64.b64decode(inline_data["data"])
                    wav_bytes = _pcm_to_wav(raw_pcm)
                    duration = len(raw_pcm) / (24000 * 1 * 2)
                    logger.info(
                        "Gemini TTS: %d bytes, %.1fs duration, voice=%s",
                        len(wav_bytes), duration, voice_name,
                    )
                    return wav_bytes

            raise RuntimeError("No audio data in Gemini TTS response")

        except Exception as exc:
            last_err = exc
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(
                    "Gemini TTS retry %d/%d: %s",
                    attempt + 1, max_retries, exc,
                )
                time.sleep(wait)

    raise RuntimeError(
        f"Gemini TTS failed after {max_retries} attempts: {last_err}"
    ) from last_err


def _pcm_to_wav(raw_pcm, sample_rate=24000, num_channels=1, sample_width=2):
    """Convert raw PCM bytes to WAV format.

    Parameters
    ----------
    raw_pcm : bytes
        Raw PCM audio data (16-bit).
    sample_rate : int
        Sample rate in Hz (default 24000).
    num_channels : int
        Number of audio channels (default 1 = mono).
    sample_width : int
        Bytes per sample (default 2 = 16-bit).

    Returns
    -------
    bytes
        Complete WAV file bytes.
    """
    buf = io.BytesIO()
    data_size = len(raw_pcm)
    # RIFF header
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    # fmt chunk
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))
    buf.write(struct.pack("<H", 1))  # PCM format
    buf.write(struct.pack("<H", num_channels))
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", sample_rate * num_channels * sample_width))
    buf.write(struct.pack("<H", num_channels * sample_width))
    buf.write(struct.pack("<H", sample_width * 8))
    # data chunk
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(raw_pcm)
    return buf.getvalue()
