from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from extensions import db
from models import User
from tools.auth.forms import LoginForm, RegistrationForm

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


def _safe_next_url(target):
    if not target:
        return None
    test_url = urlparse(urljoin(request.host_url, target))
    if test_url.scheme in {"http", "https"} and test_url.netloc == urlparse(request.host_url).netloc:
        return target
    return None


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = User.normalise_email(form.email.data)
        if User.query.filter_by(email=email).first():
            flash("Unable to create an account with that email.", "error")
        else:
            user = User(email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your account has been created.", "success")
            return redirect(url_for("home"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    next_url = _safe_next_url(request.args.get("next"))
    if form.validate_on_submit():
        email = User.normalise_email(form.email.data)
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(form.password.data) or not user.is_active:
            flash("Invalid email or password.", "error")
        else:
            login_user(user)
            return redirect(next_url or url_for("home"))
    return render_template("auth/login.html", form=form, next_url=next_url)


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
