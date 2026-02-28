"""API routes for AJAX/HTMX interactions."""

import json
import os
import uuid
from flask import Blueprint, request, redirect, url_for, jsonify, current_app, render_template, abort
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Brand, Campaign, Post, Generation, ReferenceImage
from ..security import safe_int, validate_upload

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/brands/switch", methods=["POST"])
@login_required
def switch_brand():
    """Switch the active brand."""
    brand_id = safe_int(request.form.get("brand_id"))
    if not brand_id:
        return redirect(url_for("dashboard.index"))

    brand = Brand.query.filter_by(
        id=brand_id, user_id=current_user.id
    ).first_or_404()

    # Deactivate all brands for this user
    Brand.query.filter_by(user_id=current_user.id).update({"is_active": False})

    # Activate the selected brand
    brand.is_active = True
    db.session.commit()

    # A01: Validate referrer is same-origin before redirecting (OWASP)
    from ..security import safe_referrer
    return redirect(safe_referrer(fallback_endpoint="dashboard.index"))


@api_bp.route("/prompt/preview", methods=["POST"])
@login_required
def prompt_preview():
    """Given a style_preset and brand_id, return a generated prompt text as JSON."""
    style_preset = request.form.get("style_preset", "").strip()
    brand_id = request.form.get("brand_id")

    brand = None
    bid = safe_int(brand_id)
    if bid:
        brand = Brand.query.filter_by(
            id=bid, user_id=current_user.id
        ).first()

    if not brand:
        brand = Brand.query.filter_by(
            user_id=current_user.id, is_active=True
        ).first()

    if not brand:
        return jsonify({
            "status": "error",
            "message": "No brand found. Please create or select a brand first.",
        }), 400

    # Build a prompt preview based on the brand profile and style preset
    brand_name = brand.name
    visual_style = brand.visual_style or "modern and clean"
    target_audience = brand.target_audience or "general audience"
    never_do = brand.never_do or ""

    pillars = brand.pillars
    pillar_text = ", ".join(pillars) if pillars else "lifestyle"

    colors = brand.colors
    color_text = ", ".join(colors) if colors else "brand colors"

    # Build the prompt
    prompt_parts = []

    if style_preset:
        prompt_parts.append(f"Style: {style_preset}.")

    prompt_parts.append(
        f"Create a social media image for {brand_name}."
    )
    prompt_parts.append(
        f"Visual style: {visual_style}."
    )
    prompt_parts.append(
        f"Target audience: {target_audience}."
    )
    prompt_parts.append(
        f"Content themes: {pillar_text}."
    )
    prompt_parts.append(
        f"Color palette: {color_text}."
    )

    if never_do:
        prompt_parts.append(f"Avoid: {never_do}.")

    prompt_parts.append(
        "The image should be high quality, suitable for Instagram, "
        "with a 9:16 portrait aspect ratio."
    )

    generated_prompt = " ".join(prompt_parts)

    return jsonify({
        "status": "ok",
        "prompt": generated_prompt,
        "brand_name": brand_name,
        "style_preset": style_preset,
    })


@api_bp.route("/campaigns/<int:campaign_id>/stats", methods=["GET"])
@login_required
def campaign_stats(campaign_id):
    """Return campaign statistics as JSON."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    total_posts = Post.query.filter_by(campaign_id=campaign.id).count()
    draft_count = Post.query.filter_by(campaign_id=campaign.id, status="draft").count()
    generating_count = Post.query.filter_by(campaign_id=campaign.id, status="generating").count()
    generated_count = Post.query.filter_by(campaign_id=campaign.id, status="generated").count()
    approved_count = Post.query.filter_by(campaign_id=campaign.id, status="approved").count()
    rejected_count = Post.query.filter_by(campaign_id=campaign.id, status="rejected").count()

    # Generation stats
    total_generations = Generation.query.filter_by(campaign_id=campaign.id).count()
    successful_generations = Generation.query.filter_by(
        campaign_id=campaign.id, status="success"
    ).count()
    failed_generations = Generation.query.filter_by(
        campaign_id=campaign.id, status="error"
    ).count()

    # Admins see actual cost, regular users see retail cost
    cost_col = Generation.cost if current_user.is_admin else Generation.retail_cost
    total_cost = db.session.query(db.func.sum(cost_col)).filter(
        Generation.campaign_id == campaign.id,
        Generation.status == "success",
    ).scalar() or 0.0

    return jsonify({
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "status": campaign.status,
        "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
        "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
        "posts": {
            "total": total_posts,
            "draft": draft_count,
            "generating": generating_count,
            "generated": generated_count,
            "approved": approved_count,
            "rejected": rejected_count,
        },
        "generations": {
            "total": total_generations,
            "successful": successful_generations,
            "failed": failed_generations,
        },
        "total_cost": round(total_cost, 2),
    })


ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@api_bp.route("/references/<int:campaign_id>/upload", methods=["POST"])
@login_required
def upload_reference(campaign_id):
    """Upload a reference image for a campaign's mood board."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    file = request.files.get("file")
    # OWASP A04 — defence-in-depth: ext + magic bytes + size
    ok, ext, err = validate_upload(file, ALLOWED_IMAGE_EXT, "Reference image")
    if not ok:
        return jsonify({"status": "error", "message": err}), 400

    # Save to uploads folder
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "references", str(campaign_id))
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    # Create DB record
    ref = ReferenceImage(
        brand_id=campaign.brand_id,
        campaign_id=campaign.id,
        file_path=file_path,
        purpose=request.form.get("purpose", "mood"),
    )
    db.session.add(ref)
    db.session.commit()

    web_url = f"/static/uploads/references/{campaign_id}/{filename}"
    return jsonify({
        "status": "ok",
        "id": ref.id,
        "url": web_url,
    })


@api_bp.route("/references/<int:campaign_id>", methods=["GET"])
@login_required
def list_references(campaign_id):
    """List reference images for a campaign."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    refs = ReferenceImage.query.filter_by(campaign_id=campaign.id).all()
    items = []
    for ref in refs:
        # Build web URL from file_path
        parts = ref.file_path.split("/references/")
        web_url = f"/static/uploads/references/{parts[-1]}" if len(parts) > 1 else ""
        items.append({
            "id": ref.id,
            "url": web_url,
            "purpose": ref.purpose,
        })

    return jsonify({"status": "ok", "references": items})


@api_bp.route("/references/<int:ref_id>/delete", methods=["POST"])
@login_required
def delete_reference(ref_id):
    """Delete a reference image."""
    ref = db.session.get(ReferenceImage, ref_id)
    if not ref:
        return jsonify({"status": "error", "message": "Not found."}), 404
    # Verify ownership through campaign
    campaign = Campaign.query.filter_by(
        id=ref.campaign_id, user_id=current_user.id
    ).first_or_404()

    if ref.file_path and os.path.exists(ref.file_path):
        os.remove(ref.file_path)

    db.session.delete(ref)
    db.session.commit()
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Brand-level Photo Library endpoints
# ---------------------------------------------------------------------------

@api_bp.route("/brands/<int:brand_id>/photos/upload", methods=["POST"])
@login_required
def upload_brand_photo(brand_id):
    """Upload a photo to a brand's photo library."""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()

    file = request.files.get("file")
    # OWASP A04 — defence-in-depth: ext + magic bytes + size
    ok, ext, err = validate_upload(file, ALLOWED_IMAGE_EXT, "Brand photo")
    if not ok:
        return jsonify({"status": "error", "message": err}), 400

    purpose = request.form.get("purpose", "product")
    if purpose not in ("product", "personal", "inspiration"):
        purpose = "product"

    # Save to uploads/brand_photos/<brand_id>/
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "brand_photos", str(brand_id))
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    ref = ReferenceImage(
        brand_id=brand.id,
        campaign_id=None,
        file_path=file_path,
        purpose=purpose,
    )
    db.session.add(ref)
    db.session.commit()

    web_url = f"/static/uploads/brand_photos/{brand_id}/{filename}"
    return jsonify({
        "status": "ok",
        "id": ref.id,
        "url": web_url,
        "purpose": purpose,
    })


@api_bp.route("/brands/<int:brand_id>/photos", methods=["GET"])
@login_required
def list_brand_photos(brand_id):
    """List all photos in a brand's library."""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    refs = ReferenceImage.query.filter_by(brand_id=brand.id, campaign_id=None).all()

    items = []
    for ref in refs:
        parts = ref.file_path.split("/brand_photos/")
        web_url = f"/static/uploads/brand_photos/{parts[-1]}" if len(parts) > 1 else ""
        items.append({
            "id": ref.id,
            "url": web_url,
            "purpose": ref.purpose,
        })

    return jsonify({"status": "ok", "photos": items})


@api_bp.route("/photos/<int:ref_id>/delete", methods=["POST"])
@login_required
def delete_brand_photo(ref_id):
    """Delete a brand photo."""
    ref = db.session.get(ReferenceImage, ref_id)
    if not ref:
        return jsonify({"status": "error", "message": "Not found."}), 404

    # Verify ownership through brand
    brand = Brand.query.filter_by(id=ref.brand_id, user_id=current_user.id).first_or_404()

    if ref.file_path and os.path.exists(ref.file_path):
        os.remove(ref.file_path)

    db.session.delete(ref)
    db.session.commit()
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# AI Agent endpoints (HTMX partials)
# ---------------------------------------------------------------------------

@api_bp.route("/agent/suggest-captions/<int:post_id>", methods=["POST"])
@login_required
def agent_suggest_captions(post_id):
    """Generate AI caption suggestions for a post. Returns HTML partial."""
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    campaign = Campaign.query.filter_by(
        id=post.campaign_id, user_id=current_user.id
    ).first_or_404()
    brand = db.session.get(Brand, campaign.brand_id)

    if not brand:
        return render_template("components/caption_suggestions.html", captions=[], error="No brand found.")

    # Persona-aware captions (Phase 41)
    from ..models import UserPersona
    persona = None
    pid = safe_int(request.form.get("persona_id"))
    if pid:
        persona = UserPersona.query.filter_by(id=pid, user_id=current_user.id).first()

    try:
        from ..services.agent_service import write_captions
        captions = write_captions(brand, post, campaign, persona=persona)
    except Exception as e:
        return render_template("components/caption_suggestions.html", captions=[], error=str(e))

    return render_template(
        "components/caption_suggestions.html",
        captions=captions,
        post=post,
        campaign=campaign,
    )


@api_bp.route("/agent/enhance-prompt/<int:post_id>", methods=["POST"])
@login_required
def agent_enhance_prompt(post_id):
    """Generate AI-enhanced image prompt for a post. Returns HTML partial."""
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    campaign = Campaign.query.filter_by(
        id=post.campaign_id, user_id=current_user.id
    ).first_or_404()
    brand = db.session.get(Brand, campaign.brand_id)

    if not brand:
        return render_template("components/prompt_enhanced.html", prompt="", error="No brand found.")

    # Persona-aware prompt (Phase 41)
    from ..models import UserPersona
    persona = None
    pid = safe_int(request.form.get("persona_id"))
    if pid:
        persona = UserPersona.query.filter_by(id=pid, user_id=current_user.id).first()

    try:
        from ..services.agent_service import build_smart_prompt
        enhanced = build_smart_prompt(brand, post, campaign, persona=persona)
    except Exception as e:
        return render_template("components/prompt_enhanced.html", prompt="", error=str(e))

    return render_template(
        "components/prompt_enhanced.html",
        prompt=enhanced,
        post=post,
        campaign=campaign,
    )


# ── Serve locally-saved output files (images / videos) ────────────────
@api_bp.route("/outputs/<path:filename>")
@login_required
def serve_output(filename):
    """Serve a file from references/outputs/ (generated images & videos).

    This is the fallback serving path when Kie.ai hosting is not configured.
    Files are saved here by tools/providers/google.py when KIE_API_KEY is absent.
    """
    from flask import send_from_directory
    output_dir = os.path.join(
        current_app.root_path, os.pardir, "references", "outputs"
    )
    output_dir = os.path.normpath(output_dir)
    return send_from_directory(output_dir, filename)


# ── AI Content Editor endpoint ────────────────────────────────────────
@api_bp.route("/recipes/chat", methods=["POST"])
@login_required
def recipe_editor_chat():
    """AI-powered content editor — refine recipe outputs with brand/persona.

    Accepts JSON body:
        content      (str)  — the text the user is editing
        instruction  (str)  — what they want changed
        brand_id     (int)  — optional brand for context
        persona_id   (int)  — optional persona for context
        history      (list) — optional conversation turns

    Returns JSON:
        refined_content  (str) — the updated text
        explanation      (str) — 1-3 sentence summary of changes
    """
    data = request.get_json(silent=True) or {}

    content = (data.get("content") or "").strip()
    instruction = (data.get("instruction") or "").strip()

    if not content:
        return jsonify({"status": "error", "message": "Content cannot be empty."}), 400
    if not instruction:
        return jsonify({"status": "error", "message": "Please enter an editing instruction."}), 400

    # Build brand/persona context strings
    brand_context = ""
    persona_context = ""

    bid = safe_int(data.get("brand_id"))
    if bid:
        brand = Brand.query.filter_by(id=bid, user_id=current_user.id).first()
        if brand:
            from ..recipes.base import BaseRecipe
            brand_context = BaseRecipe.build_brand_context(brand)

    pid = safe_int(data.get("persona_id"))
    if pid:
        from ..models import UserPersona
        persona = UserPersona.query.filter_by(id=pid, user_id=current_user.id).first()
        if persona:
            from ..recipes.base import BaseRecipe
            persona_context = BaseRecipe.build_persona_context(persona)

    history = data.get("history") or []

    from ..services.editor_service import refine_content

    try:
        result = refine_content(
            content=content,
            instruction=instruction,
            brand_context=brand_context,
            persona_context=persona_context,
            history=history,
        )
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except RuntimeError as re:
        return jsonify({"status": "error", "message": str(re)}), 502
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Editor chat error")
        return jsonify({"status": "error", "message": "Something went wrong. Please try again."}), 500

    return jsonify({
        "status": "ok",
        "refined_content": result["refined_content"],
        "explanation": result["explanation"],
    })


# ── Model catalog API ─────────────────────────────────────────────────
@api_bp.route("/models", methods=["GET"])
@login_required
def list_models():
    """Return model catalog as JSON. Supports ?type=image|video filter."""
    from ..services.model_service import get_model_choices
    model_type = request.args.get("type")  # "image", "video", or None for all
    if model_type in ("image", "video"):
        return jsonify({"models": get_model_choices(model_type)})
    # Return both
    from ..services.model_service import get_model_catalog
    return jsonify({
        "image_models": get_model_choices("image"),
        "video_models": get_model_choices("video"),
    })
