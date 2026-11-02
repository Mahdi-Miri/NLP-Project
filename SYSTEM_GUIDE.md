# Neapolitan Artistic Heritage Speech Dialogue System
## Technical Architecture & Execution Manual

**Course:** Natural Language Processing  
**Institution:** University of Naples Federico II  
**Domain:** Works by Caravaggio and Battistello Caracciolo visitable in the urban area of Naples

---

## 1. Modular Architecture Overview

```
NLP-Project/
├── app.py                         # Streamlit Light-Mode UI (Voice, Chat, State, Graph, Inspector)
├── config/
│   └── settings.py                # System settings (SPARQL, Neo4j, ASR, TTS, paths)
├── src/
│   ├── data_pipeline/
│   │   ├── curated_dataset.py     # Authoritative Neapolitan masterworks & ground-truth entities
│   │   ├── sparql_client.py       # DBpedia SPARQL Wrapper (fetches and enriches RDF triples)
│   │   └── graph_db.py            # Dual Graph Engine (Neo4j Cypher + Standalone Local SQLite)
│   ├── dialogue/
│   │   ├── inconsistency.py       # Contradiction Detection Engine (Attribution, Venue, City, Scope)
│   │   ├── state_tracker.py       # Multi-Turn Dialogue State & Discourse Coreference Tracker
│   │   └── chatbot.py             # Academic Knowledge-Grounded Conversational Dialogue Manager
│   ├── speech/
│   │   ├── asr.py                 # OpenAI Whisper ASR (robust float32 audio transcription)
│   │   ├── tts.py                 # Neural Edge-TTS Synthesizer with Offline pyttsx3 Fallback
│   │   └── speech_chatbot.py      # Unified Multimodal Voice Pipeline (Audio in -> Audio out)
│   └── utils/
│       └── audio_utils.py         # Audio normalization, resampling (16kHz mono), and format converters
├── scripts/
│   ├── build_graph.py             # Automated graph population and verification script
│   └── interactive_cli.py         # Terminal-based conversational evaluation interface
├── tests/
│   ├── conftest.py                # Pytest path and environment fixtures
│   ├── test_dialogue.py           # Multi-turn conversation and pronoun resolution tests
│   └── test_inconsistency.py      # Automated tests for all inconsistency types
└── data/
    ├── dbpedia_cache.json         # Cached snapshot of DBpedia RDF query results
    └── neapolitan_art_graph.db    # Embedded SQLite knowledge graph
```

---

## 2. Step-by-Step Module Execution

### Step 1: SPARQL Ingestion & Graph Building
To query DBpedia (`https://dbpedia.org/sparql`) and construct the knowledge graph:
```bash
.venv/bin/python scripts/build_graph.py
```
This executes:
1. Dynamic SPARQL queries on DBpedia for Caravaggio and Battistello Caracciolo.
2. Neo4j connectivity check and schema constraint initialization.
3. Graph node and edge population with fallback to local SQLite graph store.
4. Summary verification of all cataloged works across Neapolitan venues.

### Step 2: Running Automated Pytest Test Suite
To verify dialogue state tracking and inconsistency detection algorithms:
```bash
.venv/bin/pytest tests/
```
All unit tests validate:
- Artist attribution contradiction detection (e.g., claiming Battistello painted *The Seven Works of Mercy*).
- Venue mismatch contradiction detection (e.g., claiming *The Seven Works of Mercy* is at Capodimonte).
- Geographic mismatch contradiction detection (e.g., asking for Roman works like *The Calling of Saint Matthew* in Naples).
- Out-of-scope artist filtering (e.g., Leonardo da Vinci).
- Multi-turn state resolution and coreference handling.

### Step 3: Interactive Command Line Interface (CLI)
To test conversation turns directly from the terminal:
```bash
.venv/bin/python scripts/interactive_cli.py
```

### Step 4: Web Application (Streamlit)
To launch the complete speech dialogue web application:
```bash
.venv/bin/streamlit run app.py --server.port 8502
```
Access via browser at `http://localhost:8502`.

---

## 3. Inconsistency Detection Taxonomy

The system detects four primary classes of user contradictions:

| Violation Class | Example User Question | Detected Contradiction | Ground-Truth Correction |
|---|---|---|---|
| **Artist Mismatch** | *"Did Battistello paint The Seven Works of Mercy?"* | Attributing Caravaggio's work to Battistello | Caravaggio painted it in 1607 for Pio Monte della Misericordia. |
| **Venue Mismatch** | *"Can I see The Seven Works of Mercy at Capodimonte?"* | Misidentifying museum venue in Naples | It is permanently located at Pio Monte della Misericordia (Via dei Tribunali). |
| **City Mismatch** | *"Where can I see The Calling of Saint Matthew in Naples?"* | Asking for non-Neapolitan artwork | The painting is in Rome at the Church of San Luigi dei Francesi. |
| **Out-of-Scope Artist** | *"Are there works by Leonardo da Vinci in Naples?"* | Asking about uncataloged master | Focus is strictly Caravaggio and Battistello Caracciolo in Naples. |

---

## 4. Multi-Turn Dialogue State Representation

At each conversation turn, the dialogue state tracker maintains:
- `active_artist`: e.g., `Caravaggio` or `Battistello Caracciolo`
- `active_artwork`: e.g., `The Seven Works of Mercy`
- `active_location`: e.g., `Pio Monte della Misericordia`
- `turn_counter`: integer sequence index
- `history`: full chronological list of dialogue turns and responses
- `inconsistency_history`: log of all flagged user contradictions
