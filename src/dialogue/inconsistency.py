"""
Inconsistency Detection Engine for Neapolitan Art Dialogue System.
Detects factual and contextual contradictions in user questions:
- Artist attribution mismatches
- Naples venue/location mismatches
- Non-Neapolitan artwork inquiries (works in Rome, Florence, Paris)
- Out-of-scope artists
- Dialogue state contradictions
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.data_pipeline.curated_dataset import NON_NEAPOLITAN_ARTWORKS

logger = logging.getLogger(__name__)


class InconsistencyType(str, Enum):
    ARTIST_MISMATCH = "artist_mismatch"
    LOCATION_MISMATCH = "location_mismatch"
    CITY_MISMATCH = "city_mismatch"
    OUT_OF_SCOPE_ARTIST = "out_of_scope_artist"
    CONTEXTUAL_CONTRADICTION = "contextual_contradiction"
    NO_INCONSISTENCY = "no_inconsistency"


class InconsistencyReport(BaseModel):
    is_inconsistent: bool = False
    inconsistency_type: InconsistencyType = InconsistencyType.NO_INCONSISTENCY
    confidence: float = 1.0
    explanation: str = ""
    suggested_correction: str = ""
    claimed_entity: Optional[str] = None
    ground_truth_entity: Optional[str] = None


class InconsistencyDetector:
    """
    Rule-based and Graph-grounded Inconsistency Detector.
    Validates user queries against DBpedia-backed ground truth graph.
    """

    KNOWN_ARTISTS = ["caravaggio", "battistello", "battistello caracciolo", "caracciolo"]
    DISALLOWED_FAMOUS_ARTISTS = [
        "leonardo", "leonardo da vinci", "michelangelo", "michelangelo buonarroti",
        "raphael", "raffaello", "bernini", "titian", "tiziano", "rembrandt",
        "vermeer", "velazquez", "picasso", "monet"
    ]

    def __init__(self, graph_db: Any):
        self.graph = graph_db
        self.non_neapolitan_works = NON_NEAPOLITAN_ARTWORKS

    def detect_inconsistencies(
        self,
        query: str,
        dialogue_state: Optional[Dict[str, Any]] = None,
    ) -> InconsistencyReport:
        """
        Main entry point for inconsistency detection.
        Evaluates the query against artwork catalog, venues, and active dialogue state.
        """
        q_lower = self._normalize_query_for_speech(query)

        # 1. Check for Out-of-scope famous artists (e.g., Leonardo da Vinci)
        out_of_scope_match = self._check_out_of_scope_artist(q_lower)
        if out_of_scope_match:
            return out_of_scope_match

        # 2. Check for Non-Neapolitan artworks claimed to be in Naples
        city_mismatch = self._check_non_neapolitan_artwork(q_lower)
        if city_mismatch:
            return city_mismatch

        # 3. Check for Artist Attribution Mismatches
        artist_mismatch = self._check_artist_attribution(q_lower, dialogue_state)
        if artist_mismatch:
            return artist_mismatch

        # 4. Check for Location / Venue Mismatches within Naples
        location_mismatch = self._check_location_venue(q_lower, dialogue_state)
        if location_mismatch:
            return location_mismatch

        # 5. Check Contextual Contradictions against active state
        contextual_mismatch = self._check_contextual_state(q_lower, dialogue_state)
        if contextual_mismatch:
            return contextual_mismatch

        return InconsistencyReport(is_inconsistent=False)

    def _normalize_query_for_speech(self, query: str) -> str:
        """Normalize common speech-to-text phonetic artifacts, numerals, and prepositions."""
        q = query.lower()
        q = re.sub(r"\b7\b", "seven", q)
        q = re.sub(r"\b1st\b", "first", q)
        q = re.sub(r"\b2nd\b", "second", q)
        q = re.sub(r"\bseven\s+works\s+(?:of|for|on)\s+mercy\b", "seven works of mercy", q)
        q = re.sub(r"\bliberation\s+(?:of|for)\s+(?:saint\s+|st\.?\s+)?peter\b", "liberation of saint peter", q)
        q = re.sub(r"\bwashing\s+(?:of|for)\s+(?:the\s+)?feet\b", "washing of the feet", q)
        q = re.sub(r"\bflagellation\s+(?:of|for)\s+christ\b", "flagellation of christ", q)
        q = re.sub(r"\bmartyrdom\s+(?:of|for)\s+(?:saint\s+|st\.?\s+)?ursula\b", "martyrdom of saint ursula", q)
        q = re.sub(r"\bcapo\s+di\s+monte\b", "capodimonte", q)
        q = re.sub(r"\bpio\s+monti\b", "pio monte", q)
        q = re.sub(r"\bst\.?\s+", "saint ", q)
        return q

    def _check_out_of_scope_artist(self, query: str) -> Optional[InconsistencyReport]:
        for artist in self.DISALLOWED_FAMOUS_ARTISTS:
            pattern = r"\b" + re.escape(artist) + r"\b"
            if re.search(pattern, query):
                return InconsistencyReport(
                    is_inconsistent=True,
                    inconsistency_type=InconsistencyType.OUT_OF_SCOPE_ARTIST,
                    explanation=f"The artist '{artist.title()}' is outside the scope of this Neapolitan exhibition.",
                    suggested_correction="This system focuses strictly on Caravaggio and Battistello Caracciolo works visitable in Naples.",
                    claimed_entity=artist.title(),
                    ground_truth_entity="Caravaggio / Battistello Caracciolo",
                )
        return None

    def _check_non_neapolitan_artwork(self, query: str) -> Optional[InconsistencyReport]:
        for item in self.non_neapolitan_works:
            title_lower = item["title"].lower()
            title_no_the = title_lower[4:] if title_lower.startswith("the ") else title_lower
            if title_lower in query or title_no_the in query:
                return InconsistencyReport(
                    is_inconsistent=True,
                    inconsistency_type=InconsistencyType.CITY_MISMATCH,
                    explanation=f"'{item['title']}' is not in Naples. It is located in {item['city']} at {item['location']}.",
                    suggested_correction=f"If you are visiting Naples, you can see Caravaggio's works at Pio Monte della Misericordia, Capodimonte, or Gallerie d'Italia.",
                    claimed_entity=f"{item['title']} in Naples",
                    ground_truth_entity=f"{item['title']} in {item['city']} ({item['location']})",
                )
        return None

    def _check_artist_attribution(
        self, query: str, dialogue_state: Optional[Dict[str, Any]]
    ) -> Optional[InconsistencyReport]:
        all_artworks = self.graph.get_all_artworks()

        for art in all_artworks:
            title_lower = art["title"].lower()
            title_no_the = title_lower[4:] if title_lower.startswith("the ") else title_lower
            it_title = art.get("italian_title", "").lower()
            # Match title in query or pronouns if state has this artwork
            title_matched = (title_lower in query) or (title_no_the in query) or (bool(it_title) and it_title in query)
            if not title_matched and dialogue_state:
                active_art = dialogue_state.get("active_artwork")
                if active_art and active_art.get("title", "").lower() == title_lower:
                    if self._has_artwork_pronoun(query):
                        title_matched = True

            if title_matched:
                true_artist = art["artist"]
                other_artist = "Battistello Caracciolo" if true_artist == "Caravaggio" else "Caravaggio"

                # Check if query falsely attributes this work to the other artist (including phonetic variations)
                other_terms = ["caravaggio", "caravagio", "karavaggio"] if true_artist != "Caravaggio" else ["battistello", "batistello", "caracciolo", "caraciolo"]
                for term in other_terms:
                    pattern = r"\b" + re.escape(term) + r"\b"
                    if re.search(pattern, query):
                        # Verify user is not explicitly asking for clarification (e.g. "Did Caravaggio paint this or Battistello?")
                        if " or " in query and "who" in query:
                            continue

                        return InconsistencyReport(
                            is_inconsistent=True,
                            inconsistency_type=InconsistencyType.ARTIST_MISMATCH,
                            explanation=f"'{art['title']}' was created by {true_artist}, not {other_artist}.",
                            suggested_correction=f"{true_artist} painted '{art['title']}' around {art.get('year', 'the early 17th century')}.",
                            claimed_entity=f"Artist: {other_artist}",
                            ground_truth_entity=f"Artist: {true_artist}",
                        )
        return None

    def _check_location_venue(
        self, query: str, dialogue_state: Optional[Dict[str, Any]]
    ) -> Optional[InconsistencyReport]:
        all_artworks = self.graph.get_all_artworks()
        venues = self.graph.get_all_locations()

        for art in all_artworks:
            title_lower = art["title"].lower()
            title_no_the = title_lower[4:] if title_lower.startswith("the ") else title_lower
            it_title = art.get("italian_title", "").lower()
            title_matched = (title_lower in query) or (title_no_the in query) or (bool(it_title) and it_title in query)
            if not title_matched and dialogue_state:
                active_art = dialogue_state.get("active_artwork")
                if active_art and active_art.get("title", "").lower() == title_lower:
                    if self._has_artwork_pronoun(query):
                        title_matched = True

            if title_matched:
                true_loc = art["location"]
                for venue in venues:
                    venue_name = venue["name"]
                    # If venue is different from the true location
                    if venue_name.lower() != true_loc.lower():
                        # Check venue keywords
                        keywords = self._get_venue_keywords(venue_name)
                        for kw in keywords:
                            pattern = r"\b" + re.escape(kw) + r"\b"
                            if re.search(pattern, query):
                                return InconsistencyReport(
                                    is_inconsistent=True,
                                    inconsistency_type=InconsistencyType.LOCATION_MISMATCH,
                                    explanation=f"'{art['title']}' is not located at {venue_name}. It is permanently housed at {true_loc}.",
                                    suggested_correction=f"To view '{art['title']}', visit {true_loc} located at {art.get('location_details', {}).get('address', 'Naples')}.",
                                    claimed_entity=venue_name,
                                    ground_truth_entity=true_loc,
                                )
        return None

    def _check_contextual_state(
        self, query: str, dialogue_state: Optional[Dict[str, Any]]
    ) -> Optional[InconsistencyReport]:
        if not dialogue_state:
            return None

        active_artwork = dialogue_state.get("active_artwork")
        active_artist = dialogue_state.get("active_artist")

        if active_artwork and active_artist:
            # If current active artwork belongs to Caravaggio and user references Battistello with "he" or "his"
            true_artist = active_artwork.get("artist")
            if true_artist == "Caravaggio" and ("battistello" in query or "caracciolo" in query) and "instead" not in query:
                # Check if user is assuming the current active piece was his
                if "his other work" in query or "did he also paint" in query:
                    return InconsistencyReport(
                        is_inconsistent=True,
                        inconsistency_type=InconsistencyType.CONTEXTUAL_CONTRADICTION,
                        explanation=f"We were previously discussing '{active_artwork.get('title')}' by {true_artist}.",
                        suggested_correction=f"Battistello Caracciolo was a follower of Caravaggio, but painted his own works such as 'The Liberation of Saint Peter'.",
                        claimed_entity=f"Battistello for {active_artwork.get('title')}",
                        ground_truth_entity=f"{true_artist} for {active_artwork.get('title')}",
                    )
        return None

    def _get_venue_keywords(self, venue_name: str) -> List[str]:
        name_lower = venue_name.lower()
        if "pio monte" in name_lower:
            return ["pio monte", "misericordia"]
        if "capodimonte" in name_lower:
            return ["capodimonte", "museo di capodimonte"]
        if "zevallos" in name_lower or "gallerie d'italia" in name_lower:
            return ["zevallos", "palazzo zevallos", "gallerie d'italia", "toledo"]
        if "san martino" in name_lower or "certosa" in name_lower:
            return ["san martino", "certosa di san martino", "certosa", "vomero"]
        if "turchini" in name_lower:
            return ["pietà dei turchini", "turchini", "chiesa della pietà dei turchini"]
        return [name_lower]

    def _has_artwork_pronoun(self, query: str) -> bool:
        """Check if query contains genuine artwork pronouns using word boundaries."""
        patterns = [
            r"\b(it|its|this|that)\b",
            r"\b(this|that|the)\s+(work|painting|canvas|piece|masterpiece)\b",
        ]
        return any(bool(re.search(p, query)) for p in patterns)
