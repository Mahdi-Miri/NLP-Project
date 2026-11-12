"""
Vertical workflow diagram of the actual dialogue pipeline, rendered with Graphviz.
Reflects the real modules in src/ — not an idealized or invented architecture.
"""

from pathlib import Path
import graphviz

project_root = Path(__file__).resolve().parent.parent
docs_dir = project_root / "docs"
docs_dir.mkdir(parents=True, exist_ok=True)


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(label_lines, title):
    rows = "".join(
        f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="8.5" COLOR="#222222">{esc(line)}</FONT></TD></TR>'
        for line in label_lines
    )
    return f"""<
    <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5" BGCOLOR="#FFFFFF" COLOR="#333333">
        <TR><TD BGCOLOR="#1a1a1a" ALIGN="CENTER"><FONT COLOR="#FFFFFF" POINT-SIZE="9.5"><B>{esc(title)}</B></FONT></TD></TR>
        {rows}
    </TABLE>
    >"""


def build_pipeline_graphviz_vertical():
    dot = graphviz.Digraph(
        name="Neapolitan_Dialogue_Pipeline",
        comment="Neapolitan Artistic Heritage Dialogue System — actual processing pipeline",
    )

    dot.attr(
        rankdir="TB",
        compound="true",
        dpi="300",
        bgcolor="#ffffff",
        nodesep="0.25",
        ranksep="0.28",
        splines="spline",
        margin="0.1",
    )
    dot.attr("node", shape="none", fontname="Helvetica", fontsize="9.0")
    dot.attr(
        "edge",
        fontname="Helvetica",
        fontsize="7.8",
        fontcolor="#111111",
        color="#333333",
        arrowsize="0.7",
        penwidth="1.0",
    )

    # ---------------- One-time setup path (left side, feeds the graph) ----------------
    with dot.subgraph(name="cluster_setup") as cs:
        cs.attr(
            label="  ONE-TIME SETUP (scripts/build_graph.py)",
            labeljust="l", fontname="Helvetica-Bold", fontsize="8.5",
            fontcolor="#000000", style="rounded,dashed", color="#777777",
            bgcolor="#fbfbfb", margin="10",
        )
        cs.node("dbpedia", box(
            ["DBpedia SPARQL endpoint (dbpedia.org/sparql)",
             "Artist biographies, abstracts, URIs",
             "src/data_pipeline/sparql_client.py"],
            "DBpedia SPARQL Query",
        ))
        cs.node("curated", box(
            ["8 artworks, 5 venues, structural facts",
             "(title, artist, year, address)",
             "src/data_pipeline/curated_dataset.py"],
            "Curated Catalog",
        ))
        cs.node("cache", box(
            ["Merged snapshot written to disk",
             "data/dbpedia_cache.json"],
            "Local Cache",
        ))
        cs.edge("dbpedia", "cache")
        cs.edge("curated", "cache")

    # ---------------- Per-turn pipeline (main vertical flow) ----------------
    dot.node("input", box(
        ["Microphone audio or typed text",
         "app.py (Streamlit) or scripts/interactive_cli.py"],
        "1. User Turn",
    ))

    dot.node("asr", box(
        ["OpenAI Whisper, 'small' checkpoint, local",
         "16 kHz mono, peak-normalized audio",
         "Domain prompt biases decoding",
         "src/speech/asr.py  (voice input only)"],
        "2. Speech Recognition",
    ))

    dot.node("normalize", box(
        ["Lowercasing + regex normalization",
         "'works for mercy' -> 'works of mercy'",
         "'capo di monte' -> 'capodimonte'",
         "shared by chatbot.py and inconsistency.py"],
        "3. Text Normalization",
    ))

    dot.node("entities", box(
        ["Artwork / artist / location keyword match",
         "Pronoun resolution against dialogue state",
         "('it', 'he', 'there' -> active entity)",
         "src/dialogue/state_tracker.py"],
        "4. Entity Extraction & Coreference",
    ))

    dot.node("guard", box(
        ["5 rule checks against the graph:",
         "artist / venue / city mismatch,",
         "out-of-scope artist, context contradiction",
         "src/dialogue/inconsistency.py"],
        "5. Inconsistency Check",
    ))

    dot.node("graph", box(
        ["(:Artist)-[:PAINTED]->(:Artwork)",
         "-[:LOCATED_AT]->(:Location)-[:IN_CITY]->(:City)",
         "Neo4j (Docker, no fallback)",
         "src/data_pipeline/graph_db.py"],
        "6. Knowledge Graph Lookup",
    ))

    dot.node("respond", box(
        ["Template chosen by question type",
         "(location / authorship / dimensions / date)",
         "filled with the graph fields retrieved above",
         "src/dialogue/chatbot.py"],
        "7. Response Generation",
    ))

    dot.node("state", box(
        ["Updates active artist / artwork / location",
         "Appends turn to conversation history",
         "src/dialogue/state_tracker.py"],
        "8. Dialogue State Update",
    ))

    dot.node("tts", box(
        ["Microsoft Edge-TTS (en-GB-RyanNeural)",
         "pyttsx3 offline fallback on failure",
         "src/speech/tts.py  (voice output only)"],
        "9. Speech Synthesis",
    ))

    dot.node("output", box(
        ["Text reply + optional audio playback",
         "rendered in the Streamlit page or terminal"],
        "10. Response Delivered",
    ))

    # Main vertical flow
    dot.edge("input", "asr", label=" if voice")
    dot.edge("input", "normalize", label=" if text", style="dashed")
    dot.edge("asr", "normalize", label=" transcript")
    dot.edge("normalize", "entities")
    dot.edge("entities", "guard", label=" candidate entities + state")
    dot.edge("guard", "graph", label=" no contradiction found")
    dot.edge(
        "guard", "respond",
        label=" contradiction found -> corrective reply",
        style="dashed", penwidth="1.3", color="#000000",
    )
    dot.edge("graph", "respond", label=" matched facts")
    dot.edge("respond", "state")
    dot.edge("state", "tts", label=" if voice mode")
    dot.edge("state", "output", label=" if text mode", style="dashed")
    dot.edge("tts", "output")

    # Setup feeds the graph (not part of the per-turn loop)
    dot.edge("cache", "graph", label="  populates", style="dotted", color="#777777", constraint="false")

    output_base = str(docs_dir / "pipeline_architecture")
    dot.render(output_base, format="png", cleanup=False)
    print(f"Graphviz pipeline diagram written to: {output_base}.png and {output_base}")


if __name__ == "__main__":
    build_pipeline_graphviz_vertical()
