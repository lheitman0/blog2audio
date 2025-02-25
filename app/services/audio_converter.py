import os
import logging
from openai import OpenAI
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
import tempfile
import time

from app.config import Config
from flask import current_app

logger = logging.getLogger(__name__)

class AudioConverter:
    """
    Service for converting text to audio using OpenAI's API
    with support for long texts and error handling
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key)
        self.default_voice = Config.DEFAULT_VOICE
        self.available_voices = Config.AVAILABLE_VOICES
    
    def convert_text(self, text, voice=None, output_path=None):
        """
        Convert text to audio and save to file
        
        Args:
            text (str): Text to convert
            voice (str): Voice to use (default: Config.DEFAULT_VOICE)
            output_path (str): Path to save audio file
            
        Returns:
            str: Path to saved audio file
        """
        if not text:
            raise ValueError("No text provided for conversion")
        
        voice = voice or self.default_voice
        if voice not in self.available_voices:
            logger.warning(f"Voice {voice} not available, falling back to {self.default_voice}")
            voice = self.default_voice
        
        try:
            logger.info(f"Converting text with {len(text)} characters using voice: {voice}")
            
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Create output path if not provided
            if not output_path:
                folder = os.path.join(current_app.root_path, Config.AUDIO_UPLOAD_FOLDER)
                os.makedirs(folder, exist_ok=True)
                
                # Generate a unique filename
                timestamp = int(time.time())
                output_path = os.path.join(folder, f"audio_{timestamp}.mp3")
            
            # Write response to file
            with open(output_path, "wb") as audio_file:
                audio_file.write(response.content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting text to speech: {str(e)}")
            raise
    
    def convert_long_text(self, text_chunks, voice=None, output_path=None):
        """
        Convert long text (split into chunks) and combine into a single audio file
        
        Args:
            text_chunks (list): List of text chunks
            voice (str): Voice to use
            output_path (str): Path to save final audio file
            
        Returns:
            str: Path to saved audio file
        """
        if not text_chunks:
            raise ValueError("No text chunks provided for conversion")
        
        # Create a temp directory for chunk processing
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Processing {len(text_chunks)} text chunks")
            temp_files = []
            
            # Convert each chunk in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                
                for i, chunk in enumerate(text_chunks):
                    chunk_path = os.path.join(temp_dir, f"chunk_{i}.mp3")
                    temp_files.append(chunk_path)
                    
                    # Submit chunk conversion task
                    future = executor.submit(
                        self._convert_chunk, 
                        chunk, 
                        voice, 
                        chunk_path
                    )
                    futures.append(future)
                
                # Wait for all conversions to complete
                for future in futures:
                    future.result()  # This will raise any exceptions from the thread
            
            # Combine audio files
            combined = self._combine_audio_files(temp_files)
            
            # Create output path if not provided
            if not output_path:
                folder = os.path.join(current_app.root_path, Config.AUDIO_UPLOAD_FOLDER)
                os.makedirs(folder, exist_ok=True)
                
                # Generate a unique filename
                timestamp = int(time.time())
                output_path = os.path.join(folder, f"audio_{timestamp}.mp3")
            
            # Save combined audio
            combined.export(output_path, format="mp3")
            
            return output_path
    
    def _convert_chunk(self, text, voice, output_path):
        """Helper method to convert a single chunk"""
        return self.convert_text(text, voice, output_path)
    
    def _combine_audio_files(self, file_paths):
        """
        Combine multiple audio files into a single file
        
        Args:
            file_paths (list): List of paths to audio files
            
        Returns:
            AudioSegment: Combined audio
        """
        if not file_paths:
            raise ValueError("No audio files to combine")
        
        # Start with the first file
        combined = AudioSegment.from_mp3(file_paths[0])
        
        # Add subsequent files
        for path in file_paths[1:]:
            audio = AudioSegment.from_mp3(path)
            combined += audio
            
        return combined
    
    @staticmethod
    def get_audio_duration(file_path):
        """
        Get the duration of an audio file in seconds
        
        Args:
            file_path (str): Path to audio file
            
        Returns:
            float: Duration in seconds
        """
        try:
            audio = AudioSegment.from_mp3(file_path)
            return len(audio) / 1000.0  # Convert milliseconds to seconds
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return None