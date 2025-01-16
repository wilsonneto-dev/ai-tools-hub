# AI Tools Hub

A tool that provides various AI-powered tools on your localhost, using an OpenAI API key. 
Currently featuring Text-to-Speech conversion with translation capabilities, with plans to expand to more AI tools in the future, such as image generation, text summarization, and more.

## Current Features

### Text-to-Speech Converter
- Convert text to natural-sounding speech using OpenAI's TTS API.
- Support for multiple voices with different characteristics.
- Built-in translation to multiple languages before speech conversion.
- Real-time cost estimation and token usage tracking.
- Modern, responsive UI.
- History of conversions with playback capability.
- Support for long texts with automatic chunking.

## Tool Preview

![Tool Interface](./docs/image.png)

![Conversion History](./docs/image-1.png)

## Getting Started

### 🐳 Running with Docker (Recommended)

#### 1. Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/wilsonneto-dev/ai-tools-hub.git
cd ai-tools-hub
```

#### 2. Build the Docker Image
Build the Docker image for the application:
```bash
docker build -t ai-tools-hub .
```

#### 3. Run the Docker Container
Run the container using the following command:
```bash
docker run -d -p 5000:5000 -e OPENAI_API_KEY=your_api_key_here --name ai-tools-hub ai-tools-hub
```
Replace `your_api_key_here` with your actual OpenAI API key.

#### 4. Access the Application
Open your browser and navigate to:
[http://localhost:5000](http://localhost:5000)

---

### Prerequisites (Running without Docker)

- Python 3.8 or higher.
- OpenAI API key.
- Virtual environment (recommended).
- FFMPEG (for audio handling).

### Installation (Without Docker)

#### 1. Clone the repository
```bash
git clone https://github.com/wilsonneto-dev/ai-tools-hub.git
cd ai-tools-hub/src
```

#### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Set up environment variables
```bash
# Windows
set OPENAI_API_KEY=your_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_api_key_here
```

#### 5. Run the Application
Start the Flask development server:
```bash
python ./app.py
```

Navigate to `http://localhost:5000` in your browser.

## Cost Information

The application uses OpenAI's APIs with the following pricing:
- **Text-to-Speech**: $15.00 per 1 million characters.
- **Translation (GPT-3.5 Turbo)**: $6.00 per 1 million tokens.

Costs are calculated and displayed in real-time for each conversion.

## Project Structure

```
ai-tools-hub/
├── app.py                 # Main Flask application
├── lib/                   # Core functionality
│   ├── text_to_speech.py # Text-to-speech conversion logic
│   └── translations.py   # Translation handling
├── static/               # Static files (CSS, JS, audio files)
│   └── audio/            # Generated audio files
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── home.html         # Homepage
    └── text-to-speech.html # Text-to-speech interface
```

## Roadmap

### New Text-to-Speech Features
- [ ] Add support for file uploads (PDF, DOCX, TXT).
- [ ] Enable URL processing for article conversion.

### Additional AI Tools
- [ ] Image generation tool.
- [ ] Text summarization.

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- OpenAI for their powerful APIs.
- Flask framework.
- Bootstrap for the UI components.
- All contributors and users of this project.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.
