import requests
from bs4 import BeautifulSoup
import trafilatura
from newspaper import Article
from readability import Document
import hashlib
import logging
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)

class ContentExtractor:
    """
    Enhanced content extraction service that tries multiple methods
    to get the best quality content from a blog URL
    """
    
    def __init__(self, url):
        self.url = url
        self.title = None
        self.content = None
        self.html = None
        self.domain = self._get_domain()
    
    def _get_domain(self):
        """Extract domain from URL"""
        parsed_url = urlparse(self.url)
        return parsed_url.netloc
    
    def _fetch_html(self):
        """Fetch HTML content from URL with proper headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        try:
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            self.html = response.text
            return True
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {self.url}: {str(e)}")
            return False
    
    def _extract_with_trafilatura(self):
        """Extract content using Trafilatura library"""
        try:
            extracted = trafilatura.extract(self.html, include_comments=False, 
                                           include_tables=True, 
                                           no_fallback=False)
            if extracted:
                # Try to extract title separately if not included
                if not self.title:
                    soup = BeautifulSoup(self.html, 'html.parser')
                    self.title = soup.title.string if soup.title else None
                
                return extracted
            return None
        except Exception as e:
            logger.error(f"Trafilatura extraction error: {str(e)}")
            return None
    
    def _extract_with_newspaper(self):
        """Extract content using Newspaper3k library"""
        try:
            article = Article(self.url)
            article.download(input_html=self.html)
            article.parse()
            
            self.title = article.title
            return article.text
        except Exception as e:
            logger.error(f"Newspaper extraction error: {str(e)}")
            return None
    
    def _extract_with_readability(self):
        """Extract content using Mozilla's Readability algorithm"""
        try:
            doc = Document(self.html)
            self.title = doc.title()
            content = doc.summary()
            
            # Clean up HTML tags
            soup = BeautifulSoup(content, 'html.parser')
            return soup.get_text(separator='\n')
        except Exception as e:
            logger.error(f"Readability extraction error: {str(e)}")
            return None
    
    def _extract_with_beautifulsoup(self):
        """Extract content using BeautifulSoup with heuristics"""
        try:
            soup = BeautifulSoup(self.html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.extract()
            
            # Try to find the main content
            main_content = None
            
            # Look for article or main tags
            article = soup.find('article')
            if article:
                main_content = article
            else:
                main_content = soup.find('main') or soup.find(id=re.compile('content|main|article', re.I))
            
            # If we found main content, use that
            if main_content:
                self.title = soup.title.string if soup.title else None
                return main_content.get_text(separator='\n')
            
            # Default fallback
            self.title = soup.title.string if soup.title else None
            return soup.get_text(separator='\n')
        except Exception as e:
            logger.error(f"BeautifulSoup extraction error: {str(e)}")
            return None
    
    def extract(self):
        """
        Extract content using multiple strategies, returning the best result
        """
        if not self._fetch_html():
            return None, None
        
        # Try different extraction methods in order of preference
        content = (self._extract_with_trafilatura() or 
                   self._extract_with_newspaper() or 
                   self._extract_with_readability() or 
                   self._extract_with_beautifulsoup())
        
        if not content:
            logger.error(f"All extraction methods failed for URL: {self.url}")
            return None, None
        
        # Clean the content
        content = self._clean_content(content)
        return self.title, content
    
    def _clean_content(self, text):
        """Clean extracted content"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove email addresses for privacy
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL REMOVED]', text)
        
        # Limit paragraph length (avoids super long paragraphs)
        paragraphs = text.split('\n\n')
        cleaned_paragraphs = []
        
        for p in paragraphs:
            if len(p) > 1000:  # If paragraph is too long
                sentences = re.split(r'(?<=[.!?])\s+', p)
                chunked_paragraph = []
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < 1000:
                        current_chunk += sentence + " "
                    else:
                        chunked_paragraph.append(current_chunk.strip())
                        current_chunk = sentence + " "
                
                if current_chunk:
                    chunked_paragraph.append(current_chunk.strip())
                
                cleaned_paragraphs.extend(chunked_paragraph)
            else:
                cleaned_paragraphs.append(p)
        
        return '\n\n'.join(cleaned_paragraphs)
    
    def get_content_hash(self):
        """
        Generate a hash of the URL and content for caching purposes
        """
        if not self.content:
            return None
            
        hash_content = f"{self.url}:{self.content[:1000]}"
        return hashlib.md5(hash_content.encode()).hexdigest()