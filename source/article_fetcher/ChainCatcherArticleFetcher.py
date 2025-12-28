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


class ChainCatcherArticleFetcher(ArticleFetcher):

    def __init__(self, timeout: int = 10):
        super().__init__(ArticleSite.CHAINCATCHER)
        self._timeout = aiohttp.ClientTimeout(total=timeout, connect=5)
    
    BASE_URL = 'https://www.chaincatcher.com'
    COOKIES = {
        'i18n_redirected': 'en',
        'auth.strategy': 'local',
        'noticeTime': datetime.now(timezone(timedelta(hours=8))).strftime('%d/%m/%Y'),
    }

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        # 'Cookie': 'i18n_redirected=en; auth.strategy=local; noticeTime=9/10/2025',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i',
    }

    @override
    async def fetch(self, after: datetime) -> list[ArticlePo]:
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            url_list = await self.crawl_chaincatcher_article_url_list(session)
            article_list = []
            for url in url_list:
                article = await self.crawl_chaincatcher_single_article(session, url, after)
                if article:
                    article_list.append(article)
            return article_list

    async def crawl_chaincatcher_article_url_list(self, session: aiohttp.ClientSession) -> list[str]:
        try:
            async with session.get(ChainCatcherArticleFetcher.BASE_URL + '/en/article', cookies=ChainCatcherArticleFetcher.COOKIES, headers=ChainCatcherArticleFetcher.HEADERS) as response:
                response.raise_for_status()
                content = await response.read()

                soup = BeautifulSoup(content, 'html.parser')
                articles = soup.select('.article_wraper .article_area')

                url_list = []
                for article in articles:
                    try:
                        a_tag = article.select_one('a:has(.article_title)')
                        if not a_tag:
                            continue
                        url = a_tag.attrs.get('href')
                        if not url:
                            continue
                        url = str(url)
                        if not url.startswith('http'):
                            url = ChainCatcherArticleFetcher.BASE_URL + url
                        url_list.append(url)
                    except Exception as e:
                        logger.error(f"Error parsing article, article: {article}, error: {e}")
                        continue
                return url_list
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching the webpage: {e}")
            return []
        except Exception as e:
            logger.error(f"Unknown error: {e}")
            return []

    @staticmethod
    async def crawl_chaincatcher_single_article(session: aiohttp.ClientSession, url: str, after: datetime) -> Optional[ArticlePo]:
        try:
            async with session.get(url, cookies=ChainCatcherArticleFetcher.COOKIES, headers=ChainCatcherArticleFetcher.HEADERS) as response:
                response.raise_for_status()
                content = await response.read()
                soup = BeautifulSoup(content, 'html.parser')
                wrapper = soup.select_one('.details_wraper')
                if not wrapper:
                    return
                publish_time_tag = wrapper.select_one('.author .time')
                if not publish_time_tag:
                    return
                publish_time_str = publish_time_tag.text.strip()
                publish_time = datetime.strptime(publish_time_str, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
                publish_time = publish_time.replace(tzinfo=timezone.utc)
                if publish_time <= after:
                    return
                
                title_tag = soup.select_one('h1')
                if not title_tag:
                    return
                title = title_tag.text.strip()
                if not title:
                    return
                
                related_topic_list = []
                related_topic_tags = wrapper.select_one('.associated_labels .labels_content')
                if related_topic_tags:
                    related_topic_list = [tag.text.strip() for tag in related_topic_tags.select('a')]

                abstract = ''
                abstract_tag = wrapper.select_one('.abstract')
                if abstract_tag:
                    abstract = abstract_tag.text.strip()

                content_tag = wrapper.select_one('.rich_text_content')
                if not content_tag:
                    return

                REMOVE_ATTRIBUTES = [
                    'lang','language','onmouseover','onmouseout','script','style','font',
                    'dir','face','size','color','style','class','width','height','hspace',
                    'border','valign','align','background','bgcolor','text','link','vlink',
                    'alink','cellpadding','cellspacing', 'href', 'id', 'rel']
                for tag in content_tag.descendants:
                    if isinstance(tag, Tag):
                        tag.attrs = {key: value for key, value in tag.attrs.items()
                                    if key not in REMOVE_ATTRIBUTES}
                content = content_tag.prettify()

                if related_topic_list:
                    related_topic_str = ''
                    for topic in related_topic_list:
                        related_topic_str += f'<li>{topic}</li>'
                    content = f'<h3>Related Labels</h3>\n<ul id="related_labels">{related_topic_str}</ul>\n{content}'

                if abstract:
                    content = f'<h2 id="abstract">{abstract}</h2>\n{content}'

                return ArticlePo(
                    id=None,
                    source=ArticleSource.CHAINCATCHER,
                    site=ArticleSite.CHAINCATCHER,
                    title=title,
                    title_md5='',
                    content=content,
                    url=url,
                    create_time=datetime.now(timezone.utc),
                    publish_time=publish_time,
                )
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching the webpage, url: {url}, error: {e}")
            return
        except Exception as e:
            logger.error(f"Error parsing article, url: {url}, error: {e}")
            return

