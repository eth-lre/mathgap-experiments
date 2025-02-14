from mathgap.trees.prooftree import ProofTree, TreeNode

class Criterion:
    def satisfied(self, node: TreeNode, tree: ProofTree) -> bool:
        """ Return true if the stopping criteria for this node is satisfied """
        ...