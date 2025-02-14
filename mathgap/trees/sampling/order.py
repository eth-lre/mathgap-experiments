from mathgap.trees.prooftree import ProofTree

from mathgap.problemsample import ProblemOrder

class OrderSampler:
    def sample_order(self, tree: ProofTree, seed: int = 14) -> ProblemOrder:
        ...