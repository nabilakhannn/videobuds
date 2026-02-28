"""End-to-End Playwright tests for VideoBuds.

Tests the full browser experience: login, navigation, brand/persona management,
all 8 active recipe forms, security headers, CSRF protection, and stub recipe
blocking.

Run:
    python3 -m pytest tests/test_e2e_playwright.py -v --tb=short

Requires:
    - Server running on localhost:8080  (python3 run.py)
    - pip install playwright && python3 -m playwright install chromium
"""

import pytest
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8080"
ADMIN_EMAIL = "admin@videobuds.com"
ADMIN_PASS = "admin"
USER_EMAIL = "user@videobuds.com"
USER_PASS = "user"


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser():
    """Launch a single browser for the entire session."""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture(scope="session")
def admin_context(browser):
    """Shared admin context — login ONCE, reuse across all tests."""
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="email"]', ADMIN_EMAIL)
    page.fill('input[name="password"]', ADMIN_PASS)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    page.close()  # Close the login page, cookies stay in context
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
def user_context(browser):
    """Shared user context — login ONCE, reuse across all tests."""
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="email"]', USER_EMAIL)
    page.fill('input[name="password"]', USER_PASS)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    page.close()
    yield ctx
    ctx.close()


@pytest.fixture()
def admin_page(admin_context):
    """Fresh page in shared admin context for each test."""
    page = admin_context.new_page()
    yield page
    page.close()


@pytest.fixture()
def user_page(user_context):
    """Fresh page in shared user context for each test."""
    page = user_context.new_page()
    yield page
    page.close()


@pytest.fixture()
def anon_page(browser):
    """Unauthenticated browser page."""
    ctx = browser.new_context()
    page = ctx.new_page()
    yield page
    page.close()
    ctx.close()


# ═══════════════════════════════════════════════════════════════════════
# 1. AUTH & ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════════════

class TestAuth:
    """Login, logout, redirect-on-unauth, admin vs user."""

    def test_login_page_loads(self, anon_page):
        anon_page.goto(f"{BASE_URL}/login")
        assert anon_page.locator("input[name='email']").is_visible()
        assert anon_page.locator("input[name='password']").is_visible()

    def test_admin_is_logged_in(self, admin_page):
        """Verify admin session is active (no redirect to login)."""
        admin_page.goto(f"{BASE_URL}/")
        admin_page.wait_for_load_state("networkidle")
        assert "/login" not in admin_page.url

    def test_unauthenticated_redirect_to_login(self, anon_page):
        """Accessing protected route without login redirects to login page."""
        anon_page.goto(f"{BASE_URL}/")
        anon_page.wait_for_load_state("networkidle")
        assert "/login" in anon_page.url

    def test_recipes_require_auth(self, anon_page):
        anon_page.goto(f"{BASE_URL}/recipes/")
        anon_page.wait_for_load_state("networkidle")
        assert "/login" in anon_page.url


# ═══════════════════════════════════════════════════════════════════════
# 2. SECURITY HEADERS
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityHeaders:
    """Verify HTTP security headers on every response."""

    def test_csp_header(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/")
        headers = resp.headers
        assert "content-security-policy" in headers, "Missing CSP header"
        assert "script-src" in headers["content-security-policy"]

    def test_x_content_type_options(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/")
        assert resp.headers.get("x-frame-options") in ("DENY", "SAMEORIGIN")

    def test_referrer_policy(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/")
        assert "referrer-policy" in resp.headers


# ═══════════════════════════════════════════════════════════════════════
# 3. NAVIGATION & DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

class TestNavigation:
    """Main navigation and dashboard render correctly."""

    def test_dashboard_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.title() != ""
        assert "/login" not in admin_page.url

    def test_recipes_library_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content()
        assert "Ad Video Maker" in content or "Recipe" in content

    def test_brands_page_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/brands/")
        admin_page.wait_for_load_state("networkidle")
        assert "brand" in admin_page.content().lower()

    def test_campaigns_page_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/campaigns/")
        admin_page.wait_for_load_state("networkidle")
        assert "campaign" in admin_page.content().lower()

    def test_pricing_page_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/pricing")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert "model" in content or "pricing" in content or "price" in content


# ═══════════════════════════════════════════════════════════════════════
# 4. RECIPE LIBRARY — ACTIVE vs STUBS
# ═══════════════════════════════════════════════════════════════════════

class TestRecipeLibrary:
    """The recipe library shows active recipes and hides stubs."""

    def test_active_recipes_visible(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content()
        expected = [
            "Ad Video Maker",
            "Photo to Ad",
            "News Digest",
            "Image Creator",
            "Video Creator",
            "Content Machine",
        ]
        for name in expected:
            assert name in content, f"Active recipe '{name}' not visible in library"

    def test_stub_recipes_hidden(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content()
        stubs = ["Clip Factory", "Motion Capture", "Style Cloner"]
        for name in stubs:
            assert name not in content, f"Stub recipe '{name}' should be hidden"

    def test_stub_recipe_detail_returns_404(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/clip-factory/")
        assert resp.status == 404, f"Stub detail should 404, got {resp.status}"

    def test_stub_recipe_run_returns_404(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/clip-factory/run/")
        assert resp.status == 404, f"Stub run should 404, got {resp.status}"


# ═══════════════════════════════════════════════════════════════════════
# 5. RECIPE DETAIL & RUN FORM — ALL 6 ACTIVE RECIPES
# ═══════════════════════════════════════════════════════════════════════

class TestAdVideoMakerRecipe:
    """Ad Video Maker recipe detail and run form."""

    def test_detail_page_loads(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/ad-video-maker/")
        admin_page.wait_for_load_state("networkidle")
        assert resp.status == 200
        assert "Ad Video Maker" in admin_page.content()

    def test_run_form_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/ad-video-maker/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "No form found on run page"

    def test_run_form_has_file_upload(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/ad-video-maker/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('input[type="file"]').count() >= 1

    def test_brand_selector_visible(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/ad-video-maker/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('select[name="brand_id"]').count() >= 1, "Brand selector missing"

    def test_persona_selector_visible(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/ad-video-maker/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('select[name="persona_id"]').count() >= 1, "Persona selector missing"


class TestPhotoToAdRecipe:
    """Photo to Ad recipe detail and run form."""

    def test_detail_page_loads(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/photo-to-ad/")
        admin_page.wait_for_load_state("networkidle")
        assert resp.status == 200
        assert "Photo to Ad" in admin_page.content()

    def test_run_form_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/photo-to-ad/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "No form found"

    def test_has_file_upload(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/photo-to-ad/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('input[type="file"]').count() >= 1

    def test_brand_persona_selectors(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/photo-to-ad/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('select[name="brand_id"]').count() >= 1
        assert admin_page.locator('select[name="persona_id"]').count() >= 1


class TestNewsDigestRecipe:
    """AI News Digest recipe detail and run form (slug: news-digest)."""

    def test_detail_page_loads(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/news-digest/")
        admin_page.wait_for_load_state("networkidle")
        assert resp.status == 200
        content = admin_page.content()
        assert "News Digest" in content

    def test_run_form_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/news-digest/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "No form found"

    def test_has_topic_field(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/news-digest/run/")
        admin_page.wait_for_load_state("networkidle")
        text_inputs = admin_page.locator('textarea, input[type="text"]')
        assert text_inputs.count() >= 1, "News Digest should have text inputs"

    def test_has_seo_checkbox(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/news-digest/run/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert "seo" in content, "SEO optimization checkbox should be present"

    def test_has_format_selector(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/news-digest/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("select").count() >= 1, "Should have format selector"


class TestImageCreatorRecipe:
    """Image Creator recipe detail and run form."""

    def test_detail_page_loads(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/image-creator/")
        admin_page.wait_for_load_state("networkidle")
        assert resp.status == 200
        assert "Image Creator" in admin_page.content()

    def test_run_form_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/image-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "No form found"

    def test_has_prompt_field(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/image-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("textarea").count() >= 1, "Prompt textarea missing"

    def test_has_style_preset(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/image-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert "style" in admin_page.content().lower()

    def test_has_platform_selector(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/image-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert "platform" in content or "instagram" in content

    def test_has_model_selector(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/image-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert "model" in admin_page.content().lower()

    def test_has_reference_upload(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/image-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('input[type="file"]').count() >= 1

    def test_brand_persona_selectors(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/image-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('select[name="brand_id"]').count() >= 1
        assert admin_page.locator('select[name="persona_id"]').count() >= 1


class TestVideoCreatorRecipe:
    """Video Creator recipe detail and run form."""

    def test_detail_page_loads(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/video-creator/")
        admin_page.wait_for_load_state("networkidle")
        assert resp.status == 200
        assert "Video Creator" in admin_page.content()

    def test_run_form_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/video-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "No form found"

    def test_has_prompt_field(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/video-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("textarea").count() >= 1

    def test_has_model_selector(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/video-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content()
        assert "Veo" in content or "Kling" in content or "Sora" in content or "model" in content.lower()

    def test_has_duration_selector(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/video-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert "duration" in content or "4s" in content or "6s" in content

    def test_has_style_preset(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/video-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert "style" in admin_page.content().lower()

    def test_brand_persona_selectors(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/video-creator/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('select[name="brand_id"]').count() >= 1
        assert admin_page.locator('select[name="persona_id"]').count() >= 1


class TestContentMachineRecipe:
    """AI Content Machine recipe detail and run form."""

    def test_detail_page_loads(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/content-machine/")
        admin_page.wait_for_load_state("networkidle")
        assert resp.status == 200
        assert "Content Machine" in admin_page.content()

    def test_run_form_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/content-machine/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "No form found"

    def test_has_competitor_content_field(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/content-machine/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("textarea").count() >= 1

    def test_has_analysis_mode_selector(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/content-machine/run/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert "analysis" in content or "mode" in content or "full" in content

    def test_has_platform_selector(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/content-machine/run/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert "platform" in content or "instagram" in content

    def test_brand_persona_selectors(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/content-machine/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('select[name="brand_id"]').count() >= 1
        assert admin_page.locator('select[name="persona_id"]').count() >= 1


# ═══════════════════════════════════════════════════════════════════════
# 5b. TALKING AVATAR RECIPE
# ═══════════════════════════════════════════════════════════════════════

class TestTalkingAvatarRecipeE2E:
    """Talking Avatar recipe UI checks."""

    def test_detail_page_loads(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/talking-avatar/")
        admin_page.wait_for_load_state("networkidle")
        assert resp.status == 200
        assert "Talking Avatar" in admin_page.content()

    def test_run_form_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/talking-avatar/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "No form found"

    def test_has_headshot_upload(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/talking-avatar/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('input[type="file"]').count() >= 1

    def test_has_script_field(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/talking-avatar/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("textarea").count() >= 1

    def test_brand_persona_selectors(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/talking-avatar/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('select[name="brand_id"]').count() >= 1
        assert admin_page.locator('select[name="persona_id"]').count() >= 1


# ═══════════════════════════════════════════════════════════════════════
# 5c. INFLUENCER CONTENT KIT RECIPE
# ═══════════════════════════════════════════════════════════════════════

class TestInfluencerContentKitE2E:
    """Influencer Content Kit recipe UI checks."""

    def test_detail_page_loads(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/recipes/influencer-content-kit/")
        admin_page.wait_for_load_state("networkidle")
        assert resp.status == 200
        assert "Influencer" in admin_page.content()

    def test_run_form_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/influencer-content-kit/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "No form found"

    def test_has_character_photo_upload(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/influencer-content-kit/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('input[type="file"]').count() >= 1

    def test_has_brief_field(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/influencer-content-kit/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("textarea").count() >= 1

    def test_brand_persona_selectors(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/influencer-content-kit/run/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator('select[name="brand_id"]').count() >= 1
        assert admin_page.locator('select[name="persona_id"]').count() >= 1


# ═══════════════════════════════════════════════════════════════════════
# 6. BRAND & PERSONA
# ═══════════════════════════════════════════════════════════════════════

class TestBrandManagement:
    """Brand creation, listing, detail."""

    def test_brand_list_page(self, admin_page):
        admin_page.goto(f"{BASE_URL}/brands/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content()
        assert "Sample Brand" in content or "brand" in content.lower()

    def test_brand_create_form_exists(self, admin_page):
        admin_page.goto(f"{BASE_URL}/brands/new")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "Brand create form missing"
        assert admin_page.locator('input[name="name"]').count() >= 1


class TestPersonaManagement:
    """Persona listing and creation."""

    def test_persona_list_page(self, admin_page):
        admin_page.goto(f"{BASE_URL}/personas/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content()
        assert "persona" in content.lower()

    def test_persona_create_form_exists(self, admin_page):
        admin_page.goto(f"{BASE_URL}/personas/new/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("form").count() >= 1, "Persona create form missing"


# ═══════════════════════════════════════════════════════════════════════
# 7. CSRF PROTECTION
# ═══════════════════════════════════════════════════════════════════════

class TestCSRF:
    """CSRF tokens present on all forms."""

    def test_login_form_has_csrf(self, anon_page):
        anon_page.goto(f"{BASE_URL}/login")
        anon_page.wait_for_load_state("networkidle")
        csrf = anon_page.locator('input[name="csrf_token"]')
        assert csrf.count() >= 1, "Login form missing CSRF token"

    def test_recipe_run_form_has_csrf(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/ad-video-maker/run/")
        admin_page.wait_for_load_state("networkidle")
        csrf = admin_page.locator('input[name="csrf_token"]')
        assert csrf.count() >= 1, "Recipe run form missing CSRF token"

    def test_brand_create_form_has_csrf(self, admin_page):
        admin_page.goto(f"{BASE_URL}/brands/new")
        admin_page.wait_for_load_state("networkidle")
        csrf = admin_page.locator('input[name="csrf_token"]')
        assert csrf.count() >= 1, "Brand create form missing CSRF token"


# ═══════════════════════════════════════════════════════════════════════
# 8. RECIPE HISTORY
# ═══════════════════════════════════════════════════════════════════════

class TestRecipeHistory:
    """Recipe execution history page."""

    def test_history_page_loads(self, admin_page):
        admin_page.goto(f"{BASE_URL}/recipes/history/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert "history" in content or "run" in content or "recipe" in content


# ═══════════════════════════════════════════════════════════════════════
# 9. ADMIN-ONLY FEATURES
# ═══════════════════════════════════════════════════════════════════════

class TestAdminFeatures:
    """Admin dashboard features accessible only to admin."""

    def test_admin_dashboard_shows_content(self, admin_page):
        admin_page.goto(f"{BASE_URL}/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert "user" in content or "cost" in content or "admin" in content or "dashboard" in content


# ═══════════════════════════════════════════════════════════════════════
# 10. CROSS-USER ISOLATION
# ═══════════════════════════════════════════════════════════════════════

class TestUserIsolation:
    """Non-admin user has different experience than admin."""

    def test_user_can_access_home(self, user_page):
        resp = user_page.goto(f"{BASE_URL}/")
        user_page.wait_for_load_state("networkidle")
        assert "/login" not in user_page.url, "User should be able to access home"

    def test_user_can_access_recipes(self, user_page):
        user_page.goto(f"{BASE_URL}/recipes/")
        user_page.wait_for_load_state("networkidle")
        assert "/login" not in user_page.url
        assert "recipe" in user_page.content().lower()


# ═══════════════════════════════════════════════════════════════════════
# 11. API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

class TestAPIEndpoints:
    """Key API endpoints respond correctly."""

    def test_outputs_endpoint_404_for_missing(self, admin_page):
        resp = admin_page.goto(f"{BASE_URL}/api/outputs/nonexistent_file.jpg")
        assert resp.status == 404

    def test_api_outputs_requires_auth(self, anon_page):
        """Unauth access to API redirects to login."""
        anon_page.goto(f"{BASE_URL}/api/outputs/test.jpg")
        anon_page.wait_for_load_state("networkidle")
        assert "/login" in anon_page.url


# ═══════════════════════════════════════════════════════════════════════
# 12. HOW-TO-USE DOCUMENTATION IN RECIPES
# ═══════════════════════════════════════════════════════════════════════

class TestRecipeDocumentation:
    """Each active recipe should display how-to-use instructions."""

    @pytest.mark.parametrize("slug,keyword", [
        ("ad-video-maker", "upload"),
        ("photo-to-ad", "photo"),
        ("news-digest", "topic"),
        ("image-creator", "prompt"),
        ("video-creator", "prompt"),
        ("content-machine", "competitor"),
        ("talking-avatar", "photo"),
        ("influencer-content-kit", "character"),
    ])
    def test_recipe_detail_has_instructions(self, admin_page, slug, keyword):
        admin_page.goto(f"{BASE_URL}/recipes/{slug}/")
        admin_page.wait_for_load_state("networkidle")
        content = admin_page.content().lower()
        assert keyword in content, (
            f"Recipe '{slug}' detail page missing keyword '{keyword}' in instructions"
        )
