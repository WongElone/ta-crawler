import asyncio
from datetime import datetime, timedelta, timezone
from time import sleep
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .server import Server
from .config import STRATEGY_HOST, STRATEGY_PORT, ACTIVATED_ARTICLE_SITES, ACTIVATED_FLASH_NEWS_SITES
from .source import FlashNewsFetcherFacade, ArticleFetcherFacade, SearcherFacade
from .const import FlashNewsSite, ArticleSite
from .dao import TradebotDatabaseManagerAsync
from .run import start_wait_stop_runner


import logging
logger = logging.getLogger(__name__)

STRATEGY_BASE_URL = f"http://{STRATEGY_HOST}:{STRATEGY_PORT}"
GET_RESEARCH_INSTRUCTIONS_ENDPOINT = f"{STRATEGY_BASE_URL}/get-research-instructions"

class Main():
    def __init__(self):
        self.__flash_news_fetcher = FlashNewsFetcherFacade()
        self.__article_fetcher = ArticleFetcherFacade()
        self.__searcher_facade = SearcherFacade()
        self.__tbdm = TradebotDatabaseManagerAsync()
        self.__server = Server(self.__searcher_facade, self.__tbdm)

        self.__scheduler = self.__create_scheduler()

        self.__activated_article_sites = ACTIVATED_ARTICLE_SITES
        self.__activated_flash_news_sites = ACTIVATED_FLASH_NEWS_SITES

        self.__max_flash_news_fetch_lag_days = 3
        self.__max_article_fetch_lag_days = 21

        self.__stop_scheduler = asyncio.Event()
        self.__stop_server = asyncio.Event()

    def __create_scheduler(self):
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.crawl_flash_news, CronTrigger(second=30), max_instances=1, id="crawl_flash_news_job")
        scheduler.add_job(self.crawl_articles, CronTrigger(minute=5, second=30), max_instances=1, id="crawl_articles_job")
        return scheduler

    async def crawl_flash_news(self):
        logger.info("crawl flash news")
        async def crawl_flash_news_for_site(site: FlashNewsSite):
            try:
                logger.info(f"crawl flash news START on site: {site}")
                latest_time = await self.__tbdm.get_flash_news_last_publish_time(site)
                if (latest_time is None) or (datetime.now(timezone.utc) - latest_time > timedelta(days=self.__max_flash_news_fetch_lag_days)):
                    latest_time = datetime.now(timezone.utc) - timedelta(days=self.__max_flash_news_fetch_lag_days)
                
                flash_news_po_list = await self.__flash_news_fetcher.fetch(site=site, after=latest_time)
                await self.__tbdm.insert_many_flash_news(flash_news_po_list)
                logger.info(f"crawl flash news END on site: {site}")
            except Exception as e:
                logger.error(f"crawl flash news ERROR on site: {site}, error: {e}", exc_info=True)
        await asyncio.gather(*[crawl_flash_news_for_site(site) for site in self.__activated_flash_news_sites])


    async def crawl_articles(self):
        async def crawl_articles_for_site(site: ArticleSite):
            try:
                logger.info(f"crawl articles START on site: {site}")
                latest_time = await self.__tbdm.get_article_last_publish_time(site)
                if (latest_time is None) or (datetime.now(timezone.utc) - latest_time > timedelta(days=self.__max_article_fetch_lag_days)):
                    latest_time = datetime.now(timezone.utc) - timedelta(days=self.__max_article_fetch_lag_days)
                
                article_po_list = await self.__article_fetcher.fetch(site=site, after=latest_time)
                await self.__tbdm.insert_many_articles(article_po_list)
                logger.info(f"crawl articles END on site: {site}")
            except Exception as e:
                logger.error(f"crawl articles ERROR on site: {site}, error: {e}", exc_info=True)
        await asyncio.gather(*[crawl_articles_for_site(site) for site in self.__activated_article_sites])
        

    async def run_scheduler(self):
        logger.info("request scheduler start")
        self.__scheduler.start()
        logger.info("scheduler started")
        await self.__stop_scheduler.wait()
        logger.info("request scheduler stop")
        self.__scheduler.shutdown()
        logger.info("scheduler stopped")

    async def run_server(self):
        logger.info("request server start")
        # Start server in background task
        server_task = asyncio.create_task(self.__server.start())
        logger.info("server started")
        # Wait for stop signal
        await self.__stop_server.wait()
        logger.info("request server stop")
        # Stop the server
        await self.__server.stop()
        # Wait for server task to complete
        try:
            await asyncio.wait_for(server_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("server task did not complete within timeout, cancelling...")
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
        logger.info("server stopped")

    async def main(self):
        while True:
            try:
                await self.__tbdm.open()
                break
            except Exception as e:
                logger.error(f"Fail to open tradebot database manager: {e}", exc_info=True)
                await asyncio.sleep(5)
        try:
            await asyncio.gather(self.run_scheduler(), self.run_server())
        except Exception as e:
            logger.error(f"Error in main: {e}", exc_info=True)
            raise e
        finally:
            await self.__tbdm.close()

    def start(self):
        logger.info("START crawler")
        asyncio.run(self.main())

    def stop(self):
        logger.info("STOP crawler")
        self.__stop_server.set()
        self.__stop_scheduler.set()


if __name__ == "__main__":
    try:
        main = Main()
        start_wait_stop_runner(main.start, main.stop, "crawler")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sleep(1)
        raise e
        
