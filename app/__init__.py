from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name=None):
    """Application factory function to create and configure the Flask app"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default configuration
    app.config.from_object('app.config.Config')
    
    # Load environment specific configuration
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    
    # Load the instance config, if it exists
    app.config.from_pyfile('config.py', silent=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    limiter.init_app(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app