from pydantic import BaseModel

class LLMNewsArticle(BaseModel):
    title: str
    link: str
    ticker: str
    full_text: str
    summary: str