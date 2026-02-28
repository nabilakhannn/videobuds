"""Post editing routes (HTMX partials)."""

from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Brand, Campaign, Post
from ..services.prompt_service import build_prompt
from ..services.model_service import get_model_choices, get_cheapest_price, has_free_tier

posts_bp = Blueprint("posts", __name__)


def _model_context(current_model="nano-banana"):
    """Return template context dict for the model picker component."""
    image_models = get_model_choices("image")
    price = get_cheapest_price(current_model) if not has_free_tier(current_model) else 0.00
    return {
        "image_models": image_models,
        "current_model": current_model,
        "current_model_price": price,
    }


def _get_post_or_create(campaign_id, day):
    """Get a post by campaign_id and day, creating it if it doesn't exist."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    post = Post.query.filter_by(
        campaign_id=campaign.id, day_number=day
    ).first()

    if not post:
        post = Post(
            campaign_id=campaign.id,
            day_number=day,
            status="draft",
        )
        if campaign.start_date:
            post.scheduled_date = campaign.start_date + timedelta(days=day - 1)
        db.session.add(post)
        db.session.commit()

    return campaign, post


@posts_bp.route("/campaigns/<int:campaign_id>/posts/<int:day>", methods=["GET"])
@login_required
def get_post(campaign_id, day):
    """Return post editor HTML partial (for HTMX)."""
    campaign, post = _get_post_or_create(campaign_id, day)

    return render_template(
        "components/post_editor.html",
        campaign=campaign,
        post=post,
        day=day,
        **_model_context(),
    )


@posts_bp.route("/campaigns/<int:campaign_id>/posts/<int:day>", methods=["POST"])
@login_required
def update_post(campaign_id, day):
    """Update post fields and handle actions (save, approve, reject)."""
    campaign, post = _get_post_or_create(campaign_id, day)
    brand = db.session.get(Brand, campaign.brand_id)

    # Save form fields
    if "caption" in request.form:
        post.caption = request.form.get("caption", "").strip()

    if "style_preset" in request.form:
        post.style_preset = request.form.get("style_preset", "").strip() or None

    if "custom_prompt" in request.form:
        post.custom_prompt = request.form.get("custom_prompt", "").strip() or None

    if "content_pillar" in request.form:
        post.content_pillar = request.form.get("content_pillar", "").strip()

    if "image_type" in request.form:
        post.image_type = request.form.get("image_type", "").strip()

    # Auto-build image_prompt from style preset + brand context
    style = post.style_preset or (campaign.style_preset if campaign else None) or "minimalist"
    post.image_prompt = build_prompt(style, brand, post, custom_prompt=post.custom_prompt)

    # Handle action
    action = request.form.get("action", "save")

    if action == "approve" and post.image_url:
        post.status = "approved"
    elif action == "reject" and post.image_url:
        post.status = "rejected"

    post.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    # AI agent: learn from approval/rejection feedback (best-effort)
    if action in ("approve", "reject") and post.image_url and brand:
        try:
            from ..services.agent_service import learn_from_feedback
            learn_from_feedback(brand, post, "approved" if action == "approve" else "rejected")
        except Exception:
            pass

    return render_template(
        "components/post_editor.html",
        campaign=campaign,
        post=post,
        day=day,
        **_model_context(),
    )
