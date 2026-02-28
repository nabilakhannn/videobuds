"""Campaign management routes."""

import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Brand, Campaign, Post
from ..models.user_persona import UserPersona
from ..services.prompt_service import build_prompt
from ..services.analytics_service import track
from ..security import safe_int

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/campaigns")

# Image types that rotate across posts
IMAGE_TYPES = ["ugc", "studio", "detail", "lifestyle", "cgi", "flatlay"]


@campaigns_bp.route("/", methods=["GET"])
@login_required
def list_campaigns():
    """List campaigns for the active brand (or all) with pagination."""
    active_brand = Brand.query.filter_by(user_id=current_user.id, is_active=True).first()
    page = request.args.get("page", 1, type=int)
    per_page = 12

    query = Campaign.query.filter_by(user_id=current_user.id)
    if active_brand:
        query = query.filter_by(brand_id=active_brand.id)
    query = query.order_by(Campaign.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    brands = Brand.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "campaigns/list.html",
        campaigns_list=pagination.items,
        active_brand=active_brand,
        brands=brands,
        pagination=pagination,
    )


@campaigns_bp.route("/new", methods=["GET"])
@login_required
def new_campaign():
    """Render the new campaign form."""
    active_brand = Brand.query.filter_by(user_id=current_user.id, is_active=True).first()
    brands = Brand.query.filter_by(user_id=current_user.id).all()
    personas = UserPersona.query.filter_by(user_id=current_user.id).order_by(UserPersona.name).all()

    return render_template(
        "campaigns/new.html",
        active_brand=active_brand,
        brands=brands,
        personas=personas,
    )


@campaigns_bp.route("/", methods=["POST"])
@login_required
def create_campaign():
    """Create a campaign with N posts, rotating pillars and image types."""
    name = request.form.get("name", "").strip()
    if not name:
        flash("Campaign name is required.", "error")
        return redirect(url_for("campaigns.new_campaign"))

    # Determine the brand
    brand_id = request.form.get("brand_id")
    if brand_id:
        brand = Brand.query.filter_by(id=int(brand_id), user_id=current_user.id).first()
    else:
        brand = Brand.query.filter_by(user_id=current_user.id, is_active=True).first()

    if not brand:
        flash("Please select or activate a brand first.", "error")
        return redirect(url_for("campaigns.new_campaign"))

    # Parse start_date
    start_date_str = request.form.get("start_date", "")
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        flash("Valid start date is required (YYYY-MM-DD).", "error")
        return redirect(url_for("campaigns.new_campaign"))

    style_preset = request.form.get("style_preset", "").strip() or None
    intention = request.form.get("intention", "").strip() or None
    post_count = int(request.form.get("post_count", 30))
    post_count = max(1, min(post_count, 365))  # Clamp between 1 and 365

    end_date = start_date + timedelta(days=post_count - 1)

    # Create the campaign
    campaign = Campaign(
        brand_id=brand.id,
        user_id=current_user.id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        style_preset=style_preset,
        intention=intention,
        post_count=post_count,
        status="draft",
    )
    db.session.add(campaign)
    db.session.flush()  # Get the campaign.id

    # Get brand content pillars for rotation
    pillars = brand.pillars if brand.pillars else ["general"]

    # Create N post rows
    for day in range(1, post_count + 1):
        scheduled_date = start_date + timedelta(days=day - 1)
        content_pillar = pillars[(day - 1) % len(pillars)]
        image_type = IMAGE_TYPES[(day - 1) % len(IMAGE_TYPES)]

        post = Post(
            campaign_id=campaign.id,
            day_number=day,
            scheduled_date=scheduled_date,
            content_pillar=content_pillar,
            image_type=image_type,
            style_preset=style_preset,
            status="draft",
        )
        # Auto-generate image prompt from style preset + brand context
        post.image_prompt = build_prompt(
            style_preset or "minimalist", brand, post
        )
        db.session.add(post)

    db.session.commit()

    # Resolve persona (optional)
    persona_id = safe_int(request.form.get("persona_id"))
    persona = None
    if persona_id:
        persona = UserPersona.query.filter_by(
            id=persona_id, user_id=current_user.id
        ).first()

    # AI agent: plan campaign content — fills captions and scene descriptions (best-effort)
    try:
        from ..services.agent_service import plan_campaign
        plan_campaign(brand, campaign, persona=persona)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Agent campaign planning failed: {e}")

    track(current_user.id, "campaign_created", {
        "campaign_id": campaign.id, "post_count": post_count,
        "style_preset": style_preset or "none",
    })
    flash(f"Campaign '{name}' created with {post_count} posts.", "success")
    return redirect(url_for("campaigns.calendar", campaign_id=campaign.id))


@campaigns_bp.route("/<int:campaign_id>/calendar", methods=["GET"])
@login_required
def calendar(campaign_id):
    """Render the calendar grid with all posts -- the main campaign UI."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    posts = Post.query.filter_by(campaign_id=campaign.id)\
        .order_by(Post.day_number).all()

    brand = db.session.get(Brand, campaign.brand_id)

    # Build calendar data: group posts by week for grid rendering
    weeks = []
    current_week = []
    for post in posts:
        current_week.append(post)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
    if current_week:
        weeks.append(current_week)

    # Campaign stats
    total = len(posts)
    draft_count = sum(1 for p in posts if p.status == "draft")
    generated_count = sum(1 for p in posts if p.status == "generated")
    approved_count = sum(1 for p in posts if p.status == "approved")
    rejected_count = sum(1 for p in posts if p.status == "rejected")

    return render_template(
        "campaigns/calendar.html",
        campaign=campaign,
        brand=brand,
        posts=posts,
        weeks=weeks,
        total=total,
        draft_count=draft_count,
        generated_count=generated_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
    )


@campaigns_bp.route("/<int:campaign_id>/delete", methods=["POST"])
@login_required
def delete_campaign(campaign_id):
    """Delete a campaign and all its posts."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    campaign_name = campaign.name
    db.session.delete(campaign)
    db.session.commit()

    flash(f"Campaign '{campaign_name}' deleted.", "success")
    return redirect(url_for("campaigns.list_campaigns"))
