from flask import Flask, render_template, request, send_file, jsonify, url_for
from pathlib import Path
import os
from lib.text_to_speech import convert_text_to_speech, AVAILABLE_VOICES
from lib.translations import SUPPORTED_LANGUAGES
from lib.vtt_processor import clean_vtt_content, generate_article
import uuid
from openai import OpenAI
from datetime import datetime
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / "static" / "files"
app.config['STATIC_AUDIO'] = Path(__file__).parent / "static" / "audio"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_AUDIO'], exist_ok=True)

AUDIO_METADATA_FILE = Path(__file__).parent / "static" / "audio_metadata.json"
VTT_METADATA_FILE = Path(__file__).parent / "static" / "vtt_metadata.json"

# Initialize metadata files if they don't exist
for metadata_file in [AUDIO_METADATA_FILE, VTT_METADATA_FILE]:
    if not metadata_file.exists():
        with open(metadata_file, 'w') as f:
            json.dump([], f)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_HEY_BRO"))

def save_audio_metadata(filename, title, text, target_lang, voice, duration=None, tokens_used=None, costs=None):
    try:
        with open(AUDIO_METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    except:
        metadata = []
    
    metadata.append({
        'filename': filename,
        'title': title,
        'text': text,
        'language': SUPPORTED_LANGUAGES.get(target_lang, 'Unknown'),
        'voice': AVAILABLE_VOICES.get(voice, 'Unknown'),
        'timestamp': datetime.now().isoformat(),
        'duration': duration,
        'tokens_used': tokens_used or {},
        'costs': costs or {}
    })
    
    metadata = metadata[-50:]
    
    with open(AUDIO_METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

def get_audio_metadata():
    try:
        with open(AUDIO_METADATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_vtt_metadata(cleaned_filename, article_filename=None, original_filename=None, language=None, vtt_stats=None, tokens_used=None, costs=None):
    try:
        with open(VTT_METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    except:
        metadata = []
    
    metadata.append({
        'cleaned_filename': cleaned_filename,
        'article_filename': article_filename,
        'original_filename': original_filename,
        'language': language,
        'timestamp': datetime.now().isoformat(),
        'vtt_stats': vtt_stats or {},
        'tokens_used': tokens_used or {},
        'costs': costs or {}
    })
    
    metadata = metadata[-50:]  # Keep only last 50 entries
    
    with open(VTT_METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

def get_vtt_metadata():
    try:
        with open(VTT_METADATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/text-to-speech')
def text_to_speech():
    audio_files = get_audio_metadata()
    audio_files.reverse()
    return render_template('text-to-speech.html', 
                         audio_files=audio_files, 
                         languages=SUPPORTED_LANGUAGES,
                         voices=AVAILABLE_VOICES)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        text = request.form.get('text')
        title = request.form.get('title', '').strip() or 'Untitled'
        needs_translation = request.form.get('needs_translation') == 'on'
        target_lang = request.form.get('language') if needs_translation else None
        voice = request.form.get('voice', 'alloy')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        if needs_translation and target_lang not in SUPPORTED_LANGUAGES:
            return jsonify({'error': 'Unsupported language'}), 400

        if voice not in AVAILABLE_VOICES:
            return jsonify({'error': 'Unsupported voice'}), 400

        filename = f"{uuid.uuid4()}.mp3"
        output_path = app.config['STATIC_AUDIO'] / filename
        
        response = {'status': 'processing', 'message': 'Starting conversion...'}
        
        # Convert text to speech and get token usage
        result = convert_text_to_speech(text, output_path, target_lang if needs_translation else None, voice)
        
        # Prepare token usage data
        tokens_used = {
            'total_tokens': result.total_tokens,
            'translation_tokens': result.translation_tokens,
            'speech_tokens': result.speech_tokens
        }
        
        # Prepare cost data
        costs = {
            'translation_cost': round(result.translation_cost, 4) if result.translation_cost else 0,
            'speech_cost': round(result.speech_cost, 4) if result.speech_cost else 0,
            'total_cost': round(result.total_cost, 4) if result.total_cost else 0
        }
        
        # Save metadata with token usage and costs
        save_audio_metadata(
            filename, 
            title, 
            text, 
            target_lang if needs_translation else 'en', 
            voice,
            tokens_used=tokens_used,
            costs=costs
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Conversion completed',
            'audio_url': url_for('static', filename=f'audio/{filename}'),
            'title': title,
            'text': result.translated_text if result.translated_text else text,
            'language': SUPPORTED_LANGUAGES[target_lang] if needs_translation else 'English',
            'voice': AVAILABLE_VOICES[voice],
            'timestamp': datetime.now().isoformat(),
            'tokens_used': tokens_used,
            'costs': costs
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete-audio/<filename>', methods=['POST'])
def delete_audio(filename):
    try:
        file_path = app.config['STATIC_AUDIO'] / filename
        if file_path.exists():
            os.remove(file_path)
            
            # Update metadata
            with open(AUDIO_METADATA_FILE, 'r') as f:
                metadata = json.load(f)
            metadata = [m for m in metadata if m['filename'] != filename]
            with open(AUDIO_METADATA_FILE, 'w') as f:
                json.dump(metadata, f)
            
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/vtt-processor')
def vtt_processor():
    vtt_files = get_vtt_metadata()
    vtt_files.reverse()  # Show newest first
    return render_template('vtt-processor.html', vtt_files=vtt_files)

@app.route('/process-vtt', methods=['POST'])
def process_vtt():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.endswith('.vtt'):
            return jsonify({'error': 'Invalid file type. Please upload a .vtt file'}), 400
        
        # Read and clean VTT content
        content = file.read().decode('utf-8')
        cleaned_text, vtt_stats = clean_vtt_content(content)
        
        # Generate unique filenames
        cleaned_filename = f"cleaned_{uuid.uuid4()}.txt"
        cleaned_path = app.config['UPLOAD_FOLDER'] / cleaned_filename
        
        # Save cleaned text
        with open(cleaned_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        # Generate article if requested
        generate_article_flag = request.form.get('generate_article') == 'on'
        article_result = None
        article_filename = None
        language = request.form.get('article_language', 'en')
        
        if generate_article_flag:
            result = generate_article(cleaned_text, language)
            article_filename = f"article_{uuid.uuid4()}.md"
            article_path = app.config['UPLOAD_FOLDER'] / article_filename
            
            with open(article_path, 'w', encoding='utf-8') as f:
                f.write(result.markdown_article)
                
            article_result = {
                'markdown': result.markdown_article,
                'download_url': url_for('download_file', filename=article_filename),
                'tokens_used': result.total_tokens,
                'prompt_tokens': result.prompt_tokens,
                'completion_tokens': result.completion_tokens,
                'cost': result.total_cost,
                'input_cost': (result.prompt_tokens / 1_000_000) * 10.00,
                'output_cost': (result.completion_tokens / 1_000_000) * 30.00,
                'vtt_stats': result.vtt_stats
            }
            
            # Save metadata
            save_vtt_metadata(
                cleaned_filename=cleaned_filename,
                article_filename=article_filename,
                original_filename=file.filename,
                language=language,
                vtt_stats=vtt_stats,
                tokens_used={
                    'total_tokens': result.total_tokens,
                    'prompt_tokens': result.prompt_tokens,
                    'completion_tokens': result.completion_tokens
                },
                costs={
                    'input_cost': (result.prompt_tokens / 1_000_000) * 10.00,
                    'output_cost': (result.completion_tokens / 1_000_000) * 30.00,
                    'total_cost': result.total_cost
                }
            )
        else:
            # Save metadata without article information
            save_vtt_metadata(
                cleaned_filename=cleaned_filename,
                original_filename=file.filename,
                vtt_stats=vtt_stats
            )
        
        return jsonify({
            'status': 'success',
            'cleaned_text': cleaned_text,
            'cleaned_file_url': url_for('download_file', filename=cleaned_filename),
            'article': article_result,
            'vtt_stats': vtt_stats
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(
            app.config['UPLOAD_FOLDER'] / filename,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/delete-vtt/<filename>', methods=['POST'])
def delete_vtt(filename):
    try:
        # Delete both cleaned and article files if they exist
        for file_path in [
            app.config['UPLOAD_FOLDER'] / filename,
            app.config['UPLOAD_FOLDER'] / f"article_{filename}"
        ]:
            if file_path.exists():
                os.remove(file_path)
        
        # Update metadata
        with open(VTT_METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        metadata = [m for m in metadata if m['cleaned_filename'] != filename]
        with open(VTT_METADATA_FILE, 'w') as f:
            json.dump(metadata, f)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 