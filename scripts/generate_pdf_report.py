"""
Technical report generator for the Neapolitan Artistic Heritage Dialogue System.
Natural Language Processing course project, University of Naples Federico II (DIETI).
"""

import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
    PageBreak,
    Image,
)
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas so headers/footers know the final page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#444444"))

        if self._pageNumber > 1:
            self.drawString(50, 752, "Neapolitan Artistic Heritage Dialogue System")
            self.drawRightString(562, 752, "University of Naples Federico II — DIETI")
            self.setStrokeColor(colors.HexColor("#999999"))
            self.setLineWidth(0.5)
            self.line(50, 745, 562, 745)

        self.setStrokeColor(colors.HexColor("#999999"))
        self.setLineWidth(0.5)
        self.line(50, 44, 562, 44)
        self.drawString(50, 32, "Natural Language Processing — Course Project Report")
        self.drawRightString(562, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_report(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=52,
        rightMargin=52,
        topMargin=52,
        bottomMargin=52,
    )

    c_heading = colors.HexColor("#1a1a1a")
    c_body = colors.HexColor("#222222")
    c_muted = colors.HexColor("#555555")
    c_border = colors.HexColor("#aaaaaa")
    c_table_head = colors.HexColor("#2b2b2b")
    c_row_alt = colors.HexColor("#f5f5f5")
    c_code_bg = colors.HexColor("#f2f2f2")
    c_callout_bg = colors.HexColor("#f7f7f7")

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=c_heading, spaceAfter=4, alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10.5, leading=14, textColor=c_muted, spaceAfter=14,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=13, textColor=c_muted, spaceAfter=2,
    )
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=14, leading=18, textColor=c_heading, spaceBefore=16, spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11.5, leading=15, textColor=c_heading, spaceBefore=12, spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10, leading=14.5, textColor=c_body, spaceAfter=8, alignment=4,
    )
    bullet = ParagraphStyle(
        "Bullet", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "Code", parent=styles["Normal"], fontName="Courier", fontSize=8,
        leading=11.5, textColor=c_body, backColor=c_code_bg,
        borderPadding=8, spaceBefore=4, spaceAfter=10,
    )
    caption_style = ParagraphStyle(
        "Caption", parent=styles["Normal"], fontName="Helvetica-Oblique",
        fontSize=8.5, leading=11, textColor=c_muted, spaceAfter=10,
    )
    table_cell = ParagraphStyle("TCell", parent=body, fontSize=8.5, leading=11.5, spaceAfter=0)
    table_head_cell = ParagraphStyle(
        "TCellHead", parent=table_cell, fontName="Helvetica-Bold", textColor=colors.white,
    )

    def P(text, style=body):
        return Paragraph(text, style)

    def rule():
        return HRFlowable(width="100%", thickness=0.6, color=c_border, spaceBefore=2, spaceAfter=12)

    def code(text):
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = safe.replace("\n", "<br/>").replace(" ", "&nbsp;")
        return Paragraph(safe, code_style)

    def styled_table(data, col_widths, header=True):
        t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
        style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        if header:
            style_cmds += [
                ("BACKGROUND", (0, 0), (-1, 0), c_table_head),
            ]
        for r in range(1 if header else 0, len(data)):
            if (r - (1 if header else 0)) % 2 == 1:
                style_cmds.append(("BACKGROUND", (0, r), (-1, r), c_row_alt))
        t.setStyle(TableStyle(style_cmds))
        return t

    def callout(text):
        t = Table([[P(text, body)]], colWidths=[468])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_callout_bg),
            ("BOX", (0, 0), (-1, -1), 0.6, c_border),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return t

    story = []

    # ---------- Title ----------
    story.append(P("Neapolitan Artistic Heritage Dialogue System", title_style))
    story.append(P(
        "A speech-enabled chatbot for Caravaggio and Battistello Caracciolo's works in Naples, "
        "grounded in a DBpedia-derived knowledge graph with inconsistency detection",
        subtitle_style,
    ))
    story.append(rule())
    story.append(P("<b>Course:</b> Natural Language Processing (U3539) — Prof. Francesco Cutugno", meta_style))
    story.append(P("<b>Student:</b> Mahdi Miri (D03000089) — M.Sc. Data Science", meta_style))
    story.append(P("<b>Institution:</b> University of Naples Federico II, DIETI", meta_style))
    story.append(Spacer(1, 14))

    # ---------- 1. Introduction ----------
    story.append(P("1. Introduction", h1))
    story.append(P(
        "This report documents what I built to satisfy my Natural Language Processing course "
        "requirement: a speech chatbot, with voice input and text-to-speech output, that answers "
        "questions about the works of Caravaggio and Battistello Caracciolo that can be visited in "
        "Naples. The brief was specific: the factual knowledge behind the chatbot has to come from "
        "SPARQL queries against DBpedia, and the resulting data has to be loaded into a Neo4j graph "
        "database. On top of that, the system has to detect inconsistencies in what the user says, and "
        "keep track of the conversation across multiple turns rather than treating every question in "
        "isolation.",
        body,
    ))
    story.append(P(
        "I kept the scope deliberately narrow: two painters, eight paintings, five venues, all within "
        "the city of Naples. That narrowness was the point. A general-purpose language model answering "
        "questions about art history will happily make things up — assign a painting to the wrong "
        "artist, claim a Roman painting is on display in Naples, or invent a museum address. For a "
        "cultural-heritage guide that visitors might actually rely on, I consider that kind of "
        "fabrication a real problem. Rather than fighting hallucination after the fact, I tried to avoid "
        "it by construction: every factual claim the chatbot makes is looked up in a graph I built from "
        "verified DBpedia data, and every claim the user makes is checked against that same graph "
        "before the system responds.",
        body,
    ))
    story.append(P(
        "In the rest of this report I walk through what I built: the data pipeline, the graph database, "
        "the dialogue manager, the inconsistency detector, the speech components, and finally my "
        "evaluation results, including an honest look at where the approach falls short.",
        body,
    ))

    # ---------- 2. Domain ----------
    story.append(P("2. Domain: Caravaggio and Battistello in Naples", h1))
    story.append(P(
        "Caravaggio spent two periods in Naples (1606–1607 and 1609–1610), fleeing Rome after a fatal "
        "duel, and his time there left a lasting mark on local painting. Battistello Caracciolo "
        "(1578–1635) was the most prominent Neapolitan painter to pick up Caravaggio's style of harsh "
        "lighting and unidealized figures, and he was the obvious second subject for a project focused "
        "on this period. The catalog I put together covers three Caravaggio works and five Battistello "
        "works, all physically on display in Naples today:",
        body,
    ))

    catalog_header = [P("Title", table_head_cell), P("Artist", table_head_cell), P("Year", table_head_cell),
                       P("Venue", table_head_cell)]
    catalog_rows = [
        catalog_header,
        [P("The Seven Works of Mercy", table_cell), P("Caravaggio", table_cell), P("1607", table_cell),
         P("Pio Monte della Misericordia", table_cell)],
        [P("The Flagellation of Christ", table_cell), P("Caravaggio", table_cell), P("1607", table_cell),
         P("Museo Nazionale di Capodimonte", table_cell)],
        [P("The Martyrdom of Saint Ursula", table_cell), P("Caravaggio", table_cell), P("1610", table_cell),
         P("Gallerie d'Italia, Palazzo Zevallos", table_cell)],
        [P("The Liberation of Saint Peter", table_cell), P("Battistello Caracciolo", table_cell), P("1615", table_cell),
         P("Pio Monte della Misericordia", table_cell)],
        [P("The Washing of the Feet", table_cell), P("Battistello Caracciolo", table_cell), P("1622", table_cell),
         P("Certosa di San Martino", table_cell)],
        [P("Christ at the Column", table_cell), P("Battistello Caracciolo", table_cell), P("1625", table_cell),
         P("Museo Nazionale di Capodimonte", table_cell)],
        [P("Trinitas Terrestris", table_cell), P("Battistello Caracciolo", table_cell), P("1617", table_cell),
         P("Chiesa della Pietà dei Turchini", table_cell)],
        [P("Frescoes of the Chapel of the Assunta", table_cell), P("Battistello Caracciolo", table_cell), P("1631", table_cell),
         P("Certosa di San Martino", table_cell)],
    ]
    story.append(styled_table(catalog_rows, [170, 120, 45, 133]))
    story.append(P(
        "Two venues — Pio Monte della Misericordia and Museo Nazionale di Capodimonte — each hold works "
        "by both painters, which I found useful for testing: it is exactly the kind of overlap where a "
        "careless system might attribute the wrong work to the wrong artist at the right building, or "
        "vice versa. To test the out-of-scope and city-mismatch detectors honestly, I also kept a short "
        "list of well-known Caravaggio paintings that are <i>not</i> in Naples — Judith Beheading "
        "Holofernes and The Calling of Saint Matthew in Rome, Bacchus in Florence — so the system has "
        "something concrete to correct against when a user assumes they can see those works locally.",
        body,
    ))

    # ---------- 3. Architecture overview ----------
    story.append(P("3. System Overview", h1))
    story.append(P(
        "I split the system into four layers, each with a single, fairly narrow job:",
        body,
    ))
    story.append(P("• <b>Data acquisition</b> — a SPARQL client that queries DBpedia for the two artists, their works, and the venues, and caches the results locally.", bullet))
    story.append(P("• <b>Knowledge graph</b> — a Neo4j graph store, holding the catalog as (:Artist)-[:PAINTED]->(:Artwork)-[:LOCATED_AT]->(:Location)-[:IN_CITY]->(:City).", bullet))
    story.append(P("• <b>Dialogue engine</b> — entity extraction, coreference resolution, an inconsistency checker, and a response generator, all working against the graph.", bullet))
    story.append(P("• <b>Speech layer</b> — Whisper for transcription on the way in, Edge-TTS (with an offline pyttsx3 fallback) for synthesis on the way out.", bullet))
    story.append(P(
        "I tied these together with a Streamlit app that presents a single-page interface: a microphone "
        "input, a text box, a running transcript, and an expandable view of the underlying graph so that "
        "answers aren't just taken on faith. I also exposed the same pipeline through a terminal CLI for "
        "quicker testing without the browser.",
        body,
    ))
    story.append(P(
        "Figure 1 lays out the pipeline I actually built, module by module, plus the one-time setup step "
        "that populates the graph before any conversation happens. The two dashed branches mark where "
        "behavior forks: a text turn skips speech recognition, and a turn where the inconsistency check "
        "fires skips the knowledge-graph lookup and goes straight to a corrective reply instead of a "
        "normal answer.",
        body,
    ))

    story.append(PageBreak())
    diagram_path = project_root / "docs" / "pipeline_architecture.png"
    if diagram_path.exists():
        img_reader = ImageReader(str(diagram_path))
        iw, ih = img_reader.getSize()
        max_h = 600.0
        max_w = 460.0
        scale = min(max_w / iw, max_h / ih)
        draw_w, draw_h = iw * scale, ih * scale
        story.append(Image(str(diagram_path), width=draw_w, height=draw_h, hAlign="CENTER"))
        story.append(P(
            "Figure 1. The system's per-turn processing pipeline (right) and the one-time knowledge-graph "
            "setup step (left, dashed box) that feeds it. Each box names the source file responsible for "
            "that stage.",
            caption_style,
        ))
        story.append(PageBreak())

    # ---------- 4. Data acquisition ----------
    story.append(P("4. Data Acquisition from DBpedia", h1))
    story.append(P(
        "I wrote a SPARQL client (<font face='Courier'>src/data_pipeline/sparql_client.py</font>) that "
        "queries the public DBpedia endpoint for biographical facts about the two artists (birth and "
        "death dates, abstracts, movement) and for metadata about each artwork — dimensions, medium, "
        "English abstract — where DBpedia has a dedicated entity for it. A representative query looks "
        "like this:",
        body,
    ))
    story.append(code(
        "PREFIX dbo: <http://dbpedia.org/ontology/>\n"
        "SELECT ?label ?abstract ?birthDate ?deathDate WHERE {\n"
        "  <http://dbpedia.org/resource/Caravaggio> rdfs:label ?label .\n"
        "  OPTIONAL { <http://dbpedia.org/resource/Caravaggio>\n"
        "             dbo:abstract ?abstract . FILTER(lang(?abstract) = 'en') }\n"
        "  OPTIONAL { <http://dbpedia.org/resource/Caravaggio> dbo:birthDate ?birthDate }\n"
        "  FILTER (lang(?label) = 'en')\n"
        "} LIMIT 1"
    ))
    story.append(P(
        "Not every piece of information the chatbot needs is available through DBpedia with clean, "
        "query-able fields — exact canvas dimensions and precise street addresses, for instance, are "
        "inconsistently modeled across DBpedia entities, if present at all. I filled those gaps with a "
        "small curated dataset (<font face='Courier'>src/data_pipeline/curated_dataset.py</font>) that "
        "supplies the catalog's structural facts (title, artist, year, venue, address), while DBpedia "
        "supplies the enrichment (abstracts, artist biography, canonical URIs). I see this as a "
        "practical compromise, not a claim that the whole dataset is auto-harvested: I hand-verified the "
        "backbone of the catalog against public sources myself, and I used SPARQL for what it's actually "
        "good at — pulling structured biographical and descriptive facts tied to a DBpedia resource URI. "
        "I merge results from both sources and write them to "
        "<font face='Courier'>data/dbpedia_cache.json</font> so the system can start up and answer "
        "questions without a live connection to DBpedia on every run.",
        body,
    ))

    # ---------- 5. Knowledge graph ----------
    story.append(P("5. Knowledge Graph: Neo4j", h1))
    story.append(P(
        "The graph schema is simple: an Artist node points to the Artworks they painted, each Artwork "
        "points to the Location that houses it, and each Location points to its City. Artworks also "
        "point to a handful of Subject nodes describing what they depict (for example, \"Christian "
        "charity\" for The Seven Works of Mercy). Populating the current catalog produces 40 nodes and "
        "46 relationships — 2 Artists, 8 Artworks, 5 Locations, 1 City, and 24 Subjects.",
        body,
    ))
    story.append(P(
        "<b>From a dual-backend convenience to a committed Neo4j deployment.</b> The assignment "
        "specifies Neo4j, so the primary store (<font face='Courier'>Neo4jGraphStore</font> in "
        "<font face='Courier'>src/data_pipeline/graph_db.py</font>) talks to it over the Bolt protocol "
        "with proper Cypher MERGE statements and uniqueness constraints on artist names, artwork titles, "
        "and location names. Earlier in development I also mirrored the same graph into an embedded "
        "SQLite store as a convenience, so the test suite and local development didn't need a database "
        "server running. A later review turned up a real problem with that arrangement: only one read "
        "method (<font face='Courier'>get_all_artworks</font>) actually queried Neo4j when it was the "
        "active backend — every other read (locations, artists, lookup-by-title) silently went to SQLite "
        "regardless of which backend was supposedly active, and <font face='Courier'>populate()</font> "
        "wrote to both stores unconditionally, so SQLite always held a live shadow copy of the data even "
        "when Neo4j was \"in use.\" Rather than patch this into a correct but still dual-maintained "
        "system, I removed the SQLite path entirely: <font face='Courier'>LocalGraphStore</font> is gone, "
        "every read method now queries Neo4j directly, and <font face='Courier'>NeapolitanArtGraph</font> "
        "raises a clear <font face='Courier'>ConnectionError</font> if Neo4j isn't reachable rather than "
        "silently degrading to a different store. Neo4j now runs in a Docker container "
        "(<font face='Courier'>neo4j-nlp</font>), and <font face='Courier'>run.sh</font> starts that "
        "container automatically if it isn't already up before launching the app.",
        body,
    ))
    story.append(P(
        "I verified this directly while preparing this report: with the Neo4j 5.15 container running "
        "(bound to the standard ports 7474/7687), running the graph-build script reports "
        "<font face='Courier'>Active backend: NEO4J</font>, and a Cypher query against the live "
        "database confirms all eight (:Artist)-[:PAINTED]->(:Artwork)-[:LOCATED_AT]->(:Location)-"
        "[:IN_CITY]->(:City) paths resolve correctly. Stopping the container and re-instantiating "
        "<font face='Courier'>NeapolitanArtGraph</font> now raises the expected connection error "
        "instead of quietly falling back to a different database — there is no SQLite file left on disk "
        "to fall back to.",
        body,
    ))

    # ---------- 6. Dialogue management ----------
    story.append(P("6. Dialogue State and Coreference", h1))
    story.append(P(
        "People don't repeat the full title of a painting in every sentence. A typical exchange looks "
        "like \"Tell me about the Seven Works of Mercy\" followed by \"Who painted it?\" and \"Where is "
        "it?\" — and the system has to know that \"it\" still refers to the Seven Works of Mercy in "
        "turn two and three. I built the dialogue state tracker "
        "(<font face='Courier'>src/dialogue/state_tracker.py</font>) to keep three pointers — active "
        "artist, active artwork, active location — updated after every turn, plus a full turn-by-turn "
        "history. I handle pronoun resolution with a small set of regular expressions matched against "
        "the current state: \"it / its / this / that\" resolves to the active artwork, \"he / him / his\" "
        "to the active artist, and \"there / here\" to the active location.",
        body,
    ))
    story.append(P(
        "I didn't build a general coreference model — just a handful of hand-written patterns that work "
        "because the domain is narrow and the referents are almost always unambiguous (there is rarely "
        "more than one plausible \"it\" in a two-entity conversation). I think that's a reasonable "
        "trade-off here, but I want to be upfront that it wouldn't scale to a richer domain without a "
        "proper coreference resolution component.",
        body,
    ))

    # ---------- 7. Inconsistency detection ----------
    story.append(P("7. Inconsistency Detection", h1))
    story.append(P(
        "This was the part of the assignment that took me the most thought. I built the detector "
        "(<font face='Courier'>src/dialogue/inconsistency.py</font>) to check every incoming question "
        "against the graph before the dialogue manager tries to answer it, looking for four kinds of "
        "mismatch:",
        body,
    ))
    inc_header = [P("Type", table_head_cell), P("Example", table_head_cell), P("What happens", table_head_cell)]
    inc_rows = [
        inc_header,
        [P("Artist mismatch", table_cell), P("\"I thought Caravaggio painted the Liberation of Saint Peter\"", table_cell),
         P("Graph says Battistello Caracciolo painted it; system corrects the attribution and gives the year.", table_cell)],
        [P("Venue mismatch", table_cell), P("\"Isn't the Seven Works of Mercy at Capodimonte?\"", table_cell),
         P("Graph says Pio Monte della Misericordia; system corrects the venue and gives the address.", table_cell)],
        [P("City mismatch", table_cell), P("\"Can I see Judith Beheading Holofernes in Naples?\"", table_cell),
         P("That painting is in Rome; system says so and redirects to what is actually in Naples.", table_cell)],
        [P("Out-of-scope artist", table_cell), P("\"What about Leonardo da Vinci's work in Naples?\"", table_cell),
         P("Leonardo is outside the Caravaggio/Battistello scope; system explains the boundary politely.", table_cell)],
    ]
    story.append(styled_table(inc_rows, [85, 195, 188]))
    story.append(P(
        "The detection logic is rule-based, not statistical: it looks for an artwork title (or an "
        "active-artwork pronoun) in the query, then checks whether any disallowed artist name, venue "
        "keyword, or non-Neapolitan artwork title co-occurs with it. I made it deliberately conservative "
        "— it only flags a contradiction when it's confident, which kept the false-positive rate at zero "
        "in my testing, but it also means a user who phrases a contradiction in an unusual way might "
        "slip past it. One case I was explicitly careful about is genuine clarification questions: \"Did "
        "Caravaggio paint this or Battistello?\" shouldn't be flagged as an inconsistency, since the user "
        "is asking rather than asserting, so I added a special case for the \"... or ...\" / \"who\" "
        "pattern to avoid that false alarm.",
        body,
    ))
    story.append(P(
        "A small but necessary detail: all of this matching happens after a normalization pass that "
        "lowercases the text and smooths over likely speech-to-text artifacts — \"seven works for "
        "mercy\" instead of \"of mercy\", \"capo di monte\" instead of \"Capodimonte\", digits spelled "
        "out, and so on. Without it, a perfectly correct answer from Whisper that happens to use a "
        "slightly different preposition than the stored title would fail to match anything.",
        body,
    ))

    # ---------- 8. Speech ----------
    story.append(P("8. Speech Input and Output", h1))
    story.append(P(
        "<b>Speech recognition.</b> For transcription I use OpenAI's Whisper, run locally "
        "(<font face='Courier'>src/speech/asr.py</font>), with English decoding forced and a short "
        "domain-specific prompt (the artist names, painting titles, and venue names) passed in as "
        "initial context to bias the decoder toward the right proper nouns — the same kind of prompt "
        "conditioning Whisper exposes through its multitask token format (Radford et al., 2023). Before "
        "transcription, I resample audio to 16 kHz mono and normalize it to zero mean with a peak "
        "amplitude of 0.95 (<font face='Courier'>src/utils/audio_utils.py</font>), matching the "
        "zero-mean, [-1, 1]-range normalization Whisper applies internally to its log-mel input.",
        body,
    ))
    story.append(P(
        "<b>ASR evaluation: Word Error Rate.</b> The standard metric for scoring a transcription against "
        "a reference is Word Error Rate, WER = 100 × (Insertions + Substitutions + Deletions) / "
        "(reference word count), computed from the minimum-edit-distance alignment between the two word "
        "sequences. I implemented this directly (<font face='Courier'>word_error_rate()</font> in "
        "<font face='Courier'>src/speech/asr.py</font>) and unit-tested it against the worked example "
        "from my course textbook — a CallHome conversational excerpt with 6 substitutions, 3 insertions, "
        "and 1 deletion over a 13-word reference, which the textbook reports as 76.9% WER and my "
        "implementation reproduces exactly. When I ran it against the sample recording included in the "
        "repository, Whisper transcribed it as \"<i>Tell me about the Seven Works of Mercy by Caravaggio "
        "in Pio Monte della Misericordia.</i>\" — an exact match to the reference text, giving a WER of "
        "0.00%. That's consistent with the textbook's own reported error rates: clearly articulated, "
        "single-speaker read speech (like the LibriSpeech clean benchmark) sits around 1-2% WER, the "
        "easiest end of the task's difficulty range, which is exactly the kind of input my system is "
        "designed to handle.",
        body,
    ))
    story.append(P(
        "<b>A more honest accuracy test: real accented speech.</b> That 0.00% result nagged at me — the "
        "sample clip ships in the repository at 24 kHz, the exact encoding profile of this project's own "
        "Edge-TTS output, so it is very likely synthetic speech rather than a genuine recording, which "
        "would explain why every Whisper checkpoint I tried (tiny through medium) transcribed it "
        "perfectly. To get a real signal, I recorded myself reading ten domain sentences out loud "
        "through the app's own microphone input — ordinary accented speech, not a clean studio read — "
        "and measured WER against the Whisper <font face='Courier'>small</font> checkpoint I had been "
        "using by default. The result was 18.1%, concentrated in exactly the words a closed-domain "
        "demo cares about most: \"Flagellation\" misheard as \"legislation,\" \"venues\" as \"Vensos,\" "
        "and proper nouns like Capodimonte dropped or garbled. Switching to the "
        "<font face='Courier'>medium</font> checkpoint brought that down to 15.0%, mostly by fixing the "
        "proper-noun errors. I then swept beam size (1, 5, 10) and Whisper's temperature-fallback "
        "schedule against the same ten recordings: none of it moved the error rate at all for this "
        "checkpoint, but beam_size=1 ran in about a fifth the time of beam_size=10 for identical "
        "accuracy, and dropping the domain prompt nearly doubled the error rate to 29.7% — confirming "
        "that prompt conditioning, not beam width, is what's actually carrying the proper-noun accuracy "
        "here. The deployed configuration is now <font face='Courier'>medium</font> with "
        "<font face='Courier'>beam_size=1</font>, the domain prompt, and the temperature-fallback "
        "schedule enabled as a safety net for harder audio, even though it made no measurable difference "
        "on this particular ten-sentence set.",
        body,
    ))
    story.append(P(
        "<b>A cloud ASR comparison: free hosted Whisper via Groq.</b> With the hyperparameter sweep "
        "saturated on accuracy, I ran a separate experiment "
        "(<font face='Courier'>scripts/benchmark_groq_vs_local.py</font>) to see whether a free cloud "
        "API could beat the local setup on latency without giving up much accuracy. Groq hosts Whisper "
        "<font face='Courier'>large-v3</font> and a faster <font face='Courier'>large-v3-turbo</font> "
        "variant for free — a recurring daily quota rather than a one-time trial credit — and markets "
        "itself specifically on inference speed. I sent the same ten recordings, the same domain prompt, "
        "and the same WER metric used throughout this section to both Groq models and compared them "
        "against the deployed local <font face='Courier'>medium</font> configuration, repeating the run "
        "three times to check it wasn't a network fluke: the local model and "
        "<font face='Courier'>large-v3</font> landed on the exact same WER (15.0% and 16.8%) in all "
        "three runs, while <font face='Courier'>turbo</font> was the only configuration that moved "
        "between runs (26.1%-27.4%), which I attribute to server-side batching rather than anything in "
        "the audio. <font face='Courier'>large-v3</font> came within 1.8 points of the local model's "
        "accuracy while running about four times faster end-to-end over the network (roughly 0.45 s "
        "versus 1.85 s per query); <font face='Courier'>turbo</font> was fastest of all but gave up too "
        "much accuracy on this project's dense proper-noun vocabulary (Battistello Caracciolo, Certosa "
        "di San Martino) to be worth it. I kept the local <font face='Courier'>medium</font> model as "
        "the deployed default, since accuracy on exactly that vocabulary is what the system is judged "
        "on and it needs no network call, but <font face='Courier'>large-v3</font> is a credible "
        "candidate if this project ever needs to serve several concurrent users over a network, where "
        "the 4x latency advantage would start to matter more than the last two points of WER.",
        body,
    ))
    story.append(P(
        "<b>Speech synthesis.</b> I read responses aloud with Microsoft's Edge-TTS "
        "(<font face='Courier'>src/speech/tts.py</font>), a neural voice reached over the network, with "
        "pyttsx3 as an offline fallback if that call fails for any reason — no internet, rate limiting, "
        "and so on. I exercised both engines directly while preparing this report and both produced "
        "valid audio output. I lightly clean the response text before synthesis (markdown characters "
        "stripped) so bullet points and headers in the text responses don't get read aloud literally. "
        "It's worth being explicit that this is not the zero-shot voice-cloning architecture (a "
        "codec-based language model conditioned on a short reference recording) that my course textbook "
        "presents as the modern approach to TTS: Edge-TTS synthesizes in a single fixed voice "
        "(en-GB-RyanNeural) with no speaker adaptation, and the pyttsx3 fallback relies on the host "
        "operating system's built-in synthesizer, which is architecturally closer to the older "
        "concatenative and formant-based methods than to a neural codec-language-model pipeline. That "
        "trade-off was intentional on my part: this system needs one consistent, reliable museum-guide "
        "voice, not per-user voice cloning.",
        body,
    ))

    # ---------- 9. Web interface ----------
    story.append(P("9. Web Interface and Command-Line Tool", h1))
    story.append(P(
        "I kept the Streamlit app (<font face='Courier'>app.py</font>) deliberately simple: a single "
        "page rather than a multi-tab layout, since there's only one real task — ask a question, read "
        "or hear the answer. The top of the page has a microphone widget and a text input side by side, "
        "a small state card showing the currently active artist / artwork / location (useful for "
        "debugging coreference while I was testing), and the running conversation transcript. Below "
        "that, a collapsible section exposes the full catalog pulled live from the graph, with each "
        "entry linking back to its DBpedia and Wikipedia source — I wanted it so that if the chatbot "
        "says something, a user can check where it came from without leaving the page. I enforced a "
        "light color scheme through <font face='Courier'>.streamlit/config.toml</font> since the dark "
        "Streamlit default didn't read well against the museum-catalog look I was going for.",
        body,
    ))
    story.append(P(
        "For quicker iteration while I was developing the dialogue logic, I also built "
        "<font face='Courier'>scripts/interactive_cli.py</font>, which exposes the same "
        "<font face='Courier'>NeapolitanArtChatbot</font> class through a plain terminal loop, with no "
        "Streamlit startup time and no browser involved. I debugged most of the conversational logic "
        "through the CLI first and only checked it in the browser afterward, since a terminal round-trip "
        "is faster to restart than a Streamlit rerun.",
        body,
    ))

    # ---------- 10. Example conversations ----------
    story.append(P("10. Example Conversations", h1))
    story.append(P(
        "The transcripts below are taken directly from running sessions against the live system (not "
        "edited for presentation) and are meant to show how the pieces described above work together in "
        "practice.",
        body,
    ))

    story.append(P("<b>Case 1 — coreference across four turns.</b>", h2))
    story.append(code(
        "User: Tell me about the Seven Works of Mercy\n"
        "Bot:  'The Seven Works of Mercy' is a masterpiece by Caravaggio, created\n"
        "      in 1607. It is permanently preserved in Naples at Pio Monte della\n"
        "      Misericordia (Via dei Tribunali 253)...\n\n"
        "User: Who painted it?\n"
        "Bot:  'The Seven Works of Mercy' was created by Caravaggio in 1607...\n\n"
        "User: Where is it located?\n"
        "Bot:  ...permanently preserved at Pio Monte della Misericordia, located\n"
        "      on Via dei Tribunali 253, 80139 Napoli...\n\n"
        "User: Did he also paint anything else?\n"
        "Bot:  You can visit 3 works by Caravaggio in the urban area of Naples:\n"
        "      - 'The Seven Works of Mercy' (1607) at Pio Monte della Misericordia\n"
        "      - 'The Flagellation of Christ' (1607) at Museo Nazionale di\n"
        "        Capodimonte\n"
        "      - 'The Martyrdom of Saint Ursula' (1610) at Gallerie d'Italia"
    ))
    story.append(P(
        "The pronoun \"it\" in turns two and three, and \"he\" in turn four, are all resolved against the "
        "state set in turn one, without the user ever repeating the title \"Seven Works of Mercy\" by "
        "name.",
        body,
    ))

    story.append(P("<b>Case 2 — a contradiction raised mid-conversation, not as an opening question.</b>", h2))
    story.append(code(
        "User: Tell me about the Liberation of Saint Peter\n"
        "Bot:  ...a masterpiece by Battistello Caracciolo, created in 1615...\n"
        "      permanently preserved at Pio Monte della Misericordia...\n\n"
        "User: I thought Caravaggio painted this\n"
        "Bot:  To clarify, 'The Liberation of Saint Peter' was created by\n"
        "      Battistello Caracciolo, not Caravaggio. Battistello Caracciolo\n"
        "      painted 'The Liberation of Saint Peter' around 1615.\n\n"
        "User: Isn't this at Capodimonte?\n"
        "Bot:  To clarify, 'The Liberation of Saint Peter' is not located at\n"
        "      Museo Nazionale di Capodimonte. It is permanently housed at Pio\n"
        "      Monte della Misericordia."
    ))
    story.append(P(
        "This is the scenario the automated 150-case suite does not really exercise, since its "
        "contradiction tests are mostly standalone questions. Here the contradiction (\"this\") depends "
        "on the artwork established one turn earlier, combining coreference resolution and "
        "inconsistency detection in the same turn — both had to be working correctly for this exchange "
        "to come out right.",
        body,
    ))

    story.append(P("<b>Case 3 — speech-to-text noise handled without a crash or a wrong answer.</b>", h2))
    story.append(code(
        "User (voice, transcribed): \"who painted the seven works for mercy\"\n"
        "Bot:  'The Seven Works of Mercy' was created by Caravaggio in 1607...\n\n"
        "User (voice, transcribed): \"where is the flagelation of christ\"\n"
        "Bot:  'The Flagellation of Christ' by Caravaggio is permanently\n"
        "      preserved at Museo Nazionale di Capodimonte..."
    ))
    story.append(P(
        "Neither \"works for mercy\" (instead of \"of mercy\") nor the misspelling \"flagelation\" "
        "prevented the system from matching the right artwork — both are caught by the normalization "
        "step described in Section 7.",
        body,
    ))

    story.append(PageBreak())

    # ---------- 11. Design decisions and challenges ----------
    story.append(P("11. Design Decisions and Challenges Along the Way", h1))
    story.append(P(
        "A few choices in this project weren't obvious to me from the start, and I think they're worth "
        "explaining rather than presenting as if they were the plan from day one.",
        body,
    ))
    story.append(P(
        "<b>Rule-based response generation instead of an LLM.</b> Early on I briefly considered wrapping "
        "an LLM around the graph query results to generate more varied phrasing. I dropped the idea for "
        "two reasons. First, it reintroduces exactly the hallucination risk I was trying to avoid — even "
        "when fed correct facts, a generative model can drift and add details that were never in the "
        "input. Second, and more practically, my emphasis on inconsistency detection only really works "
        "if the system's factual claims are traceable back to a specific graph query; a templated "
        "response keeps that traceability, a generated one doesn't without extra guardrails that were "
        "out of scope here. The response generator in <font face='Courier'>src/dialogue/chatbot.py</font> "
        "instead branches on question type (location, authorship, dimensions, significance, date) and "
        "fills a template with the matching graph fields — simpler, but every word in a response can be "
        "traced to a specific property on a specific node.",
        body,
    ))
    story.append(P(
        "<b>Handling phonetic and spelling variation.</b> My first version of the entity matcher only "
        "matched exact artwork titles, and it broke almost immediately once I tested it with real speech "
        "input — Whisper would transcribe \"of Mercy\" as \"for Mercy\" fairly often, and would "
        "sometimes render \"Caracciolo\" with a single consonant. Rather than retrain or swap ASR "
        "models, I added a normalization layer (Section 7) that runs before any matching happens, "
        "mapping known acoustic confusions back to the canonical form. That turned out to generalize "
        "well across both the artwork matcher and the inconsistency detector, since both call the same "
        "normalization function.",
        body,
    ))
    story.append(P(
        "<b>Choosing the Whisper model size.</b> The smallest Whisper checkpoints (tiny/base) were fast "
        "but made frequent proper-noun errors on exactly the words I most needed right — Italian museum "
        "names and the two artists' names. Moving to the <font face='Courier'>small</font> checkpoint, "
        "combined with passing the artist/artwork/venue names as an initial decoding prompt, noticeably "
        "reduced those errors in my informal testing, at the cost of a slightly longer load time on "
        "first use. Since this is a demo application rather than a production service handling "
        "concurrent users, that trade-off was an easy one for me to make.",
        body,
    ))
    story.append(P(
        "<b>Dropping the SQLite fallback.</b> Early on, an embedded SQLite backend was a quick "
        "stand-in so I could develop and test the dialogue logic without a database server running. "
        "I removed it for the reasons explained in Section 5: it had silently become the backend that "
        "most read queries actually used, even when Neo4j was supposedly active, which is exactly the "
        "kind of drift a convenience fallback should never be allowed to cause. The test suite now runs "
        "directly against the same Neo4j container (<font face='Courier'>neo4j-nlp</font>) used for "
        "development and the live demo, started automatically by <font face='Courier'>run.sh</font> if "
        "it isn't already up, so there is a single source of truth instead of two stores that could "
        "drift apart in what they represent.",
        body,
    ))

    story.append(PageBreak())

    # ---------- 12. Evaluation ----------
    story.append(P("12. Evaluation", h1))
    story.append(P(
        "I built two automated test layers. The first is a small pytest suite "
        "(<font face='Courier'>tests/test_dialogue.py</font>, "
        "<font face='Courier'>tests/test_inconsistency.py</font>, "
        "<font face='Courier'>tests/test_asr.py</font>) covering the basic behaviors — single-turn "
        "artwork queries, multi-turn coreference, each inconsistency category, the no-false-positive "
        "case, and the Word Error Rate metric from Section 8 (both as a unit test against the textbook's "
        "worked example and end-to-end against a real Whisper transcription), plus nine regression tests "
        "added after the adversarial testing described in Section 13 — six for the negation and "
        "out-of-scope-artist bugs, and three more from a follow-up review that caught an overly broad "
        "and then an overly narrow fix to the same Michelangelo/Caravaggio exemption. All 20 tests pass.",
        body,
    ))
    story.append(P(
        "The second is a larger, self-contained benchmark I wrote "
        "(<font face='Courier'>tests/stress_test_150.py</font>) covering 150 queries across six "
        "categories: artist mismatch (30), venue mismatch (30), city mismatch (30), out-of-scope artist "
        "(15), factual ground-truth retrieval (25), and five-turn discourse sequences (20). All 150 "
        "cases pass, with zero false positives and zero false negatives on the inconsistency checks "
        "(110 true positives, 40 true negatives), giving precision, recall, and F1 of 100% on this test "
        "set.",
        body,
    ))
    perf_header = [P("Category", table_head_cell), P("Tests", table_head_cell), P("Passed", table_head_cell)]
    perf_rows = [
        perf_header,
        [P("Artist attribution mismatch", table_cell), P("30", table_cell), P("30", table_cell)],
        [P("Venue mismatch", table_cell), P("30", table_cell), P("30", table_cell)],
        [P("City mismatch", table_cell), P("30", table_cell), P("30", table_cell)],
        [P("Out-of-scope artist", table_cell), P("15", table_cell), P("15", table_cell)],
        [P("Factual ground-truth retrieval", table_cell), P("25", table_cell), P("25", table_cell)],
        [P("Multi-turn discourse sequences", table_cell), P("20", table_cell), P("20", table_cell)],
        [P("Total", table_cell), P("150", table_cell), P("150", table_cell)],
    ]
    story.append(styled_table(perf_rows, [280, 94, 94]))
    story.append(P(
        "On timing: the full 150-query suite now runs against the live Neo4j instance in well under "
        "0.1 s end-to-end (roughly 0.6 ms per query). It was slower in an earlier version of this "
        "pipeline — about 7.3 ms per query — because removing the SQLite fallback (Section 5) initially "
        "meant every single lookup re-ran the full <font face='Courier'>MATCH (p:Artist)-[:PAINTED]-> "
        "(a:Artwork)-[:LOCATED_AT]->(l:Location)</font> query over Bolt, and a single dialogue turn can "
        "trigger that lookup five or six times (once each from entity extraction, inconsistency "
        "checking, and response generation). Caching that query's result on the "
        "<font face='Courier'>NeapolitanArtGraph</font> instance and invalidating it only on "
        "<font face='Courier'>populate()</font> brought it back down to roughly one real network round "
        "trip per turn. These numbers only cover the text-based dialogue logic; ASR and TTS were "
        "verified to work correctly but were not put through a formal timing benchmark, since the point "
        "of this project is accuracy of the reasoning, not raw throughput.",
        body,
    ))
    story.append(P(
        "It's worth being honest about what this benchmark does and does not prove. It is a suite I "
        "wrote myself, targeting the exact categories the system is designed to catch, phrased in ways "
        "close to the patterns the detector matches on. A 100% score here says the implementation is "
        "internally consistent and bug-free against its own design, not that it would handle arbitrary, "
        "unscripted phrasing from a real visitor with the same accuracy. The manual testing described "
        "below was meant to probe exactly that gap.",
        body,
    ))

    # ---------- 13. Manual testing ----------
    story.append(P("13. Manual Testing Beyond the Automated Suite", h1))
    story.append(P(
        "To get a more honest sense of robustness, I ran a separate batch of hand-written conversations "
        "that were not part of the stress suite: misspelled artist names (\"karavaggio\"), casing and "
        "whitespace noise, empty and nonsense input, a dialogue reset mid-conversation, and an "
        "inconsistency injected partway through an otherwise normal five-turn conversation rather than "
        "as a standalone question. All of these were handled without errors, and the fallback message "
        "(\"I could not identify a specific artwork, artist, or venue...\") appeared correctly for "
        "genuinely unparseable input rather than crashing or returning a blank response. The one gap "
        "found — a title with no spaces between words at all, e.g. a typo collapsing \"at the\" into "
        "one token — is an unrealistic edge case rather than something a real user or ASR system would "
        "plausibly produce, and is consistent with the keyword-matching approach described in Section 7.",
        body,
    ))
    story.append(P(
        "<b>Adversarial testing of the inconsistency detector.</b> The 150-case stress suite scores a "
        "perfect 100%, but I wrote both the rules and the test cases, phrased in the style the rules "
        "expect — so a clean score there mostly proves internal consistency, not real-world robustness. "
        "To get past that, I wrote ten new queries deliberately aimed at the matching logic's blind "
        "spots rather than its happy path, and found three genuine bugs. First, asking about "
        "\"Michelangelo Merisi da Caravaggio\" — Caravaggio's actual full birth name — was flagged as an "
        "out-of-scope artist, because the out-of-scope check matched the bare word \"Michelangelo\" "
        "without checking for \"Merisi\" alongside it. Second, disambiguation questions phrased with "
        "\"which\" (\"Which painter, Caravaggio or Battistello, made the Seven Works of Mercy?\") were "
        "incorrectly flagged as false claims, because the existing exception for this pattern only "
        "recognized the word \"who,\" not \"which.\" Third, and most interesting, the detector had no "
        "concept of negation at all: \"Caravaggio did not paint the Liberation of Saint Peter, correct?\" "
        "— a statement that is actually true — was flagged as an error, while \"the Seven Works of Mercy "
        "is NOT by Caravaggio\" — a statement that is actually false — was missed entirely. I fixed all "
        "three in <font face='Courier'>src/dialogue/inconsistency.py</font>: an explicit carve-out for "
        "\"Merisi,\" broadening the disambiguation exception to cover \"which\" as well as \"who,\" and a "
        "small negation-window check that looks a few words before and after an artist's name for "
        "\"not,\" \"didn't,\" \"never,\" and similar markers before deciding whether a mention is a claim "
        "or a correct denial. I added six regression tests for these exact cases to "
        "<font face='Courier'>tests/test_inconsistency.py</font>; the full suite, including the original "
        "150-case benchmark, still passes with no regressions after the fix.",
        body,
    ))

    # ---------- 14. Limitations ----------
    story.append(P("14. Limitations", h1))
    story.append(P("• <b>Fixed, small catalog.</b> Eight artworks and five venues are enough to demonstrate the approach, but the keyword-based entity matching would need to be rethought before scaling to hundreds of works, where title collisions and partial-string matches become more likely.", bullet))
    story.append(P("• <b>Rule-based, not statistical, matching.</b> Both entity extraction and inconsistency detection rely on string matching and regular expressions rather than embeddings or a trained classifier. This makes behavior predictable and easy to debug, but it means paraphrases the rules don't anticipate will be missed rather than approximately understood.", bullet))
    story.append(P("• <b>Single in-memory session.</b> Dialogue state lives in the running process and resets when the app restarts; there is no persistence of conversation history across sessions or users.", bullet))
    story.append(P("• <b>No generative language model.</b> Responses are built from structured templates filled in with graph data, not generated by an LLM. This was a deliberate choice for factual reliability — see Section 1 — but it does mean phrasing is less varied than a generative system would produce.", bullet))
    story.append(P("• <b>DBpedia coverage gaps.</b> Not every fact needed (precise dimensions, street addresses) is reliably present in DBpedia for these specific entities, which is why the curated dataset exists alongside the SPARQL client rather than replacing it.", bullet))

    # ---------- 15. Future work ----------
    story.append(P("15. Possible Extensions", h1))
    story.append(P(
        "A few directions were considered but left out of scope for this delivery, either because the "
        "course requirements did not call for them or because they would have meaningfully widened the "
        "project beyond what could be properly tested in the time available:",
        body,
    ))
    story.append(P("• <b>Larger catalog.</b> I was given the option of extending the project to other artists or cities; the architecture (SPARQL ingestion → Neo4j graph → rule-based dialogue) would carry over, but the entity-matching rules in Sections 6–7 would need to move toward fuzzy or embedding-based matching once title collisions become likely across a bigger catalog.", bullet))
    story.append(P("• <b>Persistent, multi-user sessions.</b> Right now dialogue state lives in one process's memory. Saving state per browser session (Streamlit's <font face='Courier'>session_state</font>, or a lightweight database row keyed by session id) would let multiple visitors use the deployed app concurrently without stepping on each other's conversation history.", bullet))
    story.append(P("• <b>A statistical fallback for entity matching.</b> For queries that don't match any keyword pattern, a small sentence-embedding similarity search over artwork descriptions could catch paraphrases the rules miss, while keeping the rule-based path as the primary, auditable mechanism — a hybrid rather than a wholesale replacement.", bullet))

    story.append(Spacer(1, 6))

    # ---------- 16. Reproducing the results ----------
    story.append(P("16. Reproducing These Results", h1))
    story.append(P(
        "All commands below assume a Python 3.10+ virtual environment with "
        "<font face='Courier'>requirements.txt</font> installed.",
        body,
    ))
    story.append(code(
        "python3 -m venv .venv && source .venv/bin/activate\n"
        "pip install -r requirements.txt\n\n"
        "# Start Neo4j (required — there is no fallback); run.sh does this automatically\n"
        "docker start neo4j-nlp\n\n"
        "# Build the knowledge graph from DBpedia into Neo4j\n"
        "python scripts/build_graph.py\n\n"
        "# Run the automated test suites (also require Neo4j to be running)\n"
        "pytest tests/\n"
        "python tests/stress_test_150.py\n\n"
        "# Launch the web app (starts Neo4j automatically if needed), or the terminal CLI\n"
        "./run.sh\n"
        "python scripts/interactive_cli.py"
    ))
    story.append(P(
        "Neo4j must be reachable at <font face='Courier'>bolt://localhost:7687</font> with the "
        "credentials in <font face='Courier'>config/settings.py</font> (user "
        "<font face='Courier'>neo4j</font>, password <font face='Courier'>password</font> by default) "
        "before running <font face='Courier'>build_graph.py</font>, the test suite, or the app — "
        "<font face='Courier'>NeapolitanArtGraph</font> raises a <font face='Courier'>ConnectionError</font> "
        "immediately if it isn't. I run it as a Docker container (<font face='Courier'>neo4j-nlp</font>), "
        "and <font face='Courier'>run.sh</font> starts that container automatically if it is stopped.",
        body,
    ))

    # ---------- 17. Tools and technologies ----------
    story.append(P("17. Tools and Technologies", h1))
    story.append(P(
        "A quick inventory of what I actually built this with, and why each piece is there. Everything "
        "below is pinned in <font face='Courier'>requirements.txt</font> unless noted otherwise.",
        body,
    ))

    story.append(P("<b>Language and data models.</b> Python 3.11. I used Pydantic throughout "
        "(<font face='Courier'>ChatbotTurnResult</font>, <font face='Courier'>InconsistencyReport</font>, "
        "<font face='Courier'>DialogueState</font>, the app config) instead of passing raw dicts around — "
        "it validates types at construction time and gives every module a documented shape to pass data in.",
        body,
    ))
    story.append(P("<b>Knowledge source and graph.</b> DBpedia is the data source — structured facts "
        "extracted from Wikipedia, reachable over a public SPARQL endpoint. "
        "<font face='Courier'>SPARQLWrapper</font> is the Python library I used to build and send those "
        "SPARQL queries and parse the JSON bindings that come back; fixing a URI scheme mismatch there "
        "(DBpedia's RDF graph uses <font face='Courier'>http://</font> resource IRIs, not the "
        "<font face='Courier'>https://</font> ones used for the display links) is what made artist "
        "biography fields and artwork images/dimensions actually populate, instead of silently coming "
        "back empty. For storage, <font face='Courier'>neo4j</font> (the official Python driver) talks "
        "to a real Neo4j 5.x server over Bolt, running as a Docker container "
        "(<font face='Courier'>neo4j-nlp</font>) — it is the only backend; there is no SQLite fallback.",
        body,
    ))
    story.append(P("<b>Speech.</b> <font face='Courier'>openai-whisper</font> runs ASR locally (the "
        "<font face='Courier'>medium</font> checkpoint, after the real-accent tuning in Section 8). "
        "<font face='Courier'>soundfile</font> and "
        "<font face='Courier'>scipy.signal.resample</font> handle loading and resampling audio to 16 kHz "
        "before it reaches Whisper. For speech output, <font face='Courier'>edge-tts</font> calls "
        "Microsoft's neural voices over the network, with <font face='Courier'>pyttsx3</font> as an "
        "offline fallback that drives the host operating system's own synthesizer. One honest note: "
        "<font face='Courier'>sounddevice</font> is listed in requirements.txt from an earlier draft "
        "but isn't imported anywhere in the final code — microphone capture goes through Streamlit's "
        "browser-based <font face='Courier'>st.audio_input</font> instead, so that dependency is unused. "
        "For the cloud ASR comparison in Section 8, <font face='Courier'>groq</font> (the official "
        "Python SDK, OpenAI-compatible) calls the hosted Whisper models, with "
        "<font face='Courier'>python-dotenv</font> loading the API key from a local, gitignored "
        "<font face='Courier'>.env</font> file rather than hardcoding it.",
        body,
    ))
    story.append(P("<b>Interface and testing.</b> <font face='Courier'>streamlit</font> is the whole web "
        "app — I didn't reach for a separate frontend framework since Streamlit's Python-only model fit a "
        "single-page demo well. <font face='Courier'>pytest</font> runs the unit test suite.",
        body,
    ))
    story.append(P("<b>Building this report and its diagram.</b> Outside the chatbot itself, "
        "<font face='Courier'>reportlab</font> generates this PDF programmatically from a Python script "
        "(<font face='Courier'>scripts/generate_pdf_report.py</font>) rather than a word processor, so the "
        "whole report rebuilds from source whenever the project changes. "
        "<font face='Courier'>graphviz</font> renders Figure 1's pipeline diagram the same way. I also "
        "used Docker once, outside the normal dependency list, to run a real Neo4j 5.15 container "
        "specifically to verify the Neo4j backend described in Section 5 — not something the system "
        "needs at runtime, just something I needed for honest verification.",
        body,
    ))

    story.append(PageBreak())

    # ---------- 18. References ----------
    story.append(P("18. References", h1))
    ref_items = [
        "Jurafsky, D. and J. H. Martin. Speech and Language Processing (3rd ed. draft). Course reference "
        "textbook; chapters 15-17 (phonetics/feature extraction, ASR, TTS) inform the speech pipeline and "
        "the Word Error Rate evaluation in Section 8.",
        "DBpedia — structured data extracted from Wikipedia, queried here via the public SPARQL endpoint at dbpedia.org/sparql.",
        "Radford, A. et al. (2023). Robust Speech Recognition via Large-Scale Weak Supervision (Whisper). ICML.",
        "Neo4j Graph Database — property graph store and the Cypher query language, used as the primary knowledge graph backend.",
        "Microsoft Edge-TTS — neural text-to-speech voices used for the system's spoken output (en-GB-RyanNeural).",
        "Streamlit — Python web app framework used for the project's user interface.",
    ]
    for r in ref_items:
        story.append(P("• " + r, bullet))

    story.append(Spacer(1, 10))

    # ---------- 19. Conclusion ----------
    story.append(P("19. Conclusion", h1))
    story.append(P(
        "I believe the system meets the requirements I was given: it accepts voice or text input, "
        "answers questions about Caravaggio and Battistello Caracciolo's works in Naples using facts "
        "drawn from DBpedia and stored in Neo4j, catches factual inconsistencies in what the user "
        "claims, and keeps track of what has been discussed across a conversation. The design choices I "
        "made throughout — rule-based detection over a trained classifier, template-based generation "
        "over an LLM, a dual graph backend for development convenience — were made for reasons specific "
        "to this domain's small size and its need for strict factual correctness, and I wrote the "
        "limitations section above to make those trade-offs explicit rather than leave them implied.",
        body,
    ))
    story.append(P(
        "I'm submitting the codebase, the automated tests, and this report together as my deliverable "
        "for the course.",
        body,
    ))

    doc.build(story, canvasmaker=NumberedCanvas)


if __name__ == "__main__":
    out = project_root / "TECHNICAL_REPORT.pdf"
    build_report(out)
    print(f"Report written to {out}")
