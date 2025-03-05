from openai import OpenAI
import os
from dataclasses import dataclass

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@dataclass
class TranslationResult:
    translated_text: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'pt-br': 'Brazilian Portuguese',
    'pt-pt': 'Portugal Portuguese',
    'es': 'Spanish'
}

def split_text_for_translation(text, max_length=2000):
    """Split text into chunks for translation, preserving paragraphs and sentences."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        # If paragraph is too long, split by sentences
        if len(paragraph) > max_length:
            sentences = paragraph.replace('! ', '!<split>').replace('? ', '?<split>').replace('. ', '.<split>').split('<split>')
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= max_length:
                    current_chunk += sentence + ' '
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ' '
        else:
            if len(current_chunk) + len(paragraph) + 2 <= max_length:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def translate_text(text, target_lang) -> TranslationResult:
    """Translate text to target language using OpenAI."""
    if not target_lang or target_lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {target_lang}")
    
    chunks = split_text_for_translation(text)
    translated_chunks = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    
    for chunk in chunks:
        print(f"Translating chunk of length: {len(chunk)}")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the following text to {SUPPORTED_LANGUAGES[target_lang]}. Maintain the original formatting and tone."},
                {"role": "user", "content": chunk}
            ]
        )
        translated_chunks.append(response.choices[0].message.content)
        total_prompt_tokens += response.usage.prompt_tokens
        total_completion_tokens += response.usage.completion_tokens
    
    return TranslationResult(
        translated_text='\n'.join(translated_chunks),
        total_tokens=total_prompt_tokens + total_completion_tokens,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens
    ) 