from pathlib import Path
from openai import OpenAI
import os
from pydub import AudioSegment
from lib.translations import translate_text, SUPPORTED_LANGUAGES
from dataclasses import dataclass
from typing import Optional

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_HEY_BRO"))

# Cost rates per million units
TTS_COST_PER_MILLION_CHARS = 15.00  # $15 per 1M characters - Open AI tts1
TRANSLATION_COST_PER_MILLION_TOKENS = 6.00  # $6 per 1M tokens - Open AI gpt3 turbo

@dataclass
class ConversionResult:
    output_path: Path
    total_tokens: int
    translated_text: Optional[str] = None
    translation_tokens: Optional[int] = None
    speech_tokens: Optional[int] = None
    translation_cost: Optional[float] = None
    speech_cost: Optional[float] = None
    total_cost: Optional[float] = None

AVAILABLE_VOICES = {
    'alloy': 'Alloy - Professional and balanced, ideal for general content',
    'echo': 'Echo - Deep and well-rounded male voice, great for narration',
    'fable': 'Fable - Warm and engaging male voice, perfect for storytelling',
    'onyx': 'Onyx - Clear and authoritative male voice, suited for formal content',
    'nova': 'Nova - Warm and expressive female voice, natural for conversations',
    'shimmer': 'Shimmer - Clear and dynamic female voice, excellent for presentations'
}

def split_text(text, max_length=4000):
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

def convert_text_to_speech(input_text, output_path, target_lang=None, voice='alloy') -> ConversionResult:
    """Convert text to speech with optional translation and voice selection."""
    if voice not in AVAILABLE_VOICES:
        raise ValueError(f"Unsupported voice: {voice}")

    translation_tokens = 0
    translated_text = None
    translation_cost = 0
    
    # Translate text if needed
    if target_lang:
        translation_result = translate_text(input_text, target_lang)
        input_text = translation_result.translated_text
        translation_tokens = translation_result.total_tokens
        translated_text = input_text
        translation_cost = (translation_tokens / 1_000_000) * TRANSLATION_COST_PER_MILLION_TOKENS
    
    text_chunks = split_text(input_text)
    temp_audio_files = []
    temp_dir = Path(output_path).parent
    speech_tokens = len(input_text)  # Character count for speech API
    speech_cost = (speech_tokens / 1_000_000) * TTS_COST_PER_MILLION_CHARS

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
    
    return ConversionResult(
        output_path=output_path,
        total_tokens=translation_tokens + speech_tokens,
        translated_text=translated_text,
        translation_tokens=translation_tokens,
        speech_tokens=speech_tokens,
        translation_cost=translation_cost,
        speech_cost=speech_cost,
        total_cost=translation_cost + speech_cost
    )
