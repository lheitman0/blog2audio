import re
import nltk
from nltk.tokenize import sent_tokenize
from langdetect import detect
import logging
from bs4 import BeautifulSoup
from app.config import Config
import ssl

# Fix SSL certificate issues for NLTK
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
    
# Download NLTK data on first run
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logger = logging.getLogger(__name__)

class TextProcessor:
    """
    Service for processing and preparing text for text-to-speech conversion
    """
    
    def __init__(self, text, title=None):
        self.original_text = text
        self.title = title
        self.processed_text = None
        self.language = None
        self.chunks = []
        self.word_count = 0
    
    def process(self):
        """
        Main processing pipeline for text
        """
        if not self.original_text:
            return None
            
        # Step 1: Basic cleaning
        text = self._basic_clean(self.original_text)
        
        # Step 2: Detect language
        self.language = self._detect_language(text)
        
        # Step 3: Format text for better speech
        text = self._format_for_speech(text)
        
        # Step 4: Add title if available
        if self.title:
            text = f"{self.title}.\n\n{text}"
        
        # Step 5: Count words
        self.word_count = len(text.split())
        
        # Step 6: Split into chunks if needed
        self.chunks = self._split_into_chunks(text)
        
        # Store processed text
        self.processed_text = text
        
        return self.processed_text
    
    def _basic_clean(self, text):
        """
        Basic text cleaning operations
        """
        # Convert any remaining HTML to text
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text(separator='\n')
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove duplicate newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove excessive spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix spacing after punctuation
        text = re.sub(r'([.!?])\s*', r'\1 ', text)
        
        return text.strip()
    
    def _detect_language(self, text):
        """
        Detect the language of the text
        """
        try:
            # Use a sample of the text for faster detection
            sample = text[:1000]
            language = detect(sample)
            return language
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return 'en'  # Default to English
    
    def _format_for_speech(self, text):
        """
        Format text to sound better when spoken
        """
        # Replace common abbreviations
        replacements = {
            r'\bDr\.': 'Doctor',
            r'\bMr\.': 'Mister',
            r'\bMrs\.': 'Misses',
            r'\bMs\.': 'Miss',
            r'\bProf\.': 'Professor',
            r'\be\.g\.': 'for example',
            r'\bi\.e\.': 'that is',
            r'\betc\.': 'etcetera',
            r'\bvs\.': 'versus',
            r'\bapprox\.': 'approximately',
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        
        # Handle numbers for better speech
        text = self._format_numbers(text)
        
        # Insert pauses at paragraph breaks
        text = re.sub(r'\n\n', '.\n\n', text)
        
        return text
    
    def _format_numbers(self, text):
        """
        Format numbers for better speech
        """
        # Format dates
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', r'\1 \2 \3', text)
        
        # Format time
        text = re.sub(r'\b(\d{1,2}):(\d{2})\b', r'\1 \2', text)
        
        return text
    
    def _split_into_chunks(self, text):
        """
        Split text into manageable chunks for TTS processing
        Respects sentence boundaries
        """
        max_length = Config.MAX_TEXT_LENGTH
        
        # If text is already small enough, return as a single chunk
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = sent_tokenize(text)
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed the limit, start a new chunk
            if len(current_chunk) + len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
            else:
                current_chunk += sentence + " "
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_estimated_duration(self):
        """
        Estimate audio duration based on word count
        Assumes average speaking rate of 150 words per minute
        """
        words_per_minute = 150
        minutes = self.word_count / words_per_minute
        return minutes * 60  # Return seconds