from typing import Dict
import random

from mathgap.trees.generators.generator import Generator
from mathgap.trees.prooftree import ProofTree

class MultiGenerator(Generator):
    def __init__(self, weights_by_generator: Dict[Generator, float]):
        """ Generator that consists of multiple generators that will be sampled randomly """
        self.generators = list(weights_by_generator.keys())
        self.weights = [weights_by_generator[g] for g in self.generators]

    def generate(self, seed: int = 14) -> ProofTree:
        random.seed(seed)

        generator = random.choices(self.generators, weights=self.weights, k=1)[0]
        tree = generator.generate(seed)

        if not tree.is_symbolically_computed:
            tree.compute_symbolically()
            
        return tree