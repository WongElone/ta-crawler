from typing import Optional
from typing_extensions import TypedDict

class SearchResultDict(TypedDict):
    """
    Dictionary format for search results returned by searchers
    """
    content: str
    url: Optional[str]
