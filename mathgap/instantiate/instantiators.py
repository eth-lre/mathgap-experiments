import random
from typing import List
from mathgap.instantiate.instantiation import Instantiation

from mathgap.trees import ProofTree
from mathgap.properties import PropertyKey, PropertyType

class Instantiator:
    def instantiate(self, tree: ProofTree, instantiation: Instantiation = None, skip_existing: bool = False, seed: int = 14) -> Instantiation:
        """ 
            Instantiates a set of properties
            - tree: the tree for which the properties should be instantiated
            - instantiation: optionally, pass an existing instantiation which will be extended
            - skip_existing: if true, will simply skip all existing instantiated properties 
        """
        random.seed(seed)
        if instantiation is None:
            instantiation = Instantiation({})
        
        return self._instantiate(tree, instantiation, skip_existing, seed)

    def _instantiate(self, tree: ProofTree, instantiation: Instantiation, skip_existing: bool, seed: int) -> Instantiation:
        # Override this method
        ...

class PerPropTypeInstantiator(Instantiator):
    """ Instantiator that calls sub-instantiators per property type """
    def __init__(self, agent_inst: Instantiator, number_inst: Instantiator, entity_inst: Instantiator, attribute_inst: Instantiator, unit_inst: Instantiator) -> None:
        self.agent_inst = agent_inst
        self.number_inst = number_inst
        self.entity_inst = entity_inst
        self.attribute_inst = attribute_inst
        self.unit_inst = unit_inst

    def _instantiate(self, tree: ProofTree, instantiation: Instantiation, skip_existing: bool, seed: int) -> Instantiation:
        instantiation = self.agent_inst.instantiate(tree, instantiation, skip_existing, seed)
        instantiation = self.number_inst.instantiate(tree, instantiation, skip_existing, seed)
        instantiation = self.entity_inst.instantiate(tree, instantiation, skip_existing, seed)
        instantiation = self.attribute_inst.instantiate(tree, instantiation, skip_existing, seed)
        instantiation = self.unit_inst.instantiate(tree, instantiation, skip_existing, seed)
        return instantiation
        

class WordListInstantiator(Instantiator):
    """ 
        Instantiates all properties of a specified type with words from a list. 
        Optionally allows to enforce that each word can only be used once. 
    """
    def __init__(self, property_type: PropertyType, wordlist: List[str], enforce_uniqueness: bool = True) -> None:
        self.property_type = property_type
        self.wordlist = wordlist        
        self.enforce_uniqueness = enforce_uniqueness

    def _instantiate(self, tree: ProofTree, instantiation: Instantiation, skip_existing: bool, seed: int) -> Instantiation:
        available_words = self.wordlist.copy()
        if self.enforce_uniqueness:
            available_words = [w for w in available_words if w not in instantiation._instantiations.values()]
            
        for prop in tree.property_tracker.get_by_type(self.property_type):
            prop_key = PropertyKey(self.property_type, prop)
            if skip_existing and prop_key in instantiation: continue
            word = random.choice(available_words)
            instantiation[prop_key] = word
            if self.enforce_uniqueness:
                available_words.remove(word)
        return instantiation