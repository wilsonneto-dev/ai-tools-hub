from flask import Flask, render_template, request, send_file, jsonify, url_for
from pathlib import Path
import os
from text_to_speech import convert_text_to_speech
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

def save_audio_metadata(filename, text, duration=None):
    try:
        with open(AUDIO_METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    except:
        metadata = []
    
    metadata.append({
        'filename': filename,
        'text': text,	
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
    return render_template('text-to-speech.html', audio_files=audio_files)


@app.route('/convert', methods=['POST'])
def convert():
    try:
        text = request.form.get('text')
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        filename = f"{uuid.uuid4()}.mp3"
        output_path = app.config['STATIC_AUDIO'] / filename
        
        response = {'status': 'processing', 'message': 'Starting conversion...'}
        
        convert_text_to_speech(text, output_path)
        save_audio_metadata(filename, text[:50])
        
        return jsonify({
            'status': 'success',
            'message': 'Conversion completed',
            'audio_url': url_for('static', filename=f'audio/{filename}'),
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete-audio/<filename>', methods=['POST'])
def delete_audio():
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