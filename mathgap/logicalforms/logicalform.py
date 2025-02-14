from typing import Any, Dict, List
from mathgap.properties import PropertyKey, PropertyTracker
from mathgap.expressions import Expr
from mathgap.trees.timing import VariableKey

class EntitySpec:
    def __init__(self, entity_id: int, part_entity_ids: int = [], attribute_id: int = None, unit_id: int = None) -> None:
        self.entity_id = entity_id
        self.part_entity_ids = part_entity_ids
        self.attribute_id = attribute_id
        self.unit_id = unit_id

    @property
    def has_unit(self) -> bool:
        return self.unit_id is not None
    
    @property
    def has_part_entities(self) -> bool:
        return len(self.part_entity_ids) > 0
    
    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)

class LogicalForm: 
    def get_available_properties(self) -> Dict[str, PropertyKey|List[PropertyKey]]:
        return {}

    def get_entity_specs(self) -> List[EntitySpec]:
        """ 
            Returns specifics about each entity of this logical form. 
            This information can for example be used to infer which entity is used in combination with which unit.
        """
        return []
    
    def get_variable_keys(self) -> List[VariableKey]:
        """ Gets all the variable accesses that this logical form implies (i.e. on agent.entity) """
        ...

    def __setitem__(self, property_name: str, value: Any) -> None:
        setattr(self, property_name, value)

    def __getitem__(self, property_name: str) -> Any:
        return getattr(self, property_name)
    
    def make_axiom(self, property_tracker: PropertyTracker) -> None:
        """ 
            Converts this logical form into an axiom.
            I.e. this could mean that certain properties are assigned variable names.
        """
        pass

    def get_quantities(self) -> List[Expr]: 
        return []
    
    def to_inst_str(self, instantiation) -> str:
        """ Returns an instantiated string representation of this logical form """
        from mathgap.instantiate import Instantiation
        assert isinstance(instantiation, Instantiation), f"Expecting instantiation to be of type Instantiation but got {type(instantiation)}"
        
        prop_texts = []
        for pname,pkey in self.get_available_properties().items():
            if isinstance(pkey, list):
                prop_texts.append(f"{pname}=[{', '.join(str(instantiation[k]) for k in pkey)}]")
            else:
                if isinstance(pkey.identifier, Expr):
                    prop_texts.append(f"{pname}={pkey.identifier.to_str(instantiation, depth=1)}")
                else:
                    if pkey in instantiation:
                        prop_texts.append(f"{pname}={instantiation[pkey]}")
                    else:
                        prop_texts.append(f"{pname}={pkey}")
                
        return f"{type(self).__name__}({', '.join(prop_texts)})"

    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)