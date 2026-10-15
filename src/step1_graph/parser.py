import bz2
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List

from src.utils.text_utils import clean_wiki_markup


class WikiquoteDumpParser:
    """
    Streaming parser for Wikimedia XML dumps (both raw .xml and compressed .xml.bz2).
    Extracts structured quote records: quote text, author/speaker, source work, and categories.
    """

    def __init__(self, dump_path: Optional[str] = None):
        self.dump_path = Path(dump_path) if dump_path else None

    @staticmethod
    def _is_quote_section(header: str) -> bool:
        """Checks if a section header indicates genuine quotes from the subject."""
        h = header.lower().strip()
        # Exclude sections that are quotes about the person or misattributed
        if "quotes about" in h or "misattributed" in h or "external links" in h or "see also" in h:
            return False
        return "quote" in h or len(h) < 40

    @staticmethod
    def _extract_categories(text: str) -> List[str]:
        """Extracts category names from MediaWiki text."""
        categories = []
        for match in re.finditer(r"\[\[Category:([^\]|]+)(?:\|[^\]]+)?\]\]", text, flags=re.IGNORECASE):
            cat = match.group(1).strip()
            if cat and not cat.startswith("Wikiquote"):
                categories.append(cat)
        return categories

    def parse_page_content(self, title: str, text: str) -> List[Dict[str, Any]]:
        """
        Parses the text of a single Wikiquote page and yields quote entries.
        """
        # Skip special / meta pages
        if any(title.startswith(prefix) for prefix in ("MediaWiki:", "Template:", "Help:", "Category:", "File:")):
            return []

        categories = self._extract_categories(text)
        results = []

        current_work = None
        current_section = "Quotes"
        lines = text.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Detect section headers (e.g., == Section == or === Work Name ===)
            if line.startswith("="):
                header_match = re.match(r"^(=+)\s*(.*?)\s*\1$", line)
                if header_match:
                    level = len(header_match.group(1))
                    header_title = header_match.group(2).strip()
                    if level == 2:
                        current_section = header_title
                        current_work = None
                    elif level >= 3:
                        current_work = header_title
                i += 1
                continue

            # Skip sections not containing quotes by the subject
            if not self._is_quote_section(current_section):
                i += 1
                continue

            # Detect primary quote bullet point
            if line.startswith("*") and not line.startswith("**"):
                quote_candidate = line.lstrip("* ").strip()
                cleaned_quote = clean_wiki_markup(quote_candidate)

                # Collect citation / source from immediately following indented bullet lines
                citation_source = current_work or title
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith("**"):
                    sub_line = clean_wiki_markup(lines[j].strip().lstrip("* "))
                    if sub_line:
                        citation_source = f"{citation_source} - {sub_line}"
                    j += 1

                # Discard too short or empty quotes
                if len(cleaned_quote) >= 20 and not cleaned_quote.startswith("=="):
                    results.append({
                        "quote": cleaned_quote,
                        "author": title,
                        "source": citation_source,
                        "work": current_work or "General",
                        "categories": categories[:5],
                    })

                i = j - 1

            i += 1

        return results

    def stream_quotes(self, max_quotes: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Memory-efficient generator that streams quotes directly from the XML dump.
        """
        if not self.dump_path or not self.dump_path.exists():
            raise FileNotFoundError(f"Dump file not found at: {self.dump_path}")

        # Open either compressed bz2 or plain xml
        is_bz2 = str(self.dump_path).endswith(".bz2")
        file_obj = bz2.BZ2File(self.dump_path, "rb") if is_bz2 else open(self.dump_path, "rb")

        count = 0
        try:
            # iterparse allows streaming huge XML files without loading all DOM into RAM
            context = ET.iterparse(file_obj, events=("end",))
            title = ""
            text = ""

            for _, elem in context:
                tag = elem.tag.split("}")[-1]  # Strip XML namespace if present

                if tag == "title":
                    title = elem.text or ""
                elif tag == "text":
                    text = elem.text or ""
                elif tag == "page":
                    if title and text:
                        quotes = self.parse_page_content(title, text)
                        for q in quotes:
                            yield q
                            count += 1
                            if max_quotes and count >= max_quotes:
                                return
                    # Clear processed elements to conserve memory
                    elem.clear()

        finally:
            file_obj.close()
