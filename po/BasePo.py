from dataclasses import dataclass
from typing import Optional

@dataclass(eq=False)
class BasePo:
    """Base class for all persistent objects in the system"""
    id: Optional[int]
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__) \
            or self.id is None or other.id is None :
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __post_init__(self):
        if not hasattr(self, 'id'):
            self.id = None
