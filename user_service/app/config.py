import os

# Critical secrets must be loaded from the environment.
# Fail-fast to avoid running in an insecure or misconfigured state.
try:
    SECRET_KEY = os.environ['SECRET_KEY']
    INTERNAL_API_KEY = os.environ['INTERNAL_API_KEY']
except KeyError as e:
    # During testing, fallback is allowed to avoid complex setup
    if os.environ.get('FLASK_ENV') != 'testing':
        raise RuntimeError(f"Missing mandatory environment variable: {e.args[0]}")
    SECRET_KEY = 'testing-key'
    INTERNAL_API_KEY = 'testing-internal-key'

# Database configuration logic - Supports local, docker, and testing (SQLite)
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_USER = os.environ.get('POSTGRES_USER', 'uptime_user')
DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'uptime_password')
DB_NAME = os.environ.get('POSTGRES_DB', 'uptime_db')

# Use DATABASE_URL if provided (Standard practice for Heroku/CI/K8s)
DEFAULT_DB_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}'
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', DEFAULT_DB_URI)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Performance: Connection Pooling & Pre-ping to handle transient DB issues.
# Pre-ping ensures a stale connection is not used.
SQLALCHEMY_ENGINE_OPTIONS = {}
if not SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20
    }
