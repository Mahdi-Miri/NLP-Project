import os
import sys
import tempfile
import streamlit as st
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import config
from src.step1_graph.autocomplete import QuoteAutocompleter
from src.step1_graph.graph_db import get_quote_graph
from src.step2_voice.chatbot import WhichQuoteChatbot

# Page configuration
st.set_page_config(
    page_title="NLP Project - Citation Search and Speech Interface",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Clean Light Styling (No Emojis, Authentic Academic Engineering Interface)
st.markdown("""
<style>
    /* Force Light Theme */
    [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Typography */
    .app-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin-bottom: 0.15rem;
    }
    .app-subtitle {
        color: #64748B;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    
    /* Cards and Containers */
    .card-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    .quote-result {
        background-color: #F8FAFC;
        border-left: 4px solid #2563EB;
        border-radius: 4px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .quote-body {
        font-size: 1.1rem;
        color: #0F172A;
        line-height: 1.5;
        margin-bottom: 0.5rem;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-author {
        background-color: #EFF6FF;
        color: #1D4ED8;
    }
    .badge-source {
        background-color: #F1F5F9;
        color: #475569;
    }
    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 0.4rem;
    }
    .hint-text {
        color: #64748B;
        font-size: 0.85rem;
        margin-top: -0.3rem;
        margin-bottom: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_system():
    graph = get_quote_graph()
    ac = QuoteAutocompleter(graph)
    bot = WhichQuoteChatbot(autocompleter=ac)
    return graph, ac, bot


graph, autocompleter, chatbot = load_system()

# Sidebar: System Information & Database Counts
with st.sidebar:
    st.markdown("### Database Statistics")
    stats = graph.get_stats()
    st.write(f"Indexed Quotes: **{stats.get('quotes', 0)}**")
    st.write(f"Indexed Authors: **{stats.get('authors', 0)}**")
    st.write(f"Indexed Works: **{stats.get('works', 0)}**")

    st.markdown("---")
    st.markdown("### Enrolled Speakers")
    users = chatbot.speaker_system.list_users()
    if users:
        for u in users:
            st.markdown(f"- **{u}**")
    else:
        st.write("No speakers registered yet.")

    st.markdown("---")
    st.caption("Corso di Natural Language Processing")

# Main Header - Humanized Academic Presentation
st.markdown('<div class="app-title">Natural Language Processing - University Project</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Knowledge Graph Citation Search & Speech Recognition Interface</div>', unsafe_allow_html=True)

# Main Navigation Tabs (Clean and Direct)
tab1, tab2, tab3 = st.tabs([
    "1. Citation Search (Step 1)",
    "2. Speech Query (Step 2)",
    "3. Speaker Enrollment"
])


# ==========================================
# TAB 1: STEP 1 CITATION SEARCH
# ==========================================
with tab1:
    st.markdown('<div class="section-header">Step 1: Knowledge Graph Autocomplete & Retrieval</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-text">Type a phrase to autocomplete citations from the graph database and inspect matching sources.</div>', unsafe_allow_html=True)

    # Clean preset test buttons
    st.write("Sample queries:")
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    with col_b1:
        if st.button("Stay hungry", use_container_width=True):
            st.session_state["quote_input"] = "Stay hungry"
    with col_b2:
        if st.button("To be, or not", use_container_width=True):
            st.session_state["quote_input"] = "To be, or not"
    with col_b3:
        if st.button("Imagination is", use_container_width=True):
            st.session_state["quote_input"] = "Imagination is"
    with col_b4:
        if st.button("Darkness cannot", use_container_width=True):
            st.session_state["quote_input"] = "Darkness cannot"

    current_val = st.session_state.get("quote_input", "Stay hungry")
    user_query = st.text_input("Search phrase:", value=current_val)

    if user_query.strip():
        trace = autocompleter.autocomplete_with_trace(user_query, top_k=3)
        results = trace.get("results", [])

        st.write(f"Search Latency: **{trace.get('execution_time_ms', 0)} ms** | Method: **{trace.get('strategy', 'N/A')}**")

        if results:
            st.markdown("#### Matched Citations")
            for item in results:
                categories_text = ", ".join(item.get("categories", [])) if item.get("categories") else "General"
                st.markdown(f"""
                <div class="quote-result">
                    <div class="quote-body">"{item['full_quote']}"</div>
                    <div style="margin-top: 0.5rem; line-height: 1.8;">
                        <span class="badge badge-author">Author: {item['author']}</span>
                        <span class="badge badge-source">Work: {item['work']}</span>
                        <span class="badge" style="background:#F1F5F9; color:#334155;">Source: {item['source']}</span>
                        <span class="badge" style="background:#F8FAFC; color:#64748B;">Categories: {categories_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Optional Technical Inspection for Graph Traversal & Cypher Query
            with st.expander("Technical Details: Graph Relationships & Cypher Query"):
                if trace.get("dot_graph"):
                    st.caption("Graph Schema Visualization:")
                    st.graphviz_chart(trace["dot_graph"])
                st.caption("Neo4j Cypher Query:")
                st.code(trace.get("cypher_code", ""), language="cypher")
        else:
            st.info("No matching citation found in the graph database. Try another phrase.")


# ==========================================
# TAB 2: STEP 2 SPEECH QUERY
# ==========================================
with tab2:
    st.markdown('<div class="section-header">Step 2: Speech Recognition & Speaker Verification</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-text">Submit an audio query through the microphone or an audio file. The system identifies the speaker, transcribes speech, and plays a synthesized response.</div>', unsafe_allow_html=True)

    input_method = st.radio("Input Method:", ["Microphone Input", "Upload Audio File"], horizontal=True)

    voice_bytes = None
    if input_method == "Microphone Input":
        mic_recording = st.audio_input("Record Voice:")
        if mic_recording is not None:
            voice_bytes = mic_recording.read()
    else:
        file_upload = st.file_uploader("Upload Audio File (WAV, MP3):", type=["wav", "mp3", "m4a", "ogg"])
        if file_upload is not None:
            voice_bytes = file_upload.read()

    if voice_bytes is not None:
        if st.button("Run Speech Query", type="primary"):
            with st.spinner("Processing speech recognition and database retrieval..."):
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
                    tmp_audio.write(voice_bytes)
                    tmp_path = tmp_audio.name

                try:
                    result = chatbot.process_voice_turn(tmp_path)

                    st.markdown("---")
                    st.markdown("#### Query Results")

                    # Speaker identification status
                    speaker = result.get("speaker", "Guest")
                    conf = result.get("confidence", 0.0)
                    threshold = result.get("threshold", 0.50)
                    closest = result.get("closest_match")
                    closest_score = result.get("closest_score", 0.0)

                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        if speaker != "Guest":
                            st.success(f"Speaker Identity: **{speaker}**")
                            st.caption(f"Verification Score: {conf:.2f} (Threshold: {threshold:.2f})")
                        else:
                            all_users = chatbot.speaker_system.list_users()
                            if not all_users:
                                st.warning("Speaker Identity: **Guest** (No speaker profiles registered yet. You can enroll in tab 3).")
                            elif closest:
                                st.info(f"Speaker Identity: **Guest** (Closest enrolled speaker: '{closest}' with similarity {closest_score:.2f}, below threshold {threshold:.2f}).")
                            else:
                                st.info(f"Speaker Identity: **Guest** (Score: {conf:.2f} < Threshold: {threshold:.2f}).")

                    with col_s2:
                        st.write(f"Synthesizer Voice Profile: **{result.get('voice_used', 'Default')}**")

                    # Speech transcription
                    transcribed = result.get("transcription", "")
                    if transcribed:
                        st.markdown(f"**Speech Transcription:** \"{transcribed}\"")
                    else:
                        st.warning("No speech detected. Please speak closer to the microphone.")

                    # Response
                    st.markdown(f"**Response:** {result.get('response', '')}")

                    # Audio playback
                    audio_out_path = result.get("audio_response_path")
                    if audio_out_path and os.path.exists(audio_out_path):
                        st.markdown("#### Spoken Audio Output")
                        st.audio(audio_out_path, format="audio/mp3")

                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)


# ==========================================
# TAB 3: SPEAKER ENROLLMENT
# ==========================================
with tab3:
    st.markdown('<div class="section-header">Step 3: Speaker Enrollment</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-text">Register a speaker voice profile. The system computes a speaker acoustic embedding for voice verification.</div>', unsafe_allow_html=True)

    col_reg1, col_reg2 = st.columns(2)
    with col_reg1:
        reg_name = st.text_input("Speaker Name:", placeholder="e.g. Mahdi")
    with col_reg2:
        voice_choice = st.selectbox(
            "Output Voice Profile:",
            [
                ("en-US-GuyNeural", "Standard English - Speaker 1 (Male)"),
                ("en-US-JennyNeural", "Standard English - Speaker 2 (Female)"),
                ("en-GB-RyanNeural", "British English - Speaker 3 (Male)"),
                ("en-GB-SoniaNeural", "British English - Speaker 4 (Female)"),
                ("en-AU-WilliamNeural", "Australian English - Speaker 5 (Male)")
            ],
            format_func=lambda x: f"{x[1]}"
        )

    st.write("Record an audio sample of your voice (say: 'My name is [Name]'):")
    enroll_recording = st.audio_input("Record Speaker Voice Sample:")

    if st.button("Register Speaker", type="primary"):
        if not reg_name.strip():
            st.error("Please enter a name.")
        elif enroll_recording is None:
            st.error("Please record an audio sample first.")
        else:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_enroll:
                tmp_enroll.write(enroll_recording.read())
                tmp_enroll_path = tmp_enroll.name

            try:
                chatbot.speaker_system.register_user(
                    reg_name.strip(),
                    tmp_enroll_path,
                    voice_preference={"voice": voice_choice[0], "rate": "+0%", "pitch": "+0Hz"}
                )
                st.success(f"Speaker '{reg_name.strip()}' registered successfully.")
                st.rerun()
            finally:
                if os.path.exists(tmp_enroll_path):
                    os.unlink(tmp_enroll_path)
