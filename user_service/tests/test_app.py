import pytest
import os
import json

# Force testing configuration BEFORE importing the app
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key-123'
os.environ['INTERNAL_API_KEY'] = 'test-internal-key-123'

from app.main import app
from app.models import db
from app.models.user import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_health_check(client):
    """Test the health endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_user_registration(client):
    """Test valid user registration and password hashing."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123"
    }
    response = client.post('/register', json=payload)
    assert response.status_code == 201
    assert 'id' in response.json
    
    # Verify persistence
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user is not None
        assert user.check_password("securepassword123")

def test_invalid_email_registration(client):
    """Test registration with an invalid email format."""
    payload = {
        "username": "testuser",
        "email": "invalid-email",
        "password": "securepassword123"
    }
    response = client.post('/register', json=payload)
    assert response.status_code == 400
    assert 'Invalid email format' in response.json['error']

def test_internal_endpoint_unauthorized(client):
    """Test that internal endpoints block requests without the secret key."""
    response = client.get('/all_monitors')
    assert response.status_code == 403
    assert 'Internal access only' in response.json['message']

def test_internal_endpoint_authorized(client):
    """Test successful internal access with valid X-Internal-API-Key."""
    headers = {'X-Internal-API-Key': 'test-internal-key-123'}
    response = client.get('/all_monitors', headers=headers)
    assert response.status_code == 200
