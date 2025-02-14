from typing import Dict, List
from mathgap.logicalforms.logicalform import LogicalForm, EntitySpec

from mathgap.properties import PropertyKey, PropertyType, PropertyTracker
from mathgap.expressions import Expr, Variable
from mathgap.trees.timing import VariableKey

class PartWhole(LogicalForm):
    """ Expresses: everybody together has <quantity> of <whole_entity, attribute, unit> """
    def __init__(self, quantity: Expr, whole_entity: int, whole_attribute: int, whole_unit: int, part_agents: List[int], part_entities: List[int], part_attributes: List[int], part_units: List[int]) -> None:
        self.quantity = quantity
        self.whole_entity = whole_entity
        self.whole_attribute = whole_attribute
        self.whole_unit = whole_unit
        self.part_agents = part_agents
        self.part_entities = part_entities
        self.part_attributes = part_attributes
        self.part_units = part_units

    @property
    def quantity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.QUANTITY, self.quantity)
    
    @property
    def whole_entity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ENTITY, self.whole_entity)
    
    @property
    def part_agents_props(self) -> List[PropertyKey]:
        return [PropertyKey(PropertyType.AGENT, a) for a in self.part_agents]
    
    @property
    def whole_attribute_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ATTRIBUTE, self.whole_attribute)
    
    @property
    def whole_unit_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.UNIT, self.whole_unit)
    
    def get_available_properties(self) -> Dict[str, PropertyKey|List[PropertyKey]]:
        available_properties = {}
        if self.quantity is not None: available_properties["quantity"] = self.quantity_prop
        if self.whole_entity is not None: available_properties["whole_entity"] = self.whole_entity_prop
        if self.whole_attribute is not None: available_properties["whole_attribute"] = self.whole_attribute_prop
        if self.whole_unit is not None: available_properties["whole_unit"] = self.whole_unit_prop
        if self.part_agents is not None: available_properties["part_agents"] = self.part_agents_props
        return available_properties
    
    def get_entity_specs(self) -> List[EntitySpec]:
        return [EntitySpec(self.whole_entity, part_entity_ids=self.part_entities, attribute_id=self.whole_attribute, unit_id=self.whole_unit)] 
    
    def get_variable_keys(self) -> List[VariableKey]:
        # TODO: actually this also introduces a joint-key over all involved variables
        return [
            VariableKey([PropertyKey(PropertyType.AGENT, ag), PropertyKey(PropertyType.ENTITY, en), PropertyKey(PropertyType.ATTRIBUTE, at), PropertyKey(PropertyType.UNIT, un)]) 
            for ag,en,at,un in zip(self.part_agents, self.part_entities, self.part_attributes, self.part_units)
        ]
    
    def get_quantities(self) -> List[Expr]:
        return [self.quantity]

    def make_axiom(self, property_tracker: PropertyTracker) -> None:
        self.quantity = Variable(property_tracker.request_key(PropertyType.QUANTITY))

    