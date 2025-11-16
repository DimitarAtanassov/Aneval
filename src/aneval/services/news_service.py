import json
from pathlib import Path
from typing import List
from aneval.models.news_article import NewsArticle

def load_news_articles(json_path: str) -> List[NewsArticle]:
    with open(json_path, "r") as f:
        data = json.load(f)
    articles = []
    for ticker, news_list in data.items():
        for item in news_list:
            # Defensive: skip if any field is missing
            if all(k in item for k in ("title", "link", "ticker", "full_text")):
                articles.append(NewsArticle(**item))
    return articles