import os
from openai import AsyncOpenAI
from aneval.models.response.geval_rank import GevalRank

class GPT5oLLM:
    def __init__(self, api_key: str = None, model_name: str = None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if model_name is None:
            model_name = os.getenv("GPT_GEVAL_LLM", "gpt-5-2025-08-07")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model_name

    async def answer_prompt_async(self, prompt: str) -> GevalRank:
        response = await self.client.responses.parse(
            model=self.model_name,
            input=[
                {"role": "system", "content": "You are a helpful and precise evaluator. Respond only with the structured object."},
                {"role": "user", "content": prompt}
            ],
            text_format=GevalRank,
        )
        return response.output_parsed