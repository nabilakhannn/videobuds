"""Image generation routes."""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Brand, Campaign, Post, Generation, ReferenceImage, UserPersona
from ..services.prompt_service import build_prompt
from ..security import safe_int
from ..services.analytics_service import track
from ..services.model_service import get_model_choices, get_cheapest_price, has_free_tier

# Add project root to sys.path so we can import tools
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from tools.create_image import generate_ugc_image
from tools.config import get_cost, get_actual_cost

generate_bp = Blueprint("generate", __name__, url_prefix="/generate")


def _model_context(current_model="nano-banana"):
    """Return template context dict for the model picker component."""
    image_models = get_model_choices("image")
    price = get_cheapest_price(current_model) if not has_free_tier(current_model) else 0.00
    return {
        "image_models": image_models,
        "current_model": current_model,
        "current_model_price": price,
    }


def _run_generation(post, campaign, brand, model=None, provider=None,
                    persona=None):
    """Run image generation for a single post. Returns (success, error_message)."""
    # Always use AI agent to write a proper image-gen prompt.
    # The post.image_prompt (scene from campaign planning) is used as context
    # by build_smart_prompt, not as the final prompt.
    prompt = post.custom_prompt  # only skip AI if user wrote their own prompt
    if not prompt:
        try:
            from ..services.agent_service import build_smart_prompt
            prompt = build_smart_prompt(brand, post, campaign, persona=persona)
        except Exception:
            # Fallback to template if AI fails
            style = post.style_preset or (campaign.style_preset if campaign else None) or "minimalist"
            prompt = build_prompt(style, brand, post)
        post.image_prompt = prompt

    # Use form-selected model/provider, falling back to defaults
    model = model or "nano-banana"
    provider = provider or None  # let get_actual_cost/get_cost resolve default
    actual_cost = get_actual_cost(model, provider)
    retail_cost = get_cost(model, provider)

    # Create generation record
    generation = Generation(
        post_id=post.id,
        campaign_id=campaign.id,
        brand_id=brand.id if brand else None,
        user_id=current_user.id,
        prompt=prompt,
        model=model,
        provider=provider,
        status="processing",
        cost=actual_cost,
        retail_cost=retail_cost,
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(generation)
    post.status = "generating"
    db.session.commit()

    # AI-powered photo selection from brand library + campaign references
    try:
        from ..services.agent_service import select_photos
        reference_paths = select_photos(brand, post, campaign, persona=persona)
    except Exception:
        # Fallback: gather all brand + campaign photos
        refs = ReferenceImage.query.filter(
            db.or_(
                ReferenceImage.campaign_id == campaign.id,
                db.and_(
                    ReferenceImage.brand_id == brand.id,
                    ReferenceImage.campaign_id.is_(None),
                ),
            )
        ).all()
        reference_paths = [r.file_path for r in refs if r.file_path and os.path.exists(r.file_path)]

    try:
        result = generate_ugc_image(
            prompt=prompt,
            reference_paths=reference_paths or None,
            aspect_ratio="9:16",
            model=model,
            provider=provider,
        )

        result_url = result.get("result_url", "")

        # Save image locally for web serving
        generated_folder = current_app.config["GENERATED_FOLDER"]
        os.makedirs(generated_folder, exist_ok=True)
        local_filename = f"post_{post.id}_{generation.id}.png"
        local_path = os.path.join(generated_folder, local_filename)

        # Determine source: check local_path first, then result_url if it's a file path
        source_path = result.get("local_path", "")
        if not source_path or not os.path.exists(source_path):
            # Google provider returns local file path as result_url
            if result_url and not result_url.startswith("http") and os.path.exists(result_url):
                source_path = result_url

        import shutil
        if source_path and os.path.exists(source_path):
            shutil.copy2(source_path, local_path)
            web_url = f"/static/generated/{local_filename}"
        elif result_url.startswith("http"):
            local_path = ""
            web_url = result_url
        else:
            local_path = ""
            web_url = ""

        # Update generation record
        generation.status = "success"
        generation.result_url = result_url
        generation.local_path = local_path
        generation.completed_at = datetime.now(timezone.utc)

        # Update post
        post.image_url = web_url
        post.image_path = local_path if local_path else None
        post.status = "generated"
        post.updated_at = datetime.now(timezone.utc)

        # Update campaign total cost (actual cost for internal tracking)
        campaign.total_cost = (campaign.total_cost or 0.0) + actual_cost

        db.session.commit()

        track(current_user.id, "image_generated", {
            "post_id": post.id, "model": model, "provider": provider, "cost": actual_cost,
        })
        return True, None

    except Exception as e:
        generation.status = "error"
        generation.error_message = str(e)
        generation.completed_at = datetime.now(timezone.utc)
        post.status = "draft"
        db.session.commit()
        return False, str(e)


@generate_bp.route("/post/<int:post_id>", methods=["POST"])
@login_required
def generate_single(post_id):
    """Generate an image for a single post (JSON API)."""
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"status": "error", "message": "Post not found."}), 404
    campaign = Campaign.query.filter_by(
        id=post.campaign_id, user_id=current_user.id
    ).first_or_404()
    brand = db.session.get(Brand, campaign.brand_id)

    # Accept model/provider from request
    sel_model = request.form.get("model") or request.json.get("model", "nano-banana") if request.is_json else request.form.get("model", "nano-banana")
    sel_provider = request.form.get("provider") or (request.json.get("provider") if request.is_json else None)

    # Persona-aware generation (Phase 41)
    persona = None
    pid = safe_int(request.form.get("persona_id") or (request.json.get("persona_id") if request.is_json else None))
    if pid:
        persona = UserPersona.query.filter_by(id=pid, user_id=current_user.id).first()

    success, error = _run_generation(post, campaign, brand, model=sel_model, provider=sel_provider, persona=persona)

    if success:
        return jsonify({
            "status": "success",
            "post_id": post.id,
            "image_url": post.image_url,
            "cost": get_cost(sel_model, sel_provider),
        })
    else:
        return jsonify({"status": "error", "message": error}), 500


@generate_bp.route("/campaign/<int:campaign_id>/day/<int:day>", methods=["POST"])
@login_required
def generate_for_day(campaign_id, day):
    """Generate image for a specific day. Saves form data first, returns HTML partial."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()
    brand = db.session.get(Brand, campaign.brand_id)

    post = Post.query.filter_by(campaign_id=campaign.id, day_number=day).first()
    if not post:
        post = Post(campaign_id=campaign.id, day_number=day, status="draft")
        if campaign.start_date:
            from datetime import timedelta
            post.scheduled_date = campaign.start_date + timedelta(days=day - 1)
        db.session.add(post)
        db.session.commit()

    # Save form data if present (from the editor form)
    sel_model = "nano-banana"
    sel_provider = None
    if request.form:
        if "caption" in request.form:
            post.caption = request.form.get("caption", "").strip()
        if "style_preset" in request.form:
            post.style_preset = request.form.get("style_preset", "").strip() or None
        if "custom_prompt" in request.form:
            post.custom_prompt = request.form.get("custom_prompt", "").strip() or None
        sel_model = request.form.get("model", "nano-banana")
        sel_provider = request.form.get("provider") or None
        db.session.commit()

    # Persona-aware generation (Phase 41)
    persona = None
    pid = safe_int(request.form.get("persona_id"))
    if pid:
        persona = UserPersona.query.filter_by(id=pid, user_id=current_user.id).first()

    # Run generation with selected model
    _run_generation(post, campaign, brand, model=sel_model, provider=sel_provider, persona=persona)

    # Return HTML partial for HTMX
    return render_template(
        "components/post_editor.html",
        campaign=campaign,
        post=post,
        day=day,
        **_model_context(sel_model),
    )


def _bulk_generate_worker(app, campaign_id, brand_id, post_ids, user_id):
    """Background worker that generates images for a list of posts."""
    import threading
    with app.app_context():
        from flask_login import AnonymousUserMixin

        campaign = db.session.get(Campaign, campaign_id)
        brand = db.session.get(Brand, brand_id) if brand_id else None
        if not campaign:
            return

        job_count = 0
        for post_id in post_ids:
            post = db.session.get(Post, post_id)
            if not post:
                continue
            try:
                # Inline generation logic (can't use _run_generation because
                # it relies on current_user which isn't available in thread)
                prompt = post.custom_prompt
                if not prompt:
                    try:
                        from ..services.agent_service import build_smart_prompt
                        prompt = build_smart_prompt(brand, post, campaign)
                    except Exception:
                        style = post.style_preset or (campaign.style_preset if campaign else None) or "minimalist"
                        prompt = build_prompt(style, brand, post)
                    post.image_prompt = prompt

                model = "nano-banana"
                actual_cost = get_actual_cost(model, None)
                retail_cost = get_cost(model, None)

                generation = Generation(
                    post_id=post.id,
                    campaign_id=campaign.id,
                    brand_id=brand.id if brand else None,
                    user_id=user_id,
                    prompt=prompt,
                    model=model,
                    provider=None,
                    status="processing",
                    cost=actual_cost,
                    retail_cost=retail_cost,
                    started_at=datetime.now(timezone.utc),
                )
                db.session.add(generation)
                post.status = "generating"
                db.session.commit()

                # Gather reference images
                refs = ReferenceImage.query.filter(
                    db.or_(
                        ReferenceImage.campaign_id == campaign.id,
                        db.and_(
                            ReferenceImage.brand_id == (brand.id if brand else None),
                            ReferenceImage.campaign_id.is_(None),
                        ),
                    )
                ).all()
                reference_paths = [r.file_path for r in refs if r.file_path and os.path.exists(r.file_path)]

                result = generate_ugc_image(
                    prompt=prompt,
                    reference_paths=reference_paths or None,
                    aspect_ratio="9:16",
                    model=model,
                )

                result_url = result.get("result_url", "")

                # Save image locally
                generated_folder = app.config.get("GENERATED_FOLDER", os.path.join(str(PROJECT_ROOT), "app", "static", "generated"))
                os.makedirs(generated_folder, exist_ok=True)
                local_filename = f"post_{post.id}_{generation.id}.png"
                local_path = os.path.join(generated_folder, local_filename)

                source_path = result.get("local_path", "")
                if not source_path or not os.path.exists(source_path):
                    if result_url and not result_url.startswith("http") and os.path.exists(result_url):
                        source_path = result_url

                import shutil
                if source_path and os.path.exists(source_path):
                    shutil.copy2(source_path, local_path)
                    post.image_url = f"/static/generated/{local_filename}"
                elif result_url:
                    post.image_url = result_url
                else:
                    post.image_url = None

                generation.image_url = post.image_url
                generation.status = "success"
                generation.completed_at = datetime.now(timezone.utc)
                post.status = "review"
                db.session.commit()
                job_count += 1
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Bulk gen failed for post {post_id}: {e}")
                post.status = "draft"
                db.session.commit()

        # Update campaign status
        remaining = Post.query.filter(
            Post.campaign_id == campaign.id,
            Post.status.in_(["draft", "generating"]),
        ).count()
        campaign.status = "review" if remaining == 0 else "draft"
        db.session.commit()


@generate_bp.route("/campaign/<int:campaign_id>", methods=["POST"])
@login_required
def generate_campaign(campaign_id):
    """Bulk generate images for all draft/rejected posts in a campaign (async)."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    # Find all posts that need generation
    posts = Post.query.filter(
        Post.campaign_id == campaign.id,
        Post.status.in_(["draft", "rejected"]),
    ).order_by(Post.day_number).all()

    if not posts:
        flash("No posts to generate.", "info")
        return redirect(url_for("campaigns.calendar", campaign_id=campaign_id))

    campaign.status = "generating"
    db.session.commit()

    # Launch background thread
    import threading
    app = current_app._get_current_object()
    post_ids = [p.id for p in posts]
    thread = threading.Thread(
        target=_bulk_generate_worker,
        args=(app, campaign.id, campaign.brand_id, post_ids, current_user.id),
        daemon=True,
    )
    thread.start()

    flash(f"Generating images for {len(posts)} posts in the background. Refresh to see progress.", "success")
    return redirect(url_for("campaigns.calendar", campaign_id=campaign_id))


@generate_bp.route("/status/<int:campaign_id>", methods=["GET"])
@login_required
def generation_status(campaign_id):
    """Return generation status for HTMX polling."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    total = Post.query.filter_by(campaign_id=campaign.id).count()

    completed = Post.query.filter(
        Post.campaign_id == campaign.id,
        Post.status.in_(["generated", "approved"]),
    ).count()

    generating = Post.query.filter_by(
        campaign_id=campaign.id, status="generating"
    ).count()

    errors = Generation.query.filter_by(
        campaign_id=campaign.id, status="error"
    ).count()

    if generating > 0:
        status = "generating"
    elif errors > 0 and completed == 0:
        status = "error"
    elif completed == total:
        status = "complete"
    else:
        status = "partial"

    return jsonify({
        "total": total,
        "completed": completed,
        "generating": generating,
        "errors": errors,
        "status": status,
    })
