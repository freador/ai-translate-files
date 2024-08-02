import os
import re
from datetime import timedelta
import ollama

def translate_portuguese_to_spanish(text):
    prompt = f"""Translate the following Portuguese text to Spanish:
'{text}'
Rules:
1. Provide ONLY the direct Spanish translation.
2. Do not include any introductory phrases or explanations.
3. Do not split the translation across multiple lines.
4. Preserve punctuation and capitalization.
5. Your response must contain ONLY the Spanish translation, nothing else."""
    
    response = ollama.generate(model="llama3", prompt=prompt)  # Using llama2:13b as a proxy for llama3
    translation = response['response'].strip()
    translation = re.sub(r'^(Aquí está la traducción:|Esta es la traducción:|Aquí está la traducción directa en español:)', '', translation, flags=re.IGNORECASE)
    return translation.strip()

def timedelta_to_vtt_time(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def add_timestamp(text, start_time):
    end_time = start_time + timedelta(seconds=5)  # Assume 5-second duration
    start_str = timedelta_to_vtt_time(start_time)
    end_str = timedelta_to_vtt_time(end_time)
    timestamp = f"{start_str} --> {end_str}"
    return f"{timestamp}\n{text}"

def parse_vtt_time(time_str):
    parts = time_str.split(':')
    h = int(parts[0])
    m = int(parts[1])
    s, ms = map(float, parts[2].split('.'))
    return timedelta(hours=h, minutes=m, seconds=s, milliseconds=int(ms))

def process_vtt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    blocks = re.split(r'\n\n+', content.strip())
    
    translated_blocks = []
    current_time = timedelta()
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 2 and re.match(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', lines[0]):
            timestamp = lines[0]
            text_to_translate = ' '.join(lines[1:])
            translated_text = translate_portuguese_to_spanish(text_to_translate)
            translated_block = f"{timestamp}\n{translated_text}"
            translated_blocks.append(translated_block)
            
            end_time = timestamp.split(' --> ')[1]
            current_time = parse_vtt_time(end_time)
        else:
            text_to_translate = ' '.join(lines)
            translated_text = translate_portuguese_to_spanish(text_to_translate)
            translated_block = add_timestamp(translated_text, current_time)
            translated_blocks.append(translated_block)
            
            current_time += timedelta(seconds=5)
    
    return '\n\n'.join(translated_blocks)

def process_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.vtt'):
            file_path = os.path.join(folder_path, filename)
            print(f"Processing {filename}...")
            translated_content = process_vtt_file(file_path)
            
            output_filename = f"translated_{filename}"
            output_path = os.path.join(folder_path, output_filename)
            with open(output_path, 'w', encoding='utf-8') as output_file:
                output_file.write(translated_content)
            
            print(f"Translated content saved to {output_filename}")

if __name__ == "__main__":
    folder_path = "./portuguese"
    process_folder(folder_path)