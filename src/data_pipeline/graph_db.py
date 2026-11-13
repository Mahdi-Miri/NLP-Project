import logging
from typing import Any, Dict, List, Optional

from config.settings import config

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    Driver = Any


class Neo4jGraphStore:
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self.uri = uri or config.neo4j.uri
        self.user = user or config.neo4j.user
        self.password = password or config.neo4j.password
        self.database = database or config.neo4j.database
        self._driver: Optional[Driver] = None

    def connect(self) -> bool:
        if not NEO4J_AVAILABLE:
            logger.warning("neo4j library is not installed.")
            return False
        try:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j instance at %s", self.uri)
            return True
        except Exception as exc:
            logger.info("Neo4j connection failed at %s (%s)", self.uri, exc)
            self._driver = None
            return False

    def close(self):
        if self._driver:
            self._driver.close()

    def initialize_schema(self):
        if not self._driver:
            return
        constraints = [
            "CREATE CONSTRAINT artwork_uri_unique IF NOT EXISTS FOR (a:Artwork) REQUIRE a.uri IS UNIQUE",
            "CREATE CONSTRAINT artist_name_unique IF NOT EXISTS FOR (p:Artist) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT location_name_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT city_name_unique IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
        ]
        with self._driver.session(database=self.database) as session:
            for constraint_query in constraints:
                try:
                    session.run(constraint_query)
                except Exception as exc:
                    logger.debug("Constraint notice: %s", exc)

    def populate(self, corpus: Dict[str, Any]):
        if not self._driver:
            raise ConnectionError("Neo4j driver is not connected.")

        self.initialize_schema()

        with self._driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")

            session.run(
                """
                MERGE (c:City {name: 'Naples'})
                SET c.country = 'Italy',
                    c.uri = 'http://dbpedia.org/resource/Naples'
                """
            )

            for artist_key, a_data in corpus.get("artists", {}).items():
                session.run(
                    """
                    MERGE (p:Artist {name: $name})
                    SET p.uri = $uri,
                        p.movement = $movement,
                        p.birth_year = $birth_year,
                        p.death_year = $death_year,
                        p.birth_place = $birth_place,
                        p.death_place = $death_place,
                        p.neapolitan_periods = $neapolitan_periods,
                        p.significance = $significance,
                        p.dbpedia_abstract = $abstract,
                        p.dbpedia_training = $dbpedia_training
                    """,
                    name=artist_key,
                    uri=a_data.get("uri", ""),
                    movement=a_data.get("movement", ""),
                    birth_year=a_data.get("birth_year", 0),
                    death_year=a_data.get("death_year", 0),
                    birth_place=a_data.get("birth_place", ""),
                    death_place=a_data.get("death_place", ""),
                    neapolitan_periods=a_data.get("neapolitan_periods", ""),
                    significance=a_data.get("significance", ""),
                    abstract=a_data.get("dbpedia_abstract", ""),
                    dbpedia_training=a_data.get("dbpedia_training", ""),
                )

            for venue in corpus.get("venues", []):
                coords = venue.get("coordinates", {})
                session.run(
                    """
                    MERGE (l:Location {name: $name})
                    SET l.uri = $uri,
                        l.source_url = $source_url,
                        l.dbpedia_page = $dbpedia_page,
                        l.address = $address,
                        l.description = $description,
                        l.latitude = $latitude,
                        l.longitude = $longitude,
                        l.established = $established,
                        l.website = $website
                    WITH l
                    MATCH (c:City {name: 'Naples'})
                    MERGE (l)-[:IN_CITY]->(c)
                    """,
                    name=venue["name"],
                    uri=venue.get("uri", ""),
                    source_url=venue.get("source_url", ""),
                    dbpedia_page=venue.get("dbpedia_page", ""),
                    address=venue.get("address", ""),
                    description=venue.get("description", ""),
                    latitude=coords.get("latitude", 0.0),
                    longitude=coords.get("longitude", 0.0),
                    established=venue.get("established", 0),
                    website=venue.get("website", ""),
                )

            for art in corpus.get("artworks", []):
                session.run(
                    """
                    MERGE (a:Artwork {title: $title})
                    SET a.uri = $uri,
                        a.source_url = $source_url,
                        a.dbpedia_page = $dbpedia_page,
                        a.italian_title = $italian_title,
                        a.year = $year,
                        a.medium = $medium,
                        a.dimensions = $dimensions,
                        a.description = $description,
                        a.dbpedia_abstract = $dbpedia_abstract,
                        a.dbpedia_image = $dbpedia_image
                    WITH a
                    MATCH (p:Artist {name: $artist})
                    MERGE (p)-[:PAINTED]->(a)
                    WITH a
                    MATCH (l:Location {name: $location})
                    MERGE (a)-[:LOCATED_AT]->(l)
                    """,
                    title=art["title"],
                    uri=art.get("uri", ""),
                    source_url=art.get("source_url", ""),
                    dbpedia_page=art.get("dbpedia_page", ""),
                    italian_title=art.get("italian_title", ""),
                    year=art.get("year", 0),
                    medium=art.get("medium", ""),
                    dimensions=art.get("dimensions", ""),
                    description=art.get("description", ""),
                    dbpedia_abstract=art.get("dbpedia_abstract", ""),
                    dbpedia_image=art.get("dbpedia_image", ""),
                    artist=art["artist"],
                    location=art["location"],
                )

                for subject in art.get("subjects", []):
                    session.run(
                        """
                        MERGE (s:Subject {name: $sub_name})
                        WITH s
                        MATCH (a:Artwork {title: $title})
                        MERGE (a)-[:DEPICTS]->(s)
                        """,
                        sub_name=subject,
                        title=art["title"],
                    )

        logger.info("Successfully populated Neo4j graph database.")

    def run_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self._driver:
            raise ConnectionError("Neo4j driver not connected.")
        with self._driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]


class NeapolitanArtGraph:
    def __init__(self):
        self.neo4j_store = Neo4jGraphStore()
        self.active_backend = "neo4j"

        if not self.neo4j_store.connect():
            raise ConnectionError(
                f"Could not connect to Neo4j at {self.neo4j_store.uri}. "
                "This project requires a running Neo4j instance (e.g. `docker start neo4j-nlp`); "
                "there is no SQLite fallback."
            )
        logger.info("Using Neo4j as active graph engine.")
        self._artworks_cache: Optional[List[Dict[str, Any]]] = None

    def populate(self, corpus: Dict[str, Any]):
        self.neo4j_store.populate(corpus)
        self._artworks_cache = None

    def get_all_artworks(self) -> List[Dict[str, Any]]:
        if self._artworks_cache is not None:
            return self._artworks_cache
        query = """
        MATCH (p:Artist)-[:PAINTED]->(a:Artwork)-[:LOCATED_AT]->(l:Location)
        RETURN a.title AS title, a.italian_title AS italian_title, a.year AS year,
               a.medium AS medium, a.dimensions AS dimensions, a.description AS description,
               a.uri AS uri, a.source_url AS source_url, a.dbpedia_page AS dbpedia_page,
               a.dbpedia_abstract AS dbpedia_abstract,
               p.name AS artist, l.name AS location, l.address AS address
        """
        self._artworks_cache = self.neo4j_store.run_cypher(query)
        return self._artworks_cache

    def get_artworks_by_artist(self, artist_name: str) -> List[Dict[str, Any]]:
        all_arts = self.get_all_artworks()
        pattern = artist_name.lower()
        return [a for a in all_arts if pattern in a.get("artist", "").lower()]

    def get_artworks_by_location(self, location_name: str) -> List[Dict[str, Any]]:
        all_arts = self.get_all_artworks()
        pattern = location_name.lower()
        return [a for a in all_arts if pattern in a.get("location", "").lower()]

    def get_all_locations(self) -> List[Dict[str, Any]]:
        query = """
        MATCH (l:Location)
        RETURN l.name AS name, l.uri AS uri, l.source_url AS source_url,
               l.dbpedia_page AS dbpedia_page, l.address AS address,
               l.description AS description, l.latitude AS latitude,
               l.longitude AS longitude, l.established AS established,
               l.website AS website
        """
        records = self.neo4j_store.run_cypher(query)
        all_arts = self.get_all_artworks()
        for loc in records:
            pattern = loc["name"].lower()
            arts = [a for a in all_arts if pattern in a.get("location", "").lower()]
            loc["artworks"] = [a["title"] for a in arts]
            loc["artwork_count"] = len(arts)
        return records

    def get_all_artists(self) -> List[Dict[str, Any]]:
        query = """
        MATCH (p:Artist)
        RETURN p.name AS name, p.uri AS uri, p.movement AS movement,
               p.birth_year AS birth_year, p.death_year AS death_year,
               p.birth_place AS birth_place, p.death_place AS death_place,
               p.neapolitan_periods AS neapolitan_periods, p.significance AS significance,
               p.dbpedia_abstract AS dbpedia_abstract,
               p.dbpedia_training AS dbpedia_training
        """
        records = self.neo4j_store.run_cypher(query)
        all_arts = self.get_all_artworks()
        for artist in records:
            pattern = artist["name"].lower()
            arts = [a for a in all_arts if pattern in a.get("artist", "").lower()]
            artist["artworks"] = [a["title"] for a in arts]
            artist["artwork_count"] = len(arts)
        return records
