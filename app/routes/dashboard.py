"""Dashboard routes."""

from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from flask_login import login_required, current_user
from ..models import Brand, Campaign, Generation
from ..models.user import User
from ..extensions import db
from ..services.model_service import get_model_choices

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    if current_user.is_admin and not session.get("admin_user_view"):
        return _admin_dashboard()
    return _user_dashboard()


@dashboard_bp.route("/admin/toggle-user-view", methods=["POST"])
@login_required
def toggle_user_view():
    if not current_user.is_admin:
        return redirect(url_for("dashboard.index"))
    session["admin_user_view"] = not session.get("admin_user_view", False)
    return redirect(url_for("dashboard.index"))


def _user_dashboard():
    """Regular user dashboard — personal stats only."""
    brands = Brand.query.filter_by(user_id=current_user.id).all()
    active_brand = Brand.query.filter_by(user_id=current_user.id, is_active=True).first()

    recent_campaigns = Campaign.query.filter_by(user_id=current_user.id)\
        .order_by(Campaign.created_at.desc()).limit(5).all()

    # Cost summary — admins in user-view still see retail
    if current_user.is_admin and not session.get("admin_user_view"):
        total_spent = db.session.query(db.func.sum(Generation.cost))\
            .filter_by(user_id=current_user.id, status="success").scalar() or 0.0
    else:
        total_spent = db.session.query(db.func.sum(Generation.retail_cost))\
            .filter_by(user_id=current_user.id, status="success").scalar() or 0.0

    total_images = Generation.query.filter_by(
        user_id=current_user.id, status="success"
    ).count()

    stats = {
        "total_brands": len(brands),
        "total_campaigns": Campaign.query.filter_by(user_id=current_user.id).count(),
        "images_generated": total_images,
        "total_spent": total_spent,
    }

    return render_template(
        "dashboard/index.html",
        brands=brands,
        active_brand=active_brand,
        recent_campaigns=recent_campaigns,
        stats=stats,
    )


def _admin_dashboard():
    """Admin dashboard — platform-wide stats."""
    total_users = User.query.count()
    total_brands = Brand.query.count()
    total_campaigns = Campaign.query.count()
    total_generations = Generation.query.filter_by(status="success").count()

    total_revenue = db.session.query(db.func.sum(Generation.retail_cost))\
        .filter_by(status="success").scalar() or 0.0
    total_actual_cost = db.session.query(db.func.sum(Generation.cost))\
        .filter_by(status="success").scalar() or 0.0
    profit = total_revenue - total_actual_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

    # Recent generations with user and campaign info
    recent_generations = db.session.query(Generation, User, Campaign)\
        .join(User, Generation.user_id == User.id)\
        .outerjoin(Campaign, Generation.campaign_id == Campaign.id)\
        .filter(Generation.status == "success")\
        .order_by(Generation.created_at.desc())\
        .limit(10).all()

    # Top users by generation count
    top_users = db.session.query(
        User,
        db.func.count(Generation.id).label("gen_count"),
        db.func.coalesce(db.func.sum(Generation.retail_cost), 0).label("total_spend"),
    ).join(Generation, Generation.user_id == User.id)\
     .filter(Generation.status == "success")\
     .group_by(User.id)\
     .order_by(db.desc("gen_count"))\
     .limit(5).all()

    stats = {
        "total_users": total_users,
        "total_brands": total_brands,
        "total_campaigns": total_campaigns,
        "total_generations": total_generations,
        "total_revenue": total_revenue,
        "total_actual_cost": total_actual_cost,
        "profit": profit,
        "margin": margin,
    }

    return render_template(
        "dashboard/admin.html",
        stats=stats,
        recent_generations=recent_generations,
        top_users=top_users,
    )


@dashboard_bp.route("/admin/users")
@login_required
def admin_users():
    """Admin user list with management actions."""
    if not current_user.is_admin:
        return redirect(url_for("dashboard.index"))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("dashboard/admin_users.html", users=users)


@dashboard_bp.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@login_required
def toggle_user(user_id):
    """Deactivate or reactivate a user account."""
    if not current_user.is_admin:
        return redirect(url_for("dashboard.index"))

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("dashboard.admin_users"))
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "error")
        return redirect(url_for("dashboard.admin_users"))

    user.is_active = not user.is_active
    db.session.commit()
    action = "reactivated" if user.is_active else "deactivated"
    # A09: Log admin action for audit trail (OWASP)
    from ..security import security_log
    security_log("admin_toggle_user", admin_email=current_user.email,
                 target_email=user.email, action=action)
    flash(f"User {user.email} has been {action}.", "success")
    return redirect(url_for("dashboard.admin_users"))


@dashboard_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    """Permanently delete a user and all their data."""
    if not current_user.is_admin:
        return redirect(url_for("dashboard.index"))

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("dashboard.admin_users"))
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("dashboard.admin_users"))

    email = user.email
    # A09: Log admin action for audit trail (OWASP)
    from ..security import security_log
    security_log("admin_delete_user", admin_email=current_user.email,
                 target_email=email, target_id=user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User {email} has been permanently deleted.", "success")
    return redirect(url_for("dashboard.admin_users"))


@dashboard_bp.route("/pricing")
@login_required
def pricing():
    """Standalone pricing page showing all models, providers, and costs."""
    image_models = get_model_choices("image")
    video_models = get_model_choices("video")
    return render_template(
        "dashboard/pricing.html",
        image_models=image_models,
        video_models=video_models,
    )
