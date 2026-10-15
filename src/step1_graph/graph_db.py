import os
import sqlite3
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from config.settings import config
from src.utils.text_utils import clean_wiki_markup, normalize_query


class BaseQuoteGraph(ABC):
    """Abstract base class for quote graph database backends."""

    @abstractmethod
    def initialize_schema(self) -> None:
        pass

    @abstractmethod
    def insert_quote(self, quote: str, author: str, source: str, work: str, categories: List[str]) -> int:
        pass

    @abstractmethod
    def insert_quotes_batch(self, quotes: List[Dict[str, Any]]) -> int:
        pass

    @abstractmethod
    def search_fulltext(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def autocomplete_citation(self, prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_quote_by_id(self, quote_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_quotes_by_author(self, author_name: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_quotes_by_work(self, work_title: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class LocalQuoteGraph(BaseQuoteGraph):
    """
    Lightweight, embedded graph database using SQLite with FTS5 for full-text search.
    Provides instant out-of-the-box local execution without running external database daemons.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or config.paths.local_db_path)
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.initialize_schema()

    def initialize_schema(self) -> None:
        cursor = self.conn.cursor()

        # Node tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL UNIQUE,
                source TEXT,
                work TEXT,
                char_length INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Edge tables representing graph relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edge_said_by (
                quote_id INTEGER,
                author_id INTEGER,
                PRIMARY KEY (quote_id, author_id),
                FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edge_from_work (
                quote_id INTEGER,
                work_id INTEGER,
                PRIMARY KEY (quote_id, work_id),
                FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
                FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edge_has_category (
                quote_id INTEGER,
                category_id INTEGER,
                PRIMARY KEY (quote_id, category_id),
                FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)

        # Full-Text Index (FTS5) on quote citations
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS quotes_fts USING fts5(
                quote_id UNINDEXED,
                text,
                author,
                work,
                tokenize = 'porter unicode61'
            )
        """)

        # Auxiliary index for prefix lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_text ON quotes(text)")
        self.conn.commit()

    def _get_or_create_node(self, table: str, column: str, value: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT id FROM {table} WHERE {column} = ?", (value,))
        row = cursor.fetchone()
        if row:
            return row["id"]
        cursor.execute(f"INSERT INTO {table} ({column}) VALUES (?)", (value,))
        return cursor.lastrowid

    def insert_quote(self, quote: str, author: str, source: str, work: str, categories: List[str]) -> int:
        clean_text = clean_wiki_markup(quote)
        if not clean_text or len(clean_text) < 15:
            return -1

        author_name = author.strip() or "Unknown"
        work_title = (work or "General").strip()
        source_desc = (source or author_name).strip()

        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO quotes (text, source, work, char_length) VALUES (?, ?, ?, ?)",
                (clean_text, source_desc, work_title, len(clean_text))
            )
            quote_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Quote already stored
            cursor.execute("SELECT id FROM quotes WHERE text = ?", (clean_text,))
            return cursor.fetchone()["id"]

        # Graph node links
        author_id = self._get_or_create_node("authors", "name", author_name)
        work_id = self._get_or_create_node("works", "title", work_title)

        cursor.execute("INSERT OR IGNORE INTO edge_said_by (quote_id, author_id) VALUES (?, ?)", (quote_id, author_id))
        cursor.execute("INSERT OR IGNORE INTO edge_from_work (quote_id, work_id) VALUES (?, ?)", (quote_id, work_id))

        for cat in (categories or []):
            cat_name = cat.strip()
            if cat_name:
                cat_id = self._get_or_create_node("categories", "name", cat_name)
                cursor.execute("INSERT OR IGNORE INTO edge_has_category (quote_id, category_id) VALUES (?, ?)", (quote_id, cat_id))

        # Full-text index entry
        cursor.execute(
            "INSERT INTO quotes_fts (quote_id, text, author, work) VALUES (?, ?, ?, ?)",
            (quote_id, clean_text, author_name, work_title)
        )
        self.conn.commit()
        return quote_id

    def insert_quotes_batch(self, quotes: List[Dict[str, Any]]) -> int:
        inserted = 0
        for item in quotes:
            qid = self.insert_quote(
                quote=item.get("quote", ""),
                author=item.get("author", "Unknown"),
                source=item.get("source", ""),
                work=item.get("work", "General"),
                categories=item.get("categories", [])
            )
            if qid > 0:
                inserted += 1
        return inserted

    def search_fulltext(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        norm_query = normalize_query(query)
        if not norm_query:
            return []

        # Prepare tokens for FTS5 match query
        fts_tokens = " ".join([f'"{token}"*' for token in norm_query.split() if len(token) > 1])
        if not fts_tokens:
            fts_tokens = f'"{norm_query}"*'

        cursor = self.conn.cursor()
        try:
            sql = """
                SELECT q.id, q.text, a.name AS author, q.source, q.work,
                       bm25(quotes_fts) as score
                FROM quotes_fts f
                JOIN quotes q ON q.id = f.quote_id
                JOIN edge_said_by es ON es.quote_id = q.id
                JOIN authors a ON a.id = es.author_id
                WHERE quotes_fts MATCH ?
                ORDER BY score ASC
                LIMIT ?
            """
            cursor.execute(sql, (fts_tokens, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            # Fallback to standard LIKE matching if query formatting issues occur
            return self.autocomplete_citation(query, limit)

    def autocomplete_citation(self, prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
        clean_prefix = clean_wiki_markup(prefix)
        if not clean_prefix:
            return []

        cursor = self.conn.cursor()

        # Step A: Check for direct prefix match (highest confidence)
        sql_prefix = """
            SELECT q.id, q.text, a.name AS author, q.source, q.work, 1.0 AS score
            FROM quotes q
            JOIN edge_said_by es ON es.quote_id = q.id
            JOIN authors a ON a.id = es.author_id
            WHERE q.text LIKE ?
            ORDER BY q.char_length ASC
            LIMIT ?
        """
        cursor.execute(sql_prefix, (f"{clean_prefix}%", limit))
        results = [dict(row) for row in cursor.fetchall()]

        # Step B: If needed, supplement with substring/full-text match
        if len(results) < limit:
            remaining = limit - len(results)
            existing_ids = tuple(r["id"] for r in results) or (-1,)
            sql_sub = f"""
                SELECT q.id, q.text, a.name AS author, q.source, q.work, 0.8 AS score
                FROM quotes q
                JOIN edge_said_by es ON es.quote_id = q.id
                JOIN authors a ON a.id = es.author_id
                WHERE q.text LIKE ? AND q.id NOT IN ({','.join('?' * len(existing_ids))})
                ORDER BY q.char_length ASC
                LIMIT ?
            """
            cursor.execute(sql_sub, (f"%{clean_prefix}%", *existing_ids, remaining))
            results.extend([dict(row) for row in cursor.fetchall()])

        # Step C: If still needed, query full-text search index
        if len(results) < limit:
            fts_matches = self.search_fulltext(clean_prefix, limit=limit)
            existing_ids = {r["id"] for r in results}
            for f in fts_matches:
                if f["id"] not in existing_ids:
                    results.append(f)
                    if len(results) >= limit:
                        break

        return results

    def get_quote_by_id(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """Traverses the graph to fetch quote node and all connected author, work, and category nodes."""
        cursor = self.conn.cursor()
        sql = """
            SELECT q.id, q.text, q.source, q.work, q.char_length, a.name AS author
            FROM quotes q
            LEFT JOIN edge_said_by es ON es.quote_id = q.id
            LEFT JOIN authors a ON a.id = es.author_id
            WHERE q.id = ?
        """
        cursor.execute(sql, (quote_id,))
        row = cursor.fetchone()
        if not row:
            return None

        result = dict(row)

        # Retrieve connected categories via edge_has_category
        cat_sql = """
            SELECT c.name
            FROM categories c
            JOIN edge_has_category ehc ON ehc.category_id = c.id
            WHERE ehc.quote_id = ?
        """
        cursor.execute(cat_sql, (quote_id,))
        result["categories"] = [r["name"] for r in cursor.fetchall()]
        return result

    def get_quotes_by_author(self, author_name: str) -> List[Dict[str, Any]]:
        """Traverses the graph from an Author node to all linked Quote nodes."""
        cursor = self.conn.cursor()
        sql = """
            SELECT q.id, q.text, q.source, q.work, a.name AS author
            FROM quotes q
            JOIN edge_said_by es ON es.quote_id = q.id
            JOIN authors a ON a.id = es.author_id
            WHERE a.name LIKE ?
            ORDER BY q.id ASC
        """
        cursor.execute(sql, (f"%{author_name.strip()}%",))
        return [dict(r) for r in cursor.fetchall()]

    def get_quotes_by_work(self, work_title: str) -> List[Dict[str, Any]]:
        """Traverses the graph from a Work node to all linked Quote nodes."""
        cursor = self.conn.cursor()
        sql = """
            SELECT q.id, q.text, q.source, w.title AS work, a.name AS author
            FROM quotes q
            JOIN edge_from_work efw ON efw.quote_id = q.id
            JOIN works w ON w.id = efw.work_id
            JOIN edge_said_by es ON es.quote_id = q.id
            JOIN authors a ON a.id = es.author_id
            WHERE w.title LIKE ?
            ORDER BY q.id ASC
        """
        cursor.execute(sql, (f"%{work_title.strip()}%",))
        return [dict(r) for r in cursor.fetchall()]

    def get_stats(self) -> Dict[str, int]:
        cursor = self.conn.cursor()
        quotes_count = cursor.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
        authors_count = cursor.execute("SELECT COUNT(*) FROM authors").fetchone()[0]
        works_count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        categories_count = cursor.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        return {
            "quotes": quotes_count,
            "authors": authors_count,
            "works": works_count,
            "categories": categories_count
        }

    def close(self) -> None:
        if self.conn:
            self.conn.close()


class Neo4jQuoteGraph(BaseQuoteGraph):
    """
    Production-grade Graph Database implementation using Neo4j and official driver.
    """

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise RuntimeError("neo4j driver not installed. Please install 'neo4j' package.")

        self.uri = uri or config.graph_db.neo4j_uri
        self.user = user or config.graph_db.neo4j_user
        self.password = password or config.graph_db.neo4j_password
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.initialize_schema()

    def initialize_schema(self) -> None:
        with self.driver.session() as session:
            # Create uniqueness constraints
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (q:Quote) REQUIRE q.text IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (w:Work) REQUIRE w.title IS UNIQUE")

            # Create full-text index on Quote citations
            try:
                session.run("""
                    CREATE FULLTEXT INDEX quoteTextIndex IF NOT EXISTS
                    FOR (n:Quote) ON EACH [n.text]
                """)
            except Exception as e:
                print(f"[*] Note on Neo4j fulltext index: {e}")

    def insert_quote(self, quote: str, author: str, source: str, work: str, categories: List[str]) -> int:
        clean_text = clean_wiki_markup(quote)
        if not clean_text or len(clean_text) < 15:
            return -1

        query = """
            MERGE (q:Quote {text: $text})
            ON CREATE SET q.source = $source, q.length = size($text)
            MERGE (a:Author {name: $author})
            MERGE (w:Work {title: $work})
            MERGE (q)-[:SAID_BY]->(a)
            MERGE (q)-[:FROM_WORK]->(w)
            WITH q
            UNWIND $categories AS cat_name
            MERGE (c:Category {name: cat_name})
            MERGE (q)-[:HAS_CATEGORY]->(c)
            RETURN id(q) AS quote_id
        """
        with self.driver.session() as session:
            result = session.run(
                query,
                text=clean_text,
                author=author or "Unknown",
                source=source or author or "Unknown",
                work=work or "General",
                categories=categories or []
            )
            record = result.single()
            return record["quote_id"] if record else 1

    def insert_quotes_batch(self, quotes: List[Dict[str, Any]]) -> int:
        count = 0
        for q in quotes:
            if self.insert_quote(
                quote=q.get("quote", ""),
                author=q.get("author", "Unknown"),
                source=q.get("source", ""),
                work=q.get("work", "General"),
                categories=q.get("categories", [])
            ) > 0:
                count += 1
        return count

    def search_fulltext(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        cypher = """
            CALL db.index.fulltext.queryNodes("quoteTextIndex", $search_term) YIELD node, score
            MATCH (node)-[:SAID_BY]->(a:Author)
            OPTIONAL MATCH (node)-[:FROM_WORK]->(w:Work)
            RETURN id(node) AS id, node.text AS text, a.name AS author,
                   node.source AS source, w.title AS work, score
            ORDER BY score DESC
            LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(cypher, search_term=f"{query}*", limit=limit)
            return [dict(record) for record in result]

    def autocomplete_citation(self, prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
        clean_prefix = clean_wiki_markup(prefix)
        # Prefix Cypher matching
        cypher = """
            MATCH (q:Quote)-[:SAID_BY]->(a:Author)
            OPTIONAL MATCH (q)-[:FROM_WORK]->(w:Work)
            WHERE toLower(q.text) STARTS WITH toLower($prefix) OR toLower(q.text) CONTAINS toLower($prefix)
            RETURN id(q) AS id, q.text AS text, a.name AS author, q.source AS source, w.title AS work, 1.0 AS score
            ORDER BY size(q.text) ASC
            LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(cypher, prefix=clean_prefix, limit=limit)
            records = [dict(r) for r in result]
            if not records:
                return self.search_fulltext(clean_prefix, limit=limit)
            return records

    def get_quote_by_id(self, quote_id: int) -> Optional[Dict[str, Any]]:
        cypher = """
            MATCH (q:Quote) WHERE id(q) = $quote_id
            OPTIONAL MATCH (q)-[:SAID_BY]->(a:Author)
            OPTIONAL MATCH (q)-[:FROM_WORK]->(w:Work)
            OPTIONAL MATCH (q)-[:HAS_CATEGORY]->(c:Category)
            RETURN id(q) AS id, q.text AS text, q.source AS source,
                   a.name AS author, w.title AS work, collect(c.name) AS categories
        """
        with self.driver.session() as session:
            result = session.run(cypher, quote_id=quote_id)
            record = result.single()
            return dict(record) if record else None

    def get_quotes_by_author(self, author_name: str) -> List[Dict[str, Any]]:
        cypher = """
            MATCH (q:Quote)-[:SAID_BY]->(a:Author)
            OPTIONAL MATCH (q)-[:FROM_WORK]->(w:Work)
            WHERE toLower(a.name) CONTAINS toLower($author_name)
            RETURN id(q) AS id, q.text AS text, a.name AS author, q.source AS source, w.title AS work
            ORDER BY id(q) ASC
        """
        with self.driver.session() as session:
            result = session.run(cypher, author_name=author_name)
            return [dict(r) for r in result]

    def get_quotes_by_work(self, work_title: str) -> List[Dict[str, Any]]:
        cypher = """
            MATCH (q:Quote)-[:FROM_WORK]->(w:Work)
            OPTIONAL MATCH (q)-[:SAID_BY]->(a:Author)
            WHERE toLower(w.title) CONTAINS toLower($work_title)
            RETURN id(q) AS id, q.text AS text, a.name AS author, q.source AS source, w.title AS work
            ORDER BY id(q) ASC
        """
        with self.driver.session() as session:
            result = session.run(cypher, work_title=work_title)
            return [dict(r) for r in result]

    def get_stats(self) -> Dict[str, int]:
        with self.driver.session() as session:
            q_cnt = session.run("MATCH (n:Quote) RETURN count(n) AS cnt").single()["cnt"]
            a_cnt = session.run("MATCH (n:Author) RETURN count(n) AS cnt").single()["cnt"]
            w_cnt = session.run("MATCH (n:Work) RETURN count(n) AS cnt").single()["cnt"]
            return {"quotes": q_cnt, "authors": a_cnt, "works": w_cnt, "categories": 0}

    def close(self) -> None:
        self.driver.close()


def get_quote_graph(backend: Optional[str] = None) -> BaseQuoteGraph:
    """
    Factory function to retrieve the configured graph database instance.
    Defaults to LocalQuoteGraph for zero-setup reliable operation.
    """
    chosen_backend = (backend or config.graph_db.default_backend).lower()
    if chosen_backend == "neo4j":
        try:
            return Neo4jQuoteGraph()
        except Exception as e:
            print(f"[!] Warning: Could not connect to Neo4j ({e}). Falling back to LocalQuoteGraph.")
            return LocalQuoteGraph()
    return LocalQuoteGraph()
