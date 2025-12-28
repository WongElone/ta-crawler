import asyncio
from datetime import datetime
import json
from typing import Optional

import httpx
from perplexity import Perplexity

from . import Searcher
from ...const import SearchTool
from ..types import SearchResultDict
from ...config import PERPLEXITY_SEARCHER_MODEL, PERPLEXITY_SEARCHER_SYSTEM_PROMPT


class PerplexitySearcher(Searcher):
    def __init__(self):
        super().__init__(SearchTool.PERPLEXITY)
        timeout_config = httpx.Timeout(
            connect=5.0,
            read=120.0,  # 2 minutes for complex queries
            write=10.0,
            pool=10.0
        )
        self.client = Perplexity(timeout=timeout_config)

    async def search(self, query: str, from_time: Optional[datetime], to_time: Optional[datetime]) -> list[SearchResultDict]:
        def chat_complete():
            return self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": PERPLEXITY_SEARCHER_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                model=PERPLEXITY_SEARCHER_MODEL,
                search_after_date_filter=from_time.strftime("%m/%d/%Y") if from_time else None,
                search_before_date_filter=to_time.strftime("%m/%d/%Y") if to_time else None,
                # max_tokens=500,  # Limit response length
                # temperature=0.7,  # Control creativity
                # top_p=0.9,       # Control diversity
                # presence_penalty=0.1,  # Reduce repetition
                # frequency_penalty=0.1
            )
        completion = await asyncio.to_thread(chat_complete)

        content = completion.choices[0].message.content
        if type(content) == str:
            return [
                SearchResultDict(
                    content=content,
                    url=None
                )
            ]
        else:
            return [
                SearchResultDict(
                    content=json.dumps(item),
                    url=None
                )
                for item in content
            ]
