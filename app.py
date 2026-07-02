"""Application factory and local development entry point for iHIS."""

import logging
import click
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, redirect, render_template, url_for
from flask_login import current_user

from config import CONFIGS
from extensions import csrf, db, login_manager, migrate
from routes import BLUEPRINTS


def create_app(config_name=None):
    """Build and configure an iHIS Flask application instance."""
    app = Flask(__name__)
    selected_config = config_name or "development"
    app.config.from_object(CONFIGS.get(selected_config, CONFIGS["development"]))

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    _configure_extensions(app)
    _configure_logging(app)
    _register_blueprints(app)
    _register_pages(app)
    _register_error_handlers(app)
    _register_cli(app)
    return app


def _configure_extensions(app):
    db.init_app(app)
    import models  # noqa: F401 - registers complete metadata for migrations
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        user = db.session.get(User, user_id)
        return user if user and user.is_active and not user.is_deleted else None


def _register_cli(app):
    @app.cli.command("seed-db")
    @click.option("--admin-password", envvar="SEED_ADMIN_PASSWORD", help="Initial admin password.")
    def seed_db_command(admin_password):
        """Seed roles, permissions, reference data, and the initial administrator."""
        from services.seed import seed_database
        result = seed_database(admin_password)
        click.echo(f"Database seeded. Admin username: {result['admin'].username}")
        if result["generated_password"]:
            click.echo(f"One-time generated password: {result['generated_password']}")
            click.echo("Store it securely; it will not be shown again.")


def _configure_logging(app):
    log_dir = Path(app.root_path) / "logs"
    log_dir.mkdir(exist_ok=True)
    handler = RotatingFileHandler(log_dir / "ihis.log", maxBytes=1_000_000, backupCount=5)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    handler.setLevel(getattr(logging, app.config["LOG_LEVEL"], logging.INFO))
    if not any(isinstance(item, RotatingFileHandler) for item in app.logger.handlers):
        app.logger.addHandler(handler)
    app.logger.setLevel(handler.level)
    app.logger.info("iHIS application initialized")


def _register_blueprints(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)


def _register_pages(app):
    @app.get("/")
    def dashboard():
        if current_user.is_authenticated:
            from services.auth_service import get_redirect_for_role
            return redirect(get_redirect_for_role(current_user))
        return redirect(url_for("auth.login"))

    if app.testing:
        @app.get("/_test/error")
        def test_error():
            raise RuntimeError("Intentional test error")


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        app.logger.exception("Unhandled application error")
        return render_template("errors/500.html"), 500


if __name__ == "__main__":
    create_app().run()
