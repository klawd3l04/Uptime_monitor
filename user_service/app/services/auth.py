from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models.user import User
from app.config import INTERNAL_API_KEY

def token_required(f):
    """
    Protect public API endpoints using JWT.
    
    Verifies the signature and expiration of the token. Uses 'current_app'
    to stay decoupled from the global app instance.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Access token is required.'}), 401
        
        try:
            # Support both "Bearer <token>" and raw token formats
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'Authenticated user not found.'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired.'}), 401
        except Exception as e:
            return jsonify({'message': 'Authentication failed.', 'error': str(e)}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def internal_only(f):
    """
    Restrict access to internal service-to-service routes.
    
    Uses a shared secret key (INTERNAL_API_KEY) for fast trust evaluation
    within the private network.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-Internal-API-Key')
        if key != INTERNAL_API_KEY:
            logger_placeholder = current_app.logger
            logger_placeholder.warning("Unauthorized internal access attempt blocked.")
            return jsonify({'message': 'Forbidden: Internal access only.'}), 403
        return f(*args, **kwargs)
    return decorated
