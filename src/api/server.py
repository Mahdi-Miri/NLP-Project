import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config.settings import config
from src.step1_graph.autocomplete import QuoteAutocompleter
from src.step1_graph.graph_db import get_quote_graph
from src.step2_voice.chatbot import WhichQuoteChatbot

# Initialize FastAPI application
app = FastAPI(
    title="NLP Project - Which Quote Microservice",
    description="REST API for Wikiquote Graph Autocompletion and Interactive Voice Assistant",
    version="1.0.0"
)

# Enable CORS for web and frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for audio artifacts generated during sessions
AUDIO_CACHE_DIR = Path(tempfile.gettempdir()) / "nlp_audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Shared instances for fast cached inference
graph_db = get_quote_graph()
autocompleter = QuoteAutocompleter(graph_db)
chatbot = WhichQuoteChatbot(autocompleter=autocompleter)


# Pydantic request models
class AutocompleteRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "Stay hungry"})
    top_k: int = Field(default=3, ge=1, le=10)


class SearchRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "Einstein imagination"})
    limit: int = Field(default=5, ge=1, le=20)


class TextTurnRequest(BaseModel):
    text: str = Field(..., json_schema_extra={"example": "Who said to be or not to be?"})
    speaker: str = Field(default="Guest", json_schema_extra={"example": "Mahdi"})


@app.get("/")
def root():
    """Health check and service status."""
    return {
        "status": "online",
        "service": "Which Quote NLP Microservice",
        "version": "1.0.0",
        "docs_url": "/docs"
    }


@app.get("/api/stats")
def get_stats():
    """Returns graph database counts of quotes, authors, and works."""
    stats = graph_db.get_stats()
    return {"status": "success", "stats": stats}


@app.post("/api/step1/autocomplete")
def autocomplete_citation(payload: AutocompleteRequest):
    """
    Step 1: Autocompletes a partial citation and returns source attribution.
    """
    results = autocompleter.autocomplete(payload.query, top_k=payload.top_k)
    return {
        "query": payload.query,
        "count": len(results),
        "results": results
    }


@app.post("/api/step1/autocomplete-trace")
def autocomplete_citation_trace(payload: AutocompleteRequest):
    """
    Step 1: Autocompletes citation with execution plan, Cypher query, and graph visualization.
    """
    trace_data = autocompleter.autocomplete_with_trace(payload.query, top_k=payload.top_k)
    return {
        "status": "success",
        "trace": trace_data
    }


@app.post("/api/step1/search")
def fulltext_search(payload: SearchRequest):
    """
    Step 1: Performs full-text search across all quotes and citations.
    """
    results = graph_db.search_fulltext(payload.query, limit=payload.limit)
    return {
        "query": payload.query,
        "count": len(results),
        "results": results
    }


@app.get("/api/step2/speakers")
def list_speakers():
    """
    Step 2: Lists registered speakers and their voice preferences.
    """
    users = chatbot.speaker_system.list_users()
    profiles = [chatbot.speaker_system.profiles.get(u, {}) for u in users]
    return {
        "count": len(users),
        "speakers": users,
        "profiles": profiles
    }


@app.post("/api/step2/enroll")
async def enroll_speaker(
    name: str = Form(...),
    voice: str = Form("en-US-GuyNeural"),
    rate: str = Form("+0%"),
    pitch: str = Form("+0Hz"),
    audio: UploadFile = File(...)
):
    """
    Step 2: Enrolls a new user voice sample and stores their profile.
    """
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    # Save uploaded audio file to disk
    audio_path = config.paths.audio_dir / f"{clean_name.lower()}_enrolled.wav"
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    voice_pref = {
        "voice": voice,
        "rate": rate,
        "pitch": pitch
    }

    profile = chatbot.speaker_system.register_user(clean_name, str(audio_path), voice_preference=voice_pref)
    return {
        "status": "success",
        "message": f"User '{clean_name}' successfully enrolled.",
        "profile": profile
    }


@app.post("/api/step2/text-turn")
def text_dialogue_turn(payload: TextTurnRequest):
    """
    Step 2: Conversational chatbot text turn.
    """
    response_text = chatbot.process_text_turn(payload.text, speaker_name=payload.speaker)
    return {
        "speaker": payload.speaker,
        "input": payload.text,
        "response": response_text
    }


@app.post("/api/step2/voice-turn")
async def voice_dialogue_turn(audio: UploadFile = File(...)):
    """
    Step 2: End-to-end voice turn:
    1. Speaker Identification
    2. Whisper ASR Transcription
    3. Conversational quote discovery
    4. Personalized TTS Synthesis
    """
    # Save input audio to temporary file
    temp_input_name = f"voice_input_{uuid.uuid4().hex[:8]}.wav"
    temp_input_path = AUDIO_CACHE_DIR / temp_input_name

    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    try:
        # Run end-to-end pipeline
        turn_result = chatbot.process_voice_turn(str(temp_input_path))

        # Copy synthesized audio response to cache directory for static serving
        resp_audio_id = f"resp_{uuid.uuid4().hex[:8]}.mp3"
        cached_resp_path = AUDIO_CACHE_DIR / resp_audio_id

        if os.path.exists(turn_result["audio_response_path"]):
            shutil.copyfile(turn_result["audio_response_path"], cached_resp_path)
            audio_url = f"/api/audio/{resp_audio_id}"
        else:
            audio_url = None

        return {
            "status": "success",
            "speaker": turn_result["speaker"],
            "confidence": turn_result["confidence"],
            "transcription": turn_result["transcription"],
            "response": turn_result["response"],
            "voice_used": turn_result["voice_used"],
            "audio_url": audio_url
        }
    finally:
        # Clean up input temporary audio
        if temp_input_path.exists():
            temp_input_path.unlink()


@app.get("/api/audio/{filename}")
def get_audio_file(filename: str):
    """Serves synthesized audio response files."""
    file_path = AUDIO_CACHE_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")
