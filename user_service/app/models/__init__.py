from flask_sqlalchemy import SQLAlchemy

# Global database object. 
# Initialize without an app to avoid circular imports.
db = SQLAlchemy()
