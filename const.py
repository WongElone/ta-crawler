from enum import Enum

class FlashNewsSite(str, Enum):
    CHAINCATCHER = 'chaincatcher'
    FINNHUB = 'finnhub'
    WALLSTREETCN = 'wallstreetcn'
    INVESTING = 'investing'
    YFINANCE = 'yfinance'

class ArticleSite(str, Enum):
    CHAINCATCHER = 'chaincatcher'
    GLASSNODE = 'glassnode'

class SearchTool(str, Enum):
    BRAVE = 'brave'
    OPENROUTER = 'openrouter'
    PERPLEXITY = 'perplexity'

class FlashNewsSource(str, Enum):
    INVESTING = 'investing'
    YFINANCE = 'yfinance'
    CHAINCATCHER = 'chaincatcher'
    COINDESK = 'coindesk'
    COINTELEGRAPH = 'cointelegraph'
    CNBC = 'cnbc'
    MARKET_WATCH = 'marketwatch'
    WALLSTREETCN = 'wallstreetcn'
    OTHERS = 'others'

class ArticleSource(str, Enum):
    INVESTING = 'investing'
    YFINANCE = 'yfinance'
    CHAINCATCHER = 'chaincatcher'
    COINDESK = 'coindesk'
    GLASSNODE = 'glassnode'
    OTHERS = 'others'

class InsightCategory(str, Enum):
    RESEARCH = 'research'
    FLASHNEWS = 'flashnews'
    ARTICLE = 'article'
    USER = 'user'

FINNHUB_API_BASE_URL = 'https://finnhub.io/api/v1'