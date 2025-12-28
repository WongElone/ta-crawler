from datetime import datetime
from ..po import FlashNewsPo
from ..const import FlashNewsSite
from .flash_news_fetcher import *
class FlashNewsFetcherFacade:
    def __init__(self):
        self.__fetchers: dict[FlashNewsSite, FlashNewsFetcher] = {
            FlashNewsSite.CHAINCATCHER : ChainCatcherFlashNewsFetcher(),
            FlashNewsSite.FINNHUB : FinnHubFlashNewsFetcher(),
            FlashNewsSite.WALLSTREETCN : WallstreetCnFlashNewsFetcher(),
        }

    async def fetch(
        self, 
        site: FlashNewsSite, 
        after: datetime,
    ) -> list[FlashNewsPo]:
        """
        Fetch flash news from the given source.
        after: fetch flash news published after this time
        return in chronological order
        """
        fetcher = self.__fetchers.get(site)
        if fetcher is None:
            raise ValueError(f"Unknown flash news site: {site}")
        return await fetcher.fetch(after=after)