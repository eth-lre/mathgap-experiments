# CONCLUSION: Container
# PREMISES: Container, Comparison

# VARIABLE-TIMES: 
# - container(a.e at t1), comparison(a.e at {t1}, other.e at 0)
# - conclusion(a.e at t1)

# INPUTS:
# - both of them, with one of them matching the conclusion (attributes and units can ofc be None):
#   - subj_agent, subj_entity, subj_attribute, subj_unit
#   - obj_agent, obj_entity, obj_attribute, obj_unit
# - type of comparison

from typing import List, Dict
from mathgap.trees.rules.inference_rule import InferenceRule, Parametrization

from mathgap.logicalforms import LogicalForm, Container, Comp, ComparisonType
from mathgap.expressions import Addition, Fraction, Subtraction, Product

class ContCompCont(InferenceRule):
    """ 
        Informal:
            We know how many entities one agent has, and we know how many entities that agent has compared to the other, 
            thus we know how many entities the other has.            
    """
    def is_reverse_applicable(self, conclusion: LogicalForm, tree) -> bool:
        if isinstance(conclusion, Container): return True
        # NOTE: we don't do sanity checks on the tree because the rule is expected to introduce a new agent.entity
        #       so, the tree would have to be invalid beforehand already
        return False
    
    def assert_valid_parametrization(self, conclusion: LogicalForm, parametrization: Parametrization):
        assert isinstance(conclusion, Container), f"Conclusion is expected to be a Container! Got {type(conclusion)} instead."
        assert "comp_type" in parametrization and isinstance(parametrization["comp_type"], ComparisonType), "Requires comp_type of ComparisonType."
        
        assert "subj_agent" in parametrization and "subj_entity" in parametrization and "subj_attribute" in parametrization and "subj_unit" in parametrization,\
            f"Requires a parametrization of subj_agent, subj_entity, subj_attribute, subj_unit"
        assert "obj_agent" in parametrization and "obj_entity" in parametrization and "obj_attribute" in parametrization and "obj_unit" in parametrization,\
            f"Requires a parametrization of obj_agent, obj_entity, obj_attribute, obj_unit"

        subj = (parametrization["subj_agent"], parametrization["subj_entity"], parametrization["subj_attribute"], parametrization["subj_unit"])
        obj = (parametrization["obj_agent"], parametrization["obj_entity"], parametrization["obj_attribute"], parametrization["obj_unit"])
        concl = (conclusion.agent, conclusion.entity, conclusion.attribute, conclusion.unit)

        assert (subj == concl) != (obj == concl), f"Exactly one of subj ({subj}) or obj ({obj}) must match the conclusion ({concl})."

        ignored_keys = set(parametrization.keys()).difference(set(["comp_type", "subj_agent", "subj_entity", "subj_attribute", "subj_unit", "obj_agent", "obj_entity", "obj_attribute", "obj_unit"]))
        assert len(ignored_keys) == 0, f"Keys {ignored_keys} are provided but are not allowed."


    def apply_reverse(self, conclusion: LogicalForm, parametrization: Parametrization) -> List[LogicalForm]:
        self.assert_valid_parametrization(conclusion, parametrization)
        assert isinstance(conclusion, Container), "Conclusion is expected to be a Container"

        comp_type = parametrization["comp_type"]

        subj_agent = parametrization["subj_agent"]
        subj_entity = parametrization["subj_entity"]
        subj_attribute = parametrization["subj_attribute"]
        subj_unit = parametrization["subj_unit"]

        obj_agent = parametrization["obj_agent"]
        obj_entity = parametrization["obj_entity"]
        obj_attribute = parametrization["obj_attribute"]
        obj_unit = parametrization["obj_unit"]

        container_agent, container_entity, container_attribute, container_unit = (subj_agent, subj_entity, subj_attribute, subj_unit)\
            if obj_agent == conclusion.agent else (obj_agent, obj_entity, obj_attribute, obj_unit)

        prem_container = Container(agent=container_agent, quantity=None, entity=container_entity, attribute=container_attribute, unit=container_unit)        
        prem_comp = Comp(subj_agent=subj_agent, obj_agent=obj_agent, 
                         comp_type=comp_type, quantity=None, 
                         subj_entity=subj_entity, subj_attribute=subj_attribute, subj_unit=subj_unit, 
                         obj_entity=obj_entity, obj_attribute=obj_attribute, obj_unit=obj_unit)
        
        # TODO: could flip the order (all possible orders are deducible by the time-dag)
        return [prem_container, prem_comp]
        
    def infer_knowledge(self, premises: List[LogicalForm], conclusion: LogicalForm):
        container, comp = premises
        assert isinstance(container, Container), "First premise is expected to be a Container"
        assert isinstance(comp, Comp), "Second premise is expected to be a Comparison"
        assert isinstance(conclusion, Container), "Conclusion is expected to be a Container"
        assert container.quantity is not None, "Container quantity cannot be None"
        assert comp.quantity is not None, "Comparison quantity cannot be None"

        if comp.obj_agent == conclusion.agent:
            # subj has + subj compared to obj => obj has 
            assert comp.subj_agent == container.agent and comp.subj_entity == container.entity and comp.subj_attribute == container.attribute,\
                "Expects the container to be about the subj of the comparison"
            assert comp.obj_agent == conclusion.agent and comp.obj_entity == conclusion.entity and comp.obj_attribute == conclusion.attribute,\
                "Expects the conclusion to be about the obj of the comparison"
            
            if comp.comp_type == ComparisonType.MORE_THAN:
                conclusion.quantity = Subtraction(container.quantity, comp.quantity)
            elif comp.comp_type == ComparisonType.LESS_THAN:
                conclusion.quantity = Addition(container.quantity, comp.quantity)
            elif comp.comp_type == ComparisonType.TIMES_AS_MANY:
                conclusion.quantity = Fraction(container.quantity, comp.quantity)
            elif comp.comp_type == ComparisonType.FRACTION_OF:
                conclusion.quantity = Product(container.quantity, comp.quantity)

        elif comp.subj_agent == conclusion.agent:
            # obj has + subj compared to obj => subj has
            assert comp.obj_agent == container.agent and comp.obj_entity == container.entity and comp.obj_attribute == container.attribute,\
                "Expects the container to be about the obj of the comparison"
            assert comp.subj_agent == conclusion.agent and comp.subj_entity == conclusion.entity and comp.subj_attribute == conclusion.attribute,\
                "Expects the conclusion to be about the subj of the comparison"
            
            if comp.comp_type == ComparisonType.MORE_THAN:
                conclusion.quantity = Addition(container.quantity, comp.quantity)
            elif comp.comp_type == ComparisonType.LESS_THAN:
                conclusion.quantity = Subtraction(container.quantity, comp.quantity)
            elif comp.comp_type == ComparisonType.TIMES_AS_MANY:
                conclusion.quantity = Product(container.quantity, comp.quantity)
            elif comp.comp_type == ComparisonType.FRACTION_OF:
                conclusion.quantity = Fraction(container.quantity, comp.quantity)

        assert conclusion.quantity is not None, f"Conclusion.quantity must be set after inferring knowledge! comp.subj_agent={comp.subj_agent}, comp.obj_agent={comp.obj_agent}, conclusion.agent={conclusion.agent}, comp.comp_type={comp.comp_type}" 