from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app import db, limiter
from app.models.audio_content import AudioContent
from app.models.rss_feed import RssFeed
from app.services.rss_service import RssService
from app.routes.main import process_content_background

rss_bp = Blueprint('rss', __name__, url_prefix='/rss')

@rss_bp.route('/feeds', methods=['GET'])
def list_feeds():
    """List user's RSS feeds"""
    feeds = RssFeed.query.all()  # In the future, filter by user
    return render_template('rss/feeds.html', feeds=feeds)

@rss_bp.route('/feeds/add', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def add_feed():
    """Add a new RSS feed"""
    if request.method == 'POST':
        url = request.form.get('url')
        
        if not url:
            flash('Please enter a valid RSS feed URL', 'error')
            return redirect(url_for('rss.add_feed'))
        
        # Check if feed already exists
        existing = RssFeed.query.filter_by(url=url).first()
        if existing:
            flash('This feed is already in your list', 'warning')
            return redirect(url_for('rss.list_feeds'))
        
        try:
            # Add the feed
            rss_service = RssService()
            feed = rss_service.add_feed(url)
            
            flash(f'Successfully added feed: {feed.title or url}', 'success')
            return redirect(url_for('rss.list_feeds'))
        except ValueError as e:
            flash(f'Error adding feed: {str(e)}', 'error')
            return redirect(url_for('rss.add_feed'))
    
    return render_template('rss/add_feed.html')

@rss_bp.route('/feeds/<int:feed_id>/refresh', methods=['POST'])
def refresh_feed(feed_id):
    """Manually refresh a feed"""
    feed = RssFeed.query.get_or_404(feed_id)
    
    rss_service = RssService()
    new_contents = rss_service.fetch_feed_content(feed_id)
    
    if new_contents:
        flash(f'Found {len(new_contents)} new posts', 'success')
    else:
        flash('No new content found', 'info')
    
    return redirect(url_for('rss.list_feeds'))

@rss_bp.route('/feeds/<int:feed_id>/toggle', methods=['POST'])
def toggle_feed(feed_id):
    """Toggle active status of a feed"""
    feed = RssFeed.query.get_or_404(feed_id)
    feed.is_active = not feed.is_active
    db.session.commit()
    
    status = 'activated' if feed.is_active else 'deactivated'
    flash(f'Feed {feed.title or feed.url} has been {status}', 'success')
    
    return redirect(url_for('rss.list_feeds'))

@rss_bp.route('/feeds/<int:feed_id>/delete', methods=['POST'])
def delete_feed(feed_id):
    """Delete a feed"""
    feed = RssFeed.query.get_or_404(feed_id)
    title = feed.title or feed.url
    
    db.session.delete(feed)
    db.session.commit()
    
    flash(f'Feed {title} has been deleted', 'success')
    return redirect(url_for('rss.list_feeds'))

@rss_bp.route('/content', methods=['GET'])
def feed_content():
    """Display all content from user's feeds"""
    # Get all content from RSS feeds, ordered by newest first
    contents = AudioContent.query.filter(AudioContent.feed_id.isnot(None))\
                              .order_by(AudioContent.created_at.desc())\
                              .all()
    
    return render_template('rss/feed_content.html', contents=contents)

@rss_bp.route('/content/<int:content_id>/process', methods=['POST'])
def process_content(content_id):
    """Process a specific content item"""
    content = AudioContent.query.get_or_404(content_id)
    
    # Start processing in background
    from app.routes.main import process_content_background
    from run import app
    
    voice = 'onyx'  # Default voice or get from user preferences
    
    # Use a thread to process in background
    import threading
    thread = threading.Thread(
        target=process_content_background,
        args=(content.id, voice, app)
    )
    thread.daemon = True
    thread.start()
    
    flash('Content is being processed. Please check back soon.', 'info')
    return redirect(url_for('rss.feed_content'))