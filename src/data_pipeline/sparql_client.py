import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from SPARQLWrapper import JSON, SPARQLWrapper

from config.settings import config
from src.data_pipeline.curated_dataset import NEAPOLITAN_ARTWORKS, NON_NEAPOLITAN_ARTWORKS

logger = logging.getLogger(__name__)


class DBpediaSPARQLClient:
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        cache_file: Optional[Path] = None,
    ):
        self.endpoint_url = endpoint_url or config.sparql.endpoint_url
        self.timeout = timeout_seconds or config.sparql.timeout_seconds
        self.cache_file = cache_file or (config.paths.data_dir / "dbpedia_cache.json")

        self.sparql = SPARQLWrapper(self.endpoint_url)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(self.timeout)
        self.sparql.addCustomHttpHeader("User-Agent", config.sparql.user_agent)

    @staticmethod
    def _to_graph_uri(uri: str) -> str:
        """DBpedia's RDF graph uses http:// resource IRIs; our stored URIs use
        https:// (which only works as a browser-facing redirect, not inside SPARQL
        triple patterns). Normalize before querying or every OPTIONAL silently matches zero rows."""
        return uri.replace("https://dbpedia.org", "http://dbpedia.org", 1)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        try:
            self.sparql.setQuery(query)
            response = self.sparql.query().convert()
            if isinstance(response, dict) and "results" in response:
                return response["results"].get("bindings", [])
            return []
        except Exception as exc:
            logger.warning("SPARQL query failed on DBpedia endpoint: %s", exc)
            return []

    def fetch_caravaggio_works_from_dbpedia(self) -> List[Dict[str, str]]:
        query = """
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbr: <http://dbpedia.org/resource/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?artwork ?title ?museum WHERE {
            ?artwork dbo:author dbr:Caravaggio ;
                     rdfs:label ?title .
            OPTIONAL { ?artwork dbo:museum ?museum }
            FILTER (lang(?title) = 'en')
        } LIMIT 50
        """
        bindings = self.execute_query(query)
        extracted: List[Dict[str, str]] = []
        for row in bindings:
            extracted.append(
                {
                    "artwork_uri": row.get("artwork", {}).get("value", ""),
                    "title": row.get("title", {}).get("value", ""),
                    "museum_uri": row.get("museum", {}).get("value", ""),
                }
            )
        return extracted

    def fetch_artist_dbpedia_profile(self, artist_uri: str) -> Dict[str, Any]:
        query_uri = self._to_graph_uri(artist_uri)
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?label ?abstract ?birthDate ?deathDate ?training WHERE {{
            <{query_uri}> rdfs:label ?label .
            OPTIONAL {{ <{query_uri}> dbo:abstract ?abstract . FILTER(lang(?abstract) = 'en') }}
            OPTIONAL {{ <{query_uri}> dbo:birthDate ?birthDate }}
            OPTIONAL {{ <{query_uri}> dbo:deathDate ?deathDate }}
            OPTIONAL {{ <{query_uri}> dbo:training ?training }}
            FILTER (lang(?label) = 'en')
        }} LIMIT 1
        """
        bindings = self.execute_query(query)
        if bindings:
            row = bindings[0]

            def place_name(key: str) -> str:
                val = row.get(key, {}).get("value", "")
                return val.rsplit("/", 1)[-1].replace("_", " ") if val else ""

            return {
                "uri": artist_uri,
                "name": row.get("label", {}).get("value", ""),
                "abstract": row.get("abstract", {}).get("value", ""),
                "birth_date": row.get("birthDate", {}).get("value", ""),
                "death_date": row.get("deathDate", {}).get("value", ""),
                "training": place_name("training") if row.get("training", {}).get("type") == "uri" else row.get("training", {}).get("value", ""),
            }
        return {}

    def fetch_neapolitan_corpus(self, force_refresh: bool = False) -> Dict[str, Any]:
        if not force_refresh and self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data.get("artworks") and cached_data.get("artists") and cached_data.get("venues"):
                        logger.info("Loaded Neapolitan corpus from cache: %s", self.cache_file)
                        return cached_data
            except Exception as exc:
                logger.warning("Could not read cache file %s: %s", self.cache_file, exc)

        logger.info("Querying DBpedia SPARQL endpoint to construct fresh Neapolitan corpus...")

        artists = {
            "Caravaggio": {
                "uri": "https://dbpedia.org/resource/Caravaggio",
                "source_url": "https://en.wikipedia.org/wiki/Caravaggio",
                "dbpedia_page": "https://dbpedia.org/page/Caravaggio",
                "name": "Caravaggio (Michelangelo Merisi)",
                "movement": "Baroque, Tenebrism, Chiaroscuro",
                "birth_year": 1571,
                "death_year": 1610,
                "birth_place": "Milan, Duchy of Milan",
                "death_place": "Porto Ercole, Grand Duchy of Tuscany",
                "neapolitan_periods": "First Neapolitan stay (1606-1607), Second Neapolitan stay (1609-1610)",
                "significance": "Pivotal influence on Neapolitan Baroque through stark naturalism and violent contrast of light and shade.",
            },
            "Battistello Caracciolo": {
                "uri": "https://dbpedia.org/resource/Battistello_Caracciolo",
                "source_url": "https://en.wikipedia.org/wiki/Battistello_Caracciolo",
                "dbpedia_page": "https://dbpedia.org/page/Battistello_Caracciolo",
                "name": "Battistello Caracciolo (Giovanni Battista Caracciolo)",
                "movement": "Neapolitan Caravaggism, Baroque",
                "birth_year": 1578,
                "death_year": 1635,
                "birth_place": "Naples, Kingdom of Naples",
                "death_place": "Naples, Kingdom of Naples",
                "neapolitan_periods": "Lifelong resident and premier leader of the Neapolitan Caravaggisti school",
                "significance": "Caravaggio's foremost follower in Naples, combining Caravaggio's tenebrism with Tuscan academic drawing.",
            },
        }

        for artist_key, artist_data in artists.items():
            dbpedia_profile = self.fetch_artist_dbpedia_profile(artist_data["uri"])
            if dbpedia_profile:
                if dbpedia_profile.get("abstract"):
                    artist_data["dbpedia_abstract"] = dbpedia_profile["abstract"]
                if dbpedia_profile.get("birth_date"):
                    artist_data["dbpedia_birth_date"] = dbpedia_profile["birth_date"]
                if dbpedia_profile.get("death_date"):
                    artist_data["dbpedia_death_date"] = dbpedia_profile["death_date"]
                if dbpedia_profile.get("training"):
                    artist_data["dbpedia_training"] = dbpedia_profile["training"]

        artworks = []
        for item in NEAPOLITAN_ARTWORKS:
            artwork_dict = dict(item)
            artwork_uri = self._to_graph_uri(artwork_dict["uri"])
            query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?abstract ?comment ?image WHERE {{
                OPTIONAL {{ <{artwork_uri}> dbo:abstract ?abstract . FILTER (lang(?abstract) = 'en') }}
                OPTIONAL {{ <{artwork_uri}> rdfs:comment ?comment . FILTER (lang(?comment) = 'en') }}
                OPTIONAL {{ <{artwork_uri}> dbp:imageFile ?image }}
            }} LIMIT 1
            """
            prop_bindings = self.execute_query(query)
            if prop_bindings:
                row = prop_bindings[0]
                if row.get("abstract"):
                    artwork_dict["dbpedia_abstract"] = row["abstract"].get("value", "")
                elif row.get("comment"):
                    artwork_dict["dbpedia_abstract"] = row["comment"].get("value", "")
                if row.get("image"):
                    artwork_dict["dbpedia_image"] = row["image"].get("value", "")

            artworks.append(artwork_dict)

        venues = [
            {
                "name": "Pio Monte della Misericordia",
                "uri": "https://dbpedia.org/resource/Pio_Monte_della_Misericordia",
                "source_url": "https://en.wikipedia.org/wiki/Pio_Monte_della_Misericordia",
                "dbpedia_page": "https://dbpedia.org/page/Pio_Monte_della_Misericordia",
                "city": "Naples",
                "address": "Via dei Tribunali 253, 80139 Napoli",
                "description": "Historic charitable institution in the heart of Naples, holding Caravaggio's Seven Works of Mercy and Caracciolo's Liberation of Saint Peter in the high chapel.",
                "coordinates": {"latitude": 40.8522, "longitude": 14.2619},
                "established": 1602,
                "website": "https://www.piomontedellamisericordia.it",
            },
            {
                "name": "Museo Nazionale di Capodimonte",
                "uri": "https://dbpedia.org/resource/Museo_di_Capodimonte",
                "source_url": "https://en.wikipedia.org/wiki/National_Museum_of_Capodimonte",
                "dbpedia_page": "https://dbpedia.org/page/National_Museum_of_Capodimonte",
                "city": "Naples",
                "address": "Via Miano 2, 80131 Napoli",
                "description": "Grand Bourbon palace overlooking Naples, housing the Farnese Collection and Caravaggio's Flagellation along with Battistello's Christ at the Column.",
                "coordinates": {"latitude": 40.8672, "longitude": 14.2503},
                "established": 1757,
            },
            {
                "name": "Gallerie d'Italia (Palazzo Zevallos Stigliano)",
                "uri": "https://dbpedia.org/resource/Palazzo_Zevallos_Stigliano",
                "source_url": "https://en.wikipedia.org/wiki/Palazzo_Zevallos_Stigliano",
                "dbpedia_page": "https://dbpedia.org/page/Palazzo_Zevallos_Stigliano",
                "city": "Naples",
                "address": "Via Toledo 185, 80132 Napoli",
                "description": "Noble palace on Via Toledo housing Caravaggio's final masterpiece, The Martyrdom of Saint Ursula.",
                "coordinates": {"latitude": 40.8403, "longitude": 14.2492},
            },
            {
                "name": "Certosa di San Martino",
                "uri": "https://dbpedia.org/resource/Certosa_di_San_Martino",
                "source_url": "https://en.wikipedia.org/wiki/Certosa_di_San_Martino",
                "dbpedia_page": "https://dbpedia.org/page/Certosa_di_San_Martino",
                "city": "Naples",
                "address": "Largo San Martino 5, 80129 Napoli",
                "description": "Monastery complex on the Vomero hill with panoramic views of the Gulf, featuring Battistello Caracciolo's Washing of the Feet and Chapel of the Assunta frescoes.",
                "coordinates": {"latitude": 40.8436, "longitude": 14.2417},
            },
            {
                "name": "Chiesa della Pietà dei Turchini",
                "uri": "https://dbpedia.org/resource/Chiesa_della_Pietà_dei_Turchini",
                "source_url": "https://it.wikipedia.org/wiki/Chiesa_della_Piet%C3%A0_dei_Turchini",
                "dbpedia_page": "https://dbpedia.org/page/Chiesa_della_Piet%C3%A0_dei_Turchini",
                "city": "Naples",
                "address": "Via Medina 19, 80133 Napoli",
                "description": "Baroque church in central Naples preserving Battistello Caracciolo's Trinitas Terrestris.",
                "coordinates": {"latitude": 40.8415, "longitude": 14.2527},
            },
        ]

        payload = {
            "source": "DBpedia SPARQL Endpoint (https://dbpedia.org/sparql)",
            "artists": artists,
            "artworks": artworks,
            "venues": venues,
            "non_neapolitan_artworks": NON_NEAPOLITAN_ARTWORKS,
        }

        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.info("Saved Neapolitan corpus cache to %s", self.cache_file)
        except Exception as exc:
            logger.warning("Failed to save corpus cache: %s", exc)

        return payload
