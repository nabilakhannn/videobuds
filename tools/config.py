"""
Configuration loader for Creative Content Engine.
Loads API keys from references/.env and provides centralized constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables — try multiple .env locations gracefully
PROJECT_ROOT = Path(__file__).parent.parent
for _env_path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "references" / ".env"):
    try:
        if _env_path.exists():
            load_dotenv(_env_path)
            break
    except (PermissionError, OSError):
        pass

# --- API Keys ---
KIE_API_KEY = os.getenv("KIE_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Higgsfield AI ---
HIGGSFIELD_API_KEY_ID = os.getenv("HIGGSFIELD_API_KEY_ID")
HIGGSFIELD_API_KEY_SECRET = os.getenv("HIGGSFIELD_API_KEY_SECRET")

# --- WaveSpeed AI ---
WAVESPEED_API_KEY = os.getenv("WAVESPEED_API_KEY")
WAVESPEED_API_URL = "https://api.wavespeed.ai/api/v3"

# --- Kie AI Endpoints ---
KIE_FILE_UPLOAD_URL = "https://kieai.redpandaai.co/api/file-stream-upload"
KIE_CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
KIE_STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"

# --- Airtable ---
AIRTABLE_API_URL = "https://api.airtable.com/v0"
AIRTABLE_TABLE_NAME = "Content"

# --- Cost Constants (legacy — use get_cost() for multi-provider) ---
IMAGE_COST = 0.09   # per Nano Banana Pro image (Kie AI)
VIDEO_COST = 0.30   # per Kling/Sora video via Kie AI (approximate)
WAVESPEED_VIDEO_COST = 0.30  # per Kling/Sora video via WaveSpeed (approximate)

# --- Retail costs (shown to regular users) ---
COSTS = {
    # Image models
    ("nano-banana", "google"): 0.04,
    ("nano-banana", "kie"): 0.09,
    ("nano-banana", "higgsfield"): 0.04,
    ("nano-banana-pro", "google"): 0.13,
    ("nano-banana-pro", "kie"): 0.09,
    ("nano-banana-pro", "higgsfield"): 0.13,
    ("gpt-image-1.5", "wavespeed"): 0.07,  # ~$0.04 medium / ~$0.08 high via OpenAI — verify at wavespeed.ai
    # Video models
    ("veo-3.1", "google"): 0.50,
    ("kling-3.0", "kie"): 0.30,
    ("sora-2-pro", "kie"): 0.30,
    ("kling-3.0", "wavespeed"): 0.30,
    ("sora-2", "wavespeed"): 0.30,
    ("sora-2-pro", "wavespeed"): 0.30,
    # Higgsfield video models — credit-based (NOT free)
    # ~3 credits per 720p video; cost depends on plan ($0.007–$0.027/credit)
    ("seedance", "higgsfield"): 0.08,
    ("minimax", "higgsfield"): 0.08,
    # TTS models
    ("gemini-tts", "gemini"): 0.00,  # Gemini free tier
    # Talking head models
    ("speak-v2", "higgsfield"): 0.15,
    ("talking-photo", "higgsfield"): 0.10,
    ("infinitetalk", "wavespeed"): 0.20,
}

# --- Actual costs (what the operator actually pays — shown to admins) ---
ACTUAL_COSTS = {
    # Google AI Studio free tier — unlimited nano-banana
    ("nano-banana", "google"): 0.00,
    ("nano-banana-pro", "google"): 0.00,
    # Higgsfield — unlimited plan
    ("nano-banana", "higgsfield"): 0.00,
    ("nano-banana-pro", "higgsfield"): 0.00,
    # Paid providers
    ("nano-banana", "kie"): 0.09,
    ("nano-banana-pro", "kie"): 0.09,
    ("gpt-image-1.5", "wavespeed"): 0.07,
    ("veo-3.1", "google"): 0.00,
    ("kling-3.0", "kie"): 0.30,
    ("sora-2-pro", "kie"): 0.30,
    ("kling-3.0", "wavespeed"): 0.30,
    ("sora-2", "wavespeed"): 0.30,
    ("sora-2-pro", "wavespeed"): 0.30,
    # Higgsfield video — credit-based, NOT free (~3 credits/720p video)
    # Actual cost depends on plan: Basic $9/1000cr ≈ $0.027/vid,
    # Pro $23/4000cr ≈ $0.017/vid, Ultimate $39/10000cr ≈ $0.012/vid
    ("seedance", "higgsfield"): 0.03,
    ("minimax", "higgsfield"): 0.03,
    # TTS — Gemini free tier
    ("gemini-tts", "gemini"): 0.00,
    # Talking head — actual credit costs
    ("speak-v2", "higgsfield"): 0.05,
    ("talking-photo", "higgsfield"): 0.03,
    ("infinitetalk", "wavespeed"): 0.20,
}

# --- Default Models ---
DEFAULT_IMAGE_MODEL = "nano-banana-pro"
DEFAULT_VIDEO_MODEL = "veo-3.1"

# --- Directories ---
INPUTS_DIR = PROJECT_ROOT / "references" / "inputs"

# --- Video Models (Kie AI) ---
# Both models support image-to-video (using image_urls for the start frame).
# Kling 3.0: image/text-to-video, std/pro quality, 3-15s duration, multi-shot support
# Sora 2 Pro: image-to-video, portrait/landscape, 10s/15s, high quality
VIDEO_MODELS = {
    "kling-3.0": "kling-3.0/video",
    "sora-2-pro": "sora-2-pro-image-to-video",
    "veo-3.1": "veo-3.1-generate-preview",
}

# --- Video Models (WaveSpeed AI) ---
# Same models available through WaveSpeed's infrastructure.
# WaveSpeed uses model ID in the URL path (not request body).
WAVESPEED_VIDEO_MODELS = {
    "kling-3.0": "kwaivgi/kling-v3.0-pro/image-to-video",
    "kling-3.0-std": "kwaivgi/kling-v3.0-std/image-to-video",
    "sora-2": "openai/sora-2/image-to-video",
    "sora-2-pro": "openai/sora-2/image-to-video-pro",
}

# --- Video Models (Higgsfield AI) ---
# Seedance (ByteDance) and Minimax — affordable, good quality.
HIGGSFIELD_VIDEO_MODELS = {
    "seedance": "bytedance/seedance/2-0",
    "seedance-i2v": "bytedance/seedance/v1/pro/image-to-video",
    "minimax": "minimax-ai/video-01-director/general",
}

# --- TTS Models ---
TTS_MODELS = {
    "gemini-tts": "gemini-2.5-flash-preview-tts",
}

# --- Talking Head Models ---
TALKING_HEAD_MODELS = {
    "speak-v2": "higgsfield",       # Higgsfield Platform API
    "talking-photo": "higgsfield",  # Higgsfield Legacy API
    "infinitetalk": "wavespeed",    # WaveSpeed InfiniteTalk
}


def get_cost(model, provider=None):
    """
    Get the cost per generation for a model+provider combination.

    Args:
        model: Model name (e.g., "nano-banana-pro", "veo-3.1")
        provider: Provider name (e.g., "google", "kie"). If None, uses default.

    Returns:
        float: Cost per unit
    """
    if provider is None:
        # Import here to avoid circular imports
        from .providers import IMAGE_PROVIDERS, VIDEO_PROVIDERS
        if model in IMAGE_PROVIDERS:
            provider = IMAGE_PROVIDERS[model]["default"]
        elif model in VIDEO_PROVIDERS:
            provider = VIDEO_PROVIDERS[model]["default"]
        else:
            return 0.0
    return COSTS.get((model, provider), 0.0)


def get_actual_cost(model, provider=None):
    """
    Get the actual cost the operator pays for a model+provider combination.

    Args:
        model: Model name (e.g., "nano-banana", "nano-banana-pro")
        provider: Provider name (e.g., "google", "kie"). If None, uses default.

    Returns:
        float: Actual cost per unit
    """
    if provider is None:
        from .providers import IMAGE_PROVIDERS, VIDEO_PROVIDERS
        if model in IMAGE_PROVIDERS:
            provider = IMAGE_PROVIDERS[model]["default"]
        elif model in VIDEO_PROVIDERS:
            provider = VIDEO_PROVIDERS[model]["default"]
        else:
            return 0.0
    return ACTUAL_COSTS.get((model, provider), COSTS.get((model, provider), 0.0))


def check_credentials():
    """Verify required API keys are set. Returns list of missing keys."""
    required = {
        "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    }
    missing = [name for name, value in required.items() if not value]

    # At least one generation provider must be configured
    if not KIE_API_KEY and not GOOGLE_API_KEY:
        missing.append("KIE_API_KEY or GOOGLE_API_KEY (at least one required)")

    if missing:
        print("Missing API keys:")
        for key in missing:
            print(f"  - {key}")
        print(f"\nAdd them to: {ENV_PATH}")
    return missing


def check_wavespeed_credentials():
    """Verify WaveSpeed API key + Airtable keys are set. Returns list of missing keys."""
    required = {
        "WAVESPEED_API_KEY": WAVESPEED_API_KEY,
        "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        print("Missing API keys:")
        for key in missing:
            print(f"  - {key}")
        print(f"\nAdd them to: {ENV_PATH}")
    return missing
