import os
from dotenv import load_dotenv
import google.generativeai as genai
from aneval.models.response.llm_news_article import LLMNewsArticle

load_dotenv()  # Load variables from .env

NEWS_SUMMARY_PROMPT = (
    "You are a world-class financial news analyst. "
    "Given a news article about a stock, generate a concise, high-quality summary"
    "that highlights only the most important insights, implications, and facts for investors or analysts. "
    "Do not copy text verbatim. Focus on what is new, surprising, or actionable. "
    "Avoid generic statements. Be specific, insightful, and objective."
)

class GeminiLLM:
    def __init__(self, api_key: str = None, model_name: str = None):
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
        if model_name is None:
            model_name = os.getenv("GEMINI_LLM", "gemini-2.5-flash")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def answer_question(self, context: str, question: str) -> str:
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def summarize_news_article(self, article, prompt: str = NEWS_SUMMARY_PROMPT) -> LLMNewsArticle:
        prompt = (
            f"{prompt}\n\n"
            f"Article:\n{article.full_text}\n\n"
            f"Summary:"
        )
        response = self.model.generate_content(prompt)
        summary = response.text.strip()
        return LLMNewsArticle(
            title=article.title,
            link=article.link,
            ticker=article.ticker,
            full_text=article.full_text,
            summary=summary
        )