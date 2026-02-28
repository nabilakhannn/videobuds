"""Persona management routes — create, edit, list, delete user personas."""

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ..extensions import db
from ..models.user_persona import UserPersona
from ..security import safe_int

personas_bp = Blueprint("personas", __name__, url_prefix="/personas")


# ---------------------------------------------------------------------------
# List all personas
# ---------------------------------------------------------------------------

@personas_bp.route("/")
@login_required
def index():
    """Show all personas for the current user."""
    personas = (
        UserPersona.query
        .filter_by(user_id=current_user.id)
        .order_by(UserPersona.is_default.desc(), UserPersona.created_at.desc())
        .all()
    )
    return render_template("personas/index.html", personas=personas)


# ---------------------------------------------------------------------------
# Create new persona (wizard)
# ---------------------------------------------------------------------------

@personas_bp.route("/new/", methods=["GET", "POST"])
@login_required
def create():
    """Multi-step persona creation wizard."""
    if request.method == "GET":
        return render_template("personas/wizard.html")

    # POST — save new persona
    name = request.form.get("name", "").strip()
    if not name:
        flash("Please give your persona a name.", "error")
        return render_template("personas/wizard.html"), 400

    persona = UserPersona(
        user_id=current_user.id,
        name=name,
        tone=request.form.get("tone", "").strip(),
        voice_style=request.form.get("voice_style", "").strip(),
        bio=request.form.get("bio", "").strip(),
        industry=request.form.get("industry", "").strip(),
        target_audience=request.form.get("target_audience", "").strip(),
        writing_guidelines=request.form.get("writing_guidelines", "").strip(),
    )

    # JSON list fields
    keywords = request.form.get("brand_keywords", "").strip()
    if keywords:
        persona.brand_keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    avoid = request.form.get("avoid_words", "").strip()
    if avoid:
        persona.avoid_words = [w.strip() for w in avoid.split(",") if w.strip()]

    phrases = request.form.get("sample_phrases", "").strip()
    if phrases:
        persona.sample_phrases = [p.strip() for p in phrases.split("\n") if p.strip()]

    # If this is the user's first persona, make it default
    existing_count = UserPersona.query.filter_by(user_id=current_user.id).count()
    if existing_count == 0:
        persona.is_default = True

    # Build AI prompt summary
    persona.ai_prompt_summary = _build_ai_summary(persona)

    db.session.add(persona)
    db.session.commit()

    flash(f'Persona "{persona.name}" created!', "success")
    return redirect(url_for("personas.index"))


# ---------------------------------------------------------------------------
# Edit persona
# ---------------------------------------------------------------------------

@personas_bp.route("/<int:persona_id>/edit/", methods=["GET", "POST"])
@login_required
def edit(persona_id):
    """Edit an existing persona."""
    persona = UserPersona.query.filter_by(
        id=persona_id, user_id=current_user.id
    ).first_or_404()

    if request.method == "GET":
        return render_template("personas/edit.html", persona=persona)

    # POST — update
    persona.name = request.form.get("name", persona.name).strip()
    persona.tone = request.form.get("tone", "").strip()
    persona.voice_style = request.form.get("voice_style", "").strip()
    persona.bio = request.form.get("bio", "").strip()
    persona.industry = request.form.get("industry", "").strip()
    persona.target_audience = request.form.get("target_audience", "").strip()
    persona.writing_guidelines = request.form.get("writing_guidelines", "").strip()

    keywords = request.form.get("brand_keywords", "").strip()
    persona.brand_keywords = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []

    avoid = request.form.get("avoid_words", "").strip()
    persona.avoid_words = [w.strip() for w in avoid.split(",") if w.strip()] if avoid else []

    phrases = request.form.get("sample_phrases", "").strip()
    persona.sample_phrases = [p.strip() for p in phrases.split("\n") if p.strip()] if phrases else []

    persona.ai_prompt_summary = _build_ai_summary(persona)

    db.session.commit()
    flash(f'Persona "{persona.name}" updated.', "success")
    return redirect(url_for("personas.index"))


# ---------------------------------------------------------------------------
# Set default persona
# ---------------------------------------------------------------------------

@personas_bp.route("/<int:persona_id>/set-default/", methods=["POST"])
@login_required
def set_default(persona_id):
    """Set a persona as the default for this user."""
    persona = UserPersona.query.filter_by(
        id=persona_id, user_id=current_user.id
    ).first_or_404()

    # Clear all defaults for this user
    UserPersona.query.filter_by(user_id=current_user.id).update({"is_default": False})
    persona.is_default = True
    db.session.commit()

    flash(f'"{persona.name}" is now your default persona.', "success")
    return redirect(url_for("personas.index"))


# ---------------------------------------------------------------------------
# Delete persona
# ---------------------------------------------------------------------------

@personas_bp.route("/<int:persona_id>/delete/", methods=["POST"])
@login_required
def delete(persona_id):
    """Delete a persona."""
    persona = UserPersona.query.filter_by(
        id=persona_id, user_id=current_user.id
    ).first_or_404()

    name = persona.name
    db.session.delete(persona)
    db.session.commit()

    flash(f'Persona "{name}" deleted.', "success")
    return redirect(url_for("personas.index"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_ai_summary(persona):
    """Build a compact AI-ready prompt summary from the persona fields."""
    parts = []

    if persona.name:
        parts.append(f"Persona: {persona.name}")
    if persona.bio:
        parts.append(f"About: {persona.bio}")
    if persona.industry:
        parts.append(f"Industry: {persona.industry}")
    if persona.target_audience:
        parts.append(f"Audience: {persona.target_audience}")
    if persona.tone:
        parts.append(f"Tone: {persona.tone}")
    if persona.voice_style:
        parts.append(f"Voice: {persona.voice_style}")
    if persona.brand_keywords:
        parts.append(f"Key words to use: {', '.join(persona.brand_keywords)}")
    if persona.avoid_words:
        parts.append(f"Words to avoid: {', '.join(persona.avoid_words)}")
    if persona.sample_phrases:
        parts.append(f"Example phrases: {' | '.join(persona.sample_phrases[:5])}")
    if persona.writing_guidelines:
        parts.append(f"Guidelines: {persona.writing_guidelines}")

    return "\n".join(parts)
