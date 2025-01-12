from pathlib import Path
from openai import OpenAI
import os
from pydub import AudioSegment
from lib.translations import translate_text, SUPPORTED_LANGUAGES

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_HEY_BRO"))

AVAILABLE_VOICES = {
    'alloy': 'Alloy - Professional and balanced, ideal for general content',
    'echo': 'Echo - Deep and well-rounded male voice, great for narration',
    'fable': 'Fable - Warm and engaging male voice, perfect for storytelling',
    'onyx': 'Onyx - Clear and authoritative male voice, suited for formal content',
    'nova': 'Nova - Warm and expressive female voice, natural for conversations',
    'shimmer': 'Shimmer - Clear and dynamic female voice, excellent for presentations'
}

def split_text(text, max_length=500):
    """Split text into chunks for text-to-speech conversion."""
    print(f"Text length = {len(text)}")
    chunks = []
    while len(text) > max_length:
        split_index = text[:max_length].rfind(" ")
        if split_index == -1:
            split_index = max_length
        chunks.append(text[:split_index].strip())
        text = text[split_index:].strip()
    chunks.append(text)
    print(f"Text splitted in {len(chunks)} chunks")
    return chunks

def convert_text_to_speech(input_text, output_path, target_lang=None, voice='alloy'):
    """Convert text to speech with optional translation and voice selection."""
    if voice not in AVAILABLE_VOICES:
        raise ValueError(f"Unsupported voice: {voice}")

    # Translate text if needed
    if target_lang:
        input_text = translate_text(input_text, target_lang)
    
    text_chunks = split_text(input_text)
    temp_audio_files = []
    temp_dir = Path(output_path).parent

    try:
        for i, chunk in enumerate(text_chunks):
            temp_file = temp_dir / f"temp_{i}.mp3"
            print(f"Generating {temp_file} with voice {voice}")
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=chunk
            )
            response.write_to_file(temp_file)
            temp_audio_files.append(temp_file)

        final_audio = AudioSegment.empty()
        for temp_file in temp_audio_files:
            print(f"Preparing to join audios: {temp_file}")
            audio = AudioSegment.from_file(temp_file)
            final_audio += audio

        print("Merging audio into one file")
        final_audio.export(output_path, format="mp3")

    finally:
        # Clean up temporary files
        for temp_file in temp_audio_files:
            if temp_file.exists():
                print(f"Removing temp files: {temp_file}")
                os.remove(temp_file)

    print(f"Final audio saved on: {output_path}")
    return output_path
