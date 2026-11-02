# End-to-End System Pipeline Architecture
## Neapolitan Artistic Heritage Speech Dialogue System

The system operates as an integrated multimodal pipeline connecting semantic web data acquisition (SPARQL/DBpedia), graph database modeling (Neo4j / SQLite), inconsistency detection, dialogue state tracking, automatic speech recognition (ASR), and speech synthesis (TTS).

---

## 1. Complete Pipeline Graph (Mermaid Diagram)

```mermaid
flowchart TD
    %% Input Layer
    subgraph UI ["User Interaction Layer (Web UI & CLI)"]
        UserVoice["User Voice Input<br/>(Microphone Recording)"]
        UserText["User Text Query<br/>(Keyboard Input)"]
    end

    %% Speech-to-Text Layer
    subgraph ASR_Layer ["Speech Recognition (ASR) Engine"]
        AudioNorm["Audio Normalization & Resampling<br/>(16 kHz Mono, Float32)"]
        WhisperASR["OpenAI Whisper Model<br/>(Offline Local Inference)"]
        TranscribedText["Transcribed Utterance<br/>(Text + Language Code)"]
    end

    %% Foundational Data Pipeline
    subgraph Data_Pipeline ["Semantic Data Pipeline (DBpedia SPARQL)"]
        DBpedia["DBpedia SPARQL Endpoint<br/>(https://dbpedia.org/sparql)"]
        SPARQLClient["DBpediaSPARQLClient<br/>(Executes Semantic RDF Queries)"]
        CuratedData["Curated Ground Truth Catalog<br/>(Authoritative Neapolitan Artworks)"]
        CorpusCache["Corpus JSON Cache<br/>(dbpedia_cache.json)"]
    end

    %% Knowledge Graph Storage
    subgraph Graph_Layer ["Knowledge Graph Engine (Dual Backend)"]
        Neo4jStore["Neo4j Graph Store<br/>(Cypher Queries, Unique Constraints)"]
        LocalSQLite["Embedded SQLite Graph Store<br/>(Zero-Dependency Relational Graph)"]
        GraphSchema["Graph Schema:<br/>(:Artist)-[:PAINTED]->(:Artwork)<br/>(:Artwork)-[:LOCATED_AT]->(:Location)<br/>(:Location)-[:IN_CITY]->(:City)"]
    end

    %% Dialogue & Reasoning Engine
    subgraph Dialogue_Engine ["Dialogue Management & Reasoning Engine"]
        StateTracker["Dialogue State Tracker<br/>(Discourse Memory & Anaphora Resolution)"]
        InconsistencyDetector["Inconsistency Detection Engine<br/>- Artist Mismatch<br/>- Location Mismatch in Naples<br/>- City / Geographic Mismatch<br/>- Out-of-Scope Artist Check"]
        KnowledgeGenerator["Response Formulator<br/>(Scholarly, Academic, Grounded)"]
    end

    %% Speech Synthesis Layer
    subgraph TTS_Layer ["Speech Synthesis (TTS) Engine"]
        TTSSelector{"TTS Engine Selector"}
        EdgeTTS["Neural Edge-TTS<br/>(en-GB-RyanNeural)"]
        Pyttsx3["pyttsx3 Synthesizer<br/>(Offline Native Fallback)"]
        AudioOutput["Synthesized Spoken Audio<br/>(MP3 / Audio Playback)"]
    end

    %% Pipeline Dataflow Connections
    UserVoice --> AudioNorm
    AudioNorm --> WhisperASR
    WhisperASR --> TranscribedText
    UserText --> TranscribedText

    DBpedia --> SPARQLClient
    CuratedData --> SPARQLClient
    SPARQLClient --> CorpusCache
    CorpusCache --> Neo4jStore
    CorpusCache --> LocalSQLite
    Neo4jStore --- GraphSchema
    LocalSQLite --- GraphSchema

    TranscribedText --> StateTracker
    StateTracker --> InconsistencyDetector
    LocalSQLite -. Queries .- InconsistencyDetector
    Neo4jStore -. Queries .- InconsistencyDetector

    InconsistencyDetector --> KnowledgeGenerator
    LocalSQLite -. Ground Truth Context .- KnowledgeGenerator
    Neo4jStore -. Ground Truth Context .- KnowledgeGenerator
    StateTracker -. Active Context .- KnowledgeGenerator

    KnowledgeGenerator --> TTSSelector
    TTSSelector -->|Primary| EdgeTTS
    TTSSelector -->|Fallback| Pyttsx3
    EdgeTTS --> AudioOutput
    Pyttsx3 --> AudioOutput

    KnowledgeGenerator --> UI
    AudioOutput --> UI
```

---

## 2. Pipeline Stage Breakdown

### Stage 1: Data Ingestion & Graph Modeling
- **SPARQL Endpoint Queries:** Dynamic retrieval of RDF triples from DBpedia for Caravaggio and Battistello Caracciolo.
- **Entity Merging:** Enriches museum locations (*Pio Monte della Misericordia*, *Museo Nazionale di Capodimonte*, *Gallerie d'Italia Palazzo Zevallos*, *Certosa di San Martino*, *Chiesa della Pietà dei Turchini*) with physical addresses, coordinates, and verified historical metadata.
- **Dual Graph Store:**
  - **Neo4j:** Production-grade graph database queried via Cypher.
  - **Local SQLite Graph Store:** Embedded zero-setup fallback executing matching relational graph traversals.

### Stage 2: Spoken Input Processing (ASR)
- **Audio Preprocessing:** Ingests microphone buffers, resamples audio to 16,000 Hz single-channel float32, and handles format headers.
- **Whisper ASR Inference:** Transcribes voice inquiries locally on device without external API calls or latency overhead.

### Stage 3: Discourse State Tracking & Coreference
- Maintains structured dialogue state:
  - `active_artist`: e.g., Caravaggio or Battistello Caracciolo.
  - `active_artwork`: Current painting under discussion.
  - `active_location`: Physical venue in Naples.
  - `turn_counter`: Chronological exchange counter.
- **Anaphora Resolution:** Uses regex word-boundary patterns to resolve pronouns (`it`, `its dimensions`, `who painted it?`, `where is it located?`, `what else is there?`) to active discourse entities.

### Stage 4: Inconsistency & Contradiction Detection
Validates every user utterance against graph facts before answering:
1. **Artist Attribution Mismatch:** Identifies when an artwork by Caravaggio is falsely attributed to Battistello or vice-versa.
2. **Location Mismatch within Naples:** Catches inquiries placing works at the wrong Neapolitan institution (e.g., *The Seven Works of Mercy* at Capodimonte instead of Pio Monte).
3. **Geographic / City Mismatch:** Flags requests for masterworks permanently housed in Rome (*The Calling of Saint Matthew*), Florence (*Bacchus*), Paris (*Death of the Virgin*), or Malta (*The Beheading of Saint John the Baptist*).
4. **Out-of-Scope Artists:** Polite boundary enforcement when non-cataloged figures (e.g., Leonardo da Vinci, Raphael, Picasso) are asked about.

### Stage 5: Response Generation & Spoken Synthesis (TTS)
- Constructs clear, objective, scholarly responses formatted in humanized English.
- Synthesizes speech using high-fidelity neural voices with offline local fallback.
