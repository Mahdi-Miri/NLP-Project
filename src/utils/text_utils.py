import re
import html


def clean_wiki_markup(raw_text: str) -> str:
    """
    Strips MediaWiki markup, HTML tags, and citations to produce clean text.
    """
    if not raw_text:
        return ""

    text = html.unescape(raw_text)

    # Remove ref tags and comments
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/>", "", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)

    # Normalize internal wiki links: [[Target|Displayed]] -> Displayed, [[Target]] -> Target
    text = re.sub(r"\[\[([^|\]]+\|)?([^\]]+)\]\]", r"\2", text)

    # Remove external links: [http://... Displayed] -> Displayed
    text = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\]", "", text)

    # Remove bold/italic markup
    text = re.sub(r"'{2,5}", "", text)

    # Remove templates like {{...}}
    text = re.sub(r"\{\{[^}]+\}\}", "", text)

    # Remove leading quote formatting characters (*, ", ', :, #)
    text = re.sub(r"^[\s*#:\-\"\']+", "", text)
    text = re.sub(r"[\s\"\']+$", "", text)

    # Collapse multiple spaces into one
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_query(query: str) -> str:
    """
    Normalizes user input for text matching and search queries.
    """
    if not query:
        return ""
    # Strip punctuation and lower for robust tokenization
    cleaned = re.sub(r"[^\w\s]", " ", query.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_highlighted_match(full_quote: str, prefix_query: str) -> dict:
    """
    Highlights the autocompleted portion of the quote given the user prefix.
    """
    query_norm = normalize_query(prefix_query)
    quote_norm = normalize_query(full_quote)

    match_idx = quote_norm.find(query_norm) if query_norm else -1

    return {
        "full_text": full_quote,
        "matched": match_idx != -1,
        "completion": full_quote[match_idx + len(prefix_query):].strip() if match_idx != -1 else full_quote
    }
