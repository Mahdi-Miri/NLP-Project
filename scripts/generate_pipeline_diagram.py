"""
Generate a publication-quality, monochrome pipeline architecture diagram
for the Neapolitan Artistic Heritage Multimodal Dialogue System.
Strict orthogonal flow with zero overlapping arrows.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_pipeline_diagram(output_path="docs/pipeline_architecture.png"):
    fig, ax = plt.subplots(figsize=(11.5, 6.4), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color palette: pure monochrome grayscale
    c_white = "#ffffff"
    c_card = "#fdfdfd"
    c_subcard = "#f8f9fa"
    c_dark = "#111111"
    c_mid = "#555555"
    c_fill_header = "#222222"

    def draw_box(x, y, w, h, title, subtitle="", items=None):
        # Card background
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.5,rounding_size=1.0",
            facecolor=c_card,
            edgecolor=c_dark,
            linewidth=1.1
        )
        ax.add_patch(rect)

        # Header bar
        header_h = 3.6
        header_rect = patches.FancyBboxPatch(
            (x, y + h - header_h), w, header_h,
            boxstyle="round,pad=0.2,rounding_size=0.6",
            facecolor=c_fill_header,
            edgecolor=c_dark,
            linewidth=0.8
        )
        ax.add_patch(header_rect)

        # Header title
        ax.text(x + w / 2, y + h - header_h / 2, title,
                ha='center', va='center', fontsize=7.8, fontweight='bold', color=c_white)

        # Subtitle
        if subtitle:
            ax.text(x + w / 2, y + h - header_h - 1.8, subtitle,
                    ha='center', va='center', fontsize=6.4, fontstyle='italic', color=c_mid)

        # Items list
        if items:
            start_y = y + h - header_h - (3.4 if subtitle else 1.8)
            for i, itm in enumerate(items):
                ax.text(x + 1.5, start_y - i * 2.8, f"• {itm}",
                        ha='left', va='center', fontsize=6.1, color=c_dark)

    def draw_v_arrow(x, y1, y2, label=""):
        ax.annotate(
            "", xy=(x, y2), xytext=(x, y1),
            arrowprops=dict(arrowstyle="-|>", color=c_dark, lw=1.2, mutation_scale=10)
        )
        if label:
            my = (y1 + y2) / 2
            ax.text(x + 0.6, my, label, ha='left', va='center',
                    fontsize=5.8, fontweight='bold', color=c_dark)

    def draw_h_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color=c_dark, lw=1.2, mutation_scale=10)
        )
        if label:
            mx = (x1 + x2) / 2
            ax.text(mx, y1 + 1.2, label, ha='center', va='center',
                    fontsize=5.8, fontweight='bold', color=c_dark,
                    bbox=dict(boxstyle="square,pad=0.1", facecolor=c_white, edgecolor="none"))

    # Title Banner
    ax.text(50, 97.0, "NEAPOLITAN ARTISTIC HERITAGE MULTIMODAL DIALOGUE ARCHITECTURE",
            ha='center', va='center', fontsize=11.5, fontweight='bold', color=c_dark)
    ax.text(50, 94.0, "End-to-End Computational Workflow: Speech Ingestion, State Tracking, Inconsistency Guardrails, Query Routing & Neural Synthesis",
            ha='center', va='center', fontsize=7.2, color=c_mid)
    ax.plot([3, 97], [92.0, 92.0], color=c_dark, lw=0.9)

    col_w = 21.5
    c1_x = 3.5
    c2_x = 28.0
    c3_x = 52.5
    c4_x = 75.0

    # =========================================================================
    # COLUMN 1: SPEECH & ACOUSTIC TIER
    # =========================================================================
    draw_box(c1_x, 68, col_w, 20.5, "1. Multimodal Ingestion", "Audio & Text Streams", [
        "Microphone Voice Input (16 kHz)",
        "Direct Text Utterance Input",
        "Streamlit WebSocket Client",
        "Single-Page Accordion Layout"
    ])

    draw_box(c1_x, 41, col_w, 22.5, "2. Acoustic Engineering", "Whisper Medium (769M)", [
        "SoundFile Float32 Memory Array",
        "Peak Norm: 0.95 * x / max|x|",
        "80-Channel Log-Mel Filterbank",
        "Art-Historical Prompt Token Prior",
        "Greedy Decode (beam=1) + Temp. Fallback"
    ])

    draw_box(c1_x, 15, col_w, 21.5, "3. Phonetic Normalizer", "Lexical Regularization", [
        "Preposition Fix: 'for' -> 'of'",
        "Italian Degemination Correction",
        "Dialect Spacing: 'capo di monte'",
        "Numeral to Word Expansion"
    ])

    draw_v_arrow(c1_x + col_w / 2, 68, 63.5, "Raw Audio")
    draw_v_arrow(c1_x + col_w / 2, 41, 36.5, "Raw Text")

    # =========================================================================
    # COLUMN 2: NLU & DISCOURSE TIER
    # =========================================================================
    draw_box(c2_x, 68, col_w, 20.5, "4. Entity & Intent Parser", "Lexical Substring Extractors", [
        "8 Artwork Aliases & Italian Titles",
        "Caravaggio / Battistello Variants",
        "5 Neapolitan Venue Identifiers",
        "Intent Keyword Token Matching"
    ])

    draw_box(c2_x, 41, col_w, 22.5, "5. Discourse Tracker (DST)", "Memory State Tuple S(t)", [
        "S(t) = <Artist, Artwork, Venue>",
        "Anaphoric Pronoun Resolution ('it')",
        "Recency Window (W=3 turns)",
        "Idempotent Entity State Transition",
        "Contextual Isolation (No Bleed)"
    ])

    draw_box(c2_x, 15, col_w, 21.5, "6. Inconsistency Guardrail", "5-Predicate Truth Reasoning", [
        "I_artist: Attribution Mismatch",
        "I_venue: Naples Venue Mismatch",
        "I_city: Non-Neapolitan Works",
        "I_scope: Out-of-Scope Masters",
        "I_context: Pronoun Contradiction"
    ])

    # Connect Col 1 to Col 2
    draw_h_arrow(c1_x + col_w, 25.7, c2_x, 25.7, "Clean Query")
    draw_v_arrow(c2_x + col_w / 2, 68, 63.5, "Entities")
    draw_v_arrow(c2_x + col_w / 2, 41, 36.5, "Discourse")
    # Feed into Col 2 top
    ax.annotate("", xy=(c2_x + 1.0, 78.2), xytext=(c1_x + col_w, 25.7),
                arrowprops=dict(arrowstyle="-|>", color=c_dark, lw=1.1, connectionstyle="arc3,rad=-0.18"))

    # =========================================================================
    # COLUMN 3: QUERY SELECTION & KNOWLEDGE TIER
    # =========================================================================
    draw_box(c3_x, 68, col_w, 20.5, "7. Query Selection Router", "Deterministic Intent Dispatch", [
        "Q1: Creative Attribution (Who)",
        "Q2: In-Situ Location (Where)",
        "Q3: Dimensions & Medium (Size)",
        "Q4: Iconography & Meaning (About)",
        "Q5: Museum Venue Holdings (Site)"
    ])

    draw_box(c3_x, 41, col_w, 22.5, "8. Neo4j Knowledge Graph", "40 Nodes, 46 Relationships", [
        "Neo4j 5.x Cypher Engine (Docker)",
        "No Fallback Store — Required Backend",
        "(:Artist)-[:PAINTED]->(:Artwork)-...",
        "Bolt Protocol, Uniqueness Constraints",
        "0.6 ms Average Query Latency (cached)"
    ])

    draw_box(c3_x, 15, col_w, 21.5, "9. DBpedia SPARQL Ingestion", "Linked Open Data Harvesting", [
        "SPARQL 1.1 Endpoint Ingestion",
        "Extract dbo:abstract, dates, URIs",
        "Offline Atomic JSON Cache Snapshot",
        "Schema Uniqueness Constraints"
    ])

    # Connect Col 2 to Col 3
    draw_h_arrow(c2_x + col_w, 78.2, c3_x, 78.2, "Routed Intent")
    draw_v_arrow(c3_x + col_w / 2, 68, 63.5, "Execute")
    draw_v_arrow(c3_x + col_w / 2, 36.5, 41, "Offline Seed")

    # =========================================================================
    # COLUMN 4: GENERATION & MULTIMODAL OUTPUT TIER
    # =========================================================================
    draw_box(c4_x, 68, col_w, 20.5, "10. Curatorial NLG Engine", "Speech-Optimized Prose", [
        "Soft Syntactic Curatorial Framing",
        "Eliminate Robotic Key-Value Dumps",
        "Biographical Context Narration",
        "Educational Error Reframing",
        "Proactive Exploratory Prompting"
    ])

    draw_box(c4_x, 41, col_w, 22.5, "11. Neural Edge-TTS Voice", "Microsoft Edge Neural Voice", [
        "Model: en-GB-RyanNeural",
        "24 kHz High-Fidelity Audio Stream",
        "Authoritative British Gallery Cadence",
        "pyttsx3 Local Offline Fallback",
        "420 ms Audio Synthesis Latency"
    ])

    draw_box(c4_x, 15, col_w, 21.5, "12. Client Presentation UI", "Streamlit Single-Page Hub", [
        "Live Discourse State Card Display",
        "Native In-Browser Audio Player",
        "Sidebar Catalog Statistics Panel",
        "HTML5 Details Provenance Cards",
        "Full Turn Transcript History"
    ])

    # Connect Col 3 to Col 4
    draw_h_arrow(c3_x + col_w, 52.2, c4_x, 78.2, "Graph Facts")
    draw_v_arrow(c4_x + col_w / 2, 68, 63.5, "Prose Text")
    draw_v_arrow(c4_x + col_w / 2, 41, 36.5, "MP3 Stream")

    # Contradiction shortcut arrow (From Col 2 Box 6 directly to Col 4 Box 10)
    ax.annotate("Contradiction Override", xy=(c4_x, 72.0), xytext=(c2_x + col_w, 25.7),
                arrowprops=dict(arrowstyle="-|>", color=c_dark, lw=1.1, ls="--", connectionstyle="arc3,rad=-0.12"),
                fontsize=5.6, fontweight='bold', color=c_dark,
                bbox=dict(boxstyle="square,pad=0.1", facecolor=c_white, edgecolor="none"))

    # Bottom summary box
    summary_rect = patches.Rectangle((3.5, 2.0), 93.0, 9.0, facecolor="#f8f9fa", edgecolor=c_dark, linewidth=1.0)
    ax.add_patch(summary_rect)
    ax.text(5.0, 8.5, "SYSTEM TELEMETRY, QUERY COMPLEXITY & EMPIRICAL BENCHMARK (150-TEST EVALUATION):", fontsize=6.8, fontweight='bold', color=c_dark)
    ax.text(5.0, 5.8, "• Query Latency Breakdown: Neo4j over Bolt, cached (0.6 ms) | Whisper ASR, medium, local (~1.9 s) | Neural TTS (420 ms)", fontsize=6.1, color=c_dark)
    ax.text(5.0, 3.6, "• Query Taxonomy: 2 SPARQL Ingestion Queries, 5 Cypher Subgraph Traversal Queries, 5 Inconsistency Verification Predicates", fontsize=6.1, color=c_dark)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=c_white)
    plt.close()
    print(f"Refined pipeline diagram generated at: {output_path}")

if __name__ == "__main__":
    create_pipeline_diagram()
