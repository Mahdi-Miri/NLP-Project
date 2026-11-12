import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from src.data_pipeline.graph_db import NeapolitanArtGraph
from src.dialogue.inconsistency import InconsistencyDetector, InconsistencyReport
from src.dialogue.state_tracker import DialogueStateTracker

logger = logging.getLogger(__name__)


class ChatbotTurnResult(BaseModel):
    user_utterance: str
    system_response: str
    inconsistency_report: InconsistencyReport
    active_artist: Optional[str] = None
    active_artwork: Optional[str] = None
    active_location: Optional[str] = None
    graph_context: List[Dict[str, Any]] = []


class NeapolitanArtChatbot:
    def __init__(self, graph: Optional[NeapolitanArtGraph] = None):
        self.graph = graph or NeapolitanArtGraph()
        self.detector = InconsistencyDetector(self.graph)
        self.tracker = DialogueStateTracker()

    def process_utterance(self, utterance: str) -> ChatbotTurnResult:
        clean_utterance = utterance.strip()
        state = self.tracker.get_state()
        state_dict = {
            "active_artist": state.active_artist,
            "active_artwork": state.active_artwork,
            "active_location": state.active_location,
        }

        inconsistency = self.detector.detect_inconsistencies(clean_utterance, state_dict)

        if inconsistency.is_inconsistent:
            response_text = self._format_inconsistency_response(inconsistency)
            self.tracker.update_with_turn(
                user_utterance=clean_utterance,
                system_response=response_text,
                inconsistency=inconsistency,
            )
            return ChatbotTurnResult(
                user_utterance=clean_utterance,
                system_response=response_text,
                inconsistency_report=inconsistency,
                active_artist=state.active_artist,
                active_artwork=state.active_artwork.get("title") if state.active_artwork else None,
                active_location=state.active_location.get("name") if state.active_location else None,
            )

        anaphora = self.tracker.resolve_anaphora(clean_utterance)

        identified_artwork = self._extract_artwork(clean_utterance) or anaphora.get("artwork")
        identified_artist = self._extract_artist(clean_utterance) or anaphora.get("artist")
        identified_location = self._extract_location(clean_utterance) or anaphora.get("location")

        response_text, context_items = self._generate_response(
            utterance=clean_utterance,
            artwork=identified_artwork,
            artist=identified_artist,
            location=identified_location,
        )

        self.tracker.update_with_turn(
            user_utterance=clean_utterance,
            system_response=response_text,
            artwork=identified_artwork,
            artist=identified_artist,
            location=identified_location,
            inconsistency=inconsistency,
        )

        curr_state = self.tracker.get_state()
        return ChatbotTurnResult(
            user_utterance=clean_utterance,
            system_response=response_text,
            inconsistency_report=inconsistency,
            active_artist=curr_state.active_artist,
            active_artwork=curr_state.active_artwork.get("title") if curr_state.active_artwork else None,
            active_location=curr_state.active_location.get("name") if curr_state.active_location else None,
            graph_context=context_items,
        )

    def _format_inconsistency_response(self, inc: InconsistencyReport) -> str:
        if inc.explanation and inc.suggested_correction:
            return f"To clarify, {inc.explanation} {inc.suggested_correction}"
        return inc.explanation or inc.suggested_correction or "I noticed an inconsistency in that statement."

    def _normalize_query_for_speech(self, query: str) -> str:
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

    def _extract_artwork(self, query: str) -> Optional[Dict[str, Any]]:
        all_arts = self.graph.get_all_artworks()
        q_norm = self._normalize_query_for_speech(query)

        for art in all_arts:
            t_lower = art["title"].lower()
            t_no_the = t_lower[4:] if t_lower.startswith("the ") else t_lower
            if t_lower in q_norm or t_no_the in q_norm:
                return art
            if art.get("italian_title") and art["italian_title"].lower() in q_norm:
                return art

        title_keywords = {
            "the seven works of mercy": ["seven works", "works of mercy", "works for mercy", "mercy", "sette opere"],
            "the flagellation of christ": ["flagellation", "flagelation", "flagellazione", "flagellating"],
            "the martyrdom of saint ursula": ["ursula", "ursla", "sant'orsola", "martyrdom of ursula", "martyrdom of saint ursula", "saint ursula", "last painting", "final painting"],
            "the liberation of saint peter": ["liberation of saint peter", "liberation of peter", "freeing of saint peter", "san pietro"],
            "the washing of the feet": ["washing of the feet", "washing the feet", "washing feet", "wash feet", "feet washing", "lavanda dei piedi"],
            "christ at the column": ["christ at the column", "christ column", "cristo alla colonna", "at the column"],
            "trinitas terrestris": ["trinitas", "terrestris", "trinità terrestre", "trinita terrestre"],
            "frescoes of the chapel of the assunta": ["assunta", "chapel of the assunta", "frescoes of the assunta", "assunta frescoes"],
        }
        for art in all_arts:
            key = art["title"].lower()
            keywords = title_keywords.get(key, [])
            if any(k in q_norm for k in keywords):
                return art

        return None

    def _extract_artist(self, query: str) -> Optional[str]:
        q_norm = self._normalize_query_for_speech(query)
        caravaggio_variants = ["caravaggio", "caravagio", "karavaggio", "caravaccho", "caravashio", "merisi"]
        battistello_variants = ["battistello", "batistello", "caracciolo", "caraciolo", "battistelli"]

        has_caravaggio = any(v in q_norm for v in caravaggio_variants)
        has_battistello = any(v in q_norm for v in battistello_variants)

        if has_caravaggio and has_battistello:
            return None
        if has_battistello:
            return "Battistello Caracciolo"
        if has_caravaggio:
            return "Caravaggio"
        return None

    def _extract_location(self, query: str) -> Optional[Dict[str, Any]]:
        q_norm = self._normalize_query_for_speech(query)
        locations = self.graph.get_all_locations()

        for loc in locations:
            name_lower = loc["name"].lower()
            if name_lower in q_norm:
                return loc
            if ("pio monte" in q_norm or "piomonte" in q_norm or "pio monti" in q_norm) and "pio monte" in name_lower:
                return loc
            if ("capodimonte" in q_norm or "capo di monte" in q_norm) and "capodimonte" in name_lower:
                return loc
            if ("zevallos" in q_norm or "gallerie d'italia" in q_norm or "galleria d'italia" in q_norm) and "zevallos" in name_lower:
                return loc
            if ("san martino" in q_norm or "certosa" in q_norm) and "san martino" in name_lower:
                return loc
            if ("turchini" in q_norm or "pieta dei turchini" in q_norm or "pietà dei turchini" in q_norm) and "turchini" in name_lower:
                return loc

        return None

    def _generate_response(
        self,
        utterance: str,
        artwork: Optional[Dict[str, Any]],
        artist: Optional[str],
        location: Optional[Dict[str, Any]],
    ) -> (str, List[Dict[str, Any]]):
        u_lower = utterance.lower()
        context_items: List[Dict[str, Any]] = []

        if artwork:
            context_items.append(artwork)
            addr = artwork.get("address") or artwork.get("location_details", {}).get("address", "Naples, Italy")
            yr = artwork.get("year", "the early 17th century")
            med = artwork.get("medium", "Oil on canvas")
            dims = artwork.get("dimensions", "monumental format")
            desc = artwork.get("description", "")
            loc = artwork.get("location", "Naples")

            if any(w in u_lower for w in ["where", "location", "address", "visit", "venue", "how to see", "find"]):
                resp = (
                    f"'{artwork['title']}' by {artwork['artist']} is permanently preserved at "
                    f"{loc}, located on {addr}. "
                    f"It was painted in {yr} and executed in {med.lower()}."
                )
                return resp, context_items

            if any(w in u_lower for w in ["who painted", "who is the artist", "author", "creator", "painter"]):
                resp = (
                    f"'{artwork['title']}' was created by {artwork['artist']} in {yr}. "
                    f"You can view this masterwork in Naples at {loc}."
                )
                return resp, context_items

            if any(w in u_lower for w in ["dimension", "size", "measure", "height", "width", "medium", "canvas"]):
                resp = (
                    f"'{artwork['title']}' is executed in {med} on a monumental scale measuring {dims}. "
                    f"It is on permanent display at {loc} in Naples."
                )
                return resp, context_items

            if any(w in u_lower for w in ["significance", "meaning", "importance", "history", "about this", "context"]):
                resp = (
                    f"Regarding '{artwork['title']}', {desc} "
                    f"Painted in {yr} by {artwork.get('artist')}, it is preserved at {loc} in Naples."
                )
                return resp, context_items

            if any(w in u_lower for w in ["year", "when", "date", "period", "completed"]):
                resp = (
                    f"'{artwork['title']}' was completed by {artwork.get('artist')} in {yr}. "
                    f"It can be viewed in Naples at {loc}."
                )
                return resp, context_items

            abstract_snippet = artwork.get("dbpedia_abstract")
            lead_in = (
                f"'{artwork['title']}' is a masterpiece by {artwork['artist']}, created in {yr}. "
                f"It is permanently preserved in Naples at {loc} ({addr}), "
                f"executed in {med.lower()} with dimensions of {dims}."
            )
            paragraphs = [lead_in]
            if desc:
                paragraphs.append(desc)
            if abstract_snippet:
                paragraphs.append(f"Scholarly records note: {abstract_snippet[:220].rstrip()}...")
            return "\n\n".join(paragraphs), context_items

        if location:
            context_items.append(location)
            loc_name = location["name"]
            addr = location.get("address", "Naples, Italy")
            desc = location.get("description", "")
            established = location.get("established")
            website = location.get("website")
            works_here = self.graph.get_artworks_by_location(loc_name)

            paragraphs = [
                f"{loc_name} is located at {addr} in Naples. {desc}".strip()
            ]
            extra_facts = []
            if established:
                extra_facts.append(f"established in {established}")
            if extra_facts:
                paragraphs.append(f"{loc_name} was " + " and ".join(extra_facts) + ".")
            if website:
                paragraphs.append(f"Official website: {website}")
            if works_here:
                art_list = [f"'{w['title']}' by {w['artist']}" for w in works_here]
                if len(works_here) == 1:
                    paragraphs.append(f"On display here in our Neapolitan collection is {art_list[0]}.")
                else:
                    paragraphs.append(
                        f"In this collection, you can visit {len(works_here)} cataloged works:\n"
                        + "\n".join(f"- {item}" for item in art_list)
                    )
            else:
                paragraphs.append("No Caravaggio or Battistello Caracciolo works are currently cataloged at this location.")

            return "\n\n".join(paragraphs), context_items

        if artist:
            artworks_by_artist = self.graph.get_artworks_by_artist(artist)
            context_items.extend(artworks_by_artist)

            artist_nodes = self.graph.get_all_artists()
            artist_info = next(
                (a for a in artist_nodes if a["name"].lower() in artist.lower() or artist.lower() in a["name"].lower()),
                {},
            )
            movement = artist_info.get("movement", "Baroque, Tenebrism, Chiaroscuro")
            significance = artist_info.get("significance", "")
            neapolitan_periods = artist_info.get("neapolitan_periods", "")

            is_bio_query = any(
                w in u_lower
                for w in [
                    "who is", "who was", "biography", "movement", "style", "life",
                    "tell me about the painter", "tell me about", "about who", "he or she", "who he", "who she"
                ]
            )

            paragraphs = []
            if is_bio_query:
                if "caravaggio" in artist.lower():
                    bio = (
                        f"Michelangelo Merisi da Caravaggio (1571–1610) was a revolutionary master of the "
                        f"Italian Baroque, celebrated for his pioneering use of Tenebrism and dramatic Chiaroscuro. "
                        f"During his pivotal stays in Naples (1606–1607 and 1609–1610), his stark naturalism and "
                        f"violent contrast of light and shade exerted a defining influence on the Neapolitan Baroque."
                    )
                else:
                    bio = (
                        f"Giovanni Battista Caracciolo, known as Battistello Caracciolo (1578–1635), was Caravaggio's foremost follower "
                        f"in Naples and a central leader of Neapolitan Caravaggism and the Italian Baroque. "
                        f"He combined Caravaggio's dramatic tenebrism and chiaroscuro with refined Tuscan academic drawing."
                    )
                paragraphs.append(bio)
                training = artist_info.get("dbpedia_training")
                if training:
                    paragraphs.append(f"He trained under {training}, according to DBpedia biographical records.")
                paragraphs.append(f"In the urban area of Naples, you can visit {len(artworks_by_artist)} of his cataloged works:")
            else:
                paragraphs.append(f"You can visit {len(artworks_by_artist)} works by {artist} in the urban area of Naples:")

            art_lines = [
                f"- '{a['title']}' ({a.get('year', 'circa 1600s')}) at {a['location']}"
                for a in artworks_by_artist
            ]
            paragraphs.append("\n".join(art_lines))
            paragraphs.append("Feel free to ask about any of these paintings, their locations, dimensions, or iconography.")
            return "\n\n".join(paragraphs), context_items

        if any(w in u_lower for w in ["hello", "hi", "help", "guide", "overview", "what can you do", "intro"]):
            all_arts = self.graph.get_all_artworks()
            caravaggio_count = len([a for a in all_arts if a["artist"] == "Caravaggio"])
            battistello_count = len([a for a in all_arts if a["artist"] == "Battistello Caracciolo"])
            venues = self.graph.get_all_locations()

            return (
                f"Welcome to the Neapolitan Artistic Heritage Guide. I can assist you with "
                f"scholarly, verified information on masterworks by Caravaggio and Battistello Caracciolo "
                f"preserved across Naples.\n\n"
                f"Our catalog includes:\n"
                f"- Caravaggio: {caravaggio_count} masterworks (including 'The Seven Works of Mercy', 'The Flagellation of Christ', and 'The Martyrdom of Saint Ursula').\n"
                f"- Battistello Caracciolo: {battistello_count} works (including 'The Liberation of Saint Peter' and 'The Washing of the Feet').\n"
                f"- Historic Sites: {len(venues)} cultural museum venues and churches in Naples.\n\n"
                f"You can ask about specific paintings, artist biographies, museum locations, or historical context."
            ), []

        return (
            "I could not identify a specific artwork, artist, or venue from your question. "
            "You can ask about works by Caravaggio (such as 'The Seven Works of Mercy' or 'The Flagellation of Christ') "
            "or Battistello Caracciolo (such as 'The Liberation of Saint Peter' or 'The Washing of the Feet') "
            "visitable in Naples, or about venues like Pio Monte della Misericordia and Capodimonte."
        ), []

    def reset_dialogue(self):
        self.tracker.reset()
