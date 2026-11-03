"""Community Services Management System Flask application."""

from flask import Flask

from csms.config import DevelopmentConfig
from csms.db.database import init_db


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    """Create and configure the CSMS Flask application.

    Args:
        test_config: Optional configuration overrides used during testing.

    Returns:
        A configured Flask application.
    """
    app = Flask(__name__)

    app.config.from_object(DevelopmentConfig)

    if test_config is not None:
        app.config.update(test_config)

    # Initialize database tables if they do not exist
    database_path = str(app.config.get("DATABASE_PATH", "csms.sqlite"))
    init_db(database_path)

    from csms.ui.routes import main_blueprint

    app.register_blueprint(main_blueprint)

    return app