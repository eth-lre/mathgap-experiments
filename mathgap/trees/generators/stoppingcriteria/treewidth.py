from mathgap.trees.generators.stoppingcriteria.criterion import Criterion

from mathgap.trees.prooftree import ProofTree, TreeNode

class TreeWidthCriterion(Criterion):
    """ 
        Limits the width of the tree to be close to the desired width

        NOTE: we cannot guarantee the exact width without restricing the generation because
        reverse-applying an inference rule might add more than 1 new premise (but it might
        be the only branch we can extend on.)
    """
    def __init__(self, preferred_width: int) -> None:
        self.preferred_width = preferred_width

    def satisfied(self, node: TreeNode, tree: ProofTree) -> bool:
        tree_width = len(tree.leaf_nodes) 
        if tree_width > self.preferred_width: 
            print(f"Warning: Width of tree already exceeding the required width during generation by {tree_width - self.preferred_width}!")
        return tree_width >= self.preferred_width