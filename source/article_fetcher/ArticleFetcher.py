from abc import ABC
from datetime import datetime

from crawler.const import ArticleSite

from ...po import ArticlePo

import logging
logger = logging.getLogger(__name__)

class ArticleFetcher(ABC):

    def __init__(self, site: ArticleSite):
        self.__site = site

    async def fetch(self, after: datetime) -> list[ArticlePo]:
        raise NotImplementedError
