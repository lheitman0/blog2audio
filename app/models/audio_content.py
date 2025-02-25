from app import db
from datetime import datetime
import uuid
import os

class AudioContent(db.Model):
    """Model to store processed blog content and audio metadata"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1024), index=True, nullable=False)
    title = db.Column(db.String(255))
    content_hash = db.Column(db.String(64), unique=True, index=True)
    # Text content fields
    original_text = db.Column(db.Text)
    processed_text = db.Column(db.Text)
    word_count = db.Column(db.Integer)
    
    # Audio file fields
    filename = db.Column(db.String(255))
    file_path = db.Column(db.String(1024))
    duration = db.Column(db.Float)  # In seconds
    voice = db.Column(db.String(50))
    # Add this to the AudioContent class
    feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id', name='fk_audio_content_feed'), nullable=True)

    # feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id'), nullable=True)
    # Processing metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Status tracking
    is_processing = db.Column(db.Boolean, default=False)
    is_processed = db.Column(db.Boolean, default=False)
    error = db.Column(db.Text, nullable=True)
    
    def __init__(self, url, original_text=None, title=None, user_id=None):
        self.url = url
        self.original_text = original_text
        self.title = title
        self.user_id = user_id
        self.filename = f"{uuid.uuid4().hex}.mp3"
    
    def __repr__(self):
        return f'<AudioContent {self.title}>'
    
    @property
    def web_path(self):
        """Return the web-accessible path to the audio file"""
        if self.file_path:
            return os.path.join('/', self.file_path)
        return None
    
    @property
    def status(self):
        """Return the current status of processing"""
        if not self.is_processed and not self.is_processing:
            return "pending"
        elif self.is_processing:
            return "processing"
        elif self.is_processed and not self.error:
            return "completed"
        else:
            return "error"


class User(db.Model):
    """User model for authentication and tracking usage"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    feeds = db.relationship('RssFeed', backref='user', lazy='dynamic') 
    # User preferences
    preferred_voice = db.Column(db.String(50))
    
    # Usage tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    conversion_count = db.Column(db.Integer, default=0)
    
    # Relationships
    audio_contents = db.relationship('AudioContent', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def increment_conversion_count(self):
        """Increment the conversion count for this user"""
        self.conversion_count += 1
        db.session.commit()