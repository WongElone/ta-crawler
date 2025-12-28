import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from typing import Any, override

from ...const import FlashNewsSite, FlashNewsSource
from ...po.FlashNewsPo import FlashNewsPo
from . import FlashNewsFetcher

class ChainCatcherFlashNewsFetcher(FlashNewsFetcher):
    BASE_URL = 'https://www.chaincatcher.com'
    NEWS_LISTING_URL = "https://www.chaincatcher.com/en/news"

    def __init__(self, timeout: int = 10):
        super().__init__(FlashNewsSite.CHAINCATCHER)
        self._timeout = aiohttp.ClientTimeout(total=timeout, connect=5)

    @override
    async def fetch(self, after: datetime) -> list[FlashNewsPo]:
        result_list = await self.crawl_chaincatcher_flash_news(after)
        return [FlashNewsPo(
            id=None,
            source=FlashNewsSource.CHAINCATCHER,
            site=FlashNewsSite.CHAINCATCHER,
            title=result['title'],
            title_md5='',
            description=result['description'],
            url=result['url'],
            create_time=datetime.now(timezone.utc),
            publish_time=result['publish_datetime_utc']
        ) for result in result_list]

    async def crawl_chaincatcher_flash_news(self, after: datetime) -> list[dict[str, Any]]:
        """
        Crawl flash news from ChainCatcher website
        
        Returns:
            List of dictionaries containing title, publish_datetime_utc, and url
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(ChainCatcherFlashNewsFetcher.NEWS_LISTING_URL, headers=headers) as response:
                    response.raise_for_status()
                    content = await response.read()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    news_list = soup.find_all('div', class_='v-timeline-item')
                    result_list: list[dict] = []
                    for news in news_list:
                        try:
                            title: str = news.select_one('.timeline_title>.text').text.strip() # type: ignore
                            if not title:
                                continue
                            datetimestr: str = news.select_one('[timeattr]').attrs['timeattr'] # type: ignore
                            publish_datetime_utc = datetime.strptime(datetimestr, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
                            publish_datetime_utc = publish_datetime_utc.replace(tzinfo=timezone.utc)
                            if publish_datetime_utc < after:
                                continue
                            url: str = news.select_one('a.timeline_content').attrs['href'].strip() # type: ignore
                            if not url:
                                continue
                            if not url.startswith('http'):
                                url = ChainCatcherFlashNewsFetcher.BASE_URL + url
                            result_list.append({
                                'title': title,
                                'publish_datetime_utc': publish_datetime_utc,
                                'url': url
                            })
                            
                        except Exception as e:
                            print(f"Error parsing news: {e}")
                            continue

                    final_results = []
                    for result in result_list:
                        try:
                            if not result['url']:
                                continue
                            async with session.get(result['url'], headers=headers) as detail_response:
                                detail_response.raise_for_status()
                                detail_content = await detail_response.read()
                                soup = BeautifulSoup(detail_content, 'html.parser')
                                description: str = soup.select_one('.rich_text_content').text.strip() # type: ignore
                                result['description'] = description
                                final_results.append(result)
                            
                        except Exception as e:
                            print(f"Error fetching the webpage: {e}")
                            continue

                    return final_results
                
        except Exception as e:
            print(f"Error fetching the webpage: {e}")
            return []