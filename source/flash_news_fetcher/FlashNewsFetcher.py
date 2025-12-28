from abc import ABC, abstractmethod
from datetime import datetime

from crawler.const import FlashNewsSite

from ...po import FlashNewsPo

import logging
logger = logging.getLogger(__name__)

class FlashNewsFetcher(ABC):

    def __init__(self, site: FlashNewsSite):
        self.__site = site

    @abstractmethod
    async def fetch(self, after: datetime) -> list[FlashNewsPo]:
        pass