from datetime import datetime
import signal
import logging
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.requests import Request

from .source.SearcherFacade import SearcherFacade
from .const import SearchTool
from .dto import DoSearchRequest, CrawlerApiResponse, SearchResult
from .config import UVICORN_PORT, UVICORN_LOG_LEVEL
from .dao import TradebotDatabaseManagerAsync

log = logging.getLogger(__name__)

class Server:
    def __init__(self, searcher_facade: SearcherFacade, tdbm: TradebotDatabaseManagerAsync):
        self.__searcher_facade = searcher_facade
        self.__tdbm = tdbm
        
        self.app: Starlette = Starlette(debug=False, routes=[
            Route('/health', self.health_test_endpoint, methods=['GET']),
            Route('/search', self.search_endpoint, methods=['POST']),
        ], exception_handlers={
            Exception: self.handle_error,
        })
        """
        0.0.0.0 binds to all network interfaces, making the server accessible from:
        - Inside the container (localhost)
        - Other containers on the Docker network (via container name)
        - The host machine (via port mapping if configured)
        """
        config = uvicorn.Config(self.app, host="0.0.0.0", port=UVICORN_PORT, log_level=UVICORN_LOG_LEVEL)
        self.__uvicorn_server = uvicorn.Server(config)

        # Ensure Uvicorn loggers propagate to the root logger
        loggers_to_propagate = (
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
        )
        for logger_name in loggers_to_propagate:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = []  # Clear any existing handlers
            logging_logger.propagate = True # Allow logs to reach the root logger

    async def handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse({
            "timestamp": datetime.now().isoformat(),
            "detail": str(exc),
        }, status_code=500)
    
    async def health_test_endpoint(self, request: Request) -> Response:
        """
        Health test endpoint
        """
        if not (await self.__tdbm.test_connection()):
            return Response(content="Database connection failed", status_code=500)
        return Response(content="OK", status_code=200)
    
    async def search_endpoint(self, request: Request) -> JSONResponse:
        """
        Search endpoint for analyst module to perform searches
        Request body: DoSearchRequestDto (tool, query, fromTime, toTime)
        Response body: CrawlerApiResponse<List<SearchResultDto>>
        """
        try:
            data: DoSearchRequest = await request.json()
            
            # Parse search tool from string
            tool_str = data.get('tool')
            if not tool_str:
                raise ValueError("Search tool is required")
            tool = SearchTool(tool_str)
            
            # Get query
            query = data.get('query')
            if not query:
                raise ValueError("Query is required")

            # Get from_time
            from_time = None
            from_time_str = data.get('fromTime')
            if from_time_str is not None:
                from_time = datetime.fromisoformat(from_time_str)
            
            # Get to_time
            to_time = None
            to_time_str = data.get('toTime')
            if to_time_str is not None:
                to_time = datetime.fromisoformat(to_time_str)
            
            # Perform search
            search_results = await self.__searcher_facade.search(
                tool=tool,
                query=query,
                from_time=from_time,
                to_time=to_time
            )
            
            # Convert search results to DTO format
            result_dtos: list[SearchResult] = [
                SearchResult(content=result['content'], url=result.get('url'))
                for result in search_results
            ]
            
            # Return response in CrawlerApiResponse format
            response: CrawlerApiResponse = CrawlerApiResponse(
                success=True,
                errorMessage='',
                result=result_dtos
            )
            return JSONResponse(content=response)
            
        except Exception as e:
            log.error(f"Error in search_endpoint: {e}", exc_info=True)
            error_response: CrawlerApiResponse = CrawlerApiResponse(
                success=False,
                errorMessage=str(e),
                result=[]
            )
            return JSONResponse(content=error_response)
    
    async def start(self):
        await self.__uvicorn_server.serve()
    
    async def stop(self):
        self.__uvicorn_server.handle_exit(signal.SIGTERM, None)
