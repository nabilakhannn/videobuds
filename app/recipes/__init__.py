"""Recipe registry — auto-discovers and loads every recipe in this package.

Import this module to get access to:
    get_all_recipes()   -> list of instantiated BaseRecipe subclasses
    get_recipe(slug)    -> single recipe by slug
    recipe_count()      -> total number of available recipes

Adding a new recipe is as simple as:
    1. Create a new .py file in app/recipes/
    2. Subclass BaseRecipe
    3. Fill in the metadata + implement get_input_fields, get_steps, execute
    4. Done — the registry picks it up automatically.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, List, Optional

from .base import BaseRecipe, InputField  # noqa: F401 — re-export

# ---------------------------------------------------------------------------
# Global registry (populated on first call)
# ---------------------------------------------------------------------------

_registry: Dict[str, BaseRecipe] = {}
_loaded = False


def _discover():
    """Import every module in this package to trigger subclass registration."""
    global _loaded
    if _loaded:
        return
    import app.recipes as pkg
    for _importer, modname, _ispkg in pkgutil.iter_modules(pkg.__path__):
        if modname.startswith("_") or modname == "base":
            continue
        importlib.import_module(f"app.recipes.{modname}")
    # Instantiate every concrete subclass of BaseRecipe
    _register_subclasses(BaseRecipe)
    _loaded = True


def _register_subclasses(cls):
    """Recursively register all concrete subclasses of *cls*."""
    for sub in cls.__subclasses__():
        if sub.slug and sub.slug not in _registry:
            _registry[sub.slug] = sub()
        _register_subclasses(sub)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_recipes(*, include_inactive: bool = False) -> List[BaseRecipe]:
    """Return discovered recipe instances, sorted by category then name.

    By default only active (non-stub) recipes are returned.  Pass
    ``include_inactive=True`` to get everything (e.g. for admin views).
    """
    _discover()
    recipes = _registry.values()
    if not include_inactive:
        recipes = [r for r in recipes if r.is_active]
    return sorted(recipes, key=lambda r: (r.category, r.name))


def get_recipe(slug: str) -> Optional[BaseRecipe]:
    """Return a single recipe by slug, or None."""
    _discover()
    return _registry.get(slug)


def recipe_count(*, include_inactive: bool = False) -> int:
    """Total number of available recipes (for the sidebar badge).

    Only counts active recipes by default.
    """
    _discover()
    if include_inactive:
        return len(_registry)
    return sum(1 for r in _registry.values() if r.is_active)


def get_recipes_by_category(*, include_inactive: bool = False) -> Dict[str, List[BaseRecipe]]:
    """Return recipes grouped by category label.

    Only includes active recipes by default.
    """
    _discover()
    grouped: Dict[str, List[BaseRecipe]] = {}
    category_labels = {
        "content_creation": "Content Creation",
        "video_studio": "Video Studio",
        "repurpose": "Repurpose & Edit",
        "research": "Research & Intelligence",
        "distribution": "Auto-Post & Distribution",
    }
    for recipe in get_all_recipes(include_inactive=include_inactive):
        label = category_labels.get(recipe.category, recipe.category.replace("_", " ").title())
        grouped.setdefault(label, []).append(recipe)
    return grouped
