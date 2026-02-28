"""Brand management routes."""

import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Brand, BrandQuestionnaire
from ..services.analytics_service import track

brands_bp = Blueprint("brands", __name__, url_prefix="/brands")


@brands_bp.route("/", methods=["GET"])
@login_required
def list_brands():
    """List all brands for the current user with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = 12
    pagination = Brand.query.filter_by(user_id=current_user.id)\
        .order_by(Brand.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    active_brand = Brand.query.filter_by(user_id=current_user.id, is_active=True).first()
    return render_template(
        "brands/list.html",
        brands_list=pagination.items,
        pagination=pagination,
        active_brand=active_brand,
    )


@brands_bp.route("/new", methods=["GET"])
@login_required
def new_brand():
    """Render the new brand form."""
    return render_template("brands/new.html")


@brands_bp.route("/", methods=["POST"])
@login_required
def create_brand():
    """Create a new brand from form data."""
    name = request.form.get("name", "").strip()
    if not name:
        flash("Brand name is required.", "error")
        return redirect(url_for("brands.new_brand"))

    tagline = request.form.get("tagline", "").strip()
    visual_style = request.form.get("visual_style", "").strip()
    target_audience = request.form.get("target_audience", "").strip()
    never_do = request.form.get("never_do", "").strip()

    # Parse content_pillars from comma-separated string
    pillars_raw = request.form.get("content_pillars", "").strip()
    pillars = [p.strip() for p in pillars_raw.split(",") if p.strip()] if pillars_raw else []

    # Parse colors from JSON string
    colors_raw = request.form.get("colors", "").strip()
    try:
        colors = json.loads(colors_raw) if colors_raw else []
    except (json.JSONDecodeError, ValueError):
        colors = []

    # Parse hashtags from comma-separated string
    hashtags_raw = request.form.get("hashtags", "").strip()
    hashtags = [h.strip() for h in hashtags_raw.split(",") if h.strip()] if hashtags_raw else []

    brand = Brand(
        user_id=current_user.id,
        name=name,
        tagline=tagline,
        visual_style=visual_style,
        target_audience=target_audience,
        never_do=never_do,
        content_pillars=json.dumps(pillars),
        colors_json=json.dumps(colors),
        hashtags=json.dumps(hashtags),
    )

    # If this is the user's first brand, make it active
    existing_count = Brand.query.filter_by(user_id=current_user.id).count()
    if existing_count == 0:
        brand.is_active = True

    db.session.add(brand)
    db.session.commit()

    track(current_user.id, "brand_created", {"brand_id": brand.id, "method": "manual"})
    flash(f"Brand '{name}' created successfully.", "success")
    return redirect(url_for("brands.show_brand", brand_id=brand.id))


@brands_bp.route("/<int:brand_id>", methods=["GET"])
@login_required
def show_brand(brand_id):
    """Show brand detail / edit page."""
    from app.models.user_persona import UserPersona
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    active_brand = Brand.query.filter_by(user_id=current_user.id, is_active=True).first()
    personas = UserPersona.query.filter_by(user_id=current_user.id).order_by(UserPersona.name).all()
    return render_template("brands/detail.html", brand=brand,
                           active_brand=active_brand, personas=personas)


@brands_bp.route("/<int:brand_id>", methods=["POST"])
@login_required
def update_brand(brand_id):
    """Update brand fields."""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()

    brand.name = request.form.get("name", brand.name).strip()
    brand.tagline = request.form.get("tagline", brand.tagline or "").strip()
    brand.visual_style = request.form.get("visual_style", brand.visual_style or "").strip()
    brand.target_audience = request.form.get("target_audience", brand.target_audience or "").strip()
    brand.never_do = request.form.get("never_do", brand.never_do or "").strip()

    # Parse content_pillars from comma-separated string
    pillars_raw = request.form.get("content_pillars", "").strip()
    if pillars_raw:
        pillars = [p.strip() for p in pillars_raw.split(",") if p.strip()]
        brand.content_pillars = json.dumps(pillars)

    # Parse colors from JSON string
    colors_raw = request.form.get("colors", "").strip()
    if colors_raw:
        try:
            brand.colors_json = json.dumps(json.loads(colors_raw))
        except (json.JSONDecodeError, ValueError):
            pass

    # Parse hashtags from comma-separated string
    hashtags_raw = request.form.get("hashtags", "").strip()
    if hashtags_raw:
        hashtags = [h.strip() for h in hashtags_raw.split(",") if h.strip()]
        brand.hashtags = json.dumps(hashtags)

    # Optional fields
    if "caption_template" in request.form:
        brand.caption_template = request.form.get("caption_template", "").strip()
    if "brand_doc" in request.form:
        brand.brand_doc = request.form.get("brand_doc", "").strip()

    brand.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash(f"Brand '{brand.name}' updated.", "success")
    return redirect(url_for("brands.show_brand", brand_id=brand.id))


@brands_bp.route("/<int:brand_id>/activate", methods=["POST"])
@login_required
def activate_brand(brand_id):
    """Set a brand as the active brand, deactivating all others."""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()

    # Deactivate all brands for this user
    Brand.query.filter_by(user_id=current_user.id).update({"is_active": False})

    # Activate the selected brand
    brand.is_active = True
    db.session.commit()

    flash(f"'{brand.name}' is now your active brand.", "success")

    # A01: Validate referrer is same-origin before redirecting (OWASP)
    from ..security import safe_referrer
    return redirect(safe_referrer(fallback_endpoint="brands.list_brands"))


@brands_bp.route("/<int:brand_id>", methods=["DELETE"])
@login_required
def delete_brand(brand_id):
    """Delete a brand."""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    brand_name = brand.name

    db.session.delete(brand)
    db.session.commit()

    flash(f"Brand '{brand_name}' deleted.", "success")
    return jsonify({"status": "ok", "message": f"Brand '{brand_name}' deleted."})


@brands_bp.route("/questionnaire", methods=["GET"])
@login_required
def questionnaire():
    """Render the brand questionnaire page."""
    return render_template("brands/questionnaire.html")


@brands_bp.route("/questionnaire", methods=["POST"])
@login_required
def process_questionnaire():
    """Process simplified questionnaire and create brand with AI research."""
    brand_name = request.form.get("brand_name", "").strip()
    if not brand_name:
        flash("Brand name is required.", "error")
        return redirect(url_for("brands.questionnaire"))

    brand_description = request.form.get("brand_description", "").strip()
    industry = request.form.get("industry", "").strip()  # comma-separated
    visual_vibe = request.form.get("visual_vibe", "").strip()  # comma-separated
    target_audience = request.form.get("target_audience", "").strip()  # comma-separated
    website_url = request.form.get("website_url", "").strip()
    social_url = request.form.get("social_url", "").strip()

    # Build initial brand_doc from the minimal input
    brand_doc = f"# {brand_name}\n\n{brand_description}"
    if industry:
        brand_doc += f"\n\nIndustry: {industry}"
    if visual_vibe:
        brand_doc += f"\n\nVisual Style: {visual_vibe}"
    if target_audience:
        brand_doc += f"\n\nTarget Audience: {target_audience}"

    # Create the brand with what we know
    brand = Brand(
        user_id=current_user.id,
        name=brand_name,
        target_audience=target_audience,
        visual_style=visual_vibe,
        brand_doc=brand_doc,
    )

    # If this is the user's first brand, make it active
    existing_count = Brand.query.filter_by(user_id=current_user.id).count()
    if existing_count == 0:
        brand.is_active = True

    db.session.add(brand)
    db.session.flush()

    # Store questionnaire answers for reference
    quick_answers = {
        "brand_description": brand_description,
        "industry": industry,
        "visual_vibe": visual_vibe,
        "target_audience": target_audience,
        "website_url": website_url,
        "social_url": social_url,
    }
    for key, answer_text in quick_answers.items():
        if answer_text:
            q_record = BrandQuestionnaire(
                brand_id=brand.id,
                question_key=key,
                answer=answer_text,
            )
            db.session.add(q_record)

    db.session.commit()

    # AI agent: deep research and brand analysis (best-effort)
    try:
        from ..services.agent_service import analyze_brand
        analyze_brand(
            brand,
            description=brand_description,
            industry=industry,
            visual_vibe=visual_vibe,
            target_audience_segments=target_audience,
            website_url=website_url,
            social_url=social_url,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Agent brand analysis failed: {e}")

    track(current_user.id, "brand_created", {"brand_id": brand.id, "method": "questionnaire"})
    flash(f"Brand '{brand_name}' created! AI has built your brand identity.", "success")
    return redirect(url_for("brands.show_brand", brand_id=brand.id))


@brands_bp.route("/<int:brand_id>/photos", methods=["GET"])
@login_required
def photo_library(brand_id):
    """Render the categorized photo library for a brand."""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    from ..models import ReferenceImage
    photos = ReferenceImage.query.filter_by(brand_id=brand.id, campaign_id=None).all()

    # Group by purpose
    product_photos = [p for p in photos if p.purpose == "product"]
    personal_photos = [p for p in photos if p.purpose == "personal"]
    inspiration_photos = [p for p in photos if p.purpose in ("inspiration", "mood")]

    return render_template(
        "brands/photo_library.html",
        brand=brand,
        product_photos=product_photos,
        personal_photos=personal_photos,
        inspiration_photos=inspiration_photos,
    )


@brands_bp.route("/<int:brand_id>/generate-doc", methods=["POST"])
@login_required
def generate_brand_doc(brand_id):
    """Auto-generate a brand document from the brand's structured fields."""
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()

    pillars = json.loads(brand.content_pillars) if brand.content_pillars else []
    colors = json.loads(brand.colors_json) if brand.colors_json else []
    hashtags = json.loads(brand.hashtags) if brand.hashtags else []

    brand_doc = f"""# {brand.name} Brand Guidelines

## Brand Identity

### Tagline
{brand.tagline or 'Not specified'}

### Target Audience
{brand.target_audience or 'Not specified'}

## Visual Identity

### Style
{brand.visual_style or 'Not specified'}

### Brand Colors
{', '.join(colors) if colors else 'Not specified'}

## Content Strategy

### Content Pillars
{chr(10).join('- ' + p for p in pillars) if pillars else 'Not specified'}

### Hashtags
{' '.join(hashtags) if hashtags else 'Not specified'}

### Things to Avoid
{brand.never_do or 'Not specified'}
"""

    brand.brand_doc = brand_doc
    brand.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Brand document generated.", "success")
    return redirect(url_for("brands.show_brand", brand_id=brand.id))
