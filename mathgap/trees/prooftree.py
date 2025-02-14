import random
from typing import Dict, Generator, List, Set, Tuple, Type
from enum import Enum
from copy import deepcopy
from collections import Counter

import networkx as nx

from mathgap.trees.rules import InferenceRule
from mathgap.trees.timing import VariableKey, VariableTimes

from mathgap.properties import PropertyTracker
from mathgap.logicalforms import LogicalForm, Container

class TraversalOrder(Enum):
    DFS = "depth-first-search"
    POST = "post-order-traversal"
    TIME = "time-order-traversal"
    BFS = "breadth-first-search"

class TreeNode:
    def __init__(self, logicalform: LogicalForm, depth: int) -> None:
        self.logicalform = logicalform
        self.child_nodes = []
        self.depth = depth
        self.constraints = []
        self.rule = None

    def set_derivation(self, nodes: List['TreeNode'], rule: InferenceRule):
        self.child_nodes = nodes
        self.rule = rule

    @property
    def premises(self) -> List[LogicalForm]:
        return [n.logicalform for n in self.child_nodes]

    @property
    def is_leaf(self) -> bool:
        return len(self.premises) == 0 

class ProofTree:
    """ Represents a proof tree, where the root node can be derived from all the leaves (axioms) by using inference rules. """
    def __init__(self, root: LogicalForm, property_tracker: PropertyTracker) -> None:
        self.root_node = TreeNode(root, depth=0)
        self.leaf_nodes: List[TreeNode] = []
        self.nodes_by_lf: Dict[LogicalForm, TreeNode] = {} # map <lf to tree node>
        self.id_by_node: Dict[TreeNode, int] = {} # map <node to node-id>
        self.node_by_id: Dict[int, TreeNode] = {} # map <node-id to node>
        self.nodes_by_type: Dict[Type, List[TreeNode]] = {} # map <concept to list of nodes>
        self.parent_by_node: Dict[TreeNode, TreeNode] = {} # map <child to parent>
    
        self.times_by_node: Dict[TreeNode, VariableTimes] = {} # only the times involved in the node, map <node to map <descriptor to set <times of descriptor>>>
        self.complete_times_by_node: Dict[TreeNode, VariableTimes] = {} # all the times inherited also from parent nodes, map <node to map <descriptor to set <times of descriptor>>>

        self.depth = 0
        
        self.property_tracker = property_tracker

        self.is_symbolically_computed = False
        root_vt = VariableTimes({vk: {0} for vk in root.get_variable_keys()})
        self._register_node(self.root_node, root_vt)
        self._refresh_complete_variable_times()

    @property
    def nodes(self) -> List[TreeNode]:
        return self.nodes_by_lf.values()

    def add_derivation(self, premises: List[LogicalForm], conclusion: LogicalForm, rule: InferenceRule):
        """ Adds a derivation of some node (basically add the premises as children to the node) """
        assert conclusion in self.nodes_by_lf, "Can only add to existing nodes!"
        parent_node = self.nodes_by_lf[conclusion]
        assert parent_node.is_leaf, "Cannot add multiple derivations for a logical form!"
        
        child_nodes = [TreeNode(p, parent_node.depth + 1) for p in premises]
        self.nodes_by_lf[conclusion].set_derivation(child_nodes, rule)
        self.leaf_nodes.remove(parent_node)

        variable_times_assigns = rule.reverse_infer_variable_times(premises, conclusion, self.times_by_node[parent_node])
        for child in child_nodes:
            self.parent_by_node[child] = parent_node 
            self._register_node(child, variable_times_assigns[child.logicalform])

        self._refresh_complete_variable_times()

    def _register_node(self, node: TreeNode, variable_times_assign: VariableTimes):
        self.nodes_by_lf[node.logicalform] = node
        
        node_id = max(0, 0, *self.id_by_node.values()) + 1
        self.id_by_node[node] = node_id
        self.node_by_id[node_id] = node

        self.nodes_by_type[type(node.logicalform)] = self.nodes_by_type.get(type(node.logicalform), []) + [node]

        self.times_by_node[node] = variable_times_assign

        # update stats about the tree
        self.leaf_nodes.append(node)
        self.depth = max(self.depth, node.depth)

    def execute_query(self, start_node: TreeNode, query: str) -> TreeNode:
        """ 
            Find a node relative to some other node by traversing the tree nodes.

            E.g. conclusion.conclusion would refer to the conclusion of the conlusion that start_node is a premise of.
        """
        if len(query) == 0: return start_node

        # TODO: if necessary, make the queries more powerful (e.g. with named premises)
        instructions = query.split(".")
        node = start_node
        for instruction in instructions:
            if instruction == "conclusion":
                node = self.parent_by_node[node]
            elif instruction == "self":
                continue
            else:
                raise ValueError(f"{instruction} not supported in tree query!")
        return node

    def _refresh_complete_variable_times(self):
        """ Recomputes the complete/full variable-times for each node (e.g. after new nodes have been added to the tree) """
        for node in self.traverse(TraversalOrder.TIME):
            if node.is_leaf: continue

            self.times_by_node[node] = node.rule.infer_variable_times(
                node.premises, 
                node.logicalform, 
                {lf:self.times_by_node[self.nodes_by_lf[lf]] for lf in node.premises}
            )

    def compute_symbolically(self):
        """ Applies the inference rules in a forward manner to compute an expression for each node """
        for node in self.traverse(TraversalOrder.TIME):
            if node.is_leaf: continue
            node.rule.infer_knowledge(node.premises, node.logicalform)
        self.is_symbolically_computed = True
    
    def instantiated_quantities(self, questions: List[LogicalForm], instantiation): 
        """ 
            Extract the quantity for multiple questions/logicalforms under a specific instantiation by evaluating the expression.
            Requires that the tree has been computed symbolically.
        """
        assert self.is_symbolically_computed, "Can only compute the answer on a tree that has been computed symbolically"
        
        all_quantities = []
        for question in questions:
            quantities = question.get_quantities()
            assert len(quantities) == 1, "Cannot get more than one instantiated quantity per lf currently."
            all_quantities.append(quantities[0].eval(instantiation))
        return all_quantities
    
    def instantiated_quantity(self, lf: LogicalForm, instantiation): 
        return self.instantiated_quantities([lf], instantiation)[0]
    

    def traverse(self, order: TraversalOrder = TraversalOrder.DFS, custom_order: List[int] = None, seed: int = None) -> Generator[TreeNode, None, None]:
        """ 
            Traverses the tree either in a common order (i.e. depth-first, post etc)
            or if a custom order is specified, the nodes will be traversed in said order.
        """
        if seed is not None: random.seed(seed)

        if custom_order is not None:
            for node_id in custom_order:
                yield self.node_by_id[node_id]
        else:
            if order == TraversalOrder.DFS:
                stack = [self.root_node]
                while len(stack) > 0:
                    node = stack.pop(-1)
                    yield node

                    stack.extend(reversed(node.child_nodes))
            elif order == TraversalOrder.POST:
                def _traverse_post(node: TreeNode) -> List[TreeNode]:
                    nodes = []
                    for child in node.child_nodes:
                        nodes.extend(_traverse_post(child))
                    nodes.append(node)
                    return nodes

                for node in _traverse_post(self.root_node):
                    yield node
            elif order == TraversalOrder.TIME:
                time_dag = self.build_time_dag()
                leaf_node_ids = set([self.id_by_node[n] for n in self.leaf_nodes])
                potential_next_node_ids = [n_id for n_id in time_dag.nodes if time_dag.in_degree(n_id) == 0 and n_id in leaf_node_ids]
                visited_node_ids = [] # nodes that have been sampled so far (in order)
                blocked_node_ids = [n_id for n_id in time_dag.nodes if n_id not in potential_next_node_ids] # nodes currently blocked

                while len(potential_next_node_ids) > 0:
                    # pop random next node
                    node_id = random.choice(potential_next_node_ids)
                    node = self.node_by_id[node_id]
                    yield node

                    potential_next_node_ids.remove(node_id)
                    visited_node_ids.append(node_id)

                    # check which nodes are now no longer blocked
                    for next_node_id in blocked_node_ids:
                        next_node = self.node_by_id[next_node_id]
                        if not all([self.id_by_node[c] in visited_node_ids for c in next_node.child_nodes]): continue # not all premises have been sampled yet
                        if not all([p_id in visited_node_ids for p_id in time_dag.predecessors(next_node_id)]): continue # not all timedag parents (need to happen before) have been sampled yet
                        
                        potential_next_node_ids.append(next_node_id)
                        blocked_node_ids.remove(next_node_id)
                
                forgotten_node_ids = set(self.node_by_id.keys()).difference(set(visited_node_ids))
                assert len(forgotten_node_ids) == 0, f"Need to have sampled all nodes by the end of the traversal. Forgot nodes: {forgotten_node_ids}"
            elif order == TraversalOrder.BFS:
                raise NotImplementedError("TODO: Implement BFS")
        
    def traverse_reasoning_trace(self, leaves_order: List[int]) -> Generator[TreeNode, None, None]:
        """     
            Visits the tree in a DFS/max-inferences manner based on availability of axioms:
            Meaning, as soon as all required premises have been discovered, come to the conclusion 
            and add it to the list of available facts, iterate until no more facts can be derived
            before consuming the next axiom etc.
        """
        # NOTE: due to the tree structure, there can never be 2 nodes that we're able to visit next simultaneously
        rest_of_leaves = leaves_order.copy()
        known_facts: List[TreeNode] = []
        while len(known_facts) < len(self.nodes_by_lf.values()):
            # add leaf as new fact
            leaf_id = rest_of_leaves.pop(0)
            leaf_node = self.node_by_id[leaf_id]
            known_facts.append(leaf_node)
            yield leaf_node
            
            # while we can conclude new facts:
            new_fact_inferred = True
            while new_fact_inferred:
                new_fact_inferred = False
                for node in self.traverse(TraversalOrder.POST):
                    if node in known_facts: continue # skip known facts
                    if node.is_leaf: continue # leaves should be consumed from the provided order
                    
                    # if all premises are known to derive the node
                    if all(node in known_facts for node in node.child_nodes):
                        # add the conclusion as a new fact
                        known_facts.append(node)
                        yield node
                        new_fact_inferred = True

    def traverse_writes(self) -> Generator[Tuple[VariableKey, int], None, None]:
        """ Traverses all (write to variable at time) of the tree in no specific order """
        for node in self.traverse(TraversalOrder.DFS):
            node_vts = self.times_by_node[node]
            lf = node.logicalform
            if isinstance(lf, Container):
                vk = lf.get_variable_keys()[0]
                for vt in node_vts[vk]:
                    yield (vk, vt)

    def has_write_at_time(self, vk: VariableKey, time: int) -> bool:
        """ Checks if any node of the tree writes to a variable-key at a certain time """
        for other_vk,other_time in self.traverse_writes():
            if other_vk == vk and other_time == time: return True
        return False
    
    def validate(self) -> bool:
        """ 
            Performs sanity checks on the tree:
            - never have two writes to the same variable-key at the same time
            - never have conflicting histories (apart from the variable-key that a rule is merging the histories on, i.e. vk's present in the lfs of multiple premises)
            - the post-order should be a valid time-order
        """
        # check that no two writes to the same variable-key occur at the same time
        all_writes = list(self.traverse_writes())
        if len(set(all_writes)) != len(all_writes): 
            print(f"WARNING: Validation failed because of multiple writes to the same variable at the same time! {[item for item, freq in Counter(all_writes).items() if freq > 1]}")
            return False
        
        # check histories
        for node in self.traverse(TraversalOrder.DFS):
            # exempt variable-keys directly involved in the premises from the check
            exempt_keys = set([k for c in node.child_nodes for k in c.logicalform.get_variable_keys()])
            vts = VariableTimes({})
            conflicts = set(vts.merge_all([self.times_by_node[c] for c in node.child_nodes]))
            bad_conflicts = conflicts.difference(exempt_keys)
            if len(bad_conflicts) > 0:
                print(f"WARNING: Validation failed because of conflicting histories at node_id={self.id_by_node[node]}")
                return False
            
        # check post order
        time_dag = self.build_time_dag()
        visited_node_ids = []
        for node in self.traverse(TraversalOrder.POST):
            node_id = self.id_by_node[node]
            # NOTE: we already know all premises have been visited by definition of POST order
            # make sure all time-dag parents (need to happen before) have been visited before
            if not all([p_id in visited_node_ids for p_id in time_dag.predecessors(node_id)]): return False 
            visited_node_ids.append(node_id)
            
        return True
    
    def build_time_dag(self) -> nx.DiGraph:
        """ 
            Creates a DAG that respects the variable-times (i.e. each node points to nodes that can only happen after itself), 
            thus by following edges you advance in time.
        """
        graph = nx.DiGraph()

        # each tree-node gets its own node in the time DAG
        for node in self.nodes:
            graph.add_node(self.id_by_node[node])

        # compare each pair of nodes of the tree to establish a timeline
        for node in self.nodes:
            node_id = self.id_by_node[node]
            node_vts = self.times_by_node[node]

            for other_node in self.nodes:
                if other_node == node: continue
                other_node_id = self.id_by_node[other_node]
                other_node_vts = self.times_by_node[other_node]

                if not node_vts.can_happen_after(other_node_vts):
                    # node must happen before other_node
                    graph.add_edge(node_id, other_node_id)

        
        assert nx.is_directed_acyclic_graph(graph), "Timegraph is expected to be a DAG"
        return graph

    def copy(self) -> 'ProofTree':
        return deepcopy(self)
    
    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)