from typing import List, Type

from mathgap.trees.generators.stoppingcriteria import Criterion

from mathgap.trees.prooftree import ProofTree
from mathgap.trees.rules import InferenceRule

class Generator:
    def __init__(self, start_types: List[Type], inference_rules: List[InferenceRule], stopping_criterion: Criterion) -> None:
        """ 
            Generates a proof tree according to some specification, which includes:
            - start_types: list of logicalform-types that the tree is allowed to start with
            - inference_rules: the set of inference rules that can be applied
            - stopping_criterion: when should the generation be stopped
        """
        self.start_types = start_types
        self.inference_rules = inference_rules
        self.stopping_criterion = stopping_criterion

    def generate(self, seed:int = 14) -> ProofTree:
        """ Generates a proof tree """
        ...

