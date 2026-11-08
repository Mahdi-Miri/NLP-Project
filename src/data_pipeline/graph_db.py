import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

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
                        p.dbpedia_abstract = $abstract
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
                        l.longitude = $longitude
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


class LocalGraphStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or config.paths.local_db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    properties JSON NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    properties JSON,
                    FOREIGN KEY (source_id) REFERENCES nodes(id),
                    FOREIGN KEY (target_id) REFERENCES nodes(id)
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(relation)")
            conn.commit()

    def populate(self, corpus: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM edges")
            cursor.execute("DELETE FROM nodes")

            cursor.execute(
                "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
                ("city:Naples", "City", json.dumps({"name": "Naples", "country": "Italy"})),
            )

            for artist_name, a_data in corpus.get("artists", {}).items():
                node_id = f"artist:{artist_name}"
                props = dict(a_data)
                props["name"] = artist_name
                cursor.execute(
                    "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
                    (node_id, "Artist", json.dumps(props)),
                )

            for venue in corpus.get("venues", []):
                loc_id = f"location:{venue['name']}"
                cursor.execute(
                    "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
                    (loc_id, "Location", json.dumps(venue)),
                )
                cursor.execute(
                    "INSERT INTO edges (source_id, target_id, relation, properties) VALUES (?, ?, ?, ?)",
                    (loc_id, "city:Naples", "IN_CITY", json.dumps({})),
                )

            for art in corpus.get("artworks", []):
                art_id = f"artwork:{art['title']}"
                cursor.execute(
                    "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
                    (art_id, "Artwork", json.dumps(art)),
                )

                artist_id = f"artist:{art['artist']}"
                cursor.execute(
                    "INSERT INTO edges (source_id, target_id, relation, properties) VALUES (?, ?, ?, ?)",
                    (artist_id, art_id, "PAINTED", json.dumps({})),
                )

                loc_id = f"location:{art['location']}"
                cursor.execute(
                    "INSERT INTO edges (source_id, target_id, relation, properties) VALUES (?, ?, ?, ?)",
                    (art_id, loc_id, "LOCATED_AT", json.dumps({})),
                )

                for sub in art.get("subjects", []):
                    sub_id = f"subject:{sub}"
                    cursor.execute(
                        "INSERT OR IGNORE INTO nodes (id, label, properties) VALUES (?, ?, ?)",
                        (sub_id, "Subject", json.dumps({"name": sub})),
                    )
                    cursor.execute(
                        "INSERT INTO edges (source_id, target_id, relation, properties) VALUES (?, ?, ?, ?)",
                        (art_id, sub_id, "DEPICTS", json.dumps({})),
                    )

            conn.commit()
            logger.info("Local SQLite graph populated successfully.")

    def get_all_artworks(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.properties as art_prop,
                       p.properties as artist_prop,
                       l.properties as loc_prop
                FROM nodes a
                JOIN edges e1 ON e1.target_id = a.id AND e1.relation = 'PAINTED'
                JOIN nodes p ON p.id = e1.source_id
                JOIN edges e2 ON e2.source_id = a.id AND e2.relation = 'LOCATED_AT'
                JOIN nodes l ON l.id = e2.target_id
                WHERE a.label = 'Artwork'
                """
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                art = json.loads(row["art_prop"])
                artist = json.loads(row["artist_prop"])
                loc = json.loads(row["loc_prop"])
                art["artist_details"] = artist
                art["location_details"] = loc
                results.append(art)
            return results

    def get_artworks_by_artist(self, artist_name: str) -> List[Dict[str, Any]]:
        all_arts = self.get_all_artworks()
        pattern = artist_name.lower()
        return [a for a in all_arts if pattern in a.get("artist", "").lower()]

    def get_artworks_by_location(self, location_name: str) -> List[Dict[str, Any]]:
        all_arts = self.get_all_artworks()
        pattern = location_name.lower()
        return [a for a in all_arts if pattern in a.get("location", "").lower()]

    def get_artwork_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        all_arts = self.get_all_artworks()
        title_lower = title.strip().lower()
        for a in all_arts:
            if title_lower == a.get("title", "").lower() or title_lower in a.get("title", "").lower():
                return a
            if a.get("italian_title") and title_lower in a.get("italian_title", "").lower():
                return a
        return None

    def get_all_locations(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT properties FROM nodes WHERE label = 'Location'")
            locs = [json.loads(r["properties"]) for r in cursor.fetchall()]

            for loc in locs:
                arts = self.get_artworks_by_location(loc["name"])
                loc["artworks"] = [a["title"] for a in arts]
                loc["artwork_count"] = len(arts)
            return locs

    def get_all_artists(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT properties FROM nodes WHERE label = 'Artist'")
            artists = [json.loads(r["properties"]) for r in cursor.fetchall()]

            for artist in artists:
                arts = self.get_artworks_by_artist(artist["name"])
                artist["artworks"] = [a["title"] for a in arts]
                artist["artwork_count"] = len(arts)
            return artists


class NeapolitanArtGraph:
    def __init__(self, prefer_neo4j: bool = True):
        self.neo4j_store = Neo4jGraphStore()
        self.local_store = LocalGraphStore()
        self.active_backend = "sqlite"

        if prefer_neo4j and self.neo4j_store.connect():
            self.active_backend = "neo4j"
            logger.info("Using Neo4j as active graph engine.")
        else:
            self.active_backend = "sqlite"
            logger.info("Using embedded SQLite graph engine.")

    def populate(self, corpus: Dict[str, Any]):
        self.local_store.populate(corpus)
        if self.active_backend == "neo4j" and self.neo4j_store._driver:
            try:
                self.neo4j_store.populate(corpus)
            except Exception as exc:
                logger.warning("Failed to populate Neo4j, fell back to local store: %s", exc)

    def get_all_artworks(self) -> List[Dict[str, Any]]:
        if self.active_backend == "neo4j" and self.neo4j_store._driver:
            try:
                query = """
                MATCH (p:Artist)-[:PAINTED]->(a:Artwork)-[:LOCATED_AT]->(l:Location)
                RETURN a.title AS title, a.italian_title AS italian_title, a.year AS year,
                       a.medium AS medium, a.dimensions AS dimensions, a.description AS description,
                       a.uri AS uri, a.source_url AS source_url, a.dbpedia_page AS dbpedia_page,
                       p.name AS artist, l.name AS location, l.address AS address
                """
                records = self.neo4j_store.run_cypher(query)
                if records:
                    return records
            except Exception as exc:
                logger.warning("Neo4j query failed, delegating to local store: %s", exc)
        return self.local_store.get_all_artworks()

    def get_artworks_by_artist(self, artist_name: str) -> List[Dict[str, Any]]:
        all_arts = self.get_all_artworks()
        pattern = artist_name.lower()
        return [a for a in all_arts if pattern in a.get("artist", "").lower()]

    def get_artworks_by_location(self, location_name: str) -> List[Dict[str, Any]]:
        return self.local_store.get_artworks_by_location(location_name)

    def get_artwork_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        return self.local_store.get_artwork_by_title(title)

    def get_all_locations(self) -> List[Dict[str, Any]]:
        return self.local_store.get_all_locations()

    def get_all_artists(self) -> List[Dict[str, Any]]:
        return self.local_store.get_all_artists()
