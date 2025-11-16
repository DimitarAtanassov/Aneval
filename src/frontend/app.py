import streamlit as st
from aneval.llms.gemini import GeminiLLM
from aneval.llms.gpt5o import GPT5oLLM
from aneval.models.response.llm_news_article import LLMNewsArticle
from aneval.models.response.geval_rank import GevalRank
import sys
import json
import textwrap
import asyncio

sys.path.append("src")
from aneval.etl.news_summarizer_etl import run_etl, OUTPUT_PATH
from aneval.prompts.judge import LLM_JUDGE_PROMPT
from aneval.prompts.summeval import (
    COHERENCE_PROMPT,
    CONSISTENCY_PROMPT,
    FLUENCY_PROMPT,
    RELEVANCE_PROMPT,
)
st.set_page_config(page_title="Stock News", layout="wide")

st.markdown(
    """
    <style>
    .news-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .news-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #222;
        margin-bottom: 0.5rem;
    }
    .news-ticker {
        font-size: 0.9rem;
        color: #888;
        margin-bottom: 0.5rem;
    }
    .news-link {
        font-size: 0.95rem;
        color: #0066cc;
        text-decoration: none;
    }
    .news-body {
        font-size: 1rem;
        color: #444;
        margin-top: 0.5rem;
    }
    ::-webkit-scrollbar {
        width: 8px;
        background: #f1f1f1;
    }
    ::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
PAGE_SIZE = 10
st.title("Stock News")
st.caption("Minimalist news dashboard. Showing parsed news from `stock_news.json`.")

# --- Load news articles ---
def load_news_articles(path="stock_news_summarized.json"):
    with open(path, "r") as f:
        data = json.load(f)
    return [LLMNewsArticle(**item) for item in data]

articles = load_news_articles("stock_news_summarized.json")

# --- When "Send to LLM Judge" is clicked, populate both tabs ---
def send_to_llm_judge(article_obj):
    st.session_state["judge_summary_area"] = article_obj.summary
    st.session_state["judge_article_area"] = article_obj.full_text
    st.session_state["judge_question_area"] = ""
    st.session_state["judge_title"] = article_obj.title
    st.session_state["geval_article_area"] = article_obj.full_text
    st.session_state["geval_summary_area"] = article_obj.summary
    st.rerun()

# --- Tabs at the top ---
tabs = st.tabs(["News", "LLM Judge Results", "Geval Results"])

with tabs[0]:
    # --- MAIN CONTENT: News Display ---
    tickers = sorted(set(article.ticker for article in articles))
    selected_ticker = st.selectbox("Filter by Ticker", ["All"] + tickers)
    if selected_ticker != "All":
        articles = [a for a in articles if a.ticker == selected_ticker]

    # Pagination logic
    total_articles = len(articles)
    total_pages = max(1, (total_articles + PAGE_SIZE - 1) // PAGE_SIZE)
    if "page" not in st.session_state:
        st.session_state.page = 1

    start_idx = (st.session_state.page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    articles_to_show = articles[start_idx:end_idx]

    for idx, article in enumerate(articles_to_show):
        preview = article.full_text[:200].replace("\n", " ") + ("..." if len(article.full_text) > 200 else "")
        with st.expander(f"{article.title} — {preview}"):
            st.markdown(
                f"""
                <div class="news-card">
                    <div class="news-ticker">Ticker: <b>{article.ticker}</b></div>
                    <a class="news-link" href="{article.link}" target="_blank">Read original article</a>
                    <div class="news-body">{article.full_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Add button to send to LLM Judge
            if st.button("Send to LLM Judge", key=f"judge_btn_{start_idx+idx}"):
                send_to_llm_judge(article)

    # --- Pagination controls (bottom) ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("Previous") and st.session_state.page > 1:
            st.session_state.page -= 1
    with col3:
        if st.button("Next") and st.session_state.page < total_pages:
            st.session_state.page += 1
    with col2:
        st.markdown(f"<div style='text-align:center;'>Page {st.session_state.page} of {total_pages}</div>", unsafe_allow_html=True)

with tabs[1]:
    st.markdown("### LLM-as-a-Judge Results")
    if st.session_state.get("llm_judge_evaluating", False):
        with st.spinner("LLM is evaluating answers for summary and article..."):
            llm = GeminiLLM()
            questions = [q.strip() for q in st.session_state.get("judge_questions_area", "").split("\n") if q.strip()]
            summary = st.session_state.get("judge_summary_area", "")
            article = st.session_state.get("judge_article_area", "")
            judge_prompt_text = st.session_state.get("judge_prompt_area", LLM_JUDGE_PROMPT)
            summary_answers = []
            article_answers = []
            for q in questions:
                try:
                    summary_ans = llm.answer_question(f"{judge_prompt_text}\n\nContext:\n{summary}", q)
                except Exception as e:
                    summary_ans = f"Error: {e}"
                try:
                    article_ans = llm.answer_question(f"{judge_prompt_text}\n\nContext:\n{article}", q)
                except Exception as e:
                    article_ans = f"Error: {e}"
                summary_answers.append(summary_ans)
                article_answers.append(article_ans)
            st.session_state["llm_judge_results"] = {
                "questions": questions,
                "summary_answers": summary_answers,
                "article_answers": article_answers,
            }
            st.session_state["llm_judge_title"] = st.session_state.get("judge_title", "")
            st.session_state["llm_judge_evaluating"] = False
            st.rerun()
    elif "llm_judge_results" in st.session_state:
        questions = st.session_state["llm_judge_results"]["questions"]
        summary_answers = st.session_state["llm_judge_results"]["summary_answers"]
        article_answers = st.session_state["llm_judge_results"]["article_answers"]
        judge_prompt = st.session_state.get("judge_prompt_area", LLM_JUDGE_PROMPT)
        for idx, q in enumerate(questions):
            with st.expander(f"Q{idx+1}: {q}"):
                st.markdown("**Prompt Used:**")
                st.markdown(
                    f'<div style="max-height:300px;overflow:auto;padding-right:8px">'
                    f'<pre style="white-space:pre-wrap">{judge_prompt}</pre>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.markdown("**Summary Answer:**")
                st.info(summary_answers[idx])
                st.markdown("**Article Answer:**")
                st.success(article_answers[idx])
    else:
        st.info("No LLM-as-a-Judge results yet. Run an evaluation in the sidebar.")

with tabs[2]:
    st.markdown("### Geval Results")
    if st.session_state.get("geval_evaluating", False):
        with st.spinner("GPT-5 is evaluating Geval prompts in parallel..."):
            llm = GPT5oLLM()
            geval_article = st.session_state.get("geval_article_area", "")
            geval_summary = st.session_state.get("geval_summary_area", "")
            async def run_geval_parallel(llm, geval_article, geval_summary):
                tasks = [
                    llm.answer_prompt_async(COHERENCE_PROMPT.replace("{{Document}}", geval_article).replace("{{Summary}}", geval_summary)),
                    llm.answer_prompt_async(CONSISTENCY_PROMPT.replace("{{Document}}", geval_article).replace("{{Summary}}", geval_summary)),
                    llm.answer_prompt_async(FLUENCY_PROMPT.replace("{{Summary}}", geval_summary)),
                    llm.answer_prompt_async(RELEVANCE_PROMPT.replace("{{Document}}", geval_article).replace("{{Summary}}", geval_summary)),
                ]
                results = await asyncio.gather(*tasks)
                return {
                    "Coherence": results[0],
                    "Consistency": results[1],
                    "Fluency": results[2],
                    "Relevance": results[3],
                }
            geval_results = asyncio.run(run_geval_parallel(llm, geval_article, geval_summary))
            st.session_state["geval_results"] = geval_results
            st.session_state["geval_title"] = st.session_state.get("judge_title", "")
            st.session_state["geval_evaluating"] = False
            st.rerun()
    elif "geval_results" in st.session_state:
        geval_results = st.session_state["geval_results"]
        geval_article = st.session_state.get("geval_article_area", "")
        geval_summary = st.session_state.get("geval_summary_area", "")
        for metric, result in geval_results.items():
            with st.expander(f"{metric}"):
                st.markdown("**Prompt:**")
                # Dynamically fill the prompt for traceability
                if metric == "Coherence":
                    prompt = COHERENCE_PROMPT
                elif metric == "Consistency":
                    prompt = CONSISTENCY_PROMPT
                elif metric == "Fluency":
                    prompt = FLUENCY_PROMPT
                elif metric == "Relevance":
                    prompt = RELEVANCE_PROMPT
                else:
                    prompt = ""
                prompt_filled = prompt.replace("{{Document}}", geval_article).replace("{{Summary}}", geval_summary)
                st.markdown(
                f'<div style="max-height:300px;overflow:auto;padding-right:8px">'
                f'<pre style="white-space:pre-wrap">{prompt_filled}</pre>'
                f'</div>',
                unsafe_allow_html=True
                )
                st.markdown("**GPT-5 Evaluation Rank:**")
                st.success(result.rank if hasattr(result, "rank") else result)
    else:
        st.info("No Geval results yet. Run an evaluation in the sidebar.")

# --- SIDEBAR: LLM-as-a-Judge Evaluator and Geval ---
st.sidebar.title("Evaluation Panel")
side_tabs = st.sidebar.tabs(["LLM-as-a-Judge", "Geval"])

# Set initial values if not already set
default_questions = [
    "What is the main event or announcement described in the article?",
    "Which companies or key stakeholders are most affected, and how?",
    "What are the short-term and long-term implications for investors?",
    "Are there any notable risks, controversies, or uncertainties mentioned?",
    "What is the overall sentiment or outlook expressed in the article?"
]
st.session_state.setdefault("judge_article_area", "")
st.session_state.setdefault("judge_summary_area", "")
st.session_state.setdefault("judge_prompt_area", LLM_JUDGE_PROMPT)
st.session_state.setdefault("judge_questions_area", "\n".join(default_questions))

# --- LLM-as-a-Judge Tab ---
with side_tabs[0]:
    judge_prompt_text = st.text_area(
        "LLM-as-a-Judge Prompt",
        key="judge_prompt_area",
        height=180
    )

    # Readable, scrollable, togglable article
    with st.expander("Original Article", expanded=False):
        article_md = st.session_state.get("judge_article_area", "")
        if article_md.strip():
            st.markdown(
                f'<div style="max-height:300px;overflow:auto;padding-right:8px">{article_md}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Please load an article from the News section above.")

    # Readable, scrollable, togglable summary
    with st.expander("Generated Summary", expanded=False):
        summary_md = st.session_state.get("judge_summary_area", "")
        if summary_md.strip():
            st.markdown(
                f'<div style="max-height:300px;overflow:auto;padding-right:8px">{summary_md}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Please load an article from the News section above.")

    questions_text = st.text_area(
        "Evaluation Questions",
        key="judge_questions_area",
        height=180
    )
    questions = [q.strip() for q in questions_text.split("\n") if q.strip()]

    if st.button("Evaluate with LLM-as-a-Judge"):
        st.session_state["llm_judge_evaluating"] = True
        st.rerun()

# --- Geval Tab ---
with side_tabs[1]:
    st.markdown(
        """
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: #555; margin-right: 0.5rem;">Powered by</span>
            <span style="background: #222; color: #fff; border-radius: 4px; padding: 2px 8px; font-weight: 700; letter-spacing: 1px;">GPT-5</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display the Geval system prompt (read-only, multi-line for legibility)
    geval_system_prompt = """You are a helpful and precise evaluator.
Respond only with the structured object.
"""
    st.markdown("**System Prompt sent to GPT-5:**")
    st.code(geval_system_prompt, language="markdown")

    geval_article = st.session_state.get("geval_article_area", "")
    geval_summary = st.session_state.get("geval_summary_area", "")

    # Dynamically fill and display each prompt with the latest article/summary
    def show_prompt(title, prompt_template):
        prompt_filled = prompt_template.replace("{{Document}}", geval_article).replace("{{Summary}}", geval_summary)
        with st.expander(title, expanded=False):
            st.markdown(
                f'<div style="max-height:300px;overflow:auto;padding-right:8px">'
                f'<pre style="white-space:pre-wrap">{prompt_filled}</pre>'
                f'</div>',
                unsafe_allow_html=True
            )

    show_prompt("Coherence Prompt", COHERENCE_PROMPT)
    show_prompt("Consistency Prompt", CONSISTENCY_PROMPT)
    show_prompt("Fluency Prompt", FLUENCY_PROMPT)
    show_prompt("Relevance Prompt", RELEVANCE_PROMPT)

    if st.button("Evaluate with Geval"):
        st.session_state["geval_evaluating"] = True
        st.rerun()