from flask import Flask, render_template, request, send_file, jsonify, url_for
from pathlib import Path
import os
from lib.text_to_speech import convert_text_to_speech, AVAILABLE_VOICES
from lib.translations import SUPPORTED_LANGUAGES
import uuid
from openai import OpenAI
from datetime import datetime
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / "data" / "temp"
app.config['STATIC_AUDIO'] = Path(__file__).parent / "static" / "audio"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_AUDIO'], exist_ok=True)

AUDIO_METADATA_FILE = Path(__file__).parent / "static" / "audio_metadata.json"
if not AUDIO_METADATA_FILE.exists():
    with open(AUDIO_METADATA_FILE, 'w') as f:
        json.dump([], f)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_HEY_BRO"))

def save_audio_metadata(filename, title, text, target_lang, voice, duration=None):
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
        'duration': duration
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
        
        # Pass target_lang only if translation is needed
        convert_text_to_speech(text, output_path, target_lang if needs_translation else None, voice)
        save_audio_metadata(filename, title, text[:50], target_lang if needs_translation else 'en', voice)
        
        return jsonify({
            'status': 'success',
            'message': 'Conversion completed',
            'audio_url': url_for('static', filename=f'audio/{filename}'),
            'title': title,
            'text': text,
            'language': SUPPORTED_LANGUAGES[target_lang] if needs_translation else 'English',
            'voice': AVAILABLE_VOICES[voice],
            'timestamp': datetime.now().isoformat()
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

if __name__ == '__main__':
    app.run(debug=True) 