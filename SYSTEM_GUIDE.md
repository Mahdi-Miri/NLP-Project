# Natural Language Processing - Project Guide & Documentation

This repository contains the complete implementation of the university project for the **Corso di Natural Language Processing**, covering both **Step 1** and **Step 2**.

---

## 🏛 System Architecture Overview

```text
                               +-----------------------------+
                               |     User Voice / Mic        |
                               +--------------+--------------+
                                              |
                                              v
                              +---------------+---------------+
                              |    Speaker Identification     |
                              |  (ECAPA-TDNN / Embeddings)   |
                              +---------------+---------------+
                                              | Speaker Identity & Preferences
                                              v
+-------------------------+   +---------------+---------------+
| Automatic Speech Recog. |-->|   "Which Quote?" Chatbot      |
|    (Whisper ASR)        |   |   Conversational Agent        |
+-------------------------+   +---------------+---------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
      +------------------------------+                 +-------------------------------+
      |    Step 1: Graph Database    |                 |   Personalized TTS Synthesizer|
      |   - Quotes, Authors, Works   |                 |   - Voice: Persona & Accents  |
      |   - Full-Text Search (FTS)   |                 |   - Rate & Pitch Controls     |
      |   - Citation Autocomplete    |                 +---------------+---------------+
      +------------------------------+                                 | Spoken Audio
                                                                       v
                                                       +---------------+---------------+
                                                       |     Audio Playback/Output     |
                                                       +-------------------------------+
```

---

## 📁 Repository Structure

```text
NLP-Project/
├── .venv/                      # Isolated Python 3.11 Virtual Environment
├── requirements.txt            # Project dependencies
├── pytest.ini                  # Pytest configuration
├── config/
│   └── settings.py             # Configurable database, model, and path settings
├── src/
│   ├── step1_graph/            # Step 1: Wikiquote Graph & Autocomplete
│   │   ├── parser.py           # Streaming XML parser for MediaWiki dumps
│   │   ├── graph_db.py         # Dual Graph Database (Local SQLite+FTS5 & Neo4j)
│   │   └── autocomplete.py     # Autocomplete engine & citation search
│   ├── step2_voice/            # Step 2: "Which Quote?" Interactive Voice System
│   │   ├── asr.py              # Automatic Speech Recognition (OpenAI Whisper)
│   │   ├── speaker_id.py       # Voice enrollment & cosine-similarity recognition
│   │   ├── tts.py              # Personalized multi-voice Text-to-Speech synthesizer
│   │   └── chatbot.py          # Dialogue manager coordinating voice + graph DB
│   └── utils/
│       ├── audio_utils.py      # Audio recording, loading, and playback
│       └── text_utils.py       # MediaWiki markup stripping & text normalization
├── scripts/
│   ├── download_dump.py        # Wikimedia dump downloader with progress tracking
│   ├── build_graph.py          # Graph builder script (seed data or full dump)
│   └── enroll_speaker.py       # Interactive voice enrollment CLI
├── tests/
│   └── test_pipeline.py        # Automated test suite
└── main.py                     # Master unified interactive CLI & live demo
```

---

## 🚀 Quick Start Guide

### 1. Activate Environment
The virtual environment is located at `.venv`:
```bash
source .venv/bin/activate
```

### 2. Populate Seed Quotes (or Download Full Dump)
To immediately populate the graph database with famous quotes:
```bash
python scripts/build_graph.py --seed
```

To download and parse the official Wikimedia dump:
```bash
# Optional: Download dump (or a slice)
python scripts/download_dump.py --limit-mb 50

# Ingest dump into graph database
python scripts/build_graph.py --dump data/raw/enwikiquote-latest-pages-articles.xml.bz2 --max 5000
```

### 3. Launching the Web Application (Streamlit + FastAPI)

#### Option A: Run Streamlit Directly
```bash
streamlit run app.py --server.port 8502
```
Access the modern UI at: **`http://localhost:8502`**

#### Option B: Run via FastAPI Microservice
In terminal 1 (start FastAPI backend):
```bash
uvicorn src.api.server:app --port 8000 --reload
```
Interactive Swagger API docs available at: **`http://localhost:8000/docs`**

In terminal 2 (start Streamlit frontend):
```bash
streamlit run app.py --server.port 8502
```

### 4. Run the Interactive Unified CLI Demo
Launch the console demo:
```bash
python main.py
```

Menu options available:
- **[1] Step 1: Wikiquote Graph Autocompletion Demo**: Test typing citation beginnings (e.g., `"Stay hungry"`, `"To be, or not"`, `"Imagination is"`) to see real-time completions with author and work attribution.
- **[2] Step 2: "Which Quote?" Voice Agent**: Speak directly into the microphone for 4 seconds; the system identifies who spoke, transcribes the speech, retrieves quotes, and replies with a personalized voice.
- **[3] Step 2: "Which Quote?" Chatbot (Text Mode)**: Interactive conversational interface supporting autocomplete, author lookup (*"Who said darkness cannot drive out darkness?"*), and quiz games (*"quiz"*).
- **[4] Register / Enroll a New Speaker Profile**: Enroll your voice and choose your favorite response persona (Male, Female, Formal, Casual) and pitch/rate adjustments.
- **[5] View Graph Database Statistics**: Inspect current quote and author counts.

### 4. Direct CLI Commands
You can also run specific modes directly:
```bash
# Step 1 interactive autocompleter
python main.py --step 1

# Step 2 interactive voice conversation
python main.py --step 2

# Step 2 interactive text chat
python main.py --step text

# Database statistics
python main.py --step stats
```

---

## 🧪 Running Automated Tests

Run the full pytest suite to verify all components:
```bash
pytest tests/test_pipeline.py -v
```
All unit tests cover:
- MediaWiki markup stripping & citation parsing.
- Graph database nodes, edges, and full-text index querying.
- Quote autocompletion and score ranking.
- Speaker identification and voice profile enrollment.
- Whisper ASR and Personalized TTS synthesis.
