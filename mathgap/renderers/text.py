from typing import Any, Dict, List, Set

from mathgap.logicalforms.logicalform import EntitySpec
from mathgap.renderers.renderer import Renderer, PerTypeRenderer

from mathgap.logicalforms import Container, Transfer, Comp, CompEq, PartWhole
from mathgap.trees import ProofTree
from mathgap.trees.rules import InferenceRule
from mathgap.trees.timing import VariableTimes, VariableKey
from mathgap.problemsample import ProblemOrder
from mathgap.properties import PropertyKey
from mathgap.instantiate import Instantiation

class ToStrRenderer(Renderer):
    def render(self, obj: object) -> str:
        return str(obj)

class ListRenderer(Renderer):
    def render(self, l: List) -> str:
        return f"[{', '.join(R(e) for e in l)}]"

class SetRenderer(Renderer):
    def render(self, l: Set) -> str:
        return f"{{{', '.join(R(e) for e in l)}}}"

class DictRenderer(Renderer):
    def render(self, dct: Dict) -> str:
        return f"{{{', '.join([R(vk) + ': ' + R(vt) for vk,vt in dct.items()])}}}"

class ProofTreeRenderer(Renderer):
    def render(self, tree: ProofTree, include_variable_times: bool = False) -> str:
        out = ""
        for node in tree.traverse():
            lf = node.logicalform
            node_id = tree.id_by_node[node]

            if node.is_leaf:
                out += f"|= {R(lf)} [node{node_id}] [Axiom]\n"
            else:
                premises = node.premises
                premises_rendered = ", ".join([f"{R(p)} [node{tree.id_by_node[tree.nodes_by_lf[p]]}]" for p in premises])
                out += f"{premises_rendered} |= {R(lf)} [node{node_id}] [used: {R(node.rule)}]\n"
        
        if include_variable_times:
            out += "Variable Times:\n"    
            for node in tree.traverse():
                node_id = tree.id_by_node[node]
                out += f"\t[node{node_id}]: {R(tree.times_by_node[node])}\n"

        return out
    
class ProblemStructureRenderer(Renderer):
    def render(self, ps: ProblemOrder) -> str:
        return f"problem-structure(body={R(ps.body_node_ids)}, questions={R(ps.question_node_ids)})"

class InferenceRuleRenderer(Renderer):
    def render(self, ir: InferenceRule) -> str:
        return type(ir).__name__
    
class VariableTimesRenderer(Renderer):
    def render(self, vts: VariableTimes, join: str = ", ") -> str:
        return f"{join.join([R(vk) + ': ' + R(vt) for vk,vt in vts.times_by_var.items()])}"

class VariableKeyRenderer(Renderer):
    def render(self, vk: VariableKey) -> str:
        return f"<{', '.join([R(k) for k in vk.variable_key])}>"

# LOGICAL FORMS

class ContainerRenderer(Renderer):
    def render(self, cont: Container) -> str:
        return f"container(agent={R(cont.agent)}, quantity={R(cont.quantity)}, entity={R(cont.entity)}, attribute={R(cont.attribute)}, unit={R(cont.unit)})"
    
class TransferRenderer(Renderer):
    def render(self, transfer: Transfer) -> str:
        return f"transfer(receiver={R(transfer.receiver)}, sender={R(transfer.sender)}, quantity={R(transfer.quantity)}, entity={R(transfer.entity)}, attribute={R(transfer.attribute)}, unit={R(transfer.unit)})"

class CompRenderer(Renderer):
    def render(self, comp: Comp) -> str:
        return f"comp(comp_type={R(comp.comp_type)}, quantity={R(comp.quantity)}, subj_agent={R(comp.subj_agent)}, subj_entity={R(comp.subj_entity)}, subj_attribute={R(comp.subj_attribute)}, subj_unit={R(comp.subj_unit)}, obj_agent={R(comp.obj_agent)}, obj_entity={R(comp.obj_entity)}, obj_attribute={R(comp.obj_attribute)}, obj_unit={R(comp.obj_unit)})"

class CompEqRenderer(Renderer):
    def render(self, compeq: CompEq) -> str:
        return f"compeq(subj_agent={R(compeq.subj_agent)}, subj_entity={R(compeq.subj_entity)}, subj_attribute={R(compeq.subj_attribute)}, subj_unit={R(compeq.subj_unit)}, obj_agent={R(compeq.obj_agent)}, obj_entity={R(compeq.obj_entity)}, obj_attribute={R(compeq.obj_attribute)}, obj_unit={R(compeq.obj_unit)}, comp_type={R(compeq.comp_type)}, other_subj_agent={R(compeq.other_subj_agent)}, other_subj_entity={R(compeq.other_subj_entity)}, other_subj_attribute={R(compeq.other_subj_attribute)}, other_subj_unit={R(compeq.other_subj_unit)}, other_obj_agent={R(compeq.other_obj_agent)}, other_obj_entity={R(compeq.other_obj_entity)}, other_obj_attribute={R(compeq.other_obj_attribute)}, other_obj_unit={R(compeq.other_obj_unit)}, other_comp_type={R(compeq.other_comp_type)})"
    
class PartWholeRenderer(Renderer):
    def render(self, pw: PartWhole) -> str:
        return f"partwhole(quantity={R(pw.quantity)}, whole_entity={R(pw.whole_entity)}, attribute={R(pw.whole_attribute)}, unit={R(pw.whole_unit)}, part_entities=[{', '.join([R(e) for e in pw.part_entities])}])"

# EXPRESSIONS

# TODO

class EntitySpecRenderer(Renderer):
    def render(self, es: EntitySpec) -> str:
        return f"EntitySpec(entity_id={es.entity_id}, part_entity_ids={es.part_entity_ids}, attribute_id={es.attribute_id}, unit_id={es.unit_id})"

# INSTANTIATION

class PropertyKeyRenderer(Renderer):
    def render(self, prop_key: PropertyKey) -> str:
        return f"{prop_key.property_type.value}_{prop_key.identifier}"

class InstantiationRenderer(Renderer):
    def render(self, instantiation: Instantiation) -> str:
        joined_inst = ", ".join(f"{R(p)}: {R(v)}" for p,v in instantiation._instantiations.items())
        return f"{{{joined_inst}}}"

R = PerTypeRenderer(
        renderers={
            # NOTE: make sure to have this sorted by class hierarchy
            ProofTree: ProofTreeRenderer(),
            ProblemOrder: ProblemStructureRenderer(),
            InferenceRule: InferenceRuleRenderer(),
            Container: ContainerRenderer(),
            Transfer: TransferRenderer(),
            Comp: CompRenderer(),
            CompEq: CompEqRenderer(),
            PartWhole: PartWholeRenderer(),
            PropertyKey: PropertyKeyRenderer(),
            EntitySpec: EntitySpecRenderer(),
            Instantiation: InstantiationRenderer(),
            list: ListRenderer(),
            set: SetRenderer(),
            dict: DictRenderer(),
            VariableTimes: VariableTimesRenderer(),
            VariableKey: VariableKeyRenderer()
        },
        default_renderer=ToStrRenderer()
)