from flask import Flask, request, jsonify
import datetime
from datetime import datetime as dt
import jwt
import validators
import time
import os

from app.models import db
from app.models.user import User
from app.models.monitor import Monitor, Incident, MonitorUptime
from app.services.auth import token_required, internal_only
from app.config import (
    SQLALCHEMY_DATABASE_URI, 
    SQLALCHEMY_TRACK_MODIFICATIONS, 
    SQLALCHEMY_ENGINE_OPTIONS,
    SECRET_KEY
)

def create_app():
    """
    App factory to initialize the Flask application and extensions.
    """
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = SQLALCHEMY_ENGINE_OPTIONS
    app.config['SECRET_KEY'] = SECRET_KEY

    db.init_app(app)
    return app

app = create_app()

def init_db_with_retry():
    """
    Ensure database schema is present before handling traffic.
    
    Includes a retry loop to handle the database being 'started' but not 
    yet 'ready' during containerized boots.
    """
    if os.environ.get('FLASK_ENV') == 'testing':
        with app.app_context():
            db.create_all()
        return

    max_retries = 10
    for i in range(max_retries):
        try:
            with app.app_context():
                db.create_all()
                app.logger.info("Database tables verified.")
                return
        except Exception as e:
            app.logger.warning(f"Postgres connection attempt {i+1} failed ({e}). Retrying in 5s...")
            time.sleep(5)
    app.logger.error("FATAL: Could not establish database connection.")

# --- API Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    """Basic service health check."""
    return jsonify({"status": "healthy", "version": "1.5.2"}), 200

@app.route('/register', methods=['POST'])
def register():
    """Register a new user account with validation."""
    data = request.get_json()
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing required fields (username, email, password)'}), 400
    
    # Simple validation before hitting the DB
    if len(data['username']) < 3:
        return jsonify({'error': 'Username is too short.'}), 400
    if not validators.email(data['email']):
        return jsonify({'error': 'Invalid email format.'}), 400
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken.'}), 400

    try:
        new_user = User(username=data['username'], email=data['email'])
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'id': new_user.id, 'message': 'Account created successfully.'}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal registration failure.'}), 500

@app.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return a session token."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Credentials required.'}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password.'}), 401
    
    # Tokens expire after 24 hours
    token = jwt.encode({
        'user_id': user.id,
        'exp': dt.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'username': user.username,
        'email': user.email,
        'user_id': user.id
    }), 200

@app.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Returns the current user's profile and preferences."""
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'notification_email': current_user.notification_email or current_user.email,
        'slack_webhook_url': current_user.slack_webhook_url or ""
    }), 200

@app.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Updates user security settings and notification channels."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No updates provided.'}), 400
        
    try:
        if 'email' in data:
            if not validators.email(data['email']):
                return jsonify({'error': 'Invalid main email.'}), 400
            current_user.email = data['email']
        
        if 'notification_email' in data:
            if data['notification_email'] and not validators.email(data['notification_email']):
                return jsonify({'error': 'Invalid notification email.'}), 400
            current_user.notification_email = data['notification_email']
            
        if 'slack_webhook_url' in data:
            if data['slack_webhook_url'] and not validators.url(data['slack_webhook_url']):
                return jsonify({'error': 'Invalid Slack webhook URL.'}), 400
            current_user.slack_webhook_url = data['slack_webhook_url']
            
        if data.get('password'):
            if len(data['password']) < 6:
                return jsonify({'error': 'New password is too short.'}), 400
            current_user.set_password(data['password'])
            
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully.'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile.'}), 500

@app.route('/monitors', methods=['POST'])
@token_required
def create_monitor(current_user):
    """Add a new monitoring target with customized interval."""
    data = request.get_json()
    if not data or not data.get('url'):
        return jsonify({'error': 'URL is required.'}), 400
    
    # Ensure URL has a schema
    url = data['url']
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    if not validators.url(url):
        return jsonify({'error': 'Provided URL is invalid.'}), 400

    interval = data.get('interval_seconds', 60)
    if not isinstance(interval, int) or not (10 <= interval <= 86400):
        return jsonify({'error': 'Interval must be between 10s and 24h.'}), 400
        
    try:
        new_monitor = Monitor(
            user_id=current_user.id,
            url=url,
            interval_seconds=interval
        )
        db.session.add(new_monitor)
        db.session.flush() 
        
        # Initialize stats so the dashboard has a record to show
        new_stats = MonitorUptime(monitor_id=new_monitor.id)
        db.session.add(new_stats)
        
        db.session.commit()
        return jsonify({'id': new_monitor.id, 'message': 'Monitor initialized.'}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Database failure while creating monitor.'}), 500

@app.get('/monitors')
@token_required
def list_monitors(current_user):
    """List all monitors for the current user with aggregated uptime."""
    monitors = Monitor.query.filter_by(user_id=current_user.id).all()
    result = []
    for m in monitors:
        # Calculate uptime percentage from aggregated counters
        uptime = 100.0
        if m.uptime_stats and m.uptime_stats.total_checks > 0:
            uptime = (m.uptime_stats.up_checks / m.uptime_stats.total_checks) * 100
            
        result.append({
            "id": m.id, 
            "url": m.url, 
            "interval_seconds": m.interval_seconds, 
            "is_active": m.is_active,
            "uptime_percent": round(uptime, 2)
        })
    return jsonify(result), 200

# --- Internal Service Routes ---

@app.route('/monitors/<int:monitor_id>/stats', methods=['POST'])
@internal_only
def internal_update_stats(monitor_id):
    """
    Update uptime counters. Called by the Processor worker.
    """
    data = request.get_json()
    if not data or 'is_up' not in data:
        return jsonify({'error': 'Status payload missing.'}), 400
        
    try:
        stats = MonitorUptime.query.filter_by(monitor_id=monitor_id).first()
        if not stats:
            stats = MonitorUptime(monitor_id=monitor_id)
            db.session.add(stats)
        
        stats.total_checks += 1
        if data['is_up']:
            stats.up_checks += 1
        stats.last_updated = dt.utcnow()
        db.session.commit()
        return jsonify({'message': 'Persistent stats updated.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Aggregation failure: {e}'}), 500

@app.get('/all_monitors')
@internal_only
def internal_get_monitors():
    """Return all active monitors for the Pinger's scheduler."""
    monitors = Monitor.query.filter_by(is_active=True).all()
    return jsonify([
        {"id": m.id, "url": m.url, "interval_seconds": m.interval_seconds} 
        for m in monitors
    ]), 200

@app.route('/monitors/<int:monitor_id>/incidents', methods=['POST'])
@internal_only
def internal_log_incident(monitor_id):
    """Record a status transition (UP <-> DOWN). Called by Processor."""
    data = request.get_json()
    if not data or not data.get('event_type'):
        return jsonify({'error': 'Event type required.'}), 400
        
    try:
        new_incident = Incident(
            monitor_id=monitor_id,
            event_type=data['event_type'],
            details=data.get('details', '')
        )
        db.session.add(new_incident)
        db.session.commit()
        return jsonify({'message': 'Incident logged to audit trail.'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Logging failure: {e}'}), 500

# --- Standard Resource Management ---

@app.route('/monitors/<int:monitor_id>', methods=['DELETE'])
@token_required
def delete_monitor(current_user, monitor_id):
    """Delete a monitor and its history."""
    try:
        monitor = Monitor.query.filter_by(id=monitor_id, user_id=current_user.id).first()
        if not monitor:
            return jsonify({'error': 'Monitor not found.'}), 404
            
        db.session.delete(monitor)
        db.session.commit()
        return jsonify({'message': 'Monitor and history purged.'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete resource.'}), 500

@app.route('/monitors/<int:monitor_id>/incidents', methods=['GET'])
@token_required
def list_incidents(current_user, monitor_id):
    """Return recent incidents for a specific monitor."""
    monitor = Monitor.query.filter_by(id=monitor_id, user_id=current_user.id).first()
    if not monitor:
        return jsonify({'error': 'Monitor not found.'}), 404
        
    incidents = Incident.query.filter_by(monitor_id=monitor_id).order_by(Incident.timestamp.desc()).limit(100).all()
    return jsonify([
        {
            "id": i.id,
            "event_type": i.event_type,
            "details": i.details,
            "timestamp": i.timestamp.isoformat()
        } for i in incidents
    ]), 200

if __name__ == '__main__':
    # Ensure infrastructure is ready before binding the port
    init_db_with_retry()
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=FLASK_DEBUG)
