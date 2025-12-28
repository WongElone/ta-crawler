from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import hashlib

from . import BasePo
from ..const import ArticleSource, ArticleSite

@dataclass(eq=False)
class ArticlePo(BasePo):
    source: ArticleSource
    site: ArticleSite
    title: str
    title_md5: str
    content: str
    url: str
    create_time: datetime = datetime.now(timezone.utc)
    publish_time: datetime = datetime.now(timezone.utc)
    
    def __post_init__(self):
        super().__post_init__()
        # Auto-generate title_md5 if not provided
        if not hasattr(self, 'title_md5') or not self.title_md5:
            self.title_md5 = hashlib.md5(self.title.encode('utf-8')).hexdigest()
