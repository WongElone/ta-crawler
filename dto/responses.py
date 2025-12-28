from typing import TypeVar, Generic, Optional
from typing_extensions import TypedDict

T = TypeVar('T')

class SearchResult(TypedDict):
    """
    Search result DTO returned from crawler
    Matches SearchResultDto.java in analyst module
    """
    content: str  # Search result content
    url: Optional[str]  # URL of the search result (optional)


class CrawlerApiResponse(TypedDict, Generic[T]):
    """
    Generic response wrapper for crawler API endpoints
    All crawler API responses follow this format: success, errorMessage, result
    Matches CrawlerApiResponse.java in analyst module
    """
    success: bool  # Indicates if the API call was successful
    errorMessage: str  # Error message if the call failed
    result: T  # The result data
