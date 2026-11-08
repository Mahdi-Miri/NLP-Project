"""
Generate End-to-End Pipeline Architecture Diagram using Graphviz.
Academic Monochrome (Grayscale / Black & White) 300 DPI rendering.
Vertical Workflow Architecture (Top-to-Bottom Flow across 12 Stages).
"""

from pathlib import Path
import graphviz

project_root = Path(__file__).resolve().parent.parent
docs_dir = project_root / "docs"
docs_dir.mkdir(parents=True, exist_ok=True)


def build_pipeline_graphviz_vertical():
    dot = graphviz.Digraph(
        name="Neapolitan_Art_Pipeline_Vertical",
        comment="Neapolitan Artistic Heritage Multimodal Architecture (Vertical Flow)",
    )

    # Global Graph Attributes
    dot.attr(
        rankdir="TB",
        compound="true",
        dpi="300",
        bgcolor="#ffffff",
        nodesep="0.22",
        ranksep="0.20",
        splines="spline",
        margin="0.06",
    )

    # Default Node Attributes
    dot.attr(
        "node",
        shape="none",
        fontname="Helvetica",
        fontsize="9.0",
        color="#222222",
    )

    # Default Edge Attributes
    dot.attr(
        "edge",
        fontname="Helvetica",
        fontsize="7.6",
        fontcolor="#111111",
        color="#333333",
        arrowsize="0.65",
        penwidth="1.0",
    )

    # =========================================================================
    # CLUSTER 1: TIER I (MULTIMODAL INGESTION & ACOUSTICS)
    # =========================================================================
    with dot.subgraph(name="cluster_tier1") as c1:
        c1.attr(
            label="  TIER I: MULTIMODAL INGESTION & ACOUSTICS",
            labeljust="l",
            fontname="Helvetica-Bold",
            fontsize="9.0",
            fontcolor="#000000",
            style="rounded,solid",
            color="#555555",
            bgcolor="#fafafa",
            margin="8",
        )

        c1.node(
            "node_ingest",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>1. Multimodal Ingestion</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Mic Stream (16 kHz) / Text Input</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Streamlit WebSocket Client Hub</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• In-Memory Float32 Audio Buffer</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c1.node(
            "node_asr",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>2. Acoustic Engineering</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• OpenAI Whisper Small (244M params)</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Peak Amplitude Norm: 0.95 · x / max|x|</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• 80-Channel Log-Mel Filterbank</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Art-Historical Prompt Token Prior</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c1.node(
            "node_phonetic",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>3. Phonetic Normalizer</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Prep Correction: 'for' -&gt; 'of'</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Italian Degemination ('caravagio')</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Dialectal Spacing ('capo di monte')</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Ordinal Numeral Normalization</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c1.edge("node_ingest", "node_asr", label=" Audio Stream")
        c1.edge("node_asr", "node_phonetic", label=" Raw ASR Text")

    # =========================================================================
    # CLUSTER 2: TIER II (PARSING, STATE TRACKING & GUARDRAILS)
    # =========================================================================
    with dot.subgraph(name="cluster_tier2") as c2:
        c2.attr(
            label="  TIER II: SEMANTIC PARSING & GUARDRAILS",
            labeljust="l",
            fontname="Helvetica-Bold",
            fontsize="9.0",
            fontcolor="#000000",
            style="rounded,solid",
            color="#555555",
            bgcolor="#fafafa",
            margin="8",
        )

        c2.node(
            "node_parser",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>4. Entity &amp; Intent Parser</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• 8 Masterwork Titles &amp; Italian Aliases</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Caravaggio / Battistello Lexicon</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• 5 Neapolitan Historic Sanctuaries</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• 8-Route Intent Keyword Classifier</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c2.node(
            "node_dst",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>5. Discourse Tracker (DST)</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• State: S(t) = &lt;e_art, e_artist, e_venue&gt;</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Anaphoric Coreference ('it', 'this work')</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Recency Window Limit (W &#8804; 3 Turns)</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Context Isolation &amp; Topic Reset</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c2.node(
            "node_guardrail",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>6. Inconsistency Guardrail</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• 5-Predicate Truth Verification</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• I_artist: Attribution Contradiction</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• I_venue: Location Contradiction</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• I_city / I_scope: Scope Boundaries</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c2.edge("node_parser", "node_dst", label=" Entities & Intent")
        c2.edge("node_dst", "node_guardrail", label=" State Tuple S(t)")

    # =========================================================================
    # CLUSTER 3: TIER III (KNOWLEDGE BASE & QUERY ROUTING)
    # =========================================================================
    with dot.subgraph(name="cluster_tier3") as c3:
        c3.attr(
            label="  TIER III: KNOWLEDGE GRAPH & QUERY ROUTING",
            labeljust="l",
            fontname="Helvetica-Bold",
            fontsize="9.0",
            fontcolor="#000000",
            style="rounded,solid",
            color="#555555",
            bgcolor="#fafafa",
            margin="8",
        )

        c3.node(
            "node_router",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>7. Query Selection Router</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Deterministic Decision Tree</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Parameterized Cypher/SQL Dispatch</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Entity Priority: Art &gt; Loc &gt; Artist</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Global Overview &amp; Fallback Dispatch</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c3.node(
            "node_graph",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>8. Dual Knowledge Graph</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Primary: Neo4j 5.x Cypher Bolt Driver</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Fallback: Embedded SQLite 3 Store</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Zero-Downtime Heartbeat Circuit</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Sub-2ms Graph Query Execution</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c3.node(
            "node_dbpedia",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>9. DBpedia SPARQL Ingestion</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• W3C SPARQL 1.1 Live Harvesting</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Biographical Dates, Places, Abstracts</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Atomic Local JSON Cache Snapshot</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Schema Uniqueness Constraints</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c3.edge("node_router", "node_graph", label=" Query Exec")
        c3.edge("node_graph", "node_dbpedia", label=" Linked Enrichment")

    # =========================================================================
    # CLUSTER 4: TIER IV (GENERATION & MULTIMODAL DELIVERY)
    # =========================================================================
    with dot.subgraph(name="cluster_tier4") as c4:
        c4.attr(
            label="  TIER IV: GENERATION & MULTIMODAL DELIVERY",
            labeljust="l",
            fontname="Helvetica-Bold",
            fontsize="9.0",
            fontcolor="#000000",
            style="rounded,solid",
            color="#555555",
            bgcolor="#fafafa",
            margin="8",
        )

        c4.node(
            "node_nlg",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>10. Curatorial NLG Engine</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Fluent Speech-Optimized Prose</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Eliminates Key-Value Serializations</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Pedagogical Reframing of Errors</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Proactive Inquiry Prompts</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c4.node(
            "node_tts",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>11. Neural Edge-TTS Voice</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Microsoft Edge Neural Voice (24 kHz)</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• en-GB-RyanNeural British Cadence</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Offline pyttsx3 Synthesis Fallback</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• 420 ms Audio Streaming Pipeline</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c4.node(
            "node_client",
            """<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#FFFFFF" COLOR="#333333">
                <TR><TD BGCOLOR="#000000" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>12. Client Presentation UI</B></FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Streamlit Light Reactive Web App</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Native In-Browser HTML5 Player</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Live Discourse State Badges</FONT></TD></TR>
                <TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.0" COLOR="#333333">• Multi-Turn Audit Transcript</FONT></TD></TR>
            </TABLE>
            >""",
        )

        c4.edge("node_nlg", "node_tts", label=" Prose Text")
        c4.edge("node_tts", "node_client", label=" 24 kHz MP3")

    # =========================================================================
    # INTER-TIER VERTICAL PROPAGATION EDGES
    # =========================================================================
    dot.edge("node_phonetic", "node_parser", label=" Cleaned Query")
    dot.edge("node_guardrail", "node_router", label=" Verified Query (No Contradiction)")
    dot.edge(
        "node_guardrail",
        "node_nlg",
        label=" Contradiction Override (Pedagogical Reframing)",
        style="dashed",
        penwidth="1.3",
        color="#000000",
    )
    dot.edge("node_dbpedia", "node_nlg", label=" Retrieved Knowledge Tuples")

    # Render DOT and PNG
    output_base = str(docs_dir / "pipeline_architecture")
    dot.render(output_base, format="png", cleanup=False)
    print(f"Graphviz vertical pipeline diagram successfully generated at: {output_base}.png and {output_base}")


if __name__ == "__main__":
    build_pipeline_graphviz_vertical()
