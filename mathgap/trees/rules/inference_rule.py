from typing import Any, Dict, List, TypeAlias
from mathgap.logicalforms import LogicalForm
from mathgap.trees.timing import VariableTimes

Parametrization: TypeAlias = Dict[str, Any]

class InferenceRule:
    def __init__(self) -> None:
        pass

    def is_reverse_applicable(self, conclusion: LogicalForm, tree) -> bool:
        """ 
            Returns true, if this rule could have been used to arrive at a conclusion
            - conclusion: the logical form that is attempted to be concluded in a single step with this logical form
            - context: all the events that are happening in the current time-group
        """
        ...

    def assert_valid_parametrization(self, conclusion: LogicalForm, parametrization: Parametrization):
        """ Assert that the parametrization is valid, given the parameters of the conclusion """
        ...

    # TODO: if necessary, method that lists all valid sets of parametrizations for automatic fill-in

    def apply_reverse(self, conclusion: LogicalForm, parametrization: Parametrization) -> List[LogicalForm]:
        """ 
            Returns premises that could have lead to the specified conclusion. 
            The parametrization defines how the premises are parameterized.
        """
        ...

    def infer_knowledge(self, premises: List[LogicalForm], conclusion: LogicalForm):
        """ 
            Updates the conclusion (in-place) with all knowledge that can be inferred from the premises.
        """
        ...

    def reverse_infer_variable_times(self, premises: List[LogicalForm], conclusion: LogicalForm, conclusion_variable_times: VariableTimes) -> Dict[LogicalForm, VariableTimes]:
        """
            Infers the variable-times for all premises given those of the conclusion
        """
        # NOTE: needed during construction of the tree to guarantee proper ordering when appending new nodes
        variable_times_by_premise = {}

        conclusion_vks = set(conclusion.get_variable_keys())
        for premise in premises:
            premise_vts = VariableTimes({})
            premise_vks = premise.get_variable_keys()
            for vk in premise_vks:
                if vk in conclusion_vks:
                    # conclusion is copied
                    premise_vts[vk] = conclusion_variable_times[vk]
                else:
                    # rest is newly introduced
                    premise_vts[vk] = 0

            variable_times_by_premise[premise] = premise_vts
        return variable_times_by_premise

    def infer_variable_times(self, premises: List[LogicalForm], conclusion: LogicalForm, premises_variable_times: Dict[LogicalForm, VariableTimes]) -> VariableTimes:
        """
            Infers the variable-times for the conclusion given those of the premises
        """
        vts = VariableTimes({})
        all_conflicts = vts.merge_all([premises_variable_times[p] for p in premises])
        # TODO: sanity checks on conflicts
        return vts
    
    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)
