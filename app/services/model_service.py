"""
Unified model catalog for VideoBuds.

Provides structured model information — display names, types, providers,
pricing, free tier flags, and capabilities — consumed by templates
(model picker component) and generation routes.
"""

from tools.config import COSTS, ACTUAL_COSTS
from tools.providers import IMAGE_PROVIDERS, VIDEO_PROVIDERS


# ── Model catalog ────────────────────────────────────────────────────
# Each entry describes a single model (not a provider).
# "providers" lists every provider that can run this model,
# with per-provider retail price and free-tier flag.

MODEL_CATALOG = {
    # ── Image models ──────────────────────────────────────────────────
    "nano-banana": {
        "display_name": "Nano Banana",
        "type": "image",
        "description": "Fast, affordable image generation. Great for drafts and iteration.",
        "icon": "🍌",
        "default_provider": "google",
        "providers": {
            "google": {
                "label": "Google AI Studio",
                "retail": COSTS.get(("nano-banana", "google"), 0.04),
                "actual": ACTUAL_COSTS.get(("nano-banana", "google"), 0.00),
                "free_tier": ACTUAL_COSTS.get(("nano-banana", "google"), 0.00) == 0.00,
                "sync": True,
            },
            "higgsfield": {
                "label": "Higgsfield",
                "retail": COSTS.get(("nano-banana", "higgsfield"), 0.04),
                "actual": ACTUAL_COSTS.get(("nano-banana", "higgsfield"), 0.00),
                "free_tier": ACTUAL_COSTS.get(("nano-banana", "higgsfield"), 0.00) == 0.00,
                "sync": False,
            },
            "kie": {
                "label": "Kie AI",
                "retail": COSTS.get(("nano-banana", "kie"), 0.09),
                "actual": ACTUAL_COSTS.get(("nano-banana", "kie"), 0.09),
                "free_tier": False,
                "sync": False,
            },
        },
    },
    "nano-banana-pro": {
        "display_name": "Nano Banana Pro",
        "type": "image",
        "description": "Higher quality image generation with better detail and consistency.",
        "icon": "🍌✨",
        "default_provider": "google",
        "providers": {
            "google": {
                "label": "Google AI Studio",
                "retail": COSTS.get(("nano-banana-pro", "google"), 0.13),
                "actual": ACTUAL_COSTS.get(("nano-banana-pro", "google"), 0.00),
                "free_tier": ACTUAL_COSTS.get(("nano-banana-pro", "google"), 0.00) == 0.00,
                "sync": True,
            },
            "higgsfield": {
                "label": "Higgsfield",
                "retail": COSTS.get(("nano-banana-pro", "higgsfield"), 0.13),
                "actual": ACTUAL_COSTS.get(("nano-banana-pro", "higgsfield"), 0.00),
                "free_tier": ACTUAL_COSTS.get(("nano-banana-pro", "higgsfield"), 0.00) == 0.00,
                "sync": False,
            },
            "kie": {
                "label": "Kie AI",
                "retail": COSTS.get(("nano-banana-pro", "kie"), 0.09),
                "actual": ACTUAL_COSTS.get(("nano-banana-pro", "kie"), 0.09),
                "free_tier": False,
                "sync": False,
            },
        },
    },
    "gpt-image-1.5": {
        "display_name": "GPT Image 1.5",
        "type": "image",
        "description": "OpenAI-powered image editing and generation via WaveSpeed.",
        "icon": "🎨",
        "default_provider": "wavespeed",
        "providers": {
            "wavespeed": {
                "label": "WaveSpeed",
                "retail": COSTS.get(("gpt-image-1.5", "wavespeed"), 0.07),
                "actual": ACTUAL_COSTS.get(("gpt-image-1.5", "wavespeed"), 0.07),
                "free_tier": False,
                "sync": False,
            },
        },
    },

    # ── Video models ──────────────────────────────────────────────────
    "veo-3.1": {
        "display_name": "Veo 3.1",
        "type": "video",
        "description": "Google's latest video generation model. High quality, free tier available.",
        "icon": "🎬",
        "default_provider": "google",
        "providers": {
            "google": {
                "label": "Google AI Studio",
                "retail": COSTS.get(("veo-3.1", "google"), 0.50),
                "actual": ACTUAL_COSTS.get(("veo-3.1", "google"), 0.00),
                "free_tier": ACTUAL_COSTS.get(("veo-3.1", "google"), 0.00) == 0.00,
                "sync": False,
            },
        },
    },
    "kling-3.0": {
        "display_name": "Kling 3.0",
        "type": "video",
        "description": "High-quality video from image or text. Supports multi-shot and variable duration.",
        "icon": "📹",
        "default_provider": "wavespeed",
        "providers": {
            "wavespeed": {
                "label": "WaveSpeed",
                "retail": COSTS.get(("kling-3.0", "wavespeed"), 0.30),
                "actual": ACTUAL_COSTS.get(("kling-3.0", "wavespeed"), 0.30),
                "free_tier": False,
                "sync": False,
            },
            "kie": {
                "label": "Kie AI",
                "retail": COSTS.get(("kling-3.0", "kie"), 0.30),
                "actual": ACTUAL_COSTS.get(("kling-3.0", "kie"), 0.30),
                "free_tier": False,
                "sync": False,
            },
        },
    },
    "sora-2": {
        "display_name": "Sora 2",
        "type": "video",
        "description": "OpenAI Sora image-to-video generation.",
        "icon": "🌀",
        "default_provider": "wavespeed",
        "providers": {
            "wavespeed": {
                "label": "WaveSpeed",
                "retail": COSTS.get(("sora-2", "wavespeed"), 0.30),
                "actual": ACTUAL_COSTS.get(("sora-2", "wavespeed"), 0.30),
                "free_tier": False,
                "sync": False,
            },
        },
    },
    "sora-2-pro": {
        "display_name": "Sora 2 Pro",
        "type": "video",
        "description": "OpenAI Sora Pro — higher quality, portrait/landscape, 10-15s output.",
        "icon": "🌀✨",
        "default_provider": "wavespeed",
        "providers": {
            "wavespeed": {
                "label": "WaveSpeed",
                "retail": COSTS.get(("sora-2-pro", "wavespeed"), 0.30),
                "actual": ACTUAL_COSTS.get(("sora-2-pro", "wavespeed"), 0.30),
                "free_tier": False,
                "sync": False,
            },
            "kie": {
                "label": "Kie AI",
                "retail": COSTS.get(("sora-2-pro", "kie"), 0.30),
                "actual": ACTUAL_COSTS.get(("sora-2-pro", "kie"), 0.30),
                "free_tier": False,
                "sync": False,
            },
        },
    },
    "seedance": {
        "display_name": "Seedance 2.0",
        "type": "video",
        "description": "ByteDance's Seedance — affordable, good quality video generation. Text & image-to-video.",
        "icon": "🌱",
        "default_provider": "higgsfield",
        "providers": {
            "higgsfield": {
                "label": "Higgsfield",
                "retail": COSTS.get(("seedance", "higgsfield"), 0.20),
                "actual": ACTUAL_COSTS.get(("seedance", "higgsfield"), 0.00),
                "free_tier": ACTUAL_COSTS.get(("seedance", "higgsfield"), 0.00) == 0.00,
                "sync": False,
            },
        },
    },
    "minimax": {
        "display_name": "Minimax",
        "type": "video",
        "description": "Minimax video model — fast, affordable, great for social content. Text & image-to-video.",
        "icon": "⚡",
        "default_provider": "higgsfield",
        "providers": {
            "higgsfield": {
                "label": "Higgsfield",
                "retail": COSTS.get(("minimax", "higgsfield"), 0.20),
                "actual": ACTUAL_COSTS.get(("minimax", "higgsfield"), 0.00),
                "free_tier": ACTUAL_COSTS.get(("minimax", "higgsfield"), 0.00) == 0.00,
                "sync": False,
            },
        },
    },

    # ── TTS models ────────────────────────────────────────────────────
    "gemini-tts": {
        "display_name": "Gemini TTS",
        "type": "tts",
        "description": "Google Gemini Text-to-Speech for natural voice generation.",
        "icon": "🗣️",
        "default_provider": "gemini",
        "providers": {
            "gemini": {
                "label": "Google AI Studio",
                "retail": COSTS.get(("gemini-tts", "gemini"), 0.00),
                "actual": ACTUAL_COSTS.get(("gemini-tts", "gemini"), 0.00),
                "free_tier": True,
                "sync": True,
            },
        },
    },

    # ── Talking Head models ───────────────────────────────────────────
    "speak-v2": {
        "display_name": "Higgsfield Speak v2",
        "type": "talking_head",
        "description": "High-quality talking head video from image and audio.",
        "icon": "🧑‍🎤",
        "default_provider": "higgsfield",
        "providers": {
            "higgsfield": {
                "label": "Higgsfield",
                "retail": COSTS.get(("speak-v2", "higgsfield"), 0.15),
                "actual": ACTUAL_COSTS.get(("speak-v2", "higgsfield"), 0.05),
                "free_tier": False,
                "sync": False,
            },
        },
    },
    "talking-photo": {
        "display_name": "Higgsfield Talking Photo",
        "type": "talking_head",
        "description": "Legacy talking head video from image and audio (fallback).",
        "icon": "📸",
        "default_provider": "higgsfield",
        "providers": {
            "higgsfield": {
                "label": "Higgsfield",
                "retail": COSTS.get(("talking-photo", "higgsfield"), 0.10),
                "actual": ACTUAL_COSTS.get(("talking-photo", "higgsfield"), 0.03),
                "free_tier": False,
                "sync": False,
            },
        },
    },
    "infinitetalk": {
        "display_name": "WaveSpeed InfiniteTalk",
        "type": "talking_head",
        "description": "WaveSpeed talking head video from image and audio (last resort).",
        "icon": "🗣️",
        "default_provider": "wavespeed",
        "providers": {
            "wavespeed": {
                "label": "WaveSpeed",
                "retail": COSTS.get(("infinitetalk", "wavespeed"), 0.20),
                "actual": ACTUAL_COSTS.get(("infinitetalk", "wavespeed"), 0.20),
                "free_tier": False,
                "sync": False,
            },
        },
    },
}


# ── Public API ────────────────────────────────────────────────────────

def get_model_catalog():
    """Return the full catalog dict keyed by model slug."""
    return MODEL_CATALOG


def get_models_by_type(model_type="image"):
    """Return models filtered by type ('image' or 'video')."""
    return {
        k: v for k, v in MODEL_CATALOG.items()
        if v["type"] == model_type
    }


def get_image_models():
    """Shorthand for image models."""
    return get_models_by_type("image")


def get_video_models():
    """Shorthand for video models."""
    return get_models_by_type("video")


def get_model_info(model_slug):
    """Return info dict for a single model, or None."""
    return MODEL_CATALOG.get(model_slug)


def get_cheapest_price(model_slug):
    """Return the lowest retail price across all providers for a model."""
    info = MODEL_CATALOG.get(model_slug)
    if not info:
        return 0.0
    prices = [p["retail"] for p in info["providers"].values()]
    return min(prices) if prices else 0.0


def has_free_tier(model_slug):
    """True if any provider for this model has a free tier."""
    info = MODEL_CATALOG.get(model_slug)
    if not info:
        return False
    return any(p["free_tier"] for p in info["providers"].values())


def get_default_provider(model_slug):
    """Return the default provider name for a model."""
    info = MODEL_CATALOG.get(model_slug)
    return info["default_provider"] if info else None


def get_model_choices(model_type="image"):
    """
    Return a list of dicts suitable for template rendering.
    Each dict has: slug, display_name, icon, description, type,
    default_provider, cheapest_price, has_free_tier, providers.
    """
    models = get_models_by_type(model_type)
    choices = []
    for slug, info in models.items():
        cheapest = get_cheapest_price(slug)
        free = has_free_tier(slug)
        choices.append({
            "slug": slug,
            "display_name": info["display_name"],
            "icon": info["icon"],
            "description": info["description"],
            "type": info["type"],
            "default_provider": info["default_provider"],
            "cheapest_price": cheapest,
            "has_free_tier": free,
            "providers": [
                {
                    "name": pname,
                    "label": pinfo["label"],
                    "retail": pinfo["retail"],
                    "free_tier": pinfo["free_tier"],
                    "sync": pinfo["sync"],
                }
                for pname, pinfo in info["providers"].items()
            ],
        })
    # Sort: free tier models first, then by price ascending
    choices.sort(key=lambda c: (not c["has_free_tier"], c["cheapest_price"]))
    return choices
