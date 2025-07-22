from fastapi import FastAPI, Body, HTTPException
import requests
import subprocess
from pathlib import Path
import uuid
import json

STORAGE = Path('/app/storage')
STORY_DIR = STORAGE / 'markdown'
AUDIO_DIR = STORAGE / 'audio'
SUBTITLES_DIR = STORAGE / 'subtitles'

LANG_TO_VOICE = {
    'en': 'en_US-amy-low.onnx',
    'ru': 'ru_RU-irina-low.onnx',
    'lt': 'lt_LT-ona-low.onnx',
}

app = FastAPI()

@app.post('/generate/story')
def generate_story(params: dict = Body(...)):
    prompt = params.get('prompt', '')
    style = params.get('style', '')
    interest_tag = params.get('interest_tag', '')
    language = params.get('language', 'en')
    full_prompt = (
        f"{prompt}\n"
        f"Write a {style} short story about {interest_tag} in {language}. "
        "The story should be 300-400 words, include a fun fact at the end and "
        "cite at least two sources."
    )
    full_prompt = "".join(full_prompt)

    resp = requests.post('http://llm:11434/api/generate', json={
        'model': 'llama3:8b-instruct',
        'prompt': full_prompt,
        'stream': False
    })
    text = resp.json().get('response', '')
    story_id = str(uuid.uuid4())
    STORY_DIR.mkdir(parents=True, exist_ok=True)
    md_path = STORY_DIR / f'{story_id}.md'
    md_path.write_text(text)
    # save generation parameters
    meta_path = STORY_DIR / f'{story_id}.json'
    meta = params.copy()
    meta['id'] = story_id
    meta_path.write_text(json.dumps(meta))
    return {'id': story_id, 'markdown': str(md_path)}

@app.post('/generate/audio')
def generate_audio(data: dict = Body(...)):
    story_id = data['id']
    language = data.get('language')
    meta_file = STORY_DIR / f'{story_id}.json'
    if not language and meta_file.exists():
        language = json.loads(meta_file.read_text()).get('language', 'en')
    language = language or 'en'
    text = (STORY_DIR / f'{story_id}.md').read_text()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = AUDIO_DIR / f'{story_id}.mp3'
    if audio_path.exists():
        return {'audio': str(audio_path)}
    voice = LANG_TO_VOICE.get(language, LANG_TO_VOICE['en'])
    subprocess.run([
        'piper',
        '--model', voice,
        '--output_file', str(audio_path),
        '--text', text
    ], check=True)
    return {'audio': str(audio_path)}

@app.post('/generate/subtitles')
def generate_subtitles(data: dict = Body(...)):
    story_id = data['id']
    audio_path = AUDIO_DIR / f'{story_id}.mp3'
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail='Audio not found')
    SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
    srt_path = SUBTITLES_DIR / f'{story_id}.srt'
    if srt_path.exists():
        return {'srt': str(srt_path)}
    subprocess.run([
        'whisperx', str(audio_path),
        '--output_srt', str(srt_path),
        '--model', 'small'
    ], check=True)
    return {'srt': str(srt_path)}

@app.post('/generate/full')
def generate_full(params: dict = Body(...)):
    result = generate_story(params)
    generate_audio({'id': result['id'], 'language': params.get('language')})
    generate_subtitles({'id': result['id']})
    return result
