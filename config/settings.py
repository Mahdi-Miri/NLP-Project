from pathlib import Path
from pydantic import BaseModel, Field


class PathSettings(BaseModel):
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    local_db_path: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "neapolitan_art_graph.db")


class SPARQLSettings(BaseModel):
    endpoint_url: str = "https://dbpedia.org/sparql"
    timeout_seconds: int = 25
    user_agent: str = "NLPProjectNeapolitanHeritageBot/1.0 (University of Naples Federico II)"


class Neo4jSettings(BaseModel):
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    # Backend selection: 'sqlite' (embedded standalone) or 'neo4j'
    default_backend: str = "sqlite"


class SpeechSettings(BaseModel):
    asr_model_name: str = "medium"
    asr_device: str = "cpu"
    tts_voice: str = "en-GB-RyanNeural"
    tts_engine: str = "edge"  # 'edge' or 'pyttsx3'


class AppConfig(BaseModel):
    paths: PathSettings = PathSettings()
    sparql: SPARQLSettings = SPARQLSettings()
    neo4j: Neo4jSettings = Neo4jSettings()
    speech: SpeechSettings = SpeechSettings()


config = AppConfig()
config.paths.data_dir.mkdir(parents=True, exist_ok=True)
