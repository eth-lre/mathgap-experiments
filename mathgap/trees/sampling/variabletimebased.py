import random

from mathgap.trees.prooftree import ProofTree, TraversalOrder
from mathgap.trees.sampling.order import OrderSampler

from mathgap.problemsample import ProblemOrder


class VariableTimeBasedSampler(OrderSampler):
    """ Samples the tree in a way, where variable-times are monotonically increasing and all children are always visited before their parent """    
    def sample_order(self, tree: ProofTree, seed: int = 14) -> ProblemOrder:
        body = [tree.id_by_node[n] for n in tree.traverse(TraversalOrder.TIME, seed=seed) if n.is_leaf]
        question = tree.id_by_node[tree.root_node]

        return ProblemOrder(body, [question])

    

