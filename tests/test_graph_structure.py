import tempfile
import sqlite3
import pytest
from unittest.mock import MagicMock, patch

from src.step1_graph.graph_db import LocalQuoteGraph, Neo4jQuoteGraph
from scripts.build_graph import SEED_QUOTES


class TestLocalGraphStructure:
    """Verifies node creation, relationships (edges), constraints, and traversals in LocalQuoteGraph."""

    @pytest.fixture
    def temp_graph(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            graph = LocalQuoteGraph(db_path=tmp.name)
            yield graph
            graph.close()

    def test_node_creation_and_integrity(self, temp_graph):
        """Verifies Quote, Author, Work, and Category nodes are created with correct constraints."""
        qid = temp_graph.insert_quote(
            quote="Stay hungry, stay foolish.",
            author="Steve Jobs",
            source="Stanford Address (2005)",
            work="Speeches",
            categories=["Entrepreneurs", "Technology"]
        )
        assert qid > 0

        cursor = temp_graph.conn.cursor()

        # Check nodes
        author = cursor.execute("SELECT * FROM authors WHERE name = 'Steve Jobs'").fetchone()
        assert author is not None
        assert author["name"] == "Steve Jobs"

        work = cursor.execute("SELECT * FROM works WHERE title = 'Speeches'").fetchone()
        assert work is not None
        assert work["title"] == "Speeches"

        categories = cursor.execute("SELECT name FROM categories ORDER BY name ASC").fetchall()
        cat_names = [c["name"] for c in categories]
        assert "Entrepreneurs" in cat_names
        assert "Technology" in cat_names

    def test_relationship_edges(self, temp_graph):
        """Verifies graph edges (said_by, from_work, has_category) correctly connect nodes."""
        qid = temp_graph.insert_quote(
            quote="To be, or not to be, that is the question.",
            author="William Shakespeare",
            source="Hamlet, Act III",
            work="Hamlet",
            categories=["Playwrights", "Drama"]
        )

        # Graph traversal by quote ID
        quote_details = temp_graph.get_quote_by_id(qid)
        assert quote_details is not None
        assert quote_details["author"] == "William Shakespeare"
        assert quote_details["work"] == "Hamlet"
        assert set(quote_details["categories"]) == {"Playwrights", "Drama"}

        # Graph traversal: Author -> Quotes
        author_quotes = temp_graph.get_quotes_by_author("William Shakespeare")
        assert len(author_quotes) == 1
        assert "To be, or not to be" in author_quotes[0]["text"]

        # Graph traversal: Work -> Quotes
        work_quotes = temp_graph.get_quotes_by_work("Hamlet")
        assert len(work_quotes) == 1
        assert work_quotes[0]["author"] == "William Shakespeare"

    def test_node_deduplication(self, temp_graph):
        """Verifies authors, works, and categories are not duplicated when shared across quotes."""
        temp_graph.insert_quote(
            quote="Quote number one by author.",
            author="Albert Einstein",
            source="Source 1",
            work="Relativity",
            categories=["Physics"]
        )
        temp_graph.insert_quote(
            quote="Quote number two by same author.",
            author="Albert Einstein",
            source="Source 2",
            work="Relativity",
            categories=["Physics", "Science"]
        )

        stats = temp_graph.get_stats()
        assert stats["quotes"] == 2
        assert stats["authors"] == 1  # Only 1 Einstein node
        assert stats["works"] == 1    # Only 1 Relativity node
        assert stats["categories"] == 2  # Physics and Science

    def test_fts5_index_synchronization(self, temp_graph):
        """Verifies the FTS5 full-text index returns joined graph attributes."""
        temp_graph.insert_quote(
            quote="Imagination is more important than knowledge.",
            author="Albert Einstein",
            source="What Life Means to Einstein",
            work="Interviews",
            categories=["Physics"]
        )

        matches = temp_graph.search_fulltext("imagination", limit=1)
        assert len(matches) == 1
        assert matches[0]["author"] == "Albert Einstein"
        assert matches[0]["work"] == "Interviews"
        assert "knowledge" in matches[0]["text"]


class TestSeedDataCorrectness:
    """Validates structural correctness and relational integrity of the pre-loaded seed dataset."""

    @pytest.fixture
    def seed_graph(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            graph = LocalQuoteGraph(db_path=tmp.name)
            graph.insert_quotes_batch(SEED_QUOTES)
            yield graph
            graph.close()

    def test_seed_counts_and_no_orphaned_edges(self, seed_graph):
        """Checks that all quotes have valid author and work relationships with zero orphans."""
        cursor = seed_graph.conn.cursor()

        # Check total quotes
        quote_count = cursor.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
        assert quote_count == len(SEED_QUOTES)

        # Ensure 0 orphaned edge_said_by records
        orphaned_authors = cursor.execute("""
            SELECT COUNT(*) FROM edge_said_by es
            LEFT JOIN quotes q ON q.id = es.quote_id
            LEFT JOIN authors a ON a.id = es.author_id
            WHERE q.id IS NULL OR a.id IS NULL
        """).fetchone()[0]
        assert orphaned_authors == 0

        # Ensure 0 orphaned edge_from_work records
        orphaned_works = cursor.execute("""
            SELECT COUNT(*) FROM edge_from_work efw
            LEFT JOIN quotes q ON q.id = efw.quote_id
            LEFT JOIN works w ON w.id = efw.work_id
            WHERE q.id IS NULL OR w.id IS NULL
        """).fetchone()[0]
        assert orphaned_works == 0


class TestNeo4jMockedGraph:
    """Mock test verifying Neo4j Cypher queries and schema creation without running a live server."""

    @patch("neo4j.GraphDatabase.driver")
    def test_neo4j_initialization_cypher(self, mock_driver_cls):
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver_cls.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session

        neo_graph = Neo4jQuoteGraph(uri="bolt://localhost:7687", user="neo4j", password="password")

        # Verify uniqueness constraints and index execution
        cypher_calls = [c[0][0] for c in mock_session.run.call_args_list]
        assert any("CREATE CONSTRAINT IF NOT EXISTS FOR (q:Quote) REQUIRE q.text IS UNIQUE" in q for q in cypher_calls)
        assert any("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE" in q for q in cypher_calls)
        assert any("CREATE FULLTEXT INDEX" in q for q in cypher_calls)

    @patch("neo4j.GraphDatabase.driver")
    def test_neo4j_insert_quote_cypher(self, mock_driver_cls):
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver_cls.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session

        # Setup mock return record for inserted quote id
        mock_result = MagicMock()
        mock_result.single.return_value = {"quote_id": 42}
        mock_session.run.return_value = mock_result

        neo_graph = Neo4jQuoteGraph()
        qid = neo_graph.insert_quote(
            quote="Stay hungry, stay foolish.",
            author="Steve Jobs",
            source="Stanford Address",
            work="Speeches",
            categories=["Technology"]
        )

        assert qid == 42
        # Verify MERGE Cypher query was invoked with parameters
        last_call_args = mock_session.run.call_args
        cypher_query = last_call_args[0][0]
        cypher_params = last_call_args[1]

        assert "MERGE (q:Quote {text: $text})" in cypher_query
        assert "MERGE (a:Author {name: $author})" in cypher_query
        assert "MERGE (q)-[:SAID_BY]->(a)" in cypher_query
        assert cypher_params["author"] == "Steve Jobs"
        assert cypher_params["work"] == "Speeches"

    @patch("neo4j.GraphDatabase.driver")
    def test_neo4j_traversal_cypher(self, mock_driver_cls):
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver_cls.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session

        mock_session.run.return_value = [
            {"id": 1, "text": "Stay hungry, stay foolish.", "author": "Steve Jobs", "source": "Stanford", "work": "Speeches"}
        ]

        neo_graph = Neo4jQuoteGraph()
        results = neo_graph.get_quotes_by_author("Steve Jobs")

        assert len(results) == 1
        assert results[0]["author"] == "Steve Jobs"
        # Verify Cypher MATCH query
        last_call = mock_session.run.call_args
        assert "MATCH (q:Quote)-[:SAID_BY]->(a:Author)" in last_call[0][0]
        assert last_call[1]["author_name"] == "Steve Jobs"
