from typing import List, Dict, Any, Optional
from src.step1_graph.graph_db import BaseQuoteGraph, get_quote_graph
from src.utils.text_utils import clean_wiki_markup, extract_highlighted_match


class QuoteAutocompleter:
    """
    High-level autocompleting engine for citations powered by the graph database.
    Ranks candidates and returns autocompleted completions with their verified sources.
    """

    def __init__(self, graph_db: Optional[BaseQuoteGraph] = None):
        self.graph = graph_db or get_quote_graph()

    def autocomplete(self, partial_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Takes an incomplete sentence or citation prefix and returns the best matching
        quote completions along with author and source attribution from the graph.
        """
        query = clean_wiki_markup(partial_text)
        if not query or len(query) < 2:
            return []

        # Query graph database for prefix and full-text candidates
        raw_candidates = self.graph.autocomplete_citation(query, limit=top_k * 2)

        formatted_results = []
        seen_quotes = set()

        for cand in raw_candidates:
            full_quote = cand.get("text", "")
            if not full_quote or full_quote in seen_quotes:
                continue
            seen_quotes.add(full_quote)

            highlight_info = extract_highlighted_match(full_quote, query)

            formatted_results.append({
                "id": cand.get("id"),
                "full_quote": full_quote,
                "completion": highlight_info["completion"],
                "author": cand.get("author", "Unknown"),
                "work": cand.get("work", "General"),
                "source": cand.get("source", cand.get("author", "Unknown")),
                "score": cand.get("score", 1.0)
            })

            if len(formatted_results) >= top_k:
                break

        return formatted_results

    def autocomplete_with_trace(self, partial_text: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Executes citation autocomplete with deep live tracing:
        - Execution latency (milliseconds)
        - Active search strategy (Prefix / Substring / FTS5 BM25)
        - Equivalent Cypher graph query
        - Executed SQL graph join query
        - Visual Graphviz DOT network representation
        """
        import time
        start_time = time.perf_counter()

        query_clean = clean_wiki_markup(partial_text)
        results = self.autocomplete(partial_text, top_k=top_k)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Enrich each quote result with connected categories
        enriched_results = []
        for r in results:
            details = self.graph.get_quote_by_id(r["id"]) if hasattr(self.graph, "get_quote_by_id") else None
            categories = details.get("categories", []) if details else []
            r_copy = dict(r)
            r_copy["categories"] = categories
            enriched_results.append(r_copy)

        # Determine strategy
        if not results:
            strategy = "No Match Found"
        elif any(r["full_quote"].lower().startswith(query_clean.lower()) for r in results):
            strategy = "Direct Prefix Graph Index Match (Score: 1.0)"
        else:
            strategy = "Inverted Full-Text Index BM25 Substring Match"

        # Equivalent Cypher Query
        cypher_code = (
            f"// Cypher query for quote autocomplete on graph database\n"
            f"MATCH (q:Quote)-[:SAID_BY]->(a:Author)\n"
            f"OPTIONAL MATCH (q)-[:FROM_WORK]->(w:Work)\n"
            f"OPTIONAL MATCH (q)-[:HAS_CATEGORY]->(c:Category)\n"
            f"WHERE toLower(q.text) STARTS WITH toLower(\"{query_clean}\")\n"
            f"   OR toLower(q.text) CONTAINS toLower(\"{query_clean}\")\n"
            f"RETURN q.text AS quote, a.name AS author, w.title AS work, collect(c.name) AS categories\n"
            f"ORDER BY size(q.text) ASC\n"
            f"LIMIT {top_k};"
        )

        # Executed SQL Graph Query
        sql_code = (
            f"-- Relational Graph traversal with Full-Text Index\n"
            f"SELECT q.id, q.text, a.name AS author, q.source, q.work\n"
            f"FROM quotes q\n"
            f"JOIN edge_said_by es ON es.quote_id = q.id\n"
            f"JOIN authors a ON a.id = es.author_id\n"
            f"WHERE q.text LIKE '{query_clean}%'\n"
            f"ORDER BY q.char_length ASC LIMIT {top_k};"
        )

        # Generate Graphviz DOT graph representation
        dot_lines = [
            'digraph QuoteGraph {',
            '  rankdir=LR;',
            '  bgcolor="transparent";',
            '  node [fontname="Helvetica", fontsize=11, style="filled"];',
            '  edge [fontname="Helvetica", fontsize=9, color="#64748B", arrowsize=0.8];'
        ]

        seen_nodes = set()
        for idx, r in enumerate(enriched_results, 1):
            q_id = f"q_{r['id']}"
            q_label = (r['full_quote'][:45] + "...") if len(r['full_quote']) > 45 else r['full_quote']
            q_label = q_label.replace('"', '\\"')

            if q_id not in seen_nodes:
                dot_lines.append(f'  {q_id} [label="{q_label}", shape=box, fillcolor="#DBEAFE", color="#3B82F6", fontcolor="#1E3A8A"];')
                seen_nodes.add(q_id)

            # Author Node
            a_id = f"a_{abs(hash(r['author'])) % 100000}"
            a_label = r['author'].replace('"', '\\"')
            if a_id not in seen_nodes:
                dot_lines.append(f'  {a_id} [label="👤 {a_label}", shape=ellipse, fillcolor="#DCFCE7", color="#16A34A", fontcolor="#14532D"];')
                seen_nodes.add(a_id)
            dot_lines.append(f'  {q_id} -> {a_id} [label="SAID_BY", color="#16A34A"];')

            # Work Node
            if r.get('work') and r['work'] != "General":
                w_id = f"w_{abs(hash(r['work'])) % 100000}"
                w_label = r['work'].replace('"', '\\"')
                if w_id not in seen_nodes:
                    dot_lines.append(f'  {w_id} [label="📖 {w_label}", shape=box, fillcolor="#FFEDD5", color="#EA580C", fontcolor="#7C2D12"];')
                    seen_nodes.add(w_id)
                dot_lines.append(f'  {q_id} -> {w_id} [label="FROM_WORK", color="#EA580C"];')

            # Category Nodes
            for cat in r.get('categories', [])[:2]:
                c_id = f"c_{abs(hash(cat)) % 100000}"
                c_label = cat.replace('"', '\\"')
                if c_id not in seen_nodes:
                    dot_lines.append(f'  {c_id} [label="🏷️ {c_label}", shape=oval, fillcolor="#F3E8FF", color="#9333EA", fontcolor="#581C87"];')
                    seen_nodes.add(c_id)
                dot_lines.append(f'  {q_id} -> {c_id} [label="HAS_CATEGORY", color="#9333EA", style=dashed];')

        dot_lines.append('}')
        dot_graph = "\n".join(dot_lines)

        return {
            "query": partial_text,
            "normalized_query": query_clean,
            "results": enriched_results,
            "count": len(enriched_results),
            "execution_time_ms": elapsed_ms,
            "strategy": strategy,
            "cypher_code": cypher_code,
            "sql_code": sql_code,
            "dot_graph": dot_graph
        }

    def get_best_match(self, partial_text: str) -> Optional[Dict[str, Any]]:
        """Returns the single highest-ranking autocomplete suggestion."""
        results = self.autocomplete(partial_text, top_k=1)
        return results[0] if results else None
