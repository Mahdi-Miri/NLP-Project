import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.dialogue.inconsistency import InconsistencyReport

logger = logging.getLogger(__name__)


class DialogueTurn(BaseModel):
    user_utterance: str
    system_response: str
    active_artist: Optional[str] = None
    active_artwork: Optional[str] = None
    active_location: Optional[str] = None
    inconsistency_report: Optional[InconsistencyReport] = None


class DialogueState(BaseModel):
    active_artist: Optional[str] = None
    active_artwork: Optional[Dict[str, Any]] = None
    active_location: Optional[Dict[str, Any]] = None
    turn_counter: int = 0
    history: List[DialogueTurn] = Field(default_factory=list)
    inconsistency_history: List[InconsistencyReport] = Field(default_factory=list)


class DialogueStateTracker:
    def __init__(self):
        self.state = DialogueState()

    def get_state(self) -> DialogueState:
        return self.state

    def update_with_turn(
        self,
        user_utterance: str,
        system_response: str,
        artwork: Optional[Dict[str, Any]] = None,
        artist: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        inconsistency: Optional[InconsistencyReport] = None,
    ):
        self.state.turn_counter += 1

        if artwork:
            self.state.active_artwork = artwork
            if not artist and "artist" in artwork:
                self.state.active_artist = artwork["artist"]
            if not location and "location" in artwork:
                self.state.active_location = artwork.get("location_details") or {"name": artwork["location"]}

        if artist:
            self.state.active_artist = artist

        if location:
            self.state.active_location = location

        if inconsistency and inconsistency.is_inconsistent:
            self.state.inconsistency_history.append(inconsistency)

        turn = DialogueTurn(
            user_utterance=user_utterance,
            system_response=system_response,
            active_artist=self.state.active_artist,
            active_artwork=self.state.active_artwork.get("title") if self.state.active_artwork else None,
            active_location=self.state.active_location.get("name") if self.state.active_location else None,
            inconsistency_report=inconsistency,
        )
        self.state.history.append(turn)

    def resolve_anaphora(self, utterance: str) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {}
        u_lower = utterance.lower()

        art_patterns = [
            r"\b(it|its|this|that)\b",
            r"\b(this|that|the)\s+(work|painting|canvas|piece|masterpiece)\b",
        ]
        if any(re.search(p, u_lower) for p in art_patterns):
            if self.state.active_artwork:
                resolved["artwork"] = self.state.active_artwork

        artist_patterns = [
            r"\b(he|him|his)\b",
            r"\b(the|this)\s+(painter|artist|author|creator)\b",
        ]
        if any(re.search(p, u_lower) for p in artist_patterns):
            if self.state.active_artist:
                resolved["artist"] = self.state.active_artist

        loc_patterns = [
            r"\b(there|here)\b",
            r"\b(this|the)\s+(venue|museum|church|gallery|place|site)\b",
        ]
        if any(re.search(p, u_lower) for p in loc_patterns):
            if self.state.active_location:
                resolved["location"] = self.state.active_location

        return resolved

    def reset(self):
        self.state = DialogueState()
