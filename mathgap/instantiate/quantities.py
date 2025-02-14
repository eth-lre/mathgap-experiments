# Instantiators for quantities
from typing import Any, Dict, List
import random

from mathgap.expressions import Expr, Variable
from mathgap.instantiate.instantiation import Instantiation
from mathgap.instantiate.instantiators import Instantiator

from mathgap.trees import ProofTree
from mathgap.properties import PropertyType, PropertyKey
from mathgap.logicalforms import Container, Comp
from mathgap.trees.prooftree import TreeNode
import numpy as np

class RandIntInstantiator(Instantiator):
    """ Instantiates all numbers of a problem with random numbers in a range """
    def __init__(self, min_value: int = 2, max_value: int = 100) -> None:
        self.min_value = min_value
        self.max_value = max_value

    def _instantiate(self, tree: ProofTree, instantiation: Instantiation, skip_existing: bool, seed: int) -> Instantiation:
        for prop_id in tree.property_tracker.get_by_type(PropertyType.QUANTITY):
            prop = PropertyKey(PropertyType.QUANTITY, prop_id)
            if skip_existing and prop in instantiation: continue
            instantiation.set_even_if_present(prop, random.randint(self.min_value, self.max_value))
        return instantiation


def rand_int_inst_random(tree: ProofTree, orig_instantiation: Instantiation, parameters: List[PropertyKey],
                         min_leaf_value: int = 2, max_leaf_value: int = 100, 
                         min_inner_value: int = 2, max_inner_value: int = 1000,
                         max_attempts: int = 100_000, seed: int = 14) -> Instantiation:
    """ 
        Try to find a random instantiation of integer numbers by trying random instantiations until a valid one is found

        - tree: prooftree for which we want to find a valid instantiation
        - orig_instantiation: the current and/or partial instantiation
        - parameters: which propertykeys can be tuned (i.e. which quantities/variables)
        - leaf_min_value (incl): minimum value each quantity on leaf nodes can have
        - leaf_max_value (incl): maximum value each quantity on leaf nodes can have
        - inner_min_value (incl): minimum value each quantity on inner nodes can have
        - inner_max_value (incl): maximum value each quantity on inner nodes can have
        - max_attempts: how many tries will be performed before giving up
        - seed
    """
    random.seed(seed)

    instantiation = orig_instantiation.copy()
    quantities: List[Expr] = []
    for node in tree.traverse():
        if node.is_leaf: continue # constraints on leaves are enforced through random.range
        quantities.extend(node.logicalform.get_quantities())

    # 0. enable caching/memoization of values and gradients 
    for q in tree.root_node.logicalform.get_quantities():
        q.enable_cache(recursive=True)

    # 1. retry until a valid instantiation is found or the number of attempts is exceeded
    for _ in range(max_attempts):
        # 1.0 clear the cache
        for q in tree.root_node.logicalform.get_quantities():
            q.clear_cache(recursive=True)

        # 1.1 instantiate each of the parameters with a random valid leaf-value
        for param in parameters:
            instantiation._instantiations[param] = random.randint(min_leaf_value, max_leaf_value)

        # 1.2 test if the instantiation is valid
        is_valid = True
        for quantity in quantities:
            qval = quantity.eval(instantiation)

            if (qval < min_inner_value) or (qval > max_inner_value):
                is_valid = False
                break

        # 1.3 if we found a valid instantiation, stop looking for another one
        if is_valid:
            break

    # 3. we're done => disable the cache on all expression
    for q in tree.root_node.logicalform.get_quantities():
        q.disable_cache(recursive=True)

    return instantiation

def rand_int_inst_through_cpga(tree: ProofTree, orig_instantiation: Instantiation, 
                              parameters: List[PropertyKey], lr: float = 1.0,
                              min_leaf_value: int = 2, max_leaf_value: int = 100, 
                              min_inner_value: int = 2, max_inner_value: int = 1000,
                              max_steps: int = 1_000, re_init_after_steps: int = 100, eps: float = 1e-14, 
                              boundary_bounce: float = 0.0, seed: int = 14) -> Instantiation:
    """ 
        Try to find a pseudo-random instantiation of integer numbers through constrained projected gradient ascent 

        - tree: prooftree for which we want to find a valid instantiation
        - orig_instantiation: the current and/or partial instantiation
        - parameters: which propertykeys can be tuned (i.e. which quantities/variables)
        - lr: step-size which will be taken into the direction of a potentially valid initialization
        - leaf_min_value (incl): minimum value each quantity on leaf nodes can have
        - leaf_max_value (incl): maximum value each quantity on leaf nodes can have
        - inner_min_value (incl): minimum value each quantity on inner nodes can have
        - inner_max_value (incl): maximum value each quantity on inner nodes can have
        - max_steps: how many gradient steps to take at the max
        - re_init_after_steps: after how many steps should we retry with a different initial instantiation
        - eps: what should be considered converged
        - boundary_bounce in [0,1): instead of simply clipping to [min_leaf_value, max_leaf_value], parameters will
            "bounce-back" a random amount (scaled by boundary_bounce) from the boundary upon collision. 
            This helps to avoid values sticking to boundaries.
        - seed: 
    """
    random.seed(seed)
    np.random.seed(seed)

    instantiation = orig_instantiation.copy()
    quantities: List[Expr] = []
    for node in tree.traverse():
        if node.is_leaf: continue # constraints on leaves are enforced through clipping
        quantities.extend(node.logicalform.get_quantities())

    # 0. enable caching/memoization of values and gradients 
    for q in tree.root_node.logicalform.get_quantities():
        q.enable_cache(recursive=True)

    # 1. randomly initialize the set of tunable variables with min_leaf_value <= x <= max_leaf_value
    var_values = np.random.rand(len(parameters)) * (max_leaf_value - min_leaf_value) + min_leaf_value
    for val,prop in zip(var_values, parameters):
        instantiation._instantiations[prop] = round(val) # we round each value to integers

    # 2. perform constrained projected gradient descent
    for i in range(max_steps):
        # 2.0 clear the cache at the beginning of each gradient step
        for q in tree.root_node.logicalform.get_quantities():
            q.clear_cache(recursive=True)

        # 2.1 compute the gradient based on all quantities of non-leaf nodes
        total_grad = np.zeros(shape=(len(parameters)))
        is_invalid = False
        for quantity in quantities:
            qval = quantity.eval(instantiation)

            if qval < min_inner_value:
                # Case 1: value is too small => increase
                total_grad += quantity.grad(parameters, instantiation) * (min_inner_value - qval)
                is_invalid = True
            elif qval > max_inner_value:
                # Case 2: value is too large => decrease
                total_grad -= quantity.grad(parameters, instantiation) * (qval - max_inner_value)
                is_invalid = True
            else:
                # Case 3: value is within interval => no gradient signal
                pass # no need to even compute gradient in this case
        
        # take the mean s.t. larger trees don't get huge gradients
        mean_grad = total_grad / len(quantities)
        
        # 2.2 check if we found a valid instantiation
        if not is_invalid:
            break # if so: terminate early

        # 2.3 compute the new initialization
        new_values = var_values + lr * mean_grad
        new_values_clipped = np.clip(new_values, min_leaf_value, max_leaf_value)

        # 2.3.1 if we have bouncy boundaries, any parameter that would be clipped to the boundary bounces back a random amount
        if boundary_bounce > 0.0:
            bounce = boundary_bounce * np.random.rand(len(parameters)) * (max_leaf_value - min_leaf_value)
            new_values_clipped += (1.0 * (new_values < min_leaf_value) - 1.0 * (new_values > max_leaf_value)) * bounce

        # 2.4 check if re-initialization is either due or we're stuck (i.e. the new instantiation is too similar to the old one)
        if ((i+1) % re_init_after_steps == 0) or (np.linalg.norm(new_values_clipped - var_values) <= eps):
            # if we are stuck but haven't found a valid instantiation => restart with a different initialization
            new_values_clipped = np.random.rand(len(parameters)) * (max_leaf_value - min_leaf_value) + min_leaf_value

        # 2.5 perform the gradient update
        var_values = new_values_clipped
        for val,prop in zip(var_values, parameters):
            # we are performing the gradient computation etc with floats but round to integers for the initialization
            instantiation._instantiations[prop] = round(val)

    # 3. we're done => disable the cache on all expression
    for q in tree.root_node.logicalform.get_quantities():
        q.disable_cache(recursive=True)

    return instantiation

class PositiveRandIntInstantiator(Instantiator):
    """ 
        Instantiates all numbers of a problem with random numbers in a range,
        while making sure none of the quantities (intermediate as well as final answer) are negative.

        - leaf_min_value (incl): minimum value each quantity on leaf nodes can have
        - leaf_max_value (incl): maximum value each quantity on leaf nodes can have
        - inner_min_value (incl): minimum value each quantity on inner nodes can have
        - inner_max_value (incl): maximum value each quantity on inner nodes can have
        - strategy: what is the strategy for finding a valid instantiation
            - random: will try random instantiations until valid
            - cpga: will start with a random instantiation and perform constrained projected gradient ascent
        - validate_preselected: regardless of whether quantities have been preselected, if true, this will validate all leaf- and inner-nodes
            if false, only the non-preselected leaf-nodes as well as all inner-nodes are validated
    """
    def __init__(self, leaf_min_value: int = 2, leaf_max_value: int = 100, inner_min_value: int = 2, inner_max_value: int = 1000, 
                 strategy: str = "cpga", max_attempts: int = 1000000, validate_preselected: bool = True) -> None:
        self.leaf_min_value = leaf_min_value
        self.leaf_max_value = leaf_max_value
        self.inner_min_value = inner_min_value
        self.inner_max_value = inner_max_value
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.validate_preselected = validate_preselected

        if self.strategy == "random":
            self.rand_int_inst = RandIntInstantiator(min_value=leaf_min_value, max_value=leaf_max_value)

    def is_valid_instantiation(self, tree: ProofTree, instantiation: Instantiation, preselected_leaf_node_ids: List[int] = []) -> bool:
        for node in tree.traverse():
            for quantity in node.logicalform.get_quantities():
                value = quantity.eval(instantiation)
                if node.is_leaf:
                    # validate leaf node
                    if self.validate_preselected or tree.id_by_node[node] not in preselected_leaf_node_ids:
                      if value < self.leaf_min_value or value > self.leaf_max_value: 
                          return False
                else:
                    # validate inner node
                    if value < self.inner_min_value or value > self.inner_max_value:
                        return False
        return True

    def _instantiate(self, tree: ProofTree, orig_instantiation: Instantiation, skip_existing: bool, seed: int) -> Instantiation:
        assert tree.is_symbolically_computed, "Can only enforce positiveness of intermediates on a symbolically computed tree!"
        
        # establish the list of properties that should be instantiated
        all_vars = [PropertyKey(PropertyType.QUANTITY, pid) for pid in tree.property_tracker.get_by_type(PropertyType.QUANTITY)]
        preselected_parameters = []
        if skip_existing:
            preselected_parameters = list(orig_instantiation.get_instantiations_of_type(PropertyType.QUANTITY).keys())
        parameters = [v for v in all_vars if v not in preselected_parameters]

        if self.strategy == "random":
            # try random instantiations until a valid one is found
            instantiation = rand_int_inst_random(tree, orig_instantiation, parameters,
                                min_leaf_value=self.leaf_min_value, max_leaf_value=self.leaf_max_value,
                                min_inner_value=self.inner_min_value, max_inner_value=self.inner_max_value,
                                max_attempts=self.max_attempts, seed=seed)
        elif self.strategy == "cpga":
            # use constrained projected gradient descent to find a valid instantiation
            instantiation = rand_int_inst_through_cpga(tree, orig_instantiation, parameters, lr=np.sqrt(self.leaf_max_value - self.leaf_min_value),
                                min_leaf_value=self.leaf_min_value, max_leaf_value=self.leaf_max_value,
                                min_inner_value=self.inner_min_value, max_inner_value=self.inner_max_value,
                                max_steps=self.max_attempts, re_init_after_steps=self.max_attempts // 10,
                                boundary_bounce=0.25, seed=seed)

        # compute which tree-nodes have been preselected
        preselected_leaf_node_ids = []
        for prop_key in preselected_parameters:
            for node in tree.leaf_nodes:
                if any(isinstance(q, Variable) and q.identifier == prop_key for q in node.logicalform.get_quantities()):
                    preselected_leaf_node_ids.append(tree.id_by_node[node])

        if self.is_valid_instantiation(tree, instantiation, preselected_leaf_node_ids):
            return instantiation
        
        raise ValueError(f"Failed to find a valid instantiation after {self.max_attempts} iterations!")