from pydantic import BaseModel

class NewsArticle(BaseModel):
    title: str
    link: str
    ticker: str
    full_text: str