from typing import Dict, List
import random

from mathgap.trees.prooftree import ProofTree
from mathgap.trees.rules import InferenceRule
from mathgap.logicalforms import LogicalForm
from mathgap.trees.generators.stoppingcriteria import Criterion

class RuleSamplingPolicy:
    def get_probs(self, lf: LogicalForm, tree: ProofTree, rules: List[InferenceRule], stopping_criterion: Criterion) -> Dict[InferenceRule, float]:
        """ Returns the probabilities with which each rule should be selected for some logical form of a tree """
        ...

    def sample(self, lf: LogicalForm, tree: ProofTree, rules: List[InferenceRule], stopping_criterion: Criterion) -> InferenceRule | None:
        """ 
            Samples an inference rule by establishing which rules are applicable to extend on lf,
            and then choosing a rule according to its probability.
        """
        applicable_rules = [r for r in rules if r.is_reverse_applicable(lf, tree)] 
        
        if len(applicable_rules) == 0: return None

        rules_and_probs = self.get_probs(lf, tree, applicable_rules, stopping_criterion)
        return random.choices(list(rules_and_probs.keys()), weights=list(rules_and_probs.values()), k=1)[0]