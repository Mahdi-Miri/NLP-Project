import os
import sys
import tempfile
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import config
from src.data_pipeline.sparql_client import DBpediaSPARQLClient
from src.data_pipeline.graph_db import NeapolitanArtGraph
from src.dialogue.chatbot import NeapolitanArtChatbot
from src.dialogue.inconsistency import InconsistencyDetector, InconsistencyType
from src.speech.speech_chatbot import NeapolitanSpeechChatbot
from src.speech.asr import SpeechRecognizer
from src.speech.tts import TextToSpeechSynthesizer

st.set_page_config(
    page_title="Neapolitan Art Dialogue System | Caravaggio & Caracciolo",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        color-scheme: light !important;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"], .main {
        background-color: #fcfcfd !important;
        color: #0f172a !important;
        color-scheme: light !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    @media (prefers-color-scheme: dark) {
        :root, html, body, .stApp, [data-testid="stAppViewContainer"], .main {
            background-color: #fcfcfd !important;
            color: #0f172a !important;
            color-scheme: light !important;
        }
        section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }
        .stMarkdown, p, span, label, h1, h2, h3, h4, h5, h6 {
            color: #0f172a !important;
        }
        input, textarea, select, [data-baseweb="input"], [data-baseweb="base-input"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
    }
    
    header[data-testid="stHeader"] {
        background-color: #fcfcfd !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* Academic Header */
    .academic-header {
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 14px;
        margin-bottom: 24px;
    }
    .academic-title {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.01em;
    }
    .academic-subtitle {
        font-size: 14px;
        color: #64748b;
        margin-top: 4px;
    }
    
    /* Inconsistency Alert Box */
    .inconsistency-box {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 14px 18px;
        border-radius: 4px;
        margin-bottom: 16px;
    }
    .inconsistency-title {
        font-weight: 700;
        color: #991b1b;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .inconsistency-body {
        font-size: 14px;
        color: #7f1d1d;
        line-height: 1.5;
    }
    
    /* Dialogue State Card */
    .state-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 16px;
    }
    .state-title {
        font-size: 13px;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }
    .state-item {
        font-size: 14px;
        color: #1e293b;
        margin-bottom: 4px;
    }
    
    /* Conversation Bubbles */
    .chat-bubble-user {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
        color: #0f172a;
    }
    .chat-bubble-system {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 16px;
        color: #1e293b;
        line-height: 1.6;
    }
    
    /* Catalog Artwork Cards */
    .art-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .art-title {
        font-size: 16px;
        font-weight: 600;
        color: #0f172a;
    }
    .art-meta {
        font-size: 13px;
        color: #64748b;
        margin-top: 4px;
        margin-bottom: 8px;
    }
    .art-desc {
        font-size: 14px;
        color: #334155;
        line-height: 1.5;
        margin-bottom: 12px;
    }
    
    /* Verified Resource Links */
    .art-links-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
        padding-top: 10px;
        border-top: 1px solid #f1f5f9;
    }
    .art-link {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: 600;
        text-decoration: none !important;
        background-color: #eff6ff;
        color: #1d4ed8 !important;
        border: 1px solid #bfdbfe;
        transition: all 0.15s ease-in-out;
    }
    .art-link:hover {
        background-color: #2563eb;
        color: #ffffff !important;
        border-color: #2563eb;
    }
    .art-link-secondary {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: 500;
        text-decoration: none !important;
        background-color: #f8fafc;
        color: #475569 !important;
        border: 1px solid #e2e8f0;
        transition: all 0.15s ease-in-out;
    }
    .art-link-secondary:hover {
        background-color: #0f172a;
        color: #ffffff !important;
        border-color: #0f172a;
    }
    
    /* Card Accordion Details */
    details.art-details {
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #f1f5f9;
    }
    details.art-details summary {
        font-size: 12px;
        font-weight: 600;
        color: #64748b;
        cursor: pointer;
        user-select: none;
        outline: none;
        transition: color 0.15s ease;
    }
    details.art-details summary:hover {
        color: #2563eb;
    }
    details.art-details[open] summary {
        color: #2563eb;
        margin-bottom: 8px;
    }
    
    /* Venue Card */
    .venue-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 14px;
        height: 100%;
    }
    .venue-name {
        font-weight: 600;
        font-size: 14px;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .venue-meta {
        font-size: 12px;
        color: #64748b;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_system_pipeline():
    client = DBpediaSPARQLClient()
    corpus = client.fetch_neapolitan_corpus(force_refresh=False)
    graph = NeapolitanArtGraph()
    graph.populate(corpus)
    chatbot = NeapolitanArtChatbot(graph=graph)
    asr = SpeechRecognizer()
    tts = TextToSpeechSynthesizer()
    pipeline = NeapolitanSpeechChatbot(chatbot=chatbot, asr=asr, tts=tts)
    return client, graph, pipeline


if "dialogue_history" not in st.session_state:
    st.session_state.dialogue_history = []
if "latest_audio_path" not in st.session_state:
    st.session_state.latest_audio_path = None
if "latest_inconsistency" not in st.session_state:
    st.session_state.latest_inconsistency = None
if "mic_widget_version" not in st.session_state:
    st.session_state.mic_widget_version = 0

client, graph, pipeline = load_system_pipeline()

st.markdown(
    """
    <div class="academic-header">
        <div class="academic-title">Neapolitan Artistic Heritage Speech Dialogue System</div>
        <div class="academic-subtitle">
            Natural Language Processing | University of Naples Federico II<br>
            Works by Caravaggio and Battistello Caracciolo visitable in the urban area of Naples
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("System Architecture")
    st.markdown(f"**Knowledge Graph Backend:** `{graph.active_backend.upper()}`")
    st.markdown(f"**SPARQL Endpoint:** `https://dbpedia.org/sparql`")
    st.markdown(f"**ASR Model:** `OpenAI Whisper ({config.speech.asr_model_name})`")
    st.markdown(f"**TTS Synthesizer:** `{config.speech.tts_engine.upper()} ({config.speech.tts_voice})`")

    st.markdown("---")
    st.subheader("Dialogue Controls")
    if st.button("Reset Dialogue Memory", use_container_width=True):
        pipeline.reset()
        st.session_state.dialogue_history = []
        st.session_state.latest_audio_path = None
        st.session_state.latest_inconsistency = None
        st.session_state.last_processed_audio_bytes = None
        st.session_state.mic_widget_version += 1
        st.success("Dialogue context and entity memory cleared.")
        st.rerun()

    if st.button("Re-sync DBpedia SPARQL", use_container_width=True):
        with st.spinner("Fetching latest RDF triples from DBpedia..."):
            fresh_corpus = client.fetch_neapolitan_corpus(force_refresh=True)
            graph.populate(fresh_corpus)
            st.success("Graph re-synchronized with DBpedia.")

    st.markdown("---")
    st.subheader("Catalog Statistics")
    all_artworks = graph.get_all_artworks()
    venues = graph.get_all_locations()
    artists = graph.get_all_artists()
    st.markdown(f"- Total Artworks in Naples: **{len(all_artworks)}**")
    st.markdown(f"- Cultural Venues: **{len(venues)}**")
    st.markdown(f"- Target Artists: **Caravaggio, Battistello Caracciolo**")

col_chat, col_state = st.columns([7, 3])

with col_state:
    st.markdown("### Dialogue State Tracker")
    curr_state = pipeline.chatbot.tracker.get_state()
    active_artist = curr_state.active_artist or "None (unspecified)"
    active_art = curr_state.active_artwork.get("title") if curr_state.active_artwork else "None (unspecified)"
    active_loc = curr_state.active_location.get("name") if curr_state.active_location else "None (unspecified)"

    st.markdown(
        f"""
        <div class="state-card">
            <div class="state-title">Discourse Memory State</div>
            <div class="state-item"><strong>Active Artist:</strong> {active_artist}</div>
            <div class="state-item"><strong>Active Artwork:</strong> {active_art}</div>
            <div class="state-item"><strong>Active Venue:</strong> {active_loc}</div>
            <div class="state-item"><strong>City Focus:</strong> Naples</div>
            <div class="state-item"><strong>Turn Counter:</strong> {curr_state.turn_counter}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.latest_inconsistency and st.session_state.latest_inconsistency.is_inconsistent:
        inc = st.session_state.latest_inconsistency
        st.markdown(
            f"""
            <div class="inconsistency-box">
                <div class="inconsistency-title">Inconsistency Detected [{inc.inconsistency_type.value}]</div>
                <div class="inconsistency-body">
                    <strong>Explanation:</strong> {inc.explanation}<br>
                    <strong>Correction:</strong> {inc.suggested_correction}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_chat:
    st.markdown("### Spoken Voice & Text Inquiry")

    mic_audio = st.audio_input(
        "Record voice question via microphone:",
        key=f"mic_audio_{st.session_state.mic_widget_version}",
    )

    user_text = st.text_input(
        "Or type your question directly:",
        placeholder="e.g. Can I visit The Seven Works of Mercy at Capodimonte?",
        key="user_text_input",
    )

    submit_text = st.button("Submit Question", type="primary")

    if mic_audio is not None:
        audio_bytes = mic_audio.read()
        if audio_bytes and audio_bytes != st.session_state.get("last_processed_audio_bytes"):
            st.session_state["last_processed_audio_bytes"] = audio_bytes
            with st.spinner("Transcribing speech with Whisper ASR and querying knowledge graph..."):
                turn_res = pipeline.process_voice_turn(audio_bytes)
                st.session_state.latest_audio_path = turn_res.response_audio_path
                st.session_state.latest_inconsistency = turn_res.inconsistency_report
                st.session_state.dialogue_history.append(
                    {
                        "user": turn_res.user_utterance,
                        "system": turn_res.system_response,
                        "audio_path": turn_res.response_audio_path,
                        "inconsistency": turn_res.inconsistency_report,
                    }
                )
                st.rerun()

    if submit_text and user_text.strip():
        with st.spinner("Querying knowledge graph and synthesizing spoken response..."):
            turn_res = pipeline.process_text_turn(user_text.strip())
            st.session_state.latest_audio_path = turn_res.response_audio_path
            st.session_state.latest_inconsistency = turn_res.inconsistency_report
            st.session_state.dialogue_history.append(
                {
                    "user": turn_res.user_utterance,
                    "system": turn_res.system_response,
                    "audio_path": turn_res.response_audio_path,
                    "inconsistency": turn_res.inconsistency_report,
                }
            )
            st.rerun()

    if st.session_state.dialogue_history:
        latest = st.session_state.dialogue_history[-1]
        st.markdown(f"<div class='chat-bubble-user'><strong>Your Inquiry:</strong> {latest['user']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-bubble-system'><strong>System Response:</strong><br>{latest['system']}</div>", unsafe_allow_html=True)

        if st.session_state.latest_audio_path and os.path.exists(st.session_state.latest_audio_path):
            st.markdown("#### Spoken Audio Playback (TTS)")
            st.audio(st.session_state.latest_audio_path, format="audio/mp3")

st.markdown("---")
with st.expander("Cultural Heritage Knowledge Graph & DBpedia Ground Truth Catalog", expanded=False):
    st.markdown("### Cultural Heritage Knowledge Catalog (Naples, Italy)")
    st.markdown(
        "Ground truth acquired via SPARQL queries to DBpedia and modeled in the Knowledge Graph."
    )

    cat_col1, cat_col2 = st.columns([1, 1])

    with cat_col1:
        st.markdown("#### Caravaggio in Naples")
        caravaggio_works = graph.get_artworks_by_artist("Caravaggio")
        for art in caravaggio_works:
            source_link = art.get('source_url', '')
            dbpedia_link = art.get('dbpedia_page', '')
            st.markdown(
                f"""
                <div class="art-card">
                    <div class="art-title">{art['title']} ({art.get('year', '')})</div>
                    <div class="art-meta"><strong>Location:</strong> {art['location']} | {art.get('dimensions', '')}</div>
                    <div class="art-desc">{art.get('description', '')}</div>
                    <details class="art-details">
                        <summary>Provenance & External References</summary>
                        <div class="art-links-container" style="border-top: none; padding-top: 4px; margin-top: 4px;">
                            <a href="{source_link}" target="_blank" rel="noopener noreferrer" class="art-link">Wikipedia Article</a>
                            <a href="{dbpedia_link}" target="_blank" rel="noopener noreferrer" class="art-link-secondary">DBpedia Resource</a>
                        </div>
                    </details>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with cat_col2:
        st.markdown("#### Battistello Caracciolo in Naples")
        battistello_works = graph.get_artworks_by_artist("Battistello")
        for art in battistello_works:
            source_link = art.get('source_url', '')
            dbpedia_link = art.get('dbpedia_page', '')
            st.markdown(
                f"""
                <div class="art-card">
                    <div class="art-title">{art['title']} ({art.get('year', '')})</div>
                    <div class="art-meta"><strong>Location:</strong> {art['location']} | {art.get('dimensions', '')}</div>
                    <div class="art-desc">{art.get('description', '')}</div>
                    <details class="art-details">
                        <summary>Provenance & External References</summary>
                        <div class="art-links-container" style="border-top: none; padding-top: 4px; margin-top: 4px;">
                            <a href="{source_link}" target="_blank" rel="noopener noreferrer" class="art-link">Wikipedia Article</a>
                            <a href="{dbpedia_link}" target="_blank" rel="noopener noreferrer" class="art-link-secondary">DBpedia Resource</a>
                        </div>
                    </details>
                </div>
                """,
                unsafe_allow_html=True,
            )




