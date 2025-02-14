from typing import List
from mathgap.trees.generators.stoppingcriteria.criterion import Criterion

from mathgap.trees.prooftree import ProofTree, TreeNode

class OrCriterion(Criterion):
    """ Satisfied if any of its sub-criteria is satisfied"""
    def __init__(self, subcriteria: List[Criterion]) -> None:
        self.subcriteria: List[Criterion] = subcriteria

    def satisfied(self, node: TreeNode, tree: ProofTree) -> bool:
        return any([s.satisfied(node, tree) for s in self.subcriteria])