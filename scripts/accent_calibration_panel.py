import json
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SAMPLES_DIR = PROJECT_ROOT / "data" / "accent_test_samples"
REF_PATH = SAMPLES_DIR / "reference_sentences.json"
SENTENCES = json.loads(REF_PATH.read_text())
ORDER = list(SENTENCES.keys())

st.set_page_config(page_title="Accent Calibration", layout="centered")

if "calib_idx" not in st.session_state:
    recorded = {p.stem for p in SAMPLES_DIR.glob("s*.wav")}
    st.session_state.calib_idx = next(
        (i for i, sid in enumerate(ORDER) if sid not in recorded), len(ORDER)
    )

st.title("Accent Calibration")

if st.session_state.calib_idx >= len(ORDER):
    st.success("All 10 sentences recorded. You can close this tab.")
    st.write("Recorded files:", sorted(p.name for p in SAMPLES_DIR.glob("s*.wav")))
    st.stop()

sid = ORDER[st.session_state.calib_idx]
st.progress((st.session_state.calib_idx) / len(ORDER))
st.caption(f"Sentence {st.session_state.calib_idx + 1} of {len(ORDER)}")
st.markdown(f"## {SENTENCES[sid]}")

audio = st.audio_input("Record", key=f"audio_{sid}")

col1, col2 = st.columns(2)
with col1:
    if audio is not None and st.button("Save and next", type="primary"):
        (SAMPLES_DIR / f"{sid}.wav").write_bytes(audio.getvalue())
        st.session_state.calib_idx += 1
        st.rerun()
with col2:
    if st.button("Skip"):
        st.session_state.calib_idx += 1
        st.rerun()
