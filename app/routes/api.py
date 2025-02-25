from flask import Blueprint, request, jsonify, current_app
from app import db, limiter
from app.models.audio_content import AudioContent
from app.services.content_extractor import ContentExtractor
from app.services.text_processor import TextProcessor
from app.services.audio_converter import AudioConverter
import threading
import os
from urllib.parse import urlparse

api_bp = Blueprint('api', __name__)

@api_bp.route('/convert', methods=['POST'])
@limiter.limit("10 per hour")
def convert_url():
    """
    API endpoint to convert a blog URL to audio
    
    Expected JSON:
    {
        "url": "https://example.com/blog-post",
        "voice": "onyx"  # Optional
    }
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({
            'status': 'error',
            'message': 'URL is required'
        }), 400
    
    url = data.get('url')
    voice = data.get('voice', current_app.config['DEFAULT_VOICE'])
    
    # Validate URL
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError("Invalid URL format")
    except Exception:
        return jsonify({
            'status': 'error',
            'message': 'Invalid URL format'
        }), 400
    
    # Check if we already have this URL processed
    existing_content = AudioContent.query.filter_by(url=url).first()
    if existing_content and existing_content.is_processed and not existing_content.error:
        return jsonify({
            'status': 'success',
            'message': 'Content already processed',
            'content_id': existing_content.id,
            'audio_url': url_for('main.download_audio', content_id=existing_content.id, _external=True)
        })
    
    # Create new content entry
    new_content = AudioContent(url=url)
    db.session.add(new_content)
    db.session.commit()
    
    # Start background processing
    thread = threading.Thread(
        target=process_content_background,
        args=(new_content.id, voice)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'processing',
        'message': 'Content is being processed',
        'content_id': new_content.id,
        'status_url': url_for('api.check_status', content_id=new_content.id, _external=True)
    })

@api_bp.route('/status/<int:content_id>', methods=['GET'])
def check_status(content_id):
    """
    Check the status of a conversion
    """
    content = AudioContent.query.get_or_404(content_id)
    
    response = {
        'status': content.status,
        'content_id': content.id,
    }
    
    if content.is_processed:
        if content.error:
            response['error'] = content.error
        else:
            response['audio_url'] = url_for('main.download_audio', content_id=content.id, _external=True)
            response['title'] = content.title
            response['duration'] = content.duration
            response['word_count'] = content.word_count
    
    return jsonify(response)

@api_bp.route('/voices', methods=['GET'])
def get_voices():
    """
    Get available voices
    """
    return jsonify({
        'voices': current_app.config['AVAILABLE_VOICES'],
        'default': current_app.config['DEFAULT_VOICE']
    })

def process_content_background(content_id, voice):
    """
    Background task to process content
    """
    # Import the app outside of the function to avoid circular imports
    from run import app
    
    # Use the imported app to create a context
    with app.app_context():
        content = AudioContent.query.get(content_id)
        if not content:
            return
        
        content.is_processing = True
        db.session.commit()
        
        try:
            # Step 1: Extract content
            extractor = ContentExtractor(content.url)
            title, extracted_text = extractor.extract()
            
            if not extracted_text:
                raise ValueError("Could not extract content from the URL")
            
            content.title = title
            content.original_text = extracted_text
            content.content_hash = extractor.get_content_hash()
            db.session.commit()
            
            # Step 2: Process text
            processor = TextProcessor(extracted_text, title)
            processed_text = processor.process()
            content.processed_text = processed_text
            content.word_count = processor.word_count
            db.session.commit()
            
            # Step 3: Convert to audio
            converter = AudioConverter()
            
            if len(processor.chunks) > 1:
                audio_path = converter.convert_long_text(
                    processor.chunks,
                    voice=voice
                )
            else:
                audio_path = converter.convert_text(
                    processed_text,
                    voice=voice
                )
            
            # Get relative path for database storage
            rel_path = os.path.relpath(
                audio_path,
                os.path.join(current_app.root_path)
            )
            
            # Update database record
            # content.file_path = audio_path
            rel_path = os.path.join('static', 'audio', os.path.basename(audio_path))
            content.file_path = rel_path  # Store the relative path for web access
            content.voice = voice
            content.duration = converter.get_audio_duration(audio_path)
            content.is_processed = True
            content.is_processing = False
            db.session.commit()
            
        except Exception as e:
            content.error = str(e)
            content.is_processed = True
            content.is_processing = False
            db.session.commit()
            current_app.logger.error(f"Error processing content: {str(e)}")