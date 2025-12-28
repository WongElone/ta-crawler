
from enum import Enum
import aiohttp
from bs4 import BeautifulSoup, Tag
from datetime import datetime, timezone, timedelta
from typing import Any, List, Dict, Optional, override

from ...const import FlashNewsSite, FlashNewsSource
from ...po.FlashNewsPo import FlashNewsPo
from . import FlashNewsFetcher

import logging
logger = logging.getLogger(__name__)

class Channel(str, Enum):
    GLOBAL = 'global-channel'
    A_STOCK = 'a-stock-channel'
    US_STOCK = 'us-stock-channel'
    HK_STOCK = 'hk-stock-channel'
    FOREX = 'forex-channel'
    COMMODITY = 'commodity-channel'
    BOND = 'bond-channel'
    TECH = 'tech-channel'
    GOLD = 'goldc-channel'
    OIL = 'oil-channel'

CHANNEL_CN_NAME_MAP = {
    Channel.GLOBAL: '无分类',
    Channel.A_STOCK: 'A股',
    Channel.US_STOCK: '美股',
    Channel.HK_STOCK: '港股',
    Channel.FOREX: '外汇',
    Channel.COMMODITY: '商品',
    Channel.BOND: '债券',
    Channel.TECH: '科技',
    Channel.GOLD: '黃金',
    Channel.OIL: '原油',
}

def get_channel_cn_name(channel: Channel) -> str:
    return CHANNEL_CN_NAME_MAP[channel]

class WallstreetCnFlashNewsFetcher(FlashNewsFetcher):    
    URL = 'https://api-one-wscn.awtmt.com/apiv1/content/lives'

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0',
        'Accept': '*/*',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://wallstreetcn.com/',
        'x-client-type': 'pc',
        'x-device-id': '199c288c-a91a-dbf8-b99a-904e7ce885db',
        'x-ivanka-app': 'wscn|web|0.40.20|0.0|0',
        'x-ivanka-platform': 'wscn-platform',
        'x-taotie-device-id': '199c288c-a91a-dbf8-b99a-904e7ce885db',
        'x-track-info': '{"appId":"com.wallstreetcn.web","appVersion":"0.40.20"}',
        'Origin': 'https://wallstreetcn.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
    }

    def __init__(self, timeout: int = 10):
        super().__init__(FlashNewsSite.WALLSTREETCN)
        self._timeout = aiohttp.ClientTimeout(total=timeout, connect=5)

    def channel_str_list_to_category_name_list(self, channel_str_list: list[str]) -> list[str]:
        channel_list: list[Channel] = []
        for channel_str in channel_str_list:
            try:
                c = Channel(channel_str)
                if c == Channel.GLOBAL:
                    continue
                channel_list.append(c)
            except ValueError:
                continue
        if not channel_list:
            channel_list.append(Channel.GLOBAL)
        return [get_channel_cn_name(channel) for channel in channel_list]

    @override
    async def fetch(self, after: datetime) -> list[FlashNewsPo]:
        params = {
            'channel': 'global-channel', # us-stock-channel, tech-channel, goldc-channel,oil-channel,commodity-channel, hk-stock-channel
            'client': 'pc',
            'limit': '20',
            'first_page': 'true',
            'accept': 'live,vip-live',
            # 'score': 2 # 1 - 3, 3 is most important
        }

        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(WallstreetCnFlashNewsFetcher.URL, params=params, headers=WallstreetCnFlashNewsFetcher.HEADERS) as response:
                    response.raise_for_status()
                    data = await response.json()
                    result_list: list[FlashNewsPo] = []
                    for news in data["data"]["items"]:
                        try:
                            title = news['title']
                            content = news['content_text']
                            channel_str_list = news['channels']
                            category_name_list = self.channel_str_list_to_category_name_list(channel_str_list if channel_str_list else [])
                            if not title:
                                if content:
                                    title = content
                                    content = ''
                                else:
                                    continue
                            publish_time = datetime.fromtimestamp(float(news['display_time']), tz=timezone.utc)
                            if publish_time <= after:
                                continue
                            result_list.append(FlashNewsPo(
                                id=None,
                                source=FlashNewsSource.WALLSTREETCN,
                                site=FlashNewsSite.WALLSTREETCN,
                                title=f"[类别: {', '.join(category_name_list)}] {title}",
                                title_md5='',
                                description=content,
                                url=news['uri'],
                                create_time=datetime.now(timezone.utc),
                                publish_time=publish_time,
                            ))
                        except Exception as e:
                            logger.error(f'Error processing news: {news}, msg={e}', exc_info=True)
                    return result_list
        except aiohttp.ClientError as e:
            logger.error(f'Error fetching news: {e}', exc_info=True)
            return []
        except Exception as e:
            logger.error(f'Unknown error: {e}', exc_info=True)
            return []
        
