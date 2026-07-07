"""
pubmed.py
---------
A small helper that searches PubMed and returns article abstracts.

PubMed is a free database of medical research run by the U.S. National
Institutes of Health. We use their free "E-utilities" web service.
No API key is required for light use.

You normally don't need to edit this file.
"""

import requests

# The two PubMed web addresses we use:
SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# NCBI asks that requests identify themselves. This makes the service more
# reliable and avoids being treated as an anonymous bot.
CONTACT = {"tool": "MedEvidenceAssistant", "email": "student@example.com"}
HEADERS = {"User-Agent": "MedEvidenceAssistant/1.0"}

# Common English filler words. PubMed joins every search word with AND, so a
# natural-language question like "What is the treatment for X in adults?" fails
# because it also requires "what", "is", "the", "in", etc. Removing these turns
# the question into clean keywords that actually match articles.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "being", "been",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "do", "does", "did", "can", "could", "should", "would", "will", "shall",
    "of", "for", "to", "in", "on", "at", "by", "with", "about", "as", "into",
    "and", "or", "but", "if", "then", "than", "that", "this", "these", "those",
    "i", "you", "we", "they", "it", "my", "our", "your", "there", "here",
    "best", "good", "any", "some", "most", "more", "please", "tell", "me",
}


def _make_keyword_query(question):
    """Turn a plain-language question into PubMed-friendly keywords."""
    import re

    # Lowercase, drop punctuation, split into words.
    words = re.findall(r"[a-zA-Z0-9\-]+", question.lower())
    # Keep only meaningful words (drop filler like "what", "is", "the").
    keywords = [w for w in words if w not in STOPWORDS]
    return " ".join(keywords)


def _get_ids(term, max_results):
    """Ask PubMed for article IDs matching a search term. Returns a list."""
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
        **CONTACT,
    }
    response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json().get("esearchresult", {}).get("idlist", [])


def search_pubmed(question, max_results=5):
    """
    Search PubMed for a question and return a list of articles.

    Each article is a dictionary with:
        - title:    the article title
        - abstract: the summary text
        - pmid:     the PubMed ID number
        - url:      a link you can click to read it

    max_results = how many articles to fetch (keep it small, e.g. 5).
    """
    # Step 1: find matching article IDs. We try up to two searches:
    #   (a) the keyword version of the question (filler words removed), which
    #       works for natural-language questions like "What is the ...?"
    #   (b) if that finds nothing, the raw question as a fallback.
    keyword_query = _make_keyword_query(question)
    raw_query = question.strip().rstrip("?").strip()

    id_list = []
    for term in (keyword_query, raw_query):
        if not term:
            continue
        id_list = _get_ids(term, max_results)
        if id_list:
            break  # Found results, no need to try the next search.

    if not id_list:
        return []  # No matching articles found.

    # Step 2: fetch the details (including abstracts) for those IDs.
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml",
        **CONTACT,
    }
    fetch_response = requests.get(
        FETCH_URL, params=fetch_params, headers=HEADERS, timeout=30
    )
    fetch_response.raise_for_status()

    # Step 3: pull the useful bits out of the response.
    return _parse_articles(fetch_response.text)


def _parse_articles(xml_text):
    """Turn PubMed's XML response into a simple list of dictionaries."""
    import xml.etree.ElementTree as ET

    articles = []
    root = ET.fromstring(xml_text)

    for article in root.findall(".//PubmedArticle"):
        # Title
        title_el = article.find(".//ArticleTitle")
        title = title_el.text if title_el is not None and title_el.text else "Untitled"

        # Abstract (may come in several pieces - join them together)
        abstract_pieces = [
            piece.text
            for piece in article.findall(".//AbstractText")
            if piece.text
        ]
        abstract = " ".join(abstract_pieces).strip()
        if not abstract:
            abstract = "No abstract available."

        # PubMed ID and link
        pmid_el = article.find(".//PMID")
        pmid = pmid_el.text if pmid_el is not None else ""
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

        articles.append(
            {
                "title": title,
                "abstract": abstract,
                "pmid": pmid,
                "url": url,
            }
        )

    return articles


# Quick manual test: run "python pubmed.py" to check it works.
if __name__ == "__main__":
    question = "What is the first-line treatment for type 2 diabetes in adults?"
    print("Question:", question)
    print("Keyword search sent to PubMed:", _make_keyword_query(question), "\n")
    results = search_pubmed(question, max_results=3)
    print(f"Found {len(results)} articles:\n")
    for r in results:
        print("-", r["title"])
        print(" ", r["url"])