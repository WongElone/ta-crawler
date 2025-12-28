import logging
from typing import Optional, List

from crawler.const import ArticleSite, FlashNewsSite
from crawler.dao.AsyncpgPgClient import AsyncpgPgClient
from ..config import TRADEBOT_DB_USER, TRADEBOT_DB_PASSWORD, TRADEBOT_DB_HOST, TRADEBOT_DB_PORT, TRADEBOT_DB_NAME
from datetime import datetime
from ..po.FlashNewsPo import FlashNewsPo
from ..po.SearchResultPo import SearchResultPo
from ..po.ArticlePo import ArticlePo

log = logging.getLogger(__name__)

class TradebotDatabaseManagerAsync(AsyncpgPgClient):
    def __init__(self):
        super().__init__(
            user=TRADEBOT_DB_USER,
            password=TRADEBOT_DB_PASSWORD,
            host=TRADEBOT_DB_HOST,
            port=TRADEBOT_DB_PORT,
            db_name=TRADEBOT_DB_NAME
        )

    async def insert_many_flash_news(self, flash_news_list: List[FlashNewsPo]):
        """
        Insert multiple FlashNewsPo objects into the database
        
        Args:
            flash_news_list: List of FlashNewsPo objects to insert
            
        Returns:
            True if all records were inserted successfully, False otherwise
        """
        if not flash_news_list:
            return True
            
        query = f"""
            INSERT INTO t_flash_news (
                source, 
                site,
                title, 
                title_md5, 
                description, 
                url, 
                create_time, 
                publish_time
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (site, title_md5, publish_time) DO NOTHING
        """
        flash_news_values = [
            (news.source.value, news.site.value, news.title, news.title_md5, news.description, 
                news.url, news.create_time, news.publish_time)
            for news in flash_news_list
        ]
        await self.executemany(query, flash_news_values)

    async def insert_many_articles(self, articles_list: List[ArticlePo]):
        """
        Insert multiple ArticlePo objects into the database
        
        Args:
            articles_list: List of ArticlePo objects to insert
            
        Returns:
            True if all records were inserted successfully, False otherwise
        """
        if not articles_list:
            return True
        query = """
            INSERT INTO t_article (
                source, 
                site,
                title, 
                title_md5, 
                content, 
                url, 
                create_time, 
                publish_time
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (site, title_md5, publish_time) DO NOTHING
        """
        article_values = [
            (article.source.value, article.site.value, article.title, article.title_md5, article.content, 
                article.url, article.create_time, article.publish_time)
            for article in articles_list
        ]
        await self.executemany(query, article_values)

    async def get_article_last_publish_time(self, site: ArticleSite) -> Optional[datetime]:
        query = f"""
            SELECT MAX(publish_time) AS max_publish_time
            FROM t_article
            WHERE site = $1
        """
        result_list = await self.fetch(query, lambda record: record['max_publish_time'], site.value)
        if result_list:
            return result_list[0]
        return None

    async def get_flash_news_last_publish_time(self, site: FlashNewsSite) -> Optional[datetime]:
        query = f"""
            SELECT MAX(publish_time) AS max_publish_time
            FROM t_flash_news
            WHERE site = $1
        """
        result_list = await self.fetch(query, lambda record: record['max_publish_time'], site.value)
        if result_list:
            return result_list[0]
        return None
