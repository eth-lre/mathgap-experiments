from typing import Dict, List
from mathgap.properties import PropertyTracker
from mathgap.logicalforms.logicalform import LogicalForm, EntitySpec
from mathgap.logicalforms.comp import ComparisonType

from mathgap.properties import PropertyKey, PropertyType
from mathgap.expressions import Expr, Variable
from mathgap.trees.timing import VariableKey

class CompEq(LogicalForm):
    def __init__(self, subj_agent: int, subj_entity: int, subj_attribute: int, subj_unit: int, obj_agent: int, obj_entity: int, obj_attribute: int, obj_unit: int, comp_type: ComparisonType, other_subj_agent: int, other_subj_entity: int, other_subj_attribute: int, other_subj_unit: int, other_obj_agent: int, other_obj_entity: int, other_obj_attribute: int, other_obj_unit: int, other_comp_type: ComparisonType) -> None:
        self.subj_agent = subj_agent
        self.subj_entity = subj_entity
        self.subj_attribute = subj_attribute
        self.subj_unit = subj_unit
        self.obj_agent = obj_agent
        self.obj_entity = obj_entity
        self.obj_attribute = obj_attribute
        self.obj_unit = obj_unit
        self.comp_type = comp_type
        self.other_subj_agent = other_subj_agent
        self.other_subj_entity = other_subj_entity
        self.other_subj_attribute = other_subj_attribute
        self.other_subj_unit = other_subj_unit
        self.other_obj_agent = other_obj_agent
        self.other_obj_entity = other_obj_entity
        self.other_obj_attribute = other_obj_attribute
        self.other_obj_unit = other_obj_unit
        self.other_comp_type = other_comp_type

    @property
    def subj_agent_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.AGENT, self.subj_agent)

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
    def obj_agent_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.AGENT, self.obj_agent)

    @property
    def obj_entity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ENTITY, self.obj_entity)

    @property
    def obj_attribute_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ATTRIBUTE, self.obj_attribute)

    @property
    def obj_unit_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.UNIT, self.obj_unit)

    @property
    def comp_type_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.COMPARISON, self.comp_type)

    @property
    def other_subj_agent_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.AGENT, self.other_subj_agent)

    @property
    def other_subj_entity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ENTITY, self.other_subj_entity)

    @property
    def other_subj_attribute_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ATTRIBUTE, self.other_subj_attribute)

    @property
    def other_subj_unit_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.UNIT, self.other_subj_unit)

    @property
    def other_obj_agent_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.AGENT, self.other_obj_agent)

    @property
    def other_obj_entity_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ENTITY, self.other_obj_entity)

    @property
    def other_obj_attribute_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.ATTRIBUTE, self.other_obj_attribute)

    @property
    def other_obj_unit_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.UNIT, self.other_obj_unit)

    @property
    def other_comp_type_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.COMPARISON, self.other_comp_type)

    def get_available_properties(self) -> Dict[str, PropertyKey|List[PropertyKey]]:
        available_properties = {}
        if self.subj_agent is not None: available_properties["subj_agent"] = self.subj_agent_prop
        if self.subj_entity is not None: available_properties["subj_entity"] = self.subj_entity_prop
        if self.subj_attribute is not None: available_properties["subj_attribute"] = self.subj_attribute_prop
        if self.subj_unit is not None: available_properties["subj_unit"] = self.subj_unit_prop
        if self.obj_agent is not None: available_properties["obj_agent"] = self.obj_agent_prop
        if self.obj_entity is not None: available_properties["obj_entity"] = self.obj_entity_prop
        if self.obj_attribute is not None: available_properties["obj_attribute"] = self.obj_attribute_prop
        if self.obj_unit is not None: available_properties["obj_unit"] = self.obj_unit_prop
        if self.comp_type is not None: available_properties["comp_type"] = self.comp_type_prop
        if self.other_subj_agent is not None: available_properties["other_subj_agent"] = self.other_subj_agent_prop
        if self.other_subj_entity is not None: available_properties["other_subj_entity"] = self.other_subj_entity_prop
        if self.other_subj_attribute is not None: available_properties["other_subj_attribute"] = self.other_subj_attribute_prop
        if self.other_subj_unit is not None: available_properties["other_subj_unit"] = self.other_subj_unit_prop
        if self.other_obj_agent is not None: available_properties["other_obj_agent"] = self.other_obj_agent_prop
        if self.other_obj_entity is not None: available_properties["other_obj_entity"] = self.other_obj_entity_prop
        if self.other_obj_attribute is not None: available_properties["other_obj_attribute"] = self.other_obj_attribute_prop
        if self.other_obj_unit is not None: available_properties["other_obj_unit"] = self.other_obj_unit_prop
        if self.other_comp_type is not None: available_properties["other_comp_type"] = self.other_comp_type_prop
        return available_properties
    
    def get_entity_specs(self) -> List[EntitySpec]:
        return [
            EntitySpec(self.subj_entity, attribute_id=self.subj_attribute, unit_id=self.subj_unit),
            EntitySpec(self.obj_entity, attribute_id=self.obj_attribute, unit_id=self.obj_unit),
            EntitySpec(self.other_subj_entity, attribute_id=self.other_subj_attribute, unit_id=self.other_subj_unit),
            EntitySpec(self.other_obj_entity, attribute_id=self.other_obj_attribute, unit_id=self.other_obj_unit),            
        ]
    
    def get_variable_keys(self) -> List[VariableKey]:
        return [
            VariableKey((self.subj_agent_prop, self.subj_entity_prop, self.subj_attribute_prop, self.subj_unit_prop)),
            VariableKey((self.obj_agent_prop, self.obj_entity_prop, self.obj_attribute_prop, self.obj_unit_prop)),
            VariableKey((self.other_subj_agent_prop, self.other_subj_entity_prop, self.other_subj_attribute_prop, self.other_subj_unit_prop)),
            VariableKey((self.other_obj_agent_prop, self.other_obj_entity_prop, self.other_obj_attribute_prop, self.other_obj_unit_prop))
        ]