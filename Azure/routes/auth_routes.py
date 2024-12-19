from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Users
from . import auth_bp
import logging
from datetime import datetime

# Configure logging for audit logs
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Avoid adding multiple handlers if this code runs multiple times
if not audit_logger.handlers:
    file_handler = logging.FileHandler("audit.log")
    formatter = logging.Formatter(
        "%(asctime)s - USER: %(username)s - ACTION: %(action)s"
    )
    file_handler.setFormatter(formatter)
    audit_logger.addHandler(file_handler)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        if not username or not password:
            flash("Brugernavn og adgangskode er påkrævet.", "danger")
            return render_template("sign_up.html")
        try:
            hashed_password = generate_password_hash(password, method="pbkdf2:sha1")
            user = Users(username=username, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash("Registrering lykkedes! Log ind nu.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Registration failed: {e}", "danger")
    return render_template("sign_up.html")



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        remember = request.form.get("remember") == 'on'  # Capture the remember option

        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)

            # Log the successful login
            audit_logger.info(
                "User logged in",
                extra={
                    'username': username,
                    'action': 'LOGIN_SUCCESS'
                }
            )

            flash("Login successful.", "success")
            return redirect(url_for("main.home"))
        else:
            # Optionally log failed login attempts (not required)
            audit_logger.info(
                "Failed login attempt",
                extra={
                    'username': username,
                    'action': 'LOGIN_FAILED'
                }
            )
            flash("Invalid username or password.", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))