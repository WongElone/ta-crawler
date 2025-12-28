from datetime import datetime
from ..const import ArticleSite
from ..po import ArticlePo
from .article_fetcher import *


class ArticleFetcherFacade:
    def __init__(self):
        self.__fetchers: dict[ArticleSite, ArticleFetcher] = {
            ArticleSite.CHAINCATCHER : ChainCatcherArticleFetcher(),
            ArticleSite.GLASSNODE : GlassnodeArticleFetcher(),
        }

    async def fetch(
        self, 
        site: ArticleSite,
        after: datetime,
    ) -> list[ArticlePo]:
        """
        Fetch articles from the given source.
        return in chronological order
        """
        fetcher = self.__fetchers.get(site)
        if fetcher is None:
            raise ValueError(f"Unknown article site: {site}")
        return await fetcher.fetch(after=after)