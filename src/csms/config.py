"""Configuration settings for the CSMS Flask application."""

import os


class BaseConfig:
    """Settings shared by all application environments."""

    APP_NAME = "Community Services Management System"
    # T16: Authoritative single source of truth for the official CSMS v1.0.0 release version
    APP_VERSION = "1.0.0"
    CURRENT_SPRINT = "Sprint 0 - Developer Onboarding"

    SECRET_KEY = os.environ.get(
        "CSMS_SECRET_KEY",
        "development-only-secret-key",
    )


class DevelopmentConfig(BaseConfig):
    """Local development configuration."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Automated testing configuration."""

    TESTING = True
    DEBUG = False
    SECRET_KEY = "testing-secret-key"