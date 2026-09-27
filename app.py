import os

from flask import Flask, render_template, request
from flask_login import current_user
from flask_wtf.csrf import CSRFError

from config import config_by_name
from extensions import csrf, db, login_manager, migrate
from models import User
from tools.auth.routes import bp as auth_bp
from tools.construction_assistant.routes import bp as construction_assistant_bp
from tools.doc_qa.routes import bp as doc_qa_bp
from tools.site_report.routes import bp as site_report_bp


def create_app(test_config=None):
    """Create and configure the Mate Flask application."""
    app = Flask(__name__)

    if test_config is None:
        config_name = os.getenv("FLASK_CONFIG", "development")
        app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))
    else:
        app.config.from_mapping(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be configured before starting Mate.")

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(site_report_bp)
    app.register_blueprint(construction_assistant_bp)
    app.register_blueprint(doc_qa_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.before_request
    def require_authenticated_user():
        """Keep prototype tools behind the new identity boundary."""
        public_endpoints = {"auth.login", "auth.register", "static"}
        if request.endpoint and request.endpoint not in public_endpoints and not current_user.is_authenticated:
            return login_manager.unauthorized()
        return None

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        return render_template("error.html", message="Your form expired. Please try again."), 400

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/account")
    def account():
        return render_template("account.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
