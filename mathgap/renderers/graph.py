# Renders a proof tree as an interactive graph (html)
from typing import Any, List
import os
import shutil
import webbrowser

import networkx as nx
# from networkx.drawing.nx_agraph import graphviz_layout
from pyvis.network import Network, check_html

from mathgap.renderers.renderer import Renderer, PerTypeRenderer

from mathgap.logicalforms import Container, Transfer, Comp, CompEq, LogicalForm
from mathgap.trees.prooftree import ProofTree, TreeNode
from mathgap.trees.rules import InferenceRule
from mathgap.problemsample import ProblemOrder
from mathgap.properties import PropertyKey
from mathgap.instantiate import Instantiation
from mathgap.trees.timing import VariableTimes

from mathgap.renderers import TEXT_RENDERER

def write_network_utf8(network: Network, filename: str, notebook: bool = False, open_browser: bool = False):
    getcwd_name = filename
    check_html(getcwd_name)
    network.html = network.generate_html(notebook=notebook)

    if network.cdn_resources == "local":
        if not os.path.exists("lib"):
            os.makedirs("lib")
        if not os.path.exists("lib/bindings"):
            shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/bindings", "lib/bindings")
        if not os.path.exists(os.getcwd()+"/lib/tom-select"):
            shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/tom-select", "lib/tom-select")
        if not os.path.exists(os.getcwd()+"/lib/vis-9.1.2"):
            shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/vis-9.1.2", "lib/vis-9.1.2")
        with open(getcwd_name, "w+", encoding="utf-8") as out:
            out.write(network.html)
    elif network.cdn_resources == "in_line" or network.cdn_resources == "remote":
        with open(getcwd_name, "w+", encoding="utf-8") as out:
            out.write(network.html)
    else:
        assert "cdn_resources is not in ['in_line','remote','local']."
    if open_browser: # open the saved file in a new browser window.
        webbrowser.open(getcwd_name)

class ProofTreeRenderer(Renderer):
    def render(self, tree: ProofTree, leaves_order: List[int] = None) -> Network:
        """ 
            Renders the tree as a network.
            - tree: the tree that will be rendered
            - leaves_order: if specified, the leaves will be sorted in this order and the tree nodes will be adjusted accordingly. 
                Otherwise the tree is traversed in canonical order.
        """
        tree_traversal = tree.traverse() if leaves_order is None else tree.traverse_reasoning_trace(leaves_order)
        net = Network(notebook=False, cdn_resources="in_line", directed=True)
        net.toggle_physics(False)

        distance_x = 120
        distance_y = 120

        width_per_depth = {}
        for i,node in enumerate(tree_traversal):
            node_id = tree.id_by_node[node]

            if not node_id in net.node_ids:
                self.render_node(net, node_id, node, tree.times_by_node[node], i)

            net_node = net.get_node(node_id)
            net_node["label"] = net_node["label"].replace("-1", str(i))
            
            width_of_depth = width_per_depth.get(node.depth, 0)
            net_node["x"] = distance_x*width_of_depth
            net_node["y"] = -distance_y*node.depth
            width_per_depth[node.depth] = width_of_depth + 1

            if not node.is_leaf:
                for child in node.child_nodes:
                    child_node_id = tree.id_by_node[child]
                    if not child_node_id in net.node_ids:
                        self.render_node(net, child_node_id, child, tree.times_by_node[child], -1)
                    net.add_edge(child_node_id, node_id, color="blue")
            else:
                net_node["label"] += "\n(Ax)"

        # center each level
        max_width = max(width_per_depth.values())
        for node in tree.traverse():
            node_id = tree.id_by_node[node]
            net_node = net.get_node(node_id)
            width_of_depth = width_per_depth[node.depth]
            net_node["x"] = net_node["x"] + distance_x*(max_width - width_of_depth) / 2

        return net

    def render_node(self, net: Network, node_id: int, node: TreeNode, variable_times: VariableTimes, visitation_idx: int):
        vt_join = "\n\t"
        net.add_node(node_id, label=f"({visitation_idx})\n{type(node.logicalform).__name__} [{node_id}]", title=f"{TEXT_RENDERER(node.logicalform)}\nVariable Times:\n\t{TEXT_RENDERER(variable_times, join=vt_join)}")

COLOR_CATALOG = [
    "red",
    "green",
    "blue",
    "orange",
    "yellow",
    "purple"
]

class TimeDAGRenderer(Renderer):
    def render(self, time_dag: nx.DiGraph, tree: ProofTree, net: Network, transitive: bool = True) -> Network:
        """ 
            Renders the timeDAG (in-place) onto some existing network, assuming the underlying nodes are the same 
            (i.e. the nodes used to generate the timeDAG are the same as the ones used to generate the network).
        """
        if transitive:
            for from_id in time_dag.nodes:
                for to_id in nx.descendants(time_dag, from_id):
                    net.add_edge(from_id, to_id, color="red", dashes=True)
        else:
            for edge in time_dag.edges:
                from_id, to_id = edge
                net.add_edge(from_id, to_id, color="red", dashes=True)