#!/usr/bin/env python3
"""
Blog2Audio - Application Entry Point
Run this file to start the development server
"""
import os
from dotenv import load_dotenv
from app import create_app
from flask import render_template
import datetime

# Load environment variables from .env file
load_dotenv()

# Create the app with the specified configuration
app = create_app(os.getenv('FLASK_CONFIG') or 'development')

# Add global context processors
@app.context_processor
def inject_now():
    """Add current datetime to all templates"""
    return {'now': datetime.datetime.utcnow()}

@app.context_processor
def inject_config():
    """Add app config to all templates"""
    return {'config': app.config}

# Add error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    # port = int(os.environ.get('PORT', 5000))
    
    # Start the development server
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=app.config['DEBUG'])