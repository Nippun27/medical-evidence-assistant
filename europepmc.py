"""
europepmc.py
------------
A helper that searches Europe PMC and returns article abstracts.

Europe PMC is a free database run by the European Bioinformatics Institute.
It is similar to PubMed but broader - it also includes preprints, guidelines,
and reports (including many WHO and agency documents). No API key is needed.

Each result is returned in the SAME shape as the other sources so the app can
mix them together:
    - title, abstract, url, source
"""

import requests

# We reuse the keyword cleaner from pubmed.py so natural-language questions
# ("What is the treatment for...?") become clean search terms.
from pubmed import _make_keyword_query

SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
HEADERS = {"User-Agent": "MedEvidenceAssistant/1.0"}


def search_europepmc(question, max_results=5):
    """Search Europe PMC and return a list of article dictionaries."""
    term = _make_keyword_query(question) or question.strip()

    params = {
        "query": term,
        "format": "json",
        "pageSize": max_results,
        "resultType": "core",  # "core" includes the abstract text
        "sort": "relevance",
    }
    response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    results = response.json().get("resultList", {}).get("result", [])

    articles = []
    for item in results:
        title = item.get("title", "Untitled").strip()
        abstract = item.get("abstractText", "").strip() or "No abstract available."

        # Build the best available link to the article.
        doi = item.get("doi")
        source_db = item.get("source", "")
        item_id = item.get("id", "")
        if doi:
            url = f"https://doi.org/{doi}"
        elif source_db and item_id:
            url = f"https://europepmc.org/article/{source_db}/{item_id}"
        else:
            url = "https://europepmc.org/"

        articles.append(
            {
                "title": title,
                "abstract": abstract,
                "url": url,
                "source": "Europe PMC",
            }
        )

    return articles


# Quick manual test: run "python europepmc.py"
if __name__ == "__main__":
    results = search_europepmc("What is the first-line treatment for type 2 diabetes?", max_results=3)
    print(f"Found {len(results)} articles:\n")
    for r in results:
        print("-", r["title"])
        print(" ", r["url"])