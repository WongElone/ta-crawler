import asyncio
from datetime import datetime
import json
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model

from . import Searcher
from ...const import SearchTool
from ..types import SearchResultDict
from ...config import OPENROUTER_SEARCHER_MODEL, OPENROUTER_SEARCHER_SYSTEM_PROMPT, OPENROUTER_BASE_URL, OPENROUTER_API_KEY

class OpenrouterSearcher(Searcher):
    def __init__(self):
        super().__init__(SearchTool.OPENROUTER)

        self.model = ChatOpenAI(
            model=OPENROUTER_SEARCHER_MODEL,
            base_url=OPENROUTER_BASE_URL,
            api_key=lambda: OPENROUTER_API_KEY,
            extra_body={ # extra body seems not working
                "plugins": [
                    {
                        "id": "web",
                        "max_results": 5,  # Customize: Get more results
                        # "search_prompt": f"A web search was conducted on {datetime.now().strftime('%Y-%m-%d')}. Incorporate the following web search results into your response. IMPORTANT: Cite them using markdown links named using the domain of the source.",  # Customize prompt
                    }
                ]
            }
        )

    async def search(self, query: str, from_time: Optional[datetime], to_time: Optional[datetime]) -> list[SearchResultDict]:
        conversation = [
            {"role": "system", "content": OPENROUTER_SEARCHER_SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]
        response = await asyncio.to_thread(self.model.invoke, conversation)
        if type(response.content) == str:
            return [SearchResultDict(content=response.content, url=None)]
        else:
            return [SearchResultDict(content=json.dumps(item), url=None) for item in response.content]
