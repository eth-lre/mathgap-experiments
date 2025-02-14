from mathgap.trees.generators.stoppingcriteria.criterion import Criterion

from mathgap.trees.prooftree import ProofTree, TreeNode

class BranchDepthCriterion(Criterion):
    """ Limits the depth of each extendable tree-branch to be exactly the required-depth """
    def __init__(self, required_depth: int) -> None:
        self.required_depth = required_depth

    def satisfied(self, node: TreeNode, tree: ProofTree) -> bool:
        if node.depth > self.required_depth: 
            print("Warning: Depth of branch already exceeding the required depth during generation!")
        return node.depth >= self.required_depth
    
class TreeDepthCriterion(Criterion):
    """ Satsified as soon as one branch of the tree reaches a certain depth """
    def __init__(self, required_depth: int) -> None:
        self.required_depth = required_depth

    def satisfied(self, node: TreeNode, tree: ProofTree) -> bool:
        if tree.depth > self.required_depth: 
            print("Warning: Depth of branch already exceeding the required depth during generation!")
        return tree.depth >= self.required_depth