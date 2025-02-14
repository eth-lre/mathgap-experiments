from typing import Dict, List
import random

from mathgap.trees.generators.policies.rulesamplingpolicy import RuleSamplingPolicy
from mathgap.trees.prooftree import ProofTree

from mathgap.logicalforms import LogicalForm, Comp, Container
from mathgap.trees.rules import InferenceRule, ContCompCompeqCont, ContCompCont
from mathgap.trees.generators.stoppingcriteria import Criterion, BranchDepthCriterion

class NonlinearPolicy(RuleSamplingPolicy):

    def get_probs(self, lf: LogicalForm, tree: ProofTree, rules: List[InferenceRule], stopping_criterion: Criterion) -> Dict[InferenceRule, float]:
        
        assert isinstance(stopping_criterion, BranchDepthCriterion)
        if isinstance(lf, Container):
            node = tree.nodes_by_lf[lf]
            if node.depth < stopping_criterion.required_depth - 1:
                # sample a compeq rule
                return {r: 1.0 for r in rules if isinstance(r, ContCompCompeqCont)}
            else:
                # sample a comp rule
                return {r: 1.0 for r in rules if isinstance(r, ContCompCont)}
        elif isinstance(lf, Comp):
            return {r: 1.0 / len(rules) for r in rules}
        else:
            AssertionError("neither comp nor cont")