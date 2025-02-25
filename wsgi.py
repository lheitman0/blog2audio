"""
Blog2Audio - Production WSGI Entry Point
This file is used by production WSGI servers like Gunicorn
"""
import os
from dotenv import load_dotenv
from app import create_app
import datetime
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Create the application with production config
app = create_app('production')

# Set up logging
if not app.debug and not app.testing:
    # Set up file logging if LOG_TO_STDOUT is not set to true
    if not os.environ.get('LOG_TO_STDOUT'):
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/blog2audio.log',
                                          maxBytes=10240,
                                          backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    else:
        # Stream logs to stdout for cloud platforms
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Blog2Audio startup')

# Add global context processors
@app.context_processor
def inject_now():
    """Add current datetime to all templates"""
    return {'now': datetime.datetime.utcnow()}

@app.context_processor
def inject_config():
    """Add app config to all templates"""
    return {'config': app.config}

# This is what WSGI servers import
application = app