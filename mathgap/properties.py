from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from mathgap.expressions import Expr

class PropertyType(Enum):
    AGENT = "agent"
    ENTITY = "entity"
    ATTRIBUTE = "attribute"
    UNIT = "unit"
    QUANTITY = "quantity"
    COMPARISON = "comparison"

class PropertyKey(BaseModel):
    property_type: PropertyType
    identifier: Optional[int|Expr]

    def __init__(self, property_type: PropertyType, identifier: None|int|Expr):
        super().__init__(property_type=property_type, identifier=identifier)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PropertyKey): return False
        return self.property_type == other.property_type and self.identifier == other.identifier
    
    def __hash__(self) -> int:
        return hash((self.property_type.value, self.identifier))
    
    def __str__(self) -> str:
        return f"{self.property_type.value}_{self.identifier}"
    
    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)

class PropertyTracker:
    def __init__(self) -> None:
        self.used_ids = {t: [] for t in list(PropertyType)}
    
    def request_id(self, property_type: PropertyType) -> int:
        """ Request a free id for a property of a type """
        next_free_id = max(0, 0, *self.used_ids[property_type]) + 1
        self.used_ids[property_type].append(next_free_id)
        return next_free_id
    
    def request_key(self, property_type: PropertyType) -> PropertyKey:
        """ Request a free id for a property of a type and wrap it as a key of said type """
        identifier = self.request_id(property_type)
        return PropertyKey(property_type, identifier)
    
    def get_by_type(self, property_type: PropertyType) -> List[int]:
        """ Get all properties of the specified type """
        return self.used_ids.get(property_type, [])

