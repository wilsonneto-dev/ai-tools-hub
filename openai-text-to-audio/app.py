from flask import Flask, render_template, request, send_file, jsonify
from pathlib import Path
import os
from script import convert_text_to_speech
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / "data" / "temp"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    try:
        text = request.form.get('text')
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        output_path = app.config['UPLOAD_FOLDER'] / filename
        
        # Convert text to speech
        convert_text_to_speech(text, output_path)
        
        # Return the file
        return send_file(output_path, as_attachment=True, download_name='audio.mp3')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 