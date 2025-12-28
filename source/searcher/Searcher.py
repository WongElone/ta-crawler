from abc import ABC
from datetime import datetime
from typing import Optional

from ...const import SearchTool
from ..types import SearchResultDict

import logging
logger = logging.getLogger(__name__)

class Searcher(ABC):
    def __init__(self, tool: SearchTool):
        self._tool = tool

    async def search(self, query: str, from_time: Optional[datetime], to_time: Optional[datetime] ) -> list[SearchResultDict]:
        raise NotImplementedError
