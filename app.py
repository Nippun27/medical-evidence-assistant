"""
app.py
------
The main app. It does three things:
  1. Searches trusted medical sources (PubMed, Europe PMC, ClinicalTrials.gov).
  2. Feeds the results to the AI, which reads them and writes a cited answer (RAG).
  3. Shows everything in a simple web page (Streamlit).

To run it, open a terminal in this folder and type:
    streamlit run app.py
"""

import os

import streamlit as st
from dotenv import load_dotenv

# The three source helpers. Each one takes a question and returns a list of
# results in the same shape: title, abstract, url, source.
from pubmed import search_pubmed
from europepmc import search_europepmc
from clinicaltrials import search_clinicaltrials

# LlamaIndex does the "RAG" for us: it indexes the abstracts and lets the AI
# answer using only that text.
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# Load the API key from your .env file into the program.
load_dotenv()

# On Streamlit Cloud the key is stored in "Secrets" instead of a .env file.
# This copies it into place so the app works both locally and online.
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass  # No secrets file locally - that's fine, we use .env instead.


# Which sources are available, and the function that searches each one.
SOURCE_FUNCS = {
    "PubMed": search_pubmed,
    "Europe PMC": search_europepmc,
    "ClinicalTrials.gov": search_clinicaltrials,
}


# ---------------------------------------------------------------------------
# The AI setup. Runs once and is remembered so the app stays fast.
# ---------------------------------------------------------------------------
@st.cache_resource
def setup_ai():
    """Tell LlamaIndex which AI models to use (Google Gemini, free tier)."""
    Settings.llm = GoogleGenAI(model="gemini-2.5-flash", temperature=0)
    Settings.embed_model = GoogleGenAIEmbedding(model_name="gemini-embedding-001")


# ---------------------------------------------------------------------------
# The core work: search the chosen sources, then have the AI answer using them.
# ---------------------------------------------------------------------------
def research(question, per_source, sources):
    # 1. Gather results from every selected source.
    all_articles = []
    errors = []
    for name in sources:
        try:
            items = SOURCE_FUNCS[name](question, max_results=per_source)
        except Exception as error:
            errors.append(f"{name} could not be searched ({error}).")
            items = []
        for a in items:
            a["source"] = name  # Tag each result with where it came from.
            all_articles.append(a)

    if not all_articles:
        return None, [], errors

    # 2. Turn each result into a "Document" the AI can read. We include the
    #    source name so the AI knows where each piece of evidence came from.
    documents = [
        Document(
            text=f"Source: {a['source']}\nTitle: {a['title']}\n\n{a['abstract']}",
            metadata={"title": a["title"], "url": a["url"], "source": a["source"]},
        )
        for a in all_articles
    ]

    # 3. Build a searchable index and ask the question.
    #    The instruction keeps the AI honest: use only the sources given.
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine(similarity_top_k=len(all_articles))

    prompt = (
        f"Using only the medical sources provided, answer this question "
        f"clearly and concisely for a clinician: '{question}'. "
        f"Where useful, note which source supports a point. "
        f"If the sources do not contain the answer, say so. "
        f"Do not invent information."
    )
    answer = query_engine.query(prompt)
    return str(answer), all_articles, errors


# ---------------------------------------------------------------------------
# The web page.
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Medical Evidence Research Assistant")

st.title("Medical Evidence Research Assistant")
st.caption(
    "Searches PubMed, Europe PMC, and ClinicalTrials.gov, then summarizes the "
    "findings with citations. Research support only - not medical advice."
)

# Check the API key is present before doing anything.
if not os.getenv("GOOGLE_API_KEY") or "paste-your-key" in os.getenv("GOOGLE_API_KEY", ""):
    st.error(
        "No API key found. Copy .env.example to .env and paste your "
        "free Google AI Studio key into it, then restart the app."
    )
    st.stop()

setup_ai()

# The question box, a source picker, and a slider for how many results.
question = st.text_input(
    "Your medical question",
    placeholder="e.g. What is the first-line treatment for type 2 diabetes in adults?",
)
sources = st.multiselect(
    "Sources to search",
    options=list(SOURCE_FUNCS.keys()),
    default=list(SOURCE_FUNCS.keys()),
)
per_source = st.slider("How many results per source", 3, 10, 5)

if st.button("Search", type="primary") and question:
    if not sources:
        st.warning("Please select at least one source to search.")
        st.stop()

    with st.spinner("Searching the selected sources and reading the results..."):
        try:
            answer, articles, errors = research(question, per_source, sources)
        except Exception as error:
            st.error(f"Something went wrong: {error}")
            st.stop()

    # Let the user know if any single source failed (the rest still worked).
    for message in errors:
        st.caption(f"Note: {message}")

    if not articles:
        st.warning("No results found. Try rephrasing your question or picking more sources.")
    else:
        # Show the AI's answer.
        st.subheader("Summary")
        st.write(answer)

        # Show the sources it read, grouped with a source label.
        st.subheader("Sources")
        for i, a in enumerate(articles, start=1):
            st.markdown(f"**{i}. [{a['title']}]({a['url']})**  \n*{a['source']}*")

        st.info("Always verify against the original sources above before acting.")