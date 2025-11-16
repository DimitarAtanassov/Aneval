import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from aneval.services.news_service import load_news_articles
from aneval.llms.gemini import GeminiLLM, NEWS_SUMMARY_PROMPT
from aneval.models.response.llm_news_article import LLMNewsArticle

# Load environment variables
load_dotenv()

# Configurable paths and parameters
INPUT_PATH = Path(os.getenv("STOCK_NEWS_INPUT_PATH", "stock_news.json"))
OUTPUT_PATH = Path(os.getenv("STOCK_NEWS_OUTPUT_PATH", "stock_news_summarized.json"))
BATCH_SIZE = 10
RETRIES = 2

def save_progress(articles, output_path):
    """Save the current progress to the output JSON file."""
    with open(output_path, "w") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Progress saved: {len(articles)} articles summarized.")

def summarize_article_with_retries(llm, article, prompt, retries=2):
    """Try to summarize an article, retrying on failure."""
    for attempt in range(1, retries + 1):
        try:
            return llm.summarize_news_article(article, prompt=prompt)
        except Exception as e:
            print(f"    Attempt {attempt} failed: {e}")
            if attempt < retries:
                print("    Retrying in 5 seconds...")
                time.sleep(5)
    # If all attempts fail, return a placeholder
    print("    All attempts failed. Marked as 'AI could not generate'.")
    return LLMNewsArticle(
        title=getattr(article, "title", ""),
        link=getattr(article, "link", ""),
        ticker=getattr(article, "ticker", ""),
        full_text=getattr(article, "full_text", ""),
        summary="AI could not generate"
    )

def run_etl(custom_prompt=None):
    articles = load_news_articles(str(INPUT_PATH))
    llm = GeminiLLM()
    summarized = []

    prompt = custom_prompt if custom_prompt else NEWS_SUMMARY_PROMPT

    print(f"Loaded {len(articles)} articles from {INPUT_PATH}")

    for idx, article in enumerate(articles, 1):
        print(f"[{idx}/{len(articles)}] Summarizing: {getattr(article, 'title', '')[:60]}...")
        summary_obj = summarize_article_with_retries(llm, article, prompt, retries=RETRIES)
        summarized.append(summary_obj.dict())

        if idx % BATCH_SIZE == 0 or idx == len(articles):
            save_progress(summarized, OUTPUT_PATH)

    print(f"ETL complete. Summarized {len(summarized)} articles. Results saved to {OUTPUT_PATH}")
    return summarized

if __name__ == "__main__":
    run_etl()