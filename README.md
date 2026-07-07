# Medical Evidence Research Assistant (Phase 2 — Simple)

A small web app that searches **PubMed** for a medical question, then uses AI (RAG)
to read the results and write a **cited summary**. Built to be as simple as possible.

What it does:
1. You type a medical question.
2. It searches PubMed (a free, trusted database of medical research).
3. It reads the abstracts and writes an answer that only uses those sources.
4. It shows the answer with clickable citations.

> This is a research helper, **not medical advice**.

---

## What you need first (one time)

1. **Python 3.10 or newer** — download from https://www.python.org/downloads/
   (During install on Windows, tick the box **"Add Python to PATH"**.)
2. **An OpenAI API key** — get one at https://platform.openai.com/api-keys
   (This is what powers the AI. It costs a small amount per use.)

---

## Setup (copy–paste these commands)

Open a terminal **in this folder**, then run the commands for your system.

### 1. Create a private space for the app's tools
```
python -m venv venv
```

Turn it on:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 2. Install everything the app needs
```
pip install -r requirements.txt
```

### 3. Add your API key
- Make a copy of the file `.env.example` and name the copy `.env`
- Open `.env` and paste your key after `OPENAI_API_KEY=`

### 4. Start the app
```
streamlit run app.py
```

A web page opens in your browser. Type a question and press **Search**.

---

## Try these example questions
- What is the first-line treatment for type 2 diabetes in adults?
- Does vitamin D reduce the risk of respiratory infections?
- What are the benefits of statins for primary prevention?

---

## The files, explained
| File | What it is |
|------|------------|
| `app.py` | The app itself (the UI + the AI part). |
| `pubmed.py` | The small helper that fetches results from PubMed. |
| `requirements.txt` | The list of tools to install. |
| `.env.example` | A template for your API key. Copy it to `.env`. |

---

## If something goes wrong
- **"streamlit is not recognized"** → the private space isn't turned on. Re-run the activate command in step 1.
- **"No API key" / authentication error** → check your `.env` file has the real key with no spaces.
- **No results** → try rephrasing the question, or ask about a broader topic.

---

## Where to go next (later, not now)
- Add more sources (WHO, CDC, FDA) alongside PubMed.
- Add a "download as PDF" button for the report.
- Let the AI **compare** what different sources say and flag disagreements.
