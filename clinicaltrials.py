"""
clinicaltrials.py
-----------------
A helper that searches ClinicalTrials.gov and returns study summaries.

ClinicalTrials.gov is the U.S. registry of clinical trials (studies testing
treatments on people). Researchers check it to see what is being studied,
what is recruiting, and what results exist. It has a free API, no key needed.

Each result is returned in the SAME shape as the other sources:
    - title, abstract, url, source
"""

import requests

from pubmed import _make_keyword_query

# Version 2 of the ClinicalTrials.gov API returns clean JSON.
SEARCH_URL = "https://clinicaltrials.gov/api/v2/studies"
HEADERS = {"User-Agent": "MedEvidenceAssistant/1.0"}


def search_clinicaltrials(question, max_results=5):
    """Search ClinicalTrials.gov and return a list of study dictionaries."""
    term = _make_keyword_query(question) or question.strip()

    params = {
        "query.term": term,
        "pageSize": max_results,
        "format": "json",
    }
    response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    studies = response.json().get("studies", [])

    articles = []
    for study in studies:
        protocol = study.get("protocolSection", {})
        ident = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        desc = protocol.get("descriptionModule", {})

        nct_id = ident.get("nctId", "")
        title = ident.get("briefTitle", "Untitled study").strip()
        overall_status = status.get("overallStatus", "Unknown status")
        summary = desc.get("briefSummary", "").strip() or "No summary available."

        # Put the trial's status into the text so the AI can mention it.
        abstract = f"Trial status: {overall_status}. {summary}"
        url = f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "https://clinicaltrials.gov/"

        articles.append(
            {
                "title": title,
                "abstract": abstract,
                "url": url,
                "source": "ClinicalTrials.gov",
            }
        )

    return articles


# Quick manual test: run "python clinicaltrials.py"
if __name__ == "__main__":
    results = search_clinicaltrials("type 2 diabetes treatment", max_results=3)
    print(f"Found {len(results)} studies:\n")
    for r in results:
        print("-", r["title"])
        print(" ", r["url"])