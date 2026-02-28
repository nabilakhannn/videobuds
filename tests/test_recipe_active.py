"""Unit tests for is_active recipe filtering (L3 — hide stub recipes)."""

import pytest


class TestBaseRecipeIsActive:
    def test_default_is_active_true(self):
        """BaseRecipe.is_active defaults to True."""
        from app.recipes.base import BaseRecipe
        assert BaseRecipe.is_active is True

    def test_stub_recipes_are_inactive(self):
        """All 6 known stub recipes should have is_active = False."""
        from app.recipes import get_all_recipes

        all_recipes = get_all_recipes(include_inactive=True)
        stub_slugs = {
            "clip-factory", "social-scraper",
            "vertical-reframe", "motion-capture", "multi-scene-video",
            "style-cloner",
        }
        for recipe in all_recipes:
            if recipe.slug in stub_slugs:
                assert recipe.is_active is False, (
                    f"{recipe.slug} should be is_active=False"
                )

    def test_real_recipes_are_active(self):
        """Non-stub recipes should be active."""
        from app.recipes import get_all_recipes

        active_recipes = get_all_recipes()
        active_slugs = {r.slug for r in active_recipes}

        # These are the known real (implemented) recipes
        expected_active = {"ad-video-maker", "photo-to-ad", "news-digest", "image-creator", "video-creator", "content-machine", "talking-avatar", "influencer-content-kit"}
        for slug in expected_active:
            assert slug in active_slugs, f"{slug} should be active"


class TestGetAllRecipesFiltering:
    def test_default_excludes_inactive(self):
        """get_all_recipes() should NOT return stub recipes by default."""
        from app.recipes import get_all_recipes

        recipes = get_all_recipes()
        for r in recipes:
            assert r.is_active is True, f"{r.slug} should not appear in default list"

    def test_include_inactive_returns_all(self):
        """get_all_recipes(include_inactive=True) should return everything."""
        from app.recipes import get_all_recipes

        all_recipes = get_all_recipes(include_inactive=True)
        active_only = get_all_recipes(include_inactive=False)
        assert len(all_recipes) > len(active_only)
        assert len(all_recipes) == len(active_only) + 6  # exactly 6 stubs

    def test_sorted_by_category_then_name(self):
        """Result should be sorted by (category, name)."""
        from app.recipes import get_all_recipes

        recipes = get_all_recipes()
        keys = [(r.category, r.name) for r in recipes]
        assert keys == sorted(keys)


class TestRecipeCount:
    def test_count_excludes_inactive(self):
        """recipe_count() should only count active recipes."""
        from app.recipes import recipe_count, get_all_recipes

        assert recipe_count() == len(get_all_recipes())

    def test_count_include_inactive(self):
        """recipe_count(include_inactive=True) should count everything."""
        from app.recipes import recipe_count, get_all_recipes

        assert recipe_count(include_inactive=True) == len(
            get_all_recipes(include_inactive=True)
        )


class TestGetRecipesByCategory:
    def test_excludes_inactive_by_default(self):
        """get_recipes_by_category() should not include stub recipes."""
        from app.recipes import get_recipes_by_category

        grouped = get_recipes_by_category()
        for cat, recipes in grouped.items():
            for r in recipes:
                assert r.is_active is True, (
                    f"{r.slug} in category {cat!r} should not appear"
                )

    def test_include_inactive_returns_stubs(self):
        """get_recipes_by_category(include_inactive=True) should include stubs."""
        from app.recipes import get_recipes_by_category

        grouped = get_recipes_by_category(include_inactive=True)
        all_slugs = set()
        for recipes in grouped.values():
            for r in recipes:
                all_slugs.add(r.slug)

        # Should include at least one known stub
        assert "clip-factory" in all_slugs


class TestGetRecipeBySlug:
    def test_get_recipe_returns_inactive_too(self):
        """get_recipe(slug) should return a recipe even if inactive (for run history)."""
        from app.recipes import get_recipe

        recipe = get_recipe("clip-factory")
        assert recipe is not None
        assert recipe.is_active is False

    def test_get_recipe_returns_active(self):
        """get_recipe(slug) works for active recipes."""
        from app.recipes import get_recipe

        recipe = get_recipe("video-creator")
        assert recipe is not None
        assert recipe.is_active is True
