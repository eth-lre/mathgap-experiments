# CONCLUSION: PartWhole
# PREMISES: Container, ..., Container

# VARIABLE-TIMES: 
# - container(1_agent.1_entity at 0), ..., container(n_agent.n_entity at 0)
# - conclusion(1_agent.1_entity at 0, n_agent.n_entity at 0)

# INPUTS:
# None
from typing import List, Dict
from mathgap.trees.rules.inference_rule import InferenceRule, Parametrization

from mathgap.logicalforms import LogicalForm, Container, PartWhole
from mathgap.expressions import Sum

class ContPartWhole(InferenceRule):
    """ 
        Informal:
            We know how many entities one agent has, and we know how many entities that agent has compared to the other, 
            thus we know how many entities the other has.            
    """
    def is_reverse_applicable(self, conclusion: LogicalForm, tree) -> bool:
        if isinstance(conclusion, PartWhole): return True
        # NOTE: we don't do sanity checks on the tree because agent.entity is already known from the partwhole
        #       so, the tree would have to be invalid beforehand already
        return False
    
    def assert_valid_parametrization(self, conclusion: LogicalForm, parametrization: Parametrization):
        assert isinstance(conclusion, PartWhole), f"Conclusion is expected to be a PartWhole! Got {type(conclusion)} instead."
        assert len(parametrization.keys()) == 0, f"Rule {type(self).__name__} requires no parameters but {parametrization} was provided!"

    def apply_reverse(self, conclusion: LogicalForm, parametrization: Parametrization) -> List[LogicalForm]:
        self.assert_valid_parametrization(conclusion, parametrization)
        assert isinstance(conclusion, PartWhole), "Conclusion is expected to be a PartWhole"
        
        premises: List[Container] = []
        for agent_i, entity_i, attribute_i, unit_i in zip(conclusion.part_agents, conclusion.part_entities, conclusion.part_attributes, conclusion.part_units):
            premises.append(Container(agent=agent_i, quantity=None, entity=entity_i, attribute=attribute_i, unit=unit_i))
        
        return premises

    def infer_knowledge(self, premises: List[Container], conclusion: LogicalForm):
        assert all([isinstance(c, Container) for c in premises]), "All premises are expected to be a Container"
        assert isinstance(conclusion, PartWhole), "Conclusion is expected to be a PartWhole"
        assert all(c.quantity is not None for c in premises), "No containers quantity cannot be None"

        conclusion.quantity = Sum([c.quantity for c in premises])

        assert conclusion.quantity is not None, f"Conclusion.quantity must be set after inferring knowledge!"