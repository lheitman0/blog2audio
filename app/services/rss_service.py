import feedparser
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging
from app import db
from app.models.rss_feed import RssFeed
from app.models.audio_content import AudioContent
from app.services.content_extractor import ContentExtractor

logger = logging.getLogger(__name__)

class RssService:
    """Service for managing RSS feeds and fetching content"""
    
    def __init__(self):
        pass
    
    def add_feed(self, url, user_id=None):
        """
        Add a new RSS feed and fetch initial data
        
        Args:
            url (str): URL of the RSS feed
            user_id (int, optional): User ID to associate with
            
        Returns:
            RssFeed: The created feed object
        """
        # Parse feed to get initial metadata
        feed_data = feedparser.parse(url)
        
        if feed_data.bozo:  # feedparser sets bozo to 1 if there's an error
            logger.error(f"Error parsing feed {url}: {feed_data.bozo_exception}")
            raise ValueError(f"Could not parse feed: {url}")
        
        # Extract feed information
        feed_title = feed_data.feed.get('title', None)
        feed_description = feed_data.feed.get('description', None)
        
        # Create new feed
        new_feed = RssFeed(
            url=url,
            title=feed_title,
            description=feed_description,
            user_id=user_id
        )
        
        db.session.add(new_feed)
        db.session.commit()
        
        # Process initial entries
        self.fetch_feed_content(new_feed.id, max_entries=5)
        
        return new_feed
    
    def fetch_feed_content(self, feed_id, max_entries=10):
        """
        Fetch content from an RSS feed and create AudioContent entries
        
        Args:
            feed_id (int): ID of the feed to process
            max_entries (int): Maximum entries to process
            
        Returns:
            list: List of created AudioContent objects
        """
        feed = RssFeed.query.get(feed_id)
        if not feed:
            logger.error(f"Feed not found: {feed_id}")
            return []
        
        if not feed.is_active:
            logger.warning(f"Feed is inactive: {feed.url}")
            return []
        
        try:
            # Parse feed
            feed_data = feedparser.parse(feed.url)
            
            # Update feed metadata
            feed.last_checked = datetime.utcnow()
            feed.title = feed_data.feed.get('title', feed.title)
            
            if hasattr(feed_data.feed, 'updated_parsed') and feed_data.feed.updated_parsed:
                feed.last_updated = datetime(*feed_data.feed.updated_parsed[:6])
            
            # Process entries
            new_contents = []
            entries_processed = 0
            
            for entry in feed_data.entries[:max_entries]:
                # Skip if we've hit our limit
                if entries_processed >= max_entries:
                    break
                
                # Get the link to the full content
                if hasattr(entry, 'link') and entry.link:
                    link = entry.link
                    
                    # Check if we already have this content
                    existing = AudioContent.query.filter_by(url=link).first()
                    if existing:
                        logger.debug(f"Content already exists: {link}")
                        continue
                    
                    # Create new content entry
                    title = entry.get('title', None)
                    
                    new_content = AudioContent(
                        url=link,
                        title=title,
                        user_id=feed.user_id,
                        feed_id=feed.id
                    )
                    
                    db.session.add(new_content)
                    new_contents.append(new_content)
                    entries_processed += 1
            
            # Reset error count on successful fetch
            feed.error_count = 0
            db.session.commit()
            
            return new_contents
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed.url}: {str(e)}")
            
            # Increment error count
            feed.error_count += 1
            db.session.commit()
            
            return []
    
    def process_all_feeds(self):
        """
        Process all active feeds to fetch new content
        
        Returns:
            int: Count of new content items created
        """
        active_feeds = RssFeed.query.filter_by(is_active=True).all()
        new_item_count = 0
        
        for feed in active_feeds:
            # Skip feeds that have been checked recently (< 30 min ago)
            if feed.last_checked and (datetime.utcnow() - feed.last_checked < timedelta(minutes=30)):
                continue
                
            items = self.fetch_feed_content(feed.id)
            new_item_count += len(items)
        
        return new_item_count