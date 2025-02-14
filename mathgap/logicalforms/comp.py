from typing import Dict, List
from enum import Enum
from mathgap.properties import PropertyTracker
from mathgap.logicalforms.logicalform import LogicalForm, EntitySpec

from mathgap.properties import PropertyKey, PropertyType
from mathgap.expressions import Expr, Variable
from mathgap.trees.timing import VariableKey

class ComparisonType(Enum):
    MORE_THAN = "more"
    LESS_THAN = "less"
    TIMES_AS_MANY = "times"
    FRACTION_OF = "dividedby"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)
    
ALL_COMP_TYPES = [ComparisonType.MORE_THAN, ComparisonType.LESS_THAN, ComparisonType.TIMES_AS_MANY, ComparisonType.FRACTION_OF]
ADDITIVE_COMP_TYPES = [ComparisonType.MORE_THAN, ComparisonType.LESS_THAN]
ALL_COMP_TYPES_EXCEPT_DIVISION = [ComparisonType.MORE_THAN, ComparisonType.LESS_THAN, ComparisonType.TIMES_AS_MANY]

class Comp(LogicalForm):
    """ 
        Puts in relation the quantity of the subject with the quantity of the subject
        I.e. Subj. has 5 more apples than obj has peaches.
    """
    def __init__(self, subj_agent: int, obj_agent: int, 
                 comp_type: ComparisonType, quantity: Expr, 
                 subj_entity: int, subj_attribute: int, subj_unit: int, 
                 obj_entity: int, obj_attribute: int, obj_unit: int) -> None:
        self.subj_agent = subj_agent
        self.obj_agent = obj_agent
        self.comp_type = comp_type
        self.quantity = quantity
        self.subj_entity = subj_entity
        self.subj_attribute = subj_attribute
        self.subj_unit = subj_unit
        self.obj_entity = obj_entity
        self.obj_attribute = obj_attribute
        self.obj_unit = obj_unit

    @property
    def subj_agent_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.AGENT, self.subj_agent)

    @property
    def obj_agent_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.AGENT, self.obj_agent)

    @property
    def comparison_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.COMPARISON, self.comp_type)

    @property
    def quantity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.QUANTITY, self.quantity)

    @property
    def subj_entity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ENTITY, self.subj_entity)

    @property
    def subj_attribute_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ATTRIBUTE, self.subj_attribute)

    @property
    def subj_unit_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.UNIT, self.subj_unit)
    
    @property
    def obj_entity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ENTITY, self.obj_entity)

    @property
    def obj_attribute_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ATTRIBUTE, self.obj_attribute)

    @property
    def obj_unit_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.UNIT, self.obj_unit)
    
    def get_available_properties(self) -> Dict[str, PropertyKey|List[PropertyKey]]:
        available_properties = {}
        if self.subj_agent is not None: available_properties["subj_agent"] = self.subj_agent_prop
        if self.obj_agent is not None: available_properties["obj_agent"] = self.obj_agent_prop
        if self.comp_type is not None: available_properties["comparison"] = self.comparison_prop
        if self.quantity is not None: available_properties["quantity"] = self.quantity_prop
        if self.subj_entity is not None: available_properties["subj_entity"] = self.subj_entity_prop
        if self.subj_attribute is not None: available_properties["subj_attribute"] = self.subj_attribute_prop
        if self.subj_unit is not None: available_properties["subj_unit"] = self.subj_unit_prop
        if self.obj_entity is not None: available_properties["obj_entity"] = self.obj_entity_prop
        if self.obj_attribute is not None: available_properties["obj_attribute"] = self.obj_attribute_prop
        if self.obj_unit is not None: available_properties["obj_unit"] = self.obj_unit_prop
        return available_properties
    
    def get_entity_specs(self) -> List[EntitySpec]:
        return [
            EntitySpec(self.subj_entity, attribute_id=self.subj_attribute, unit_id=self.subj_unit),
            EntitySpec(self.obj_entity, attribute_id=self.obj_attribute, unit_id=self.obj_unit)
        ]
    
    def get_variable_keys(self) -> List[VariableKey]:
        return [
            VariableKey((self.subj_agent_prop, self.subj_entity_prop, self.subj_attribute_prop, self.subj_unit_prop)),
            VariableKey((self.obj_agent_prop, self.obj_entity_prop, self.obj_attribute_prop, self.obj_unit_prop))
        ]
    
    def get_quantities(self) -> List[Expr]:
        return [self.quantity]

    def make_axiom(self, property_tracker: PropertyTracker) -> None:
        self.quantity = Variable(property_tracker.request_key(PropertyType.QUANTITY))