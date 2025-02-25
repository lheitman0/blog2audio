from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from app import db, cache, limiter
from app.models.audio_content import AudioContent, User
from app.services.content_extractor import ContentExtractor
from app.services.text_processor import TextProcessor
from app.services.audio_converter import AudioConverter
from urllib.parse import urlparse
import os
import hashlib
from werkzeug.utils import secure_filename
import threading

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    """Home page with form for submitting blog URL"""
    return render_template('index.html')

@main_bp.route('/process', methods=['POST'])
@limiter.limit("5 per minute")
def process_url():
    """Process the submitted URL"""
    url = request.form.get('url')
    voice = request.form.get('voice', current_app.config['DEFAULT_VOICE'])
    
    if not url:
        flash('Please enter a valid URL', 'error')
        return redirect(url_for('main.index'))
    
    # Validate URL
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError("Invalid URL format")
    except Exception:
        flash('Please enter a valid URL', 'error')
        return redirect(url_for('main.index'))
    
    # Check if we already have this URL processed
    existing_content = AudioContent.query.filter_by(url=url).first()
    if existing_content and existing_content.is_processed:
        return redirect(url_for('main.result', content_id=existing_content.id))
    
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
    
    return redirect(url_for('main.processing', content_id=new_content.id))

@main_bp.route('/processing/<int:content_id>')
def processing(content_id):
    """Show processing status"""
    content = AudioContent.query.get_or_404(content_id)
    
    if content.is_processed:
        return redirect(url_for('main.result', content_id=content_id))
    
    return render_template('processing.html', content=content)

@main_bp.route('/status/<int:content_id>')
def status(content_id):
    """AJAX endpoint to check processing status"""
    content = AudioContent.query.get_or_404(content_id)
    
    return jsonify({
        'status': content.status,
        'error': content.error,
        'is_processed': content.is_processed
    })

@main_bp.route('/result/<int:content_id>')
def result(content_id):
    """Show result page with processed audio"""
    content = AudioContent.query.get_or_404(content_id)
    
    if not content.is_processed:
        return redirect(url_for('main.processing', content_id=content_id))
    
    if content.error:
        flash(f"Error processing content: {content.error}", 'error')
        return redirect(url_for('main.index'))
    
    return render_template('result.html', content=content)

@main_bp.route('/download/<int:content_id>')
def download_audio(content_id):
    """Download the audio file"""
    content = AudioContent.query.get_or_404(content_id)
    
    if not content.is_processed or not content.file_path or content.error:
        flash("Audio file is not available", 'error')
        return redirect(url_for('main.index'))
    
    return send_file(
        content.file_path,
        as_attachment=True,
        download_name=f"{secure_filename(content.title or 'blog-audio')}.mp3",
        mimetype='audio/mpeg'
    )

def process_content_background(content_id, voice, app=None):
    """
    Background task to process content
    """
    # Import the app outside of the function to avoid circular imports
    if app is None:
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