import os
from collections.abc import Generator
from unittest.mock import patch

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")

from page_analyzer.app import create_app


@pytest.fixture()
def app() -> Generator:
    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def mock_db_cursor():
    with patch("page_analyzer.routes.db_cursor") as mock:
        yield mock
