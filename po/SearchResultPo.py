from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import hashlib

from . import BasePo
from ..const import SearchTool

@dataclass(eq=False)
class SearchResultPo(BasePo):
    strategy_class_name: str
    query: str
    tool: SearchTool
    content: str
    content_md5: str
    url: Optional[str] = None
    create_time: datetime = datetime.now(timezone.utc)
    
    def __post_init__(self):
        super().__post_init__()
        # Auto-generate content_md5 if not provided
        if not hasattr(self, 'content_md5') or not self.content_md5:
            self.content_md5 = hashlib.md5(self.content.encode('utf-8')).hexdigest()
