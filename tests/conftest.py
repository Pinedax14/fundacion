"""
Configuración base para tests
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app import create_app, db
from app.models import Usuario


@pytest.fixture
def app():
    """Create app for testing"""
    app, _ = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands"""
    return app.test_cli_runner()
