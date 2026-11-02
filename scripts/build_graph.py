"""
Build Graph Script.
Queries DBpedia SPARQL endpoint and loads entities and relations into the Neo4j / Local Graph Database.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_pipeline.sparql_client import DBpediaSPARQLClient
from src.data_pipeline.graph_db import NeapolitanArtGraph


def main():
    print("=" * 60)
    print("Building Neapolitan Art Knowledge Graph from DBpedia SPARQL")
    print("=" * 60)

    # 1. Fetch data from DBpedia
    client = DBpediaSPARQLClient()
    print("Executing SPARQL queries against DBpedia...")
    corpus = client.fetch_neapolitan_corpus(force_refresh=False)
    print(f"Retrieved {len(corpus['artworks'])} artworks, {len(corpus['artists'])} artists, {len(corpus['venues'])} venues.")

    # 2. Populate Graph
    print("\nInitializing Graph Database...")
    graph = NeapolitanArtGraph()
    print(f"Active backend: {graph.active_backend.upper()}")
    graph.populate(corpus)

    # 3. Verify graph contents
    artworks = graph.get_all_artworks()
    venues = graph.get_all_locations()
    artists = graph.get_all_artists()

    print("\nKnowledge Graph Verification:")
    print(f"- Total Artists in Graph: {len(artists)}")
    for a in artists:
        print(f"  * {a['name']}: {a.get('artwork_count', 0)} works")

    print(f"\n- Total Venues in Naples: {len(venues)}")
    for v in venues:
        print(f"  * {v['name']}: {v.get('artwork_count', 0)} works ({v.get('address', '')})")

    print(f"\n- Total Artworks in Naples: {len(artworks)}")
    for art in artworks:
        print(f"  * '{art['title']}' ({art.get('year', '')}) by {art['artist']} @ {art['location']}")

    print("\nGraph build completed successfully.")


if __name__ == "__main__":
    main()
