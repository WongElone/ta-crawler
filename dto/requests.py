from typing import NotRequired
from datetime import datetime
from typing_extensions import TypedDict

class DoSearchRequest(TypedDict, total=False):
    """
    Request DTO for crawler search endpoint
    Matches DoSearchRequestDto.java in analyst module
    """
    tool: str  # SearchTool enum value
    query: str  # Built search query string
    fromTime: NotRequired[str]  # ISO format datetime string
    toTime: NotRequired[str]  # ISO format datetime string
