import re
from pathlib import Path
from openai import OpenAI
import os
from dataclasses import dataclass
from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_HEY_BRO"))

@dataclass
class ProcessingResult:
    cleaned_text: str
    markdown_article: str
    total_tokens: int
    total_cost: float
    prompt_tokens: int
    completion_tokens: int
    vtt_stats: dict  # Stats about VTT processing

def clean_vtt_content(content: str) -> tuple[str, dict]:
    """Remove timestamps and line numbers from VTT content."""
    logger.info("Starting VTT content cleaning")
    initial_lines = len(content.split('\n'))
    initial_chars = len(content)
    
    # Split content into lines
    lines = content.split('\n')
    cleaned_lines = []
    timestamps_removed = 0
    numbers_removed = 0
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Skip WEBVTT header
        if line.strip() == 'WEBVTT':
            continue
            
        # Skip line numbers (they are usually just numbers)
        if line.strip().isdigit():
            numbers_removed += 1
            continue
            
        # Skip timestamp lines (they match the format 00:00:00.000 --> 00:00:00.000)
        if re.match(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', line.strip()):
            timestamps_removed += 1
            continue
            
        # Add non-timestamp, non-empty lines
        cleaned_lines.append(line.strip())
    
    final_text = '\n'.join(cleaned_lines)
    final_lines = len(cleaned_lines)
    final_chars = len(final_text)
    
    stats = {
        'initial_lines': initial_lines,
        'final_lines': final_lines,
        'lines_removed': initial_lines - final_lines,
        'timestamps_removed': timestamps_removed,
        'numbers_removed': numbers_removed,
        'initial_chars': initial_chars,
        'final_chars': final_chars,
        'chars_removed': initial_chars - final_chars,
    }
    
    logger.info(f"VTT cleaning complete: {initial_lines} lines -> {final_lines} lines")
    logger.info(f"Removed {timestamps_removed} timestamps and {numbers_removed} line numbers")
    logger.info(f"Character reduction: {initial_chars} -> {final_chars} ({stats['chars_removed']} removed)")
    
    return final_text, stats

def split_text(text: str, max_tokens: int = 25000) -> list[str]:
    """Split text into chunks that fit within token limits."""
    logger.info(f"Starting text splitting with max_tokens={max_tokens}")
    
    # Rough estimate: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    chunks = []
    
    while len(text) > max_chars:
        # Find a good splitting point
        split_point = text[:max_chars].rfind('\n')
        if split_point == -1:
            split_point = text[:max_chars].rfind('. ')
        if split_point == -1:
            split_point = max_chars
            
        chunks.append(text[:split_point])
        text = text[split_point:].strip()
    
    chunks.append(text)
    logger.info(f"Text split into {len(chunks)} chunks")
    return chunks

def generate_article(text: str, language: str = "en") -> ProcessingResult:
    """Generate a markdown article from the cleaned VTT content."""
    logger.info(f"Starting article generation in {language}")
    chunks = split_text(text)
    article_parts = []
    total_tokens = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    
    # Get VTT processing stats
    _, vtt_stats = clean_vtt_content(text)
    
    # Language-specific system prompts
    language_prompts = {
        "pt-BR": """Você é um especialista em converter transcrições de reuniões em artigos bem estruturados.
    Sua tarefa é analisar a transcrição da reunião e criar um artigo abrangente que:
    0. Seu foco deve ser nos tópicos e discussões de Design de Sistemas
    1. Capture e transmita os tópicos e discussões
    2. Organize o conteúdo em uma estrutura lógica com cabeçalhos
    3. Use formatação markdown adequada, incluindo cabeçalhos, listas e ênfase quando apropriado
    4. Isto deve ser um artigo, um post de blog
    5. Você não deve incluir nomes de participantes, mas organizar a discussão como um artigo
    6. Ignore discussões de gerenciamento de comunidade ou de reunião
    7. Aborde todas as discussões profundas e trade-offs discutidos e adicione-os no artigo
    8. O artigo é um artigo educacional sobre design de sistemas, todas as discussões, trade-offs, ferramentas e conceitos são super importantes
    9. Sinta-se à vontade para expandir algumas discussões com mais conhecimento e contexto
    
    Formate a saída como um artigo markdown adequado com:
    - Um título e introdução claros
    - Seções organizadas com cabeçalhos
    - Conteúdo informativo e educacional""",
        
        "pt-PT": """És um especialista em converter transcrições de reuniões em artigos bem estruturados.
    A tua tarefa é analisar a transcrição da reunião e criar um artigo abrangente que:
    0. O teu foco deve ser nos tópicos e discussões de Design de Sistemas
    1. Capture e transmita os tópicos e discussões
    2. Organize o conteúdo numa estrutura lógica com cabeçalhos
    3. Use formatação markdown adequada, incluindo cabeçalhos, listas e ênfase quando apropriado
    4. Isto deve ser um artigo, um post de blog
    5. Não deves incluir nomes de participantes, mas organizar a discussão como um artigo
    6. Ignora discussões de gestão de comunidade ou de reunião
    7. Aborda todas as discussões profundas e trade-offs discutidos e adiciona-os no artigo
    8. O artigo é um artigo educacional sobre design de sistemas, todas as discussões, trade-offs, ferramentas e conceitos são super importantes
    9. Sente-te à vontade para expandir algumas discussões com mais conhecimento e contexto
    
    Formata a saída como um artigo markdown adequado com:
    - Um título e introdução claros
    - Secções organizadas com cabeçalhos
    - Conteúdo informativo e educacional""",
        
        "es": """Eres un experto en convertir transcripciones de reuniones en artículos bien estructurados.
    Tu tarea es analizar la transcripción de la reunión y crear un artículo completo que:
    0. Tu enfoque debe estar en los temas y discusiones de Diseño de Sistemas
    1. Capture y transmita los temas y discusiones
    2. Organice el contenido en una estructura lógica con encabezados
    3. Use formato markdown adecuado, incluyendo encabezados, listas y énfasis cuando sea apropiado
    4. Esto debe ser un artículo, una publicación de blog
    5. No debes incluir nombres de participantes, pero organizar la discusión como un artículo
    6. Ignora las discusiones de gestión de comunidad o de reunión
    7. Aborda todas las discusiones profundas y compensaciones discutidas y agrégalas en el artículo
    8. El artículo es un artículo educativo sobre diseño de sistemas, todas las discusiones, compensaciones, herramientas y conceptos son super importantes
    9. Siéntete libre de expandir algunas discusiones con más conocimiento y contexto
    
    Formatea la salida como un artículo markdown adecuado con:
    - Un título e introducción claros
    - Secciones organizadas con encabezados
    - Contenido informativo y educativo""",
        
        "en": """You are an expert at converting meeting transcripts into well-structured articles.
    Your task is to analyze the meeting transcript and create a comprehensive article that:
    0. Your focus should be in the System Design topics and discussions
    1. Captures and transmits the topics and discussions
    2. Organizes the content in a logical structure with headers
    3. Uses proper markdown formatting including headers, lists, and emphasis where appropriate
    4. This should be an article, a blog post
    5. You should not include participant names, but organize the discussion as an article
    6. Ignore community managing or meeting managing discussions
    7. Go through all the deep discussions and trade-offs discussed and add it in the article
    8. The article is an educational article regarding system design, all the discussion, trade-offs, tools and concepts are super important
    9. Feel free to expand some discussions with more knowledge and context
    
    Format the output as a proper markdown article with:
    - A clear title and introduction
    - Organized sections with headers
    - Informational and educational content"""
    }
    
    system_prompt = language_prompts.get(language, language_prompts["en"])
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)}")
        
        if i == 0:
            prompt = f"Here's the first part of a meeting transcript. Create the beginning of the article:\n\n{chunk}"
        else:
            prompt = f"Here's the next part of the transcript. Continue the article maintaining the same style:\n\n{chunk}"
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        article_parts.append(response.choices[0].message.content)
        total_tokens += response.usage.total_tokens
        total_prompt_tokens += response.usage.prompt_tokens
        total_completion_tokens += response.usage.completion_tokens
        
        logger.info(f"Chunk {i+1} processed: {response.usage.total_tokens} tokens " +
                   f"(prompt: {response.usage.prompt_tokens}, " +
                   f"completion: {response.usage.completion_tokens})")
    
    # Calculate cost based on GPT-4 Turbo pricing:
    # Input tokens: $10.00 per 1M tokens
    # Output tokens: $30.00 per 1M tokens
    input_cost = (total_prompt_tokens / 1_000_000) * 10.00
    output_cost = (total_completion_tokens / 1_000_000) * 30.00
    total_cost = input_cost + output_cost
    
    logger.info(f"Article generation complete. Total tokens: {total_tokens} " +
               f"(prompt: {total_prompt_tokens}, completion: {total_completion_tokens})")
    logger.info(f"Cost breakdown - Input: ${input_cost:.4f} ($10/1M tokens), " +
               f"Output: ${output_cost:.4f} ($30/1M tokens), Total: ${total_cost:.4f}")
    
    return ProcessingResult(
        cleaned_text=text,
        markdown_article='\n\n'.join(article_parts),
        total_tokens=total_tokens,
        total_cost=total_cost,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
        vtt_stats=vtt_stats
    ) 