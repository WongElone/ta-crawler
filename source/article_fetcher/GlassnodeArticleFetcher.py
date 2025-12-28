from datetime import datetime
from typing import Optional, override, TypedDict

import aiohttp
from bs4 import BeautifulSoup, Tag
from datetime import datetime, timezone, timedelta

from crawler.const import ArticleSite, ArticleSource

from ...po import ArticlePo
from . import ArticleFetcher

import logging
logger = logging.getLogger(__name__)

class ArticleInfo(TypedDict):
    url: str
    title: str
    publish_datetime: datetime

class GlassnodeArticleFetcher(ArticleFetcher):
    BASE_URL = 'https://insights.glassnode.com'

    def __init__(self, timeout: int = 10):
        super().__init__(ArticleSite.GLASSNODE)
        self._timeout = aiohttp.ClientTimeout(total=timeout, connect=5)
    

    @override
    async def fetch(self, after: datetime) -> list[ArticlePo]:
        result_list: list[ArticlePo] = []
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            for article_info in await self.crawl_article_list(session, after):
                try:
                    content = await self.crawl_single_article(session, article_info)
                    if not content:
                        continue
                    result_list.append(ArticlePo(
                        id=None,
                        source=ArticleSource.GLASSNODE,
                        site=ArticleSite.GLASSNODE,
                        title=article_info['title'],
                        title_md5='',
                        content=content,
                        url=article_info['url'],
                        publish_time=article_info['publish_datetime'],
                    ))
                except Exception as e:
                    logger.error(f'Error fetching article: {e}', exc_info=True)
                    continue
        return result_list

    async def crawl_article_list(self, session: aiohttp.ClientSession, after: datetime) -> list[ArticleInfo]:
        async with session.get(f'{GlassnodeArticleFetcher.BASE_URL}/tag/newsletter/') as response:
            response.raise_for_status()
            content = await response.read()
            soup = BeautifulSoup(content, 'html.parser')
            articles = soup.select('article')
            article_info_list: list[ArticleInfo] = []
            for article in articles:
                try:
                    url_tag = article.select_one('a.post-card-content-link')
                    if not url_tag:
                        continue
                    url = f'{GlassnodeArticleFetcher.BASE_URL}{url_tag.attrs['href']}'
                    title_tag = article.select_one('.post-card-title')
                    if not title_tag:
                        continue
                    title = title_tag.text.strip()
                    publish_datetime_tag = article.select_one('time.post-card-meta-date')
                    if not publish_datetime_tag:
                        continue
                    publish_datetime = datetime.strptime(str(publish_datetime_tag.attrs['datetime']).strip(), '%Y-%m-%d')
                    publish_datetime = publish_datetime.replace(tzinfo=timezone.utc)
                    if (publish_datetime <= after):
                        continue
                    article_info_list.append({
                        'url': url,
                        'title': title,
                        'publish_datetime': publish_datetime
                    })
                except Exception as e:
                    logger.error(f'Error parsing article: {e}', exc_info=True)
            return article_info_list

    @staticmethod
    async def crawl_single_article(session: aiohttp.ClientSession, article_info: ArticleInfo) -> Optional[str]:
        async with session.get(article_info['url']) as response:
            response.raise_for_status()
            content = await response.read()
            soup = BeautifulSoup(content, 'html.parser')
    
            article = soup.select_one("#site-main > article")
            if not article:
                return None
    
            byline = article.select_one('.article-byline')
            if byline:
                byline.decompose()
    
            script_tags = article.find_all('script')
            if script_tags:
                for tag in script_tags:
                    tag.decompose()
            noscript_tags = article.find_all('noscript')
            if noscript_tags:
                for tag in noscript_tags:
                    tag.decompose()
            img_tags = article.find_all('img')
            if img_tags:
                for tag in img_tags:
                    tag.decompose()
            figure_tags = article.find_all('figure')
            if figure_tags:
                for tag in figure_tags:
                    tag.decompose()
            
            separator = article.find('hr')
            if separator:
                # Start with the immediate next sibling
                current_sibling = separator.next_sibling
    
                # Loop through and remove all subsequent siblings
                while current_sibling:
                    next_to_remove = current_sibling
                    current_sibling = current_sibling.next_sibling # Get the next sibling before removing
                    next_to_remove.extract() # or next_to_remove.decompose()
    
            REMOVE_ATTRIBUTES = [
                'lang','language','onmouseover','onmouseout','script','style','font',
                'dir','face','size','color','style','class','width','height','hspace',
                'border','valign','align','background','bgcolor','text','link','vlink',
                'alink','cellpadding','cellspacing', 'href', 'id', 'rel']
            for tag in article.descendants:
                if isinstance(tag, Tag):
                    tag.attrs = {key: value for key, value in tag.attrs.items()
                                if key not in REMOVE_ATTRIBUTES}
            return article.prettify()