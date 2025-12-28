import aiohttp
from datetime import datetime, timezone
from typing import override

from ...const import FlashNewsSite, FlashNewsSource, FINNHUB_API_BASE_URL
from ...po.FlashNewsPo import FlashNewsPo
from . import FlashNewsFetcher
from ...config import FINNHUB_API_KEY

import logging
logger = logging.getLogger(__name__)

class FinnHubFlashNewsFetcher(FlashNewsFetcher):
    """
    Mainly for crypto flash news
    """
    NEWS_ENDPOINT = '/news'

    def __init__(self, timeout: int = 10):
        super().__init__(FlashNewsSite.FINNHUB)
        self._timeout = aiohttp.ClientTimeout(total=timeout, connect=5)

    @override
    async def fetch(self, after: datetime) -> list[FlashNewsPo]:
        if not FINNHUB_API_KEY:
            logger.warning("finnhub not authenticated, can't fetch flash news")
            return []
        
        result_list: list[FlashNewsPo] = []
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            for category in ['crypto']:
                try:
                    async with session.get(f'{FINNHUB_API_BASE_URL}{FinnHubFlashNewsFetcher.NEWS_ENDPOINT}?category={category}', headers={ 'X-Finnhub-Token': FINNHUB_API_KEY }) as response:
                        response.raise_for_status()
                        data = await response.json()
                        for news in data:
                            source = FlashNewsSource.OTHERS
                            if news.get('source'):
                                try:
                                    source = FlashNewsSource(news['source'].lower())
                                except ValueError:
                                    pass
                            try:
                                publish_time = datetime.fromtimestamp(news['datetime'], tz=timezone.utc)
                                if publish_time <= after:
                                    continue
                                po = FlashNewsPo(
                                    id=None,
                                    source=source,
                                    site=FlashNewsSite.FINNHUB,
                                    title=f"[Category: {category}] {news['headline']}",
                                    title_md5='',
                                    description=news['summary'],
                                    url=news['url'],
                                    create_time=datetime.now(timezone.utc),
                                    publish_time=publish_time,
                                )
                                result_list.append(po)
                            except Exception as e:
                                logger.error(f'Error processing category: {category}, news: {news}', exc_info=True)
                except aiohttp.ClientError as e:
                    logger.error(f'Error fetching news: {e}', exc_info=True)
                except Exception as e:
                    logger.error(f'Unknown error: {e}', exc_info=True)
            
        return result_list