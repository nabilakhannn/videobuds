"""
Provider registry and routing for multi-provider generation.

Maps models to their default provider and available alternatives.
Providers are selected per-model, with overrides supported.

Usage:
    from tools.providers import get_image_provider, get_video_provider, is_sync

    provider, name = get_image_provider("nano-banana-pro")          # Google (default)
    provider, name = get_image_provider("nano-banana-pro", "kie")   # Kie AI (override)
    provider, name = get_video_provider("veo-3.1")                  # Google (default)
    provider, name = get_video_provider("kling-3.0")                # WaveSpeed (default)
"""

from . import kie, google, wavespeed, higgsfield, tts

# --- Image model registry ---
IMAGE_PROVIDERS = {
    "nano-banana": {
        "default": "google",
        "providers": {"google": google, "kie": kie, "higgsfield": higgsfield},
    },
    "nano-banana-pro": {
        "default": "google",
        "providers": {"google": google, "kie": kie, "higgsfield": higgsfield},
    },
    "gpt-image-1.5": {
        "default": "wavespeed",
        "providers": {"wavespeed": wavespeed},
    },
}

# --- Video model registry ---
VIDEO_PROVIDERS = {
    "kling-3.0": {
        "default": "wavespeed",
        "providers": {"kie": kie, "wavespeed": wavespeed},
    },
    "sora-2": {
        "default": "wavespeed",
        "providers": {"wavespeed": wavespeed},
    },
    "sora-2-pro": {
        "default": "wavespeed",
        "providers": {"kie": kie, "wavespeed": wavespeed},
    },
    "veo-3.1": {
        "default": "google",
        "providers": {"google": google},
    },
    "seedance": {
        "default": "higgsfield",
        "providers": {"higgsfield": higgsfield},
    },
    "minimax": {
        "default": "higgsfield",
        "providers": {"higgsfield": higgsfield},
    },
}


# --- TTS model registry ---
TTS_PROVIDERS = {
    "gemini-tts": {
        "default": "gemini",
        "providers": {"gemini": tts},
    },
}

# --- Talking Head model registry ---
TALKING_HEAD_PROVIDERS = {
    "speak-v2": {
        "default": "higgsfield",
        "providers": {"higgsfield": higgsfield},
    },
    "talking-photo": {
        "default": "higgsfield",
        "providers": {"higgsfield": higgsfield},
    },
    "infinitetalk": {
        "default": "wavespeed",
        "providers": {"wavespeed": wavespeed},
    },
}


def get_tts_provider(model="gemini-tts", provider_override=None):
    """
    Get the provider module for a TTS model.

    Args:
        model: TTS model name (e.g., "gemini-tts")
        provider_override: Force a specific provider

    Returns:
        tuple: (provider_module, provider_name)
    """
    model_config = TTS_PROVIDERS.get(model)
    if not model_config:
        raise ValueError(f"Unknown TTS model: '{model}'. Available: {list(TTS_PROVIDERS.keys())}")

    provider_name = provider_override or model_config["default"]
    provider = model_config["providers"].get(provider_name)
    if not provider:
        available = list(model_config["providers"].keys())
        raise ValueError(f"Provider '{provider_name}' not available for '{model}'. Available: {available}")

    return provider, provider_name


def get_talking_head_provider(model="speak-v2", provider_override=None):
    """
    Get the provider module for a talking head model.

    Args:
        model: Talking head model name (e.g., "speak-v2", "infinitetalk")
        provider_override: Force a specific provider

    Returns:
        tuple: (provider_module, provider_name)
    """
    model_config = TALKING_HEAD_PROVIDERS.get(model)
    if not model_config:
        raise ValueError(f"Unknown talking head model: '{model}'. Available: {list(TALKING_HEAD_PROVIDERS.keys())}")

    provider_name = provider_override or model_config["default"]
    provider = model_config["providers"].get(provider_name)
    if not provider:
        available = list(model_config["providers"].keys())
        raise ValueError(f"Provider '{provider_name}' not available for '{model}'. Available: {available}")

    return provider, provider_name


def get_image_provider(model="nano-banana-pro", provider_override=None):
    """
    Get the provider module for an image model.

    Args:
        model: Image model name (e.g., "nano-banana-pro")
        provider_override: Force a specific provider (e.g., "kie")

    Returns:
        tuple: (provider_module, provider_name)
    """
    model_config = IMAGE_PROVIDERS.get(model)
    if not model_config:
        raise ValueError(f"Unknown image model: '{model}'. Available: {list(IMAGE_PROVIDERS.keys())}")

    provider_name = provider_override or model_config["default"]
    provider = model_config["providers"].get(provider_name)
    if not provider:
        available = list(model_config["providers"].keys())
        raise ValueError(f"Provider '{provider_name}' not available for '{model}'. Available: {available}")

    return provider, provider_name


def get_video_provider(model="veo-3.1", provider_override=None):
    """
    Get the provider module for a video model.

    Args:
        model: Video model name (e.g., "veo-3.1", "kling-3.0")
        provider_override: Force a specific provider

    Returns:
        tuple: (provider_module, provider_name)
    """
    model_config = VIDEO_PROVIDERS.get(model)
    if not model_config:
        raise ValueError(f"Unknown video model: '{model}'. Available: {list(VIDEO_PROVIDERS.keys())}")

    provider_name = provider_override or model_config["default"]
    provider = model_config["providers"].get(provider_name)
    if not provider:
        available = list(model_config["providers"].keys())
        raise ValueError(f"Provider '{provider_name}' not available for '{model}'. Available: {available}")

    return provider, provider_name


def is_sync(provider_module, generation_type):
    """
    Check if a provider's generation is synchronous (no polling needed).

    Args:
        provider_module: The provider module (e.g., google, kie)
        generation_type: "image" or "video"

    Returns:
        bool: True if synchronous (result returned immediately)
    """
    return getattr(provider_module, f"{generation_type}_IS_SYNC", False)
