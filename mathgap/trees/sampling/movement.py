from mathgap.trees.prooftree import ProofTree, TraversalOrder
from mathgap.trees.sampling.order import OrderSampler

from mathgap.problemsample import ProblemOrder

class FrontMovementOrderSampler(OrderSampler):
    
    def __init__(self, move_idx: int=0):
        """ 
            Initialize with the left-to-right index of the moved leaf node
        """
        self.move_idx = move_idx

    def sample_order(self, tree: ProofTree, seed: int = 14) -> ProblemOrder:
        # move_idx = 0 defaults to no movement
        assert 0 <= self.move_idx < len(tree.leaf_nodes)
        body = []
        for i, n in enumerate([n for n in tree.traverse(order=TraversalOrder.POST) if n.is_leaf]):
            if i == self.move_idx: moved_node = tree.id_by_node[n]
            else: body.append(tree.id_by_node[n])
        body = [moved_node] + body
        question = tree.id_by_node[tree.root_node]

        return ProblemOrder(body, [question])