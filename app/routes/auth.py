"""Authentication routes."""

from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import db
from ..models.user import User
from ..services.analytics_service import track, identify
from ..security import (
    rate_limit,
    safe_redirect,
    validate_password,
    validate_email,
    security_log,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@rate_limit(max_calls=15, period=60)  # 15 attempts per minute per IP
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                security_log("login_blocked_inactive", email=email)
                flash("Your account has been deactivated. Contact an administrator.", "error")
                return render_template("auth/login.html")
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user)
            security_log("login_success", email=email, user_id=user.id)
            track(user.id, "user_logged_in")
            # A01: Validate redirect target to prevent open-redirect attacks
            next_page = request.args.get("next")
            return redirect(safe_redirect(next_page))

        # A09: Log failed login attempt for security monitoring
        security_log("login_failed", email=email)
        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@rate_limit(max_calls=5, period=60)  # 5 registrations per minute per IP
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")

        # A07: Validate email format (OWASP)
        email_valid, email_error = validate_email(email)
        if not email_valid:
            flash(email_error, "error")
            return render_template("auth/register.html")

        # A07: Validate password strength (OWASP ASVS §2.1.1)
        pw_valid, pw_error = validate_password(password)
        if not pw_valid:
            flash(pw_error, "error")
            return render_template("auth/register.html")

        if not display_name:
            flash("Display name is required.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html")

        user = User(email=email, display_name=display_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        security_log("user_registered", email=email, user_id=user.id)
        track(user.id, "user_registered", {"email": email})
        identify(user.id, {"email": email, "display_name": display_name})

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Account settings — change display name, email, or password."""
    if request.method == "POST":
        action = request.form.get("action", "profile")

        if action == "profile":
            new_name = request.form.get("display_name", "").strip()
            new_email = request.form.get("email", "").strip().lower()

            if not new_name:
                flash("Display name is required.", "error")
                return render_template("auth/account.html")

            if not new_email:
                flash("Email is required.", "error")
                return render_template("auth/account.html")

            # Check email uniqueness (if changed)
            if new_email != current_user.email:
                existing = User.query.filter_by(email=new_email).first()
                if existing:
                    flash("That email is already in use.", "error")
                    return render_template("auth/account.html")

            current_user.display_name = new_name
            current_user.email = new_email
            db.session.commit()
            flash("Profile updated.", "success")

        elif action == "password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            if not current_user.check_password(current_pw):
                security_log("password_change_failed", email=current_user.email,
                             reason="wrong_current_password")
                flash("Current password is incorrect.", "error")
                return render_template("auth/account.html")

            # A07: Validate new password strength (OWASP ASVS §2.1.1)
            pw_valid, pw_error = validate_password(new_pw)
            if not pw_valid:
                flash(pw_error, "error")
                return render_template("auth/account.html")

            if new_pw != confirm_pw:
                flash("New passwords do not match.", "error")
                return render_template("auth/account.html")

            current_user.set_password(new_pw)
            db.session.commit()
            security_log("password_changed", email=current_user.email,
                         user_id=current_user.id)
            flash("Password changed successfully.", "success")

        return redirect(url_for("auth.account"))

    return render_template("auth/account.html")


@auth_bp.route("/logout")
@login_required
def logout():
    security_log("logout", email=current_user.email, user_id=current_user.id)
    logout_user()
    return redirect(url_for("auth.login"))
