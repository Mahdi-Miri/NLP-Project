import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import List, Dict, Any
from config.settings import config
from src.step1_graph.graph_db import get_quote_graph
from src.step1_graph.parser import WikiquoteDumpParser

# High-quality starter quotes for instant testing and demonstration
SEED_QUOTES: List[Dict[str, Any]] = [
    {
        "quote": "To be, or not to be, that is the question: Whether 'tis nobler in the mind to suffer the slings and arrows of outrageous fortune.",
        "author": "William Shakespeare",
        "source": "Hamlet, Act III, Scene 1",
        "work": "Hamlet",
        "categories": ["Playwrights", "English literature", "Drama"]
    },
    {
        "quote": "All the world's a stage, and all the men and women merely players.",
        "author": "William Shakespeare",
        "source": "As You Like It, Act II, Scene 7",
        "work": "As You Like It",
        "categories": ["Playwrights", "English literature", "Drama"]
    },
    {
        "quote": "Imagination is more important than knowledge. For knowledge is limited, whereas imagination embraces the entire world.",
        "author": "Albert Einstein",
        "source": "What Life Means to Einstein (1929)",
        "work": "Interviews",
        "categories": ["Physicists", "Nobel laureates", "Scientists"]
    },
    {
        "quote": "God does not play dice with the universe.",
        "author": "Albert Einstein",
        "source": "Letter to Max Born (1926)",
        "work": "Letters",
        "categories": ["Physicists", "Scientists", "Philosophy"]
    },
    {
        "quote": "Stay hungry, stay foolish.",
        "author": "Steve Jobs",
        "source": "Stanford University Commencement Address (2005)",
        "work": "Speeches",
        "categories": ["Entrepreneurs", "Technology", "Apple"]
    },
    {
        "quote": "Your time is limited, so don't waste it living someone else's life.",
        "author": "Steve Jobs",
        "source": "Stanford University Commencement Address (2005)",
        "work": "Speeches",
        "categories": ["Entrepreneurs", "Inspiration"]
    },
    {
        "quote": "I have a dream that one day this nation will rise up and live out the true meaning of its creed.",
        "author": "Martin Luther King Jr.",
        "source": "March on Washington for Jobs and Freedom (1963)",
        "work": "I Have a Dream",
        "categories": ["Civil rights activists", "Orators", "Peace"]
    },
    {
        "quote": "Be the change that you wish to see in the world.",
        "author": "Mahatma Gandhi",
        "source": "Attributed / Collected Works",
        "work": "General",
        "categories": ["Leaders", "Peace", "Philosophy"]
    },
    {
        "quote": "Be yourself; everyone else is already taken.",
        "author": "Oscar Wilde",
        "source": "Attributed",
        "work": "Aphorisms",
        "categories": ["Writers", "Irish literature", "Wit"]
    },
    {
        "quote": "We are all in the gutter, but some of us are looking at the stars.",
        "author": "Oscar Wilde",
        "source": "Lady Windermere's Fan (1892)",
        "work": "Lady Windermere's Fan",
        "categories": ["Writers", "Plays", "Wit"]
    },
    {
        "quote": "The fool doth think he is wise, but the wise man knows himself to be a fool.",
        "author": "William Shakespeare",
        "source": "As You Like It, Act V, Scene 1",
        "work": "As You Like It",
        "categories": ["Playwrights", "Wisdom"]
    },
    {
        "quote": "Two things are infinite: the universe and human stupidity; and I'm not sure about the universe.",
        "author": "Albert Einstein",
        "source": "Attributed / The Ultimate Quotable Einstein",
        "work": "Aphorisms",
        "categories": ["Physicists", "Humor", "Philosophy"]
    },
    {
        "quote": "In the middle of difficulty lies opportunity.",
        "author": "Albert Einstein",
        "source": "Three Rules of Work (1979)",
        "work": "Aphorisms",
        "categories": ["Physicists", "Inspiration"]
    },
    {
        "quote": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs",
        "source": "Stanford Address (2005)",
        "work": "Speeches",
        "categories": ["Entrepreneurs", "Career"]
    },
    {
        "quote": "Darkness cannot drive out darkness; only light can do that. Hate cannot drive out hate; only love can do that.",
        "author": "Martin Luther King Jr.",
        "source": "Strength to Love (1963)",
        "work": "Strength to Love",
        "categories": ["Civil rights activists", "Peace"]
    }
]


def populate_seed_quotes(backend: str = "sqlite") -> None:
    """Populates the graph database with starter quotes."""
    print(f"[*] Initializing graph database using backend: '{backend}'...")
    graph = get_quote_graph(backend=backend)
    inserted = graph.insert_quotes_batch(SEED_QUOTES)
    stats = graph.get_stats()
    print(f"[+] Successfully loaded {inserted} seed quotes into the graph database.")
    print(f"[+] Graph Statistics: {stats}")


def parse_and_populate_dump(dump_path: str, backend: str = "sqlite", max_quotes: int = 1000) -> None:
    """Parses Wikiquote dump file and inserts quotes into the graph database."""
    print(f"[*] Parsing dump file: {dump_path} (max quotes: {max_quotes})...")
    parser = WikiquoteDumpParser(dump_path)
    graph = get_quote_graph(backend=backend)

    batch = []
    total_inserted = 0

    for item in parser.stream_quotes(max_quotes=max_quotes):
        batch.append(item)
        if len(batch) >= 100:
            inserted = graph.insert_quotes_batch(batch)
            total_inserted += inserted
            print(f"[*] Progress: Ingested {total_inserted} quotes...")
            batch = []

    if batch:
        inserted = graph.insert_quotes_batch(batch)
        total_inserted += inserted

    stats = graph.get_stats()
    print(f"[+] Done! Total ingested quotes: {total_inserted}")
    print(f"[+] Final Graph Statistics: {stats}")


def main():
    arg_parser = argparse.ArgumentParser(description="Build and populate the Wikiquote Graph Database.")
    arg_parser.add_argument("--backend", choices=["sqlite", "neo4j"], default="sqlite", help="Graph DB backend")
    arg_parser.add_argument("--seed", action="store_true", help="Populate with seed quotes for instant demo")
    arg_parser.add_argument("--dump", type=str, help="Path to Wikimedia XML / bz2 dump file")
    arg_parser.add_argument("--max", type=int, default=1000, help="Maximum quotes to ingest from dump")

    args = arg_parser.parse_args()

    if args.dump:
        parse_and_populate_dump(args.dump, backend=args.backend, max_quotes=args.max)
    else:
        populate_seed_quotes(backend=args.backend)


if __name__ == "__main__":
    main()
