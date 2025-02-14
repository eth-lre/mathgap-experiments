from typing import Dict, List
from mathgap.logicalforms.logicalform import LogicalForm, EntitySpec

from mathgap.properties import PropertyKey, PropertyTracker, PropertyType
from mathgap.expressions import Expr, Variable
from mathgap.trees.timing import VariableKey

class Transfer(LogicalForm):
    """ Expresses: <sender> gives <quantity> of <entity, attribute, unit> to <receiver> """
    def __init__(self, receiver: int, sender: int, quantity: Expr, entity: int, attribute: int, unit: int) -> None:
        self.receiver = receiver
        self.sender = sender
        self.quantity = quantity
        self.entity = entity
        self.attribute = attribute
        self.unit = unit

    @property
    def receiver_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.AGENT, self.receiver)

    @property
    def sender_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.AGENT, self.sender)

    @property
    def quantity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.QUANTITY, self.quantity)

    @property
    def entity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ENTITY, self.entity)

    @property
    def attribute_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ATTRIBUTE, self.attribute)

    @property
    def unit_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.UNIT, self.unit)
    
    def get_available_properties(self) -> Dict[str, PropertyKey|List[PropertyKey]]:
        available_properties = {}
        if self.receiver is not None: available_properties["receiver"] = self.receiver_prop
        if self.sender is not None: available_properties["sender"] = self.sender_prop
        if self.quantity is not None: available_properties["quantity"] = self.quantity_prop
        if self.entity is not None: available_properties["entity"] = self.entity_prop
        if self.attribute is not None: available_properties["attribute"] = self.attribute_prop
        if self.unit is not None: available_properties["unit"] = self.unit_prop
        return available_properties
    
    def get_entity_specs(self) -> List[EntitySpec]:
        return [EntitySpec(self.entity, attribute_id=self.attribute, unit_id=self.unit)]
    
    def get_variable_keys(self) -> List[VariableKey]:
        return [
            VariableKey((self.receiver_prop, self.entity_prop, self.attribute_prop, self.unit_prop)),
            VariableKey((self.sender_prop, self.entity_prop, self.attribute_prop, self.unit_prop))
        ]
    
    def get_quantities(self) -> List[Expr]:
        return [self.quantity]
    
    def make_axiom(self, property_tracker: PropertyTracker) -> None:
        self.quantity = Variable(property_tracker.request_key(PropertyType.QUANTITY))