from app import db
from datetime import datetime

class RssFeed(db.Model):
    """Model to store RSS feed subscriptions"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1024), nullable=False, index=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    last_checked = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime)
    error_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_rss_feed_user'), nullable=True)

    # Relationship with content
    contents = db.relationship('AudioContent', backref='feed', lazy='dynamic')
    
    def __init__(self, url, title=None, description=None, user_id=None):
        self.url = url
        self.title = title
        self.description = description
        self.user_id = user_id
    
    def __repr__(self):
        return f'<RssFeed {self.title or self.url}>'
    
    @property
    def status(self):
        """Return the current status of the feed"""
        if not self.is_active:
            return "inactive"
        elif self.error_count > 3:
            return "error"
        else:
            return "active"