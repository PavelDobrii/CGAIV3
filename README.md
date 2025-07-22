# Offline Story Generation Pipeline

This repository provides a fully offline pipeline for generating short stories with text-to-speech audio and subtitles. The setup uses only open source models and runs entirely in Docker containers.

## Hardware Requirements

- Minimum **16&nbsp;GB RAM**
- GPU with at least **8&nbsp;GB VRAM**
- Docker with GPU access (e.g. NVIDIA Container Toolkit)
- Docker Compose v2 or later (the `docker compose` CLI)

## Components

| Service   | Purpose                  | Image/Technology |
|-----------|--------------------------|------------------|
| `llm`     | Story generation         | [Ollama](https://github.com/jmorganca/ollama) with `llama3:8b-instruct` |
| `tts`     | Text to speech           | [Piper](https://github.com/rhasspy/piper) |
| `subtitles` | Subtitle generation    | [WhisperX&nbsp;2.1](https://github.com/m-bain/whisperX) |
| `api`     | REST interface           | FastAPI/uvicorn |

All services are started via `docker compose` and communicate on an internal Docker network. Generated files are written to the `storage/` directory which is mounted into the containers.

```
storage/
├── audio/      # generated mp3 files
├── subtitles/  # .srt subtitle files
└── markdown/   # generated stories in Markdown
```

## Quick Start

1. **Clone the repository**

```bash
git clone https://github.com/yourname/cgaiv3.git
cd cgaiv3
```

2. **Start the pipeline**

```bash
docker compose pull
docker compose up -d
```

The first start will download the models. Once all containers are running, the API is available on `http://localhost:8000`.

## API Usage

### 1. Generate a story

```bash
curl -X POST http://localhost:8000/generate/story \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Tell me about space travel","style":"narrative","interest_tag":"science","language":"en","search_query":"latest space news"}'
```
This returns the ID of the story and the path to the Markdown file.
You can optionally pass a `search_query` field to include recent information from
DuckDuckGo search results in the story prompt.

### 2. Convert the story to speech

```bash
curl -X POST http://localhost:8000/generate/audio \
  -H "Content-Type: application/json" \
  -d '{"id":"<story-id>", "language":"en"}'
```
Generates an mp3 file in `storage/audio/`.

### 3. Generate subtitles for the audio

```bash
curl -X POST http://localhost:8000/generate/subtitles \
  -H "Content-Type: application/json" \
  -d '{"id":"<story-id>"}'
```
Produces an `.srt` file alongside the audio.

### 4. Full workflow

One call can perform all steps:

```bash
curl -X POST http://localhost:8000/generate/full \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Tell me about space travel","style":"narrative","interest_tag":"science","language":"en","search_query":"latest space news"}'
```

### Language selection

The audio endpoint accepts a `language` parameter (`en`, `ru` or `lt`). The
appropriate Piper voice is selected automatically.

### Cached generation

If an mp3 or subtitle file already exists for a story, the API reuses it instead
of regenerating the content.

## Offline Use

All models are pulled and executed locally. After the first download, the pipeline works without Internet access. Generated assets remain in the `storage/` directory for reuse.
If you supply a `search_query`, the API performs an online DuckDuckGo search, so Internet access is required for that feature.

## License

This project is released under the MIT License. The included models follow their respective open licenses (Meta Llama 3 Community License for `llama3`, MIT for Piper and Apache&nbsp;2.0 for WhisperX).

