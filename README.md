# aneval

**aneval** is a minimalist financial news evaluation dashboard. It uses LLMs (Gemini, GPT-5, etc.) to generate news article summaries, evaluate summary quality, and compare summary answers to full-article answers using a set of financial analysis questions.

---

## Features

- **News Dashboard:** Browse and filter financial news articles.
- **LLM-as-a-Judge:** Ask an LLM to answer key questions using both the article and its summary, then compare the answers for relevance and consistency.
- **Geval Evaluation:** Use GPT-5 to rate summaries on coherence, consistency, fluency, and relevance.
- **Parallel LLM Calls:** Fast evaluation by running LLM calls in parallel.
- **Interactive UI:** All results, prompts, and evaluations are shown in a clean Streamlit interface.

---

## Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/aneval.git
cd aneval
```

### 2. Install dependencies

I Recommend using [Poetry](https://python-poetry.org/) for dependency management:

```bash
poetry install
```

If you prefer pip and a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Set up environment variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp aneval/.env.example .env
# Edit .env and add your Gemini, OpenAI, and Voyage API keys
```

### 4. Prepare news data

- Place your raw news articles in `aneval/stock_news.json`.
- Run the ETL script to generate summaries:

```bash
python src/aneval/etl/news_summarizer_etl.py
```

This will create `aneval/stock_news_summarized.json`.

### 5. Run the Streamlit app

```bash
poetry run streamlit run src/frontend/app.py
```

---

## File Structure

```
aneval/
├── src/
│   ├── aneval/
│   │   ├── etl/
│   │   ├── llms/
│   │   ├── models/
│   │   ├── prompts/
│   │   ├── services/
│   │   └── ...
│   └── frontend/
│       └── app.py
├── stock_news.json
├── stock_news_summarized.json
├── .env
├── .env.example
└── README.md
```

---

## Configuration

- **API Keys:** Set in `.env` (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `VOYAGE_API_KEY`)
- **Model Names:** Set in `.env` (`GEMINI_LLM`, `GPT_GEVAL_LLM`)
- **News Data Paths:** Set in `.env` (`STOCK_NEWS_INPUT_PATH`, `STOCK_NEWS_OUTPUT_PATH`)

---

## How It Works

1. **Summarization:** The ETL script uses Gemini to summarize each news article.
2. **Evaluation:** In the app, select an article and send it to the LLM Judge.
3. **Q&A:** The LLM answers a set of financial questions using both the summary and the full article.
4. **Comparison:** The LLM compares the two sets of answers for relevance and consistency.
5. **Geval:** Optionally, GPT-5 rates the summary on multiple metrics.

---

## Customization

- **Prompts:** Edit prompts in `src/aneval/prompts/`.
- **Questions:** Edit the default questions in `app.py` or via the sidebar in the app.

---

## License

MIT License

---

## Contact

For questions or contributions, open an issue or contact [Dimitar Atanassov](mailto:dimitar.atanassovse@gmail.com).