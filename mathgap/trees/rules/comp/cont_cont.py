# CONCLUSION: Comparison
# PREMISES: Container, Container

# VARIABLE-TIMES: 
# - container(a.e at t1), container(b.e at t2)
# - comparison(a.e at t1, b.e at t2)

# INPUTS: None

from typing import List, Dict
from mathgap.trees.rules.inference_rule import InferenceRule, Parametrization

from mathgap.logicalforms import LogicalForm, Container, Comp, ComparisonType
from mathgap.expressions import Fraction, Subtraction
from mathgap.trees.timing import VariableTimes, VariableKey

class ContContComp(InferenceRule):
    """
        Informal:
            We know how many one agent has, 
            and we know how many another agent has, 
            thus we know how one agent compares to the other.
            
            Note: This does not allow us to say anything about the total of either agent, except if it directly involves the total.
    """
    def is_reverse_applicable(self, conclusion: LogicalForm, tree) -> bool:
        if not isinstance(conclusion, Comp): return False
        # the tree must no contain a write (e.g. container) to either one of the two agent.entities involved in the comp
        # from mathgap.trees import ProofTree
        # tree: ProofTree = tree
        vts = tree.times_by_node[tree.nodes_by_lf[conclusion]]
        for vk in conclusion.get_variable_keys():
            for vt in vts[vk]:
                if tree.has_write_at_time(vk, vt): return False
        return True

    def assert_valid_parametrization(self, conclusion: LogicalForm, parametrization: Parametrization):
        assert isinstance(conclusion, Comp), f"Conclusion is expected to be a Comparison! Got {type(conclusion)} instead."
        assert len(parametrization.keys()) == 0, f"Rule {type(self).__name__} requires no parameters but {parametrization} was provided!"

    def apply_reverse(self, conclusion: LogicalForm, parametrization: Parametrization) -> List[LogicalForm]:
        self.assert_valid_parametrization(conclusion, parametrization)
        assert isinstance(conclusion, Comp), "Conclusion is expected to be a Comparison"

        subj_agent = conclusion.subj_agent
        subj_entity = conclusion.subj_entity
        subj_attribute = conclusion.subj_attribute
        subj_unit = conclusion.subj_unit

        obj_agent = conclusion.obj_agent
        obj_entity = conclusion.obj_entity
        obj_attribute = conclusion.obj_attribute
        obj_unit = conclusion.obj_unit

        prem_subj_container = Container(agent=subj_agent, quantity=None,
                                        entity=subj_entity, attribute=subj_attribute, unit=subj_unit)
        prem_obj_container = Container(agent=obj_agent, quantity=None,
                                       entity=obj_entity, attribute=obj_attribute, unit=obj_unit)
    
        # TODO: could flip the order (all possible orders are deducible by the time-dag)
        return [prem_subj_container, prem_obj_container]

    def infer_knowledge(self, premises: List[LogicalForm], conclusion: LogicalForm):
        container1, container2 = premises
        assert isinstance(container1, Container), "First premise is expected to be a Container"
        assert isinstance(container2, Container), "Second premise is expected to be a Container"
        assert isinstance(conclusion, Comp), "Conclusion is expected to be a Comparison"
        assert container1.quantity is not None, "First container quantity cannot be None"
        assert container2.quantity is not None, "Second container quantity cannot be None"

        if container1.agent == conclusion.subj_agent:
            subj_container = container1
            obj_container = container2
        else:
            obj_container = container1
            subj_container = container2

        if conclusion.comp_type == ComparisonType.MORE_THAN:
            conclusion.quantity = Subtraction(subj_container.quantity, obj_container.quantity)
        elif conclusion.comp_type == ComparisonType.LESS_THAN:
            conclusion.quantity = Subtraction(obj_container.quantity, subj_container.quantity)
        elif conclusion.comp_type == ComparisonType.TIMES_AS_MANY:
            conclusion.quantity = Fraction(subj_container.quantity, obj_container.quantity)
        elif conclusion.comp_type == ComparisonType.FRACTION_OF:
            conclusion.quantity = Fraction(obj_container.quantity, subj_container.quantity)

        assert conclusion.quantity is not None, f"Conclusion.quantity must be set after inferring knowledge! conclusion.comp_type={conclusion.comp_type}"