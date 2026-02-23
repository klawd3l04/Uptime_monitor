from datetime import datetime as dt
from app.models import db

class Monitor(db.Model):
    """
    Represents a web target being monitored.
    
    A reference to a user and a custom check interval are maintained to allow 
    for tiered service levels or specific needs.
    """
    __tablename__ = 'monitors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    interval_seconds = db.Column(db.Integer, default=60, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=dt.utcnow)
    
    # Relationships with cascading delete to ensure no orphaned data remains
    incidents = db.relationship('Incident', backref='monitor', lazy=True, cascade="all, delete-orphan")
    uptime_stats = db.relationship('MonitorUptime', backref='monitor', uselist=False, cascade="all, delete-orphan")

class Incident(db.Model):
    """
    Logs state change events (UP/DOWN).
    
    Events are stored separately from real-time status to maintain a verifiable 
    audit trail of site reliability over time.
    """
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('monitors.id'), nullable=False)
    event_type = db.Column(db.String(20), nullable=False) # 'DOWN', 'UP'
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=dt.utcnow)

class MonitorUptime(db.Model):
    """
    Aggregated uptime metrics for fast dashboard rendering.
    
    Maintains a counter updated by the Processor worker instead of 
    calculating stats on the fly.
    """
    __tablename__ = 'monitor_uptime_stats'
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('monitors.id'), nullable=False, unique=True)
    total_checks = db.Column(db.Integer, default=0)
    up_checks = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=dt.utcnow)
