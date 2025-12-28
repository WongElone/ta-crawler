from datetime import datetime
from typing import Optional
from ..const import SearchTool
from .searcher import *
from .types import SearchResultDict


class SearcherFacade:
    def __init__(self):
        self.__searchers: dict[SearchTool, Searcher] = {
            SearchTool.PERPLEXITY : PerplexitySearcher(),
            SearchTool.OPENROUTER : OpenrouterSearcher(),
        }

    async def search(
        self, 
        tool: SearchTool,
        query: str,
        from_time: Optional[datetime],
        to_time: Optional[datetime]
    ) -> list[SearchResultDict]:
        """
        Search using the given tool with the provided query.
        return results in relevance order as list of dicts
        """
        searcher = self.__searchers.get(tool)
        if searcher is None:
            raise ValueError(f"Unknown search tool: {tool}")
        return await searcher.search(query, from_time, to_time)