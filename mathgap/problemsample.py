from typing import Dict, List

from mathgap.logicalforms import LogicalForm
from mathgap.trees.prooftree import ProofTree, TreeNode

class ProblemOrder:
    def __init__(self, body_node_ids: List[int], question_node_ids: List[int]):
        """ 
            Basically an uninstantiated world model representing a math word problem on a prooftree
            (i.e. speficies in which nodes will constitute the body and question of the MWP and in what order)
        """
        self.body_node_ids = body_node_ids
        self.question_node_ids = question_node_ids

    def get_body(self, tree: ProofTree) -> List[LogicalForm]:
        # NOTE: should use the same tree structure that was also used to generate the ids in the first place
        return [tree.node_by_id[i].logicalform for i in self.body_node_ids]

    def get_questions(self, tree: ProofTree) -> List[LogicalForm]:
        # NOTE: should use the same tree structure that was also used to generate the ids in the first place
        return [tree.node_by_id[i].logicalform for i in self.question_node_ids]
    
    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)