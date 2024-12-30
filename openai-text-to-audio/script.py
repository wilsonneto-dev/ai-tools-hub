from pathlib import Path
from openai import OpenAI
import os
from pydub import AudioSegment

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

name = "text"
data_path = Path(__file__).parent / "data"
input_file = data_path / f"{name}.txt"
output_file = data_path / f"{name}.mp3"

def split_text(text, max_length=500):
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

with open(input_file, "r") as file:
    input_text = file.read()

text_chunks = split_text(input_text)

temp_audio_files = []
for i, chunk in enumerate(text_chunks):
    temp_file = data_path / f"temp_{i}.mp3"
    print(f"Generating {temp_file}")
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=chunk
    )
    response.write_to_file(Path(__file__).parent / "data" /  temp_file)
    temp_audio_files.append(temp_file)

final_audio = AudioSegment.empty()
for temp_file in temp_audio_files:
    print(f"Preparing to join audios: {temp_file}")
    audio = AudioSegment.from_file(temp_file)
    final_audio += audio

print("Merging audion into one file")
final_audio.export(output_file, format="mp3")

for temp_file in temp_audio_files:
    print(f"Removing temp files: {temp_file}")
    os.remove(temp_file)

print(f"Final audio saved on: {output_file}")