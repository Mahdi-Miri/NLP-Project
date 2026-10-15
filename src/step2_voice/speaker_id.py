import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import torch

from config.settings import config
from src.utils.audio_utils import load_audio


class SpeakerIdentificationSystem:
    """
    Speaker recognition module using pre-trained neural speaker embeddings (ECAPA-TDNN).
    Manages user registration, embedding storage, and cosine-similarity speaker verification.
    """

    def __init__(self, model_source: Optional[str] = None, threshold: Optional[float] = None):
        self.model_source = model_source or config.voice.speaker_model_source
        self.threshold = threshold or config.voice.speaker_similarity_threshold
        self.profiles_path = Path(config.paths.profiles_path)
        self.embeddings_path = Path(config.paths.embeddings_path)

        self._encoder = None
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.embeddings: Dict[str, np.ndarray] = {}

        self._load_database()

    def _load_encoder(self):
        """Lazy-loads the pre-trained speaker encoder."""
        if self._encoder is None:
            try:
                from speechbrain.inference.speaker import EncoderClassifier
                print(f"[*] Loading pre-trained speaker encoder '{self.model_source}'...")
                self._encoder = EncoderClassifier.from_hparams(source=self.model_source, run_opts={"device": "cpu"})
                print("[+] Speaker encoder loaded successfully.")
            except Exception as e:
                print(f"[!] Warning: Could not load HuggingFace model ({e}). Using acoustic fallback.")
                self._encoder = "fallback"

    def _load_database(self) -> None:
        """Loads registered user profiles and embedding vectors from disk."""
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
            except Exception as e:
                print(f"[!] Failed to load profiles: {e}")
                self.profiles = {}

        if self.embeddings_path.exists():
            try:
                npz_data = np.load(self.embeddings_path)
                self.embeddings = {name: npz_data[name] for name in npz_data.files}
            except Exception as e:
                print(f"[!] Failed to load embeddings: {e}")
                self.embeddings = {}

    def _save_database(self) -> None:
        """Persists registered profiles and embeddings to disk."""
        profiles_file = Path(self.profiles_path)
        embeddings_file = Path(self.embeddings_path)

        profiles_file.parent.mkdir(parents=True, exist_ok=True)
        with open(profiles_file, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, indent=2)

        if self.embeddings:
            embeddings_file.parent.mkdir(parents=True, exist_ok=True)
            np.savez(embeddings_file, **self.embeddings)

    def extract_embedding(self, audio_input: Any) -> np.ndarray:
        """
        Extracts a normalized speaker embedding vector from an audio file or numpy array.
        """
        self._load_encoder()

        # Handle file path or numpy array
        if isinstance(audio_input, (str, Path)):
            audio_data, sr = load_audio(str(audio_input), target_sr=16000)
        elif isinstance(audio_input, np.ndarray):
            audio_data = audio_input
        else:
            raise TypeError("Expected file path or numpy array for audio input.")

        # Ensure audio has sufficient length (at least ~0.5s)
        if len(audio_data) < 4000:
            audio_data = np.pad(audio_data, (0, 4000 - len(audio_data)), mode="wrap")

        if self._encoder != "fallback":
            tensor = torch.tensor(audio_data, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                emb = self._encoder.encode_batch(tensor)
                emb_np = emb.squeeze().cpu().numpy()
        else:
            # Fallback: lightweight spectral fingerprint
            import scipy.signal
            f, t, spec = scipy.signal.spectrogram(audio_data, fs=16000, nperseg=256)
            emb_np = np.mean(spec, axis=1)[:192]
            if len(emb_np) < 192:
                emb_np = np.pad(emb_np, (0, 192 - len(emb_np)))

        # Normalize to unit length for cosine similarity
        norm = np.linalg.norm(emb_np)
        if norm > 0:
            emb_np = emb_np / norm

        return emb_np.astype(np.float32)

    def register_user(
        self,
        name: str,
        audio_path: str,
        voice_preference: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enrolls a new user by calculating their voice embedding and saving their profile.
        """
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("User name cannot be empty.")

        print(f"[*] Extracting speaker embedding for '{clean_name}'...")
        embedding = self.extract_embedding(audio_path)
        self.embeddings[clean_name] = embedding

        # Assign voice preference or default preset
        default_pref = config.voice.voice_presets.get(
            clean_name,
            config.voice.voice_presets.get("Default", {"voice": "en-US-AriaNeural", "rate": "+0%", "pitch": "+0Hz"})
        )
        pref = voice_preference or default_pref

        self.profiles[clean_name] = {
            "name": clean_name,
            "voice_preference": pref,
            "sample_audio": str(audio_path)
        }

        self._save_database()
        print(f"[+] Successfully registered user '{clean_name}'.")
        return self.profiles[clean_name]

    def identify_speaker(self, audio_input: Any) -> Tuple[str, float, Dict[str, Any]]:
        """
        Compares the input voice against registered embeddings using cosine similarity.
        Returns: (recognized_name, similarity_score, user_profile)
        """
        if not self.embeddings:
            guest_profile = {
                "name": "Guest",
                "voice_preference": config.voice.voice_presets.get("Default")
            }
            return "Guest", 0.0, guest_profile

        target_emb = self.extract_embedding(audio_input)

        best_name = "Guest"
        best_score = -1.0

        for name, registered_emb in self.embeddings.items():
            # Cosine similarity between unit-normalized vectors is simply the dot product
            sim = float(np.dot(target_emb, registered_emb))
            if sim > best_score:
                best_score = sim
                best_name = name

        # Check against similarity threshold
        if best_score < self.threshold:
            guest_profile = {
                "name": "Guest",
                "voice_preference": config.voice.voice_presets.get("Default"),
                "closest_match": best_name if best_name != "Guest" else None,
                "closest_score": round(best_score, 3) if best_score > -1 else 0.0,
                "threshold": self.threshold
            }
            return "Guest", round(best_score, 3), guest_profile

        profile = dict(self.profiles.get(best_name, {}))
        profile["similarity"] = round(best_score, 3)
        return best_name, round(best_score, 3), profile

    def list_users(self) -> List[str]:
        """Returns list of currently registered speaker names."""
        return list(self.profiles.keys())
