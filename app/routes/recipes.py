"""Recipes blueprint — Workflow Library, detail pages, run, status, history.

Provides:
    /recipes/                        — library grid (all recipes by category)
    /recipes/<slug>/                 — detail page with how-to-use guide
    /recipes/<slug>/run/             — start a new run (form + submit)
    /recipes/run/<id>/status         — HTMX poll endpoint for progress
    /recipes/run/<id>/approve        — approve script and start Phase 2
    /recipes/history/                — user's past runs across all recipes

Two-phase execution model (for recipes that support it):
    Phase 1 (SCRIPT):  Analyses input → writes creative script
                       → sets status to ``awaiting_approval``
    Phase 2 (PRODUCTION): User approves/edits script
                       → generates images + videos → ``completed``
"""

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ..extensions import db
from ..models.brand import Brand
from ..models.recipe import Recipe
from ..models.recipe_run import RecipeRun
from ..models.user_persona import UserPersona
from ..security import safe_int, validate_upload

logger = logging.getLogger(__name__)
recipes_bp = Blueprint("recipes", __name__, url_prefix="/recipes")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_recipe_db_row(recipe_cls):
    """Create or update a Recipe DB row for this slug.

    Also syncs the ``is_enabled`` DB flag from the class-level
    ``is_active`` attribute so the DB always reflects the source of truth.
    """
    row = Recipe.query.filter_by(slug=recipe_cls.slug).first()
    if not row:
        row = Recipe(
            slug=recipe_cls.slug,
            name=recipe_cls.name,
            description=recipe_cls.short_description,
            category=recipe_cls.category,
            icon=recipe_cls.icon,
            estimated_cost_label=recipe_cls.estimated_cost,
            is_enabled=getattr(recipe_cls, "is_active", True),
        )
        db.session.add(row)
        db.session.commit()
    else:
        # Keep DB in sync with class attribute (source of truth)
        cls_active = getattr(recipe_cls, "is_active", True)
        if row.is_enabled != cls_active:
            row.is_enabled = cls_active
            db.session.commit()
    return row


def _make_progress_callback(run_id):
    """Return a callback that updates the RecipeRun row in the database.

    Called from the recipe's execute() each time a step begins:
        on_progress(step_index, label)

    IMPORTANT: Must be called from within an active app context (the
    background thread's ``_execute_recipe`` provides one).
    """
    def _on_progress(step_index: int, label: str):
        try:
            run_row = db.session.get(RecipeRun, run_id)
            if run_row is None:
                return
            run_row.status = "running"
            run_row.steps_completed = step_index
            run_row.current_step_label = label
            if run_row.started_at is None:
                run_row.started_at = datetime.now(timezone.utc)
            db.session.commit()
        except Exception:
            logger.exception("Progress callback error for run %s", run_id)
    return _on_progress


def _execute_recipe(app, recipe, run_id, user_id, inputs,
                    brand_id=None, persona_id=None):
    """Run a recipe inside an app context (called from a background thread).

    Handles both single-phase and two-phase recipes:
    - If the result includes ``phase == "script"``, the run is paused
      at ``awaiting_approval`` so the user can review the script.
    - Otherwise the run completes normally.

    Resilience:
    - Primary try/except catches recipe errors and sets status = "failed"
    - Secondary (inner) try/except ensures DB write for error state
    - Final outer try/except is a catch-all so the thread never dies silently
    """
    try:
        with app.app_context():
            run_row = db.session.get(RecipeRun, run_id)
            if run_row is None:
                logger.error("RecipeRun %s vanished before execution", run_id)
                return

            run_row.status = "running"
            run_row.started_at = datetime.now(timezone.utc)
            db.session.commit()

            on_progress = _make_progress_callback(run_id)

            # Fetch Brand and Persona objects (if selected)
            brand = db.session.get(Brand, brand_id) if brand_id else None
            persona = db.session.get(UserPersona, persona_id) if persona_id else None

            try:
                result = recipe.execute(
                    inputs=inputs,
                    run_id=run_id,
                    user_id=user_id,
                    on_progress=on_progress,
                    brand=brand,
                    persona=persona,
                )

                # Persist results
                run_row = db.session.get(RecipeRun, run_id)

                phase = result.get("phase")

                if phase == "script":
                    # ── Two-phase recipe: pause for approval ──
                    run_row.status = "awaiting_approval"
                    run_row.steps_completed = 2  # Steps 0 & 1 done
                    run_row.current_step_label = "Waiting for your approval…"
                    run_row.outputs = result.get("outputs", [])
                    run_row.cost = result.get("cost", 0.0)
                    db.session.commit()

                    logger.info(
                        "Recipe run %s awaiting approval — %d output(s)",
                        run_id, len(run_row.outputs),
                    )
                else:
                    # ── Single-phase or Phase 2 complete ──
                    outputs = result.get("outputs", [])

                    # Detect error-only results: if every output contains
                    # an error indicator and there's no real media, mark
                    # the run as "failed" so the UI is honest.
                    has_real_output = any(
                        o.get("type") in ("image", "video", "audio")
                        or (o.get("type") == "text"
                            and "❌" not in (o.get("title", "") + o.get("value", "")))
                        for o in outputs
                    )
                    if outputs and not has_real_output:
                        run_row.status = "failed"
                        # Surface the first error message
                        first_err = next(
                            (o.get("value", "") for o in outputs
                             if "❌" in o.get("title", "")),
                            "Recipe returned errors without producing output."
                        )
                        run_row.error_message = first_err[:2000]
                    else:
                        run_row.status = "completed"

                    run_row.steps_completed = run_row.total_steps
                    run_row.current_step_label = "Done"
                    run_row.outputs = outputs
                    run_row.cost = result.get("cost", 0.0)
                    run_row.retail_cost = result.get("retail_cost", result.get("cost", 0.0))
                    run_row.model_used = result.get("model_used", "")
                    run_row.completed_at = datetime.now(timezone.utc)
                    db.session.commit()

                    logger.info(
                        "Recipe run %s %s — %d output(s), cost $%.4f",
                        run_id, run_row.status, len(run_row.outputs), run_row.cost,
                    )

            except Exception as exc:
                logger.exception("Recipe run %s failed", run_id)
                try:
                    # Rollback any partial transaction before writing error state
                    db.session.rollback()
                    run_row = db.session.get(RecipeRun, run_id)
                    if run_row:
                        run_row.status = "failed"
                        run_row.error_message = str(exc)[:2000]
                        run_row.completed_at = datetime.now(timezone.utc)
                        db.session.commit()
                except Exception:
                    logger.exception("Failed to save error state for run %s", run_id)

    except Exception:
        # ── Ultimate catch-all — thread must never die silently ──
        logger.exception(
            "CRITICAL: Unhandled error in recipe thread for run %s "
            "(outside app context or DB completely unavailable)", run_id
        )


def _launch_recipe_execution(app, recipe, run_id, user_id, inputs,
                             brand_id=None, persona_id=None):
    """Spawn a daemon thread that executes the recipe in the background."""
    thread = threading.Thread(
        target=_execute_recipe,
        args=(app, recipe, run_id, user_id, inputs),
        kwargs={"brand_id": brand_id, "persona_id": persona_id},
        daemon=True,
        name=f"recipe-run-{run_id}",
    )
    thread.start()
    logger.info("Launched background thread for recipe run %s", run_id)


def _reap_stale_runs(max_age_minutes=None):
    """Mark any runs stuck in 'running' for longer than *max_age_minutes* as
    'failed'.  This catches threads that crashed without setting an error
    state, or API calls that hung forever.

    When *max_age_minutes* is ``None`` (the default), the value is read from
    ``current_app.config['RECIPE_TIMEOUT_MINUTES']`` (default 30).

    Called opportunistically from the library page — lightweight query,
    no background thread needed.
    """
    if max_age_minutes is None:
        max_age_minutes = current_app.config.get("RECIPE_TIMEOUT_MINUTES", 30)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
    stale = RecipeRun.query.filter(
        RecipeRun.status == "running",
        RecipeRun.started_at < cutoff,
    ).all()

    for run in stale:
        run.status = "failed"
        run.error_message = (
            f"Run timed out after {max_age_minutes} minutes — "
            "the background thread may have crashed or an API call hung. "
            "Please try again."
        )
        run.completed_at = datetime.now(timezone.utc)
        logger.warning("Reaped stale run %s (started at %s)", run.id, run.started_at)

    if stale:
        db.session.commit()
        logger.info("Reaped %d stale recipe run(s)", len(stale))


# ---------------------------------------------------------------------------
# Library (card grid, categories, count badge)
# ---------------------------------------------------------------------------

@recipes_bp.route("/")
@login_required
def library():
    """Show all available recipes grouped by category."""
    from ..recipes import get_recipes_by_category, recipe_count

    # Opportunistically clean up any stale runs (cheap query)
    try:
        _reap_stale_runs()
    except Exception:
        logger.debug("Stale run reaper skipped (non-critical)", exc_info=True)

    categories = get_recipes_by_category()
    count = recipe_count()

    return render_template(
        "recipes/library.html",
        categories=categories,
        recipe_count=count,
    )


# ---------------------------------------------------------------------------
# Detail page (description + how-to-use guide)
# ---------------------------------------------------------------------------

@recipes_bp.route("/<slug>/")
@login_required
def detail(slug):
    """Show the detail page for a single recipe.

    Inactive (stub) recipes are hidden from the library grid and must not
    be viewable via direct URL either — return 404 for those.
    """
    from ..recipes import get_recipe

    recipe = get_recipe(slug)
    if not recipe:
        abort(404)

    # Block access to inactive/stub recipes
    if not getattr(recipe, "is_active", True):
        abort(404)

    db_row = _ensure_recipe_db_row(recipe)

    return render_template(
        "recipes/detail.html",
        recipe=recipe,
        db_row=db_row,
    )


# ---------------------------------------------------------------------------
# Run a recipe (form + submit)
# ---------------------------------------------------------------------------

@recipes_bp.route("/<slug>/run/", methods=["GET", "POST"])
@login_required
def run(slug):
    """GET: show the run form.  POST: create a RecipeRun and kick it off."""
    from ..recipes import get_recipe

    recipe = get_recipe(slug)
    if not recipe:
        abort(404)

    # Block access to inactive/stub recipes
    if not getattr(recipe, "is_active", True):
        abort(404)

    db_row = _ensure_recipe_db_row(recipe)

    # Check if recipe is enabled in DB
    if not db_row.is_enabled:
        abort(403)

    if request.method == "GET":
        # Fetch user's brands and personas for optional context selectors
        user_brands = Brand.query.filter_by(user_id=current_user.id).order_by(Brand.name).all()
        user_personas = UserPersona.query.filter_by(user_id=current_user.id).order_by(UserPersona.name).all()

        return render_template(
            "recipes/run.html",
            recipe=recipe,
            db_row=db_row,
            fields=recipe.get_input_fields(),
            steps=recipe.get_steps(),
            brands=user_brands,
            personas=user_personas,
        )

    # --- POST: create the run ---

    # Allowed upload extensions (server-side validation)
    ALLOWED_UPLOAD_EXT = {
        ".png", ".jpg", ".jpeg", ".webp", ".gif",  # images
        ".mp4", ".mov", ".webm",                     # videos
        ".mp3", ".wav", ".m4a",                      # audio
        ".pdf", ".txt", ".csv",                      # documents
    }

    # Collect inputs from form
    inputs = {}
    for field in recipe.get_input_fields():
        if field.field_type == "file":
            f = request.files.get(field.name)
            if f and f.filename:
                # OWASP A04 — defence-in-depth: ext + magic bytes + size
                ok, ext, err = validate_upload(
                    f, ALLOWED_UPLOAD_EXT, field.label
                )
                if not ok:
                    return render_template(
                        "recipes/run.html",
                        recipe=recipe,
                        db_row=db_row,
                        fields=recipe.get_input_fields(),
                        steps=recipe.get_steps(),
                        error=err,
                        old_inputs=inputs,
                        brands=Brand.query.filter_by(user_id=current_user.id).all(),
                        personas=UserPersona.query.filter_by(user_id=current_user.id).all(),
                    ), 400

                upload_dir = os.path.join(
                    current_app.config.get("UPLOAD_FOLDER", "app/static/uploads"),
                    "recipe_uploads",
                    str(current_user.id),
                )
                os.makedirs(upload_dir, exist_ok=True)
                fname = f"{uuid.uuid4().hex[:12]}{ext}"
                fpath = os.path.join(upload_dir, fname)
                f.save(fpath)
                inputs[field.name] = fpath
        else:
            val = request.form.get(field.name, "").strip()
            if val:
                inputs[field.name] = val
            elif field.default is not None:
                inputs[field.name] = str(field.default)

    # Validate required fields
    missing = []
    for field in recipe.get_input_fields():
        if field.required and field.name not in inputs:
            missing.append(field.label)

    if missing:
        return render_template(
            "recipes/run.html",
            recipe=recipe,
            db_row=db_row,
            fields=recipe.get_input_fields(),
            steps=recipe.get_steps(),
            error=f"Please fill in: {', '.join(missing)}",
            old_inputs=inputs,
            brands=Brand.query.filter_by(user_id=current_user.id).all(),
            personas=UserPersona.query.filter_by(user_id=current_user.id).all(),
        ), 400

    # Recipe-specific cross-field validation (e.g. "script OR brief")
    custom_error = recipe.validate_inputs(inputs)
    if custom_error:
        return render_template(
            "recipes/run.html",
            recipe=recipe,
            db_row=db_row,
            fields=recipe.get_input_fields(),
            steps=recipe.get_steps(),
            error=custom_error,
            old_inputs=inputs,
            brands=Brand.query.filter_by(user_id=current_user.id).all(),
            personas=UserPersona.query.filter_by(user_id=current_user.id).all(),
        ), 400

    # Validate text input lengths (server-side enforcement)
    max_text = current_app.config.get("MAX_TEXT_INPUT_LENGTH", 500)
    max_textarea = current_app.config.get("MAX_TEXTAREA_INPUT_LENGTH", 5000)

    for field in recipe.get_input_fields():
        val = inputs.get(field.name, "")
        if not isinstance(val, str):
            continue
        limit = max_textarea if field.field_type == "textarea" else max_text
        if len(val) > limit:
            return render_template(
                "recipes/run.html",
                recipe=recipe,
                db_row=db_row,
                fields=recipe.get_input_fields(),
                steps=recipe.get_steps(),
                error=f"'{field.label}' exceeds the maximum length of {limit:,} characters.",
                old_inputs=inputs,
                brands=Brand.query.filter_by(user_id=current_user.id).all(),
                personas=UserPersona.query.filter_by(user_id=current_user.id).all(),
            ), 400

    # Create RecipeRun row
    run_row = RecipeRun(
        recipe_id=db_row.id,
        user_id=current_user.id,
        brand_id=safe_int(request.form.get("brand_id")),
        persona_id=safe_int(request.form.get("persona_id")),
        status="pending",
        total_steps=len(recipe.get_steps()),
        current_step_label=recipe.get_steps()[0] if recipe.get_steps() else "",
    )
    run_row.inputs = inputs
    db.session.add(run_row)
    db.session.commit()

    # Increment usage counter
    db_row.usage_count = (db_row.usage_count or 0) + 1
    db.session.commit()

    # Kick off Phase 1 in a background thread
    _launch_recipe_execution(
        app=current_app._get_current_object(),
        recipe=recipe,
        run_id=run_row.id,
        user_id=current_user.id,
        inputs=inputs,
        brand_id=run_row.brand_id,
        persona_id=run_row.persona_id,
    )

    return redirect(url_for("recipes.run_status", run_id=run_row.id))


# ---------------------------------------------------------------------------
# Approve script and launch Phase 2
# ---------------------------------------------------------------------------

@recipes_bp.route("/run/<int:run_id>/approve", methods=["POST"])
@login_required
def approve_script(run_id):
    """Approve (and optionally edit) the AI-generated script, then launch
    Phase 2 (image + video generation).

    The form POSTs JSON-encoded approved scenes and the original inputs.
    """
    run_row = RecipeRun.query.filter_by(
        id=run_id, user_id=current_user.id
    ).first_or_404()

    if run_row.status != "awaiting_approval":
        abort(400, "This run is not awaiting approval.")

    db_recipe = db.session.get(Recipe, run_row.recipe_id)
    if not db_recipe:
        abort(404)

    from ..recipes import get_recipe
    recipe_cls = get_recipe(db_recipe.slug)
    if not recipe_cls:
        abort(404)

    # ── Collect approved (possibly edited) scenes from the form ──
    approved_scenes = []
    scene_count = safe_int(request.form.get("scene_count"), 0)

    for i in range(scene_count):
        scene = {
            "scene_description": request.form.get(f"scene_{i}_description", "").strip(),
            "video_motion": request.form.get(f"scene_{i}_motion", "").strip(),
            "ad_copy": request.form.get(f"scene_{i}_ad_copy", "").strip(),
        }
        # Only include scenes that have at least a description
        if scene["scene_description"]:
            approved_scenes.append(scene)

    if not approved_scenes:
        return redirect(url_for("recipes.run_status", run_id=run_id))

    # ── Build Phase 2 inputs ──
    original_inputs = run_row.inputs
    phase2_inputs = {
        **original_inputs,
        "_phase": "production",
        "_approved_scenes": approved_scenes,
        "_script_outputs": run_row.outputs,  # Carry forward analysis & script
    }

    # Update the run status
    run_row.status = "running"
    run_row.current_step_label = "Generating images…"
    run_row.steps_completed = 2  # Script phase done
    db.session.commit()

    # Launch Phase 2 in background
    _launch_recipe_execution(
        app=current_app._get_current_object(),
        recipe=recipe_cls,
        run_id=run_row.id,
        user_id=current_user.id,
        inputs=phase2_inputs,
        brand_id=run_row.brand_id,
        persona_id=run_row.persona_id,
    )

    return redirect(url_for("recipes.run_status", run_id=run_row.id))


# ---------------------------------------------------------------------------
# Run status (poll endpoint for progress bar)
# ---------------------------------------------------------------------------

@recipes_bp.route("/run/<int:run_id>/status")
@login_required
def run_status(run_id):
    """Show (or poll) the progress of a recipe run."""
    run_row = RecipeRun.query.filter_by(
        id=run_id, user_id=current_user.id
    ).first_or_404()

    db_recipe = db.session.get(Recipe, run_row.recipe_id)

    # Load the Python recipe class for step labels
    from ..recipes import get_recipe
    recipe_cls = get_recipe(db_recipe.slug) if db_recipe else None

    # Brands & personas for the AI editor (only needed when completed)
    editor_brands = []
    editor_personas = []
    if run_row.status == "completed":
        editor_brands = Brand.query.filter_by(user_id=current_user.id).order_by(Brand.name).all()
        editor_personas = UserPersona.query.filter_by(user_id=current_user.id).order_by(UserPersona.name).all()

    # HTMX poll — return just the progress fragment
    if request.headers.get("HX-Request"):
        html = render_template(
            "recipes/_run_progress.html",
            run=run_row,
            recipe=recipe_cls,
            db_row=db_recipe,
            editor_brands=editor_brands,
            editor_personas=editor_personas,
        )
        # HTTP 286 tells HTMX to stop polling (htmx standard).
        # Stop when status is terminal or paused for user approval.
        terminal_statuses = ("completed", "failed", "cancelled", "awaiting_approval")
        status_code = 286 if run_row.status in terminal_statuses else 200
        return html, status_code

    return render_template(
        "recipes/run_status.html",
        run=run_row,
        recipe=recipe_cls,
        db_row=db_recipe,
        editor_brands=editor_brands,
        editor_personas=editor_personas,
    )


# ---------------------------------------------------------------------------
# Run status JSON (for programmatic polling)
# ---------------------------------------------------------------------------

@recipes_bp.route("/run/<int:run_id>/status.json")
@login_required
def run_status_json(run_id):
    """Return run progress as JSON (for HTMX or JS polling)."""
    run_row = RecipeRun.query.filter_by(
        id=run_id, user_id=current_user.id
    ).first_or_404()

    return jsonify({
        "id": run_row.id,
        "status": run_row.status,
        "steps_completed": run_row.steps_completed,
        "total_steps": run_row.total_steps,
        "current_step_label": run_row.current_step_label,
        "progress_pct": run_row.progress_pct,
        "outputs": run_row.outputs,
        "error": run_row.error_message,
        "cost": run_row.retail_cost if not current_user.is_admin else run_row.cost,
    })


# ---------------------------------------------------------------------------
# Run history (all past runs for the current user)
# ---------------------------------------------------------------------------

@recipes_bp.route("/history/")
@login_required
def history():
    """Show the user's recipe run history."""
    # Reap stale runs so the history page shows accurate statuses
    try:
        _reap_stale_runs()
    except Exception:
        logger.debug("Stale run reaper skipped (non-critical)", exc_info=True)

    page = safe_int(request.args.get("page"), 1)
    per_page = 20

    query = RecipeRun.query.filter_by(user_id=current_user.id)\
        .order_by(RecipeRun.created_at.desc())

    # Optional filter by recipe slug
    slug_filter = request.args.get("recipe")
    if slug_filter:
        recipe_row = Recipe.query.filter_by(slug=slug_filter).first()
        if recipe_row:
            query = query.filter_by(recipe_id=recipe_row.id)

    # Optional filter by status
    status_filter = request.args.get("status")
    if status_filter in ("pending", "running", "completed", "failed", "cancelled", "awaiting_approval"):
        query = query.filter_by(status=status_filter)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    runs = pagination.items

    # Load recipe names for display (include inactive so history entries for
    # hidden stub recipes still show their names correctly)
    from ..recipes import get_all_recipes
    recipe_map = {r.slug: r for r in get_all_recipes(include_inactive=True)}
    db_recipes = {r.id: r for r in Recipe.query.all()}

    return render_template(
        "recipes/history.html",
        runs=runs,
        pagination=pagination,
        recipe_map=recipe_map,
        db_recipes=db_recipes,
        slug_filter=slug_filter,
        status_filter=status_filter,
    )
