from pathlib import Path
from pydantic import BaseModel, Field


class PathSettings(BaseModel):
    # Base project directories
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    raw_data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw")
    processed_data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed")
    audio_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "audio_samples")
    profiles_path: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed" / "speaker_profiles.json")
    embeddings_path: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed" / "speaker_embeddings.npz")
    local_db_path: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed" / "wikiquote_graph.db")


class GraphDBSettings(BaseModel):
    # Neo4j connection defaults
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"

    # Backend selection: 'sqlite' (embedded zero-setup) or 'neo4j'
    default_backend: str = "sqlite"


class VoiceModuleSettings(BaseModel):
    # ASR model configuration
    asr_model_name: str = "base"
    asr_device: str = "cpu"

    # Speaker recognition configuration
    speaker_model_source: str = "speechbrain/spkrec-ecapa-voxceleb"
    speaker_similarity_threshold: float = 0.50
    sample_rate: int = 16000

    # TTS configuration
    tts_engine: str = "edge"  # 'edge' or 'pyttsx3'
    default_voice: str = "en-US-GuyNeural"
    voice_presets: dict = {
        "User1": {"voice": "en-US-GuyNeural", "rate": "+0%", "pitch": "+0Hz"},
        "User2": {"voice": "en-US-JennyNeural", "rate": "+0%", "pitch": "+0Hz"},
        "Scholar": {"voice": "en-GB-RyanNeural", "rate": "-5%", "pitch": "-2Hz"},
        "Default": {"voice": "en-US-AriaNeural", "rate": "+0%", "pitch": "+0Hz"}
    }


class AppConfig(BaseModel):
    paths: PathSettings = PathSettings()
    graph_db: GraphDBSettings = GraphDBSettings()
    voice: VoiceModuleSettings = VoiceModuleSettings()


config = AppConfig()

# Ensure directories exist
config.paths.raw_data_dir.mkdir(parents=True, exist_ok=True)
config.paths.processed_data_dir.mkdir(parents=True, exist_ok=True)
config.paths.audio_dir.mkdir(parents=True, exist_ok=True)
