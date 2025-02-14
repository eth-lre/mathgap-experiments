from typing import Dict, List, Tuple, Generator as GenType, Type
import random

from mathgap.trees.generators.generator import Generator
from mathgap.trees.generators.stoppingcriteria import Criterion
from mathgap.trees.generators.policies import RuleSamplingPolicy

from mathgap.trees.prooftree import ProofTree
from mathgap.trees.rules import InferenceRule, ContContComp, ContCompCompeqCont, ContTransferCont, ContCompCont, ContPartWhole
from mathgap.logicalforms import LogicalForm, Container, ComparisonType, Comp, PartWhole, ADDITIVE_COMP_TYPES
from mathgap.properties import PropertyType, PropertyTracker, PropertyKey
from mathgap.expressions import Variable

class GeneralGenerator(Generator):
    def __init__(self, start_types: List[Type], inference_rules: List[InferenceRule], rule_sampling_policy: RuleSamplingPolicy, stopping_criterion: Criterion, 
                 min_part_whole: int = 2, max_part_whole: int = 4, comp_same_entity_prob: float = 0.5, compeq_same_entity_prob: float = 1.0, 
                 comp_allowed_comparisons: List[ComparisonType] = ADDITIVE_COMP_TYPES,
                 use_attribute: bool = False, use_unit: bool = False) -> None:
        """ 
            - start_types: the types of lf that the inference tree can have at its root?
            - inference_rules: the allowed inference rules which can be applied to generate the tree
            - rule_sampling_policy: specifies how to sample from the rules whenever a node is expanded
                e.g. this can be dependent on the current state of the tree or totally random
            - max_part_whole: how many parts a part-whole can have at maximum (the minimum will always be 2)
            - comp_same_entity_prob: with which probability should a comparison be between the same types of entities (incl. attribute and unit) (p(different entities) = 1.0 - comp_same_type_prob)
            - compeq_same_entity_prob: with which probability should a comp-eq be between the same types of entities (incl. attribute and unit)
            - comp_allowed_comparisons: what are the list of allowed comparisons for Comp-nodes
            - use_attribute: whether the generated entities will have attributes
            - use_unit: whether the generated entities will have units
        """
        super().__init__(start_types, inference_rules, stopping_criterion)
        self.rule_sampling_policy = rule_sampling_policy
        self.min_part_whole = min_part_whole
        self.max_part_whole = max_part_whole
        self.comp_same_entity_prob = comp_same_entity_prob
        self.compeq_same_entity_prob = compeq_same_entity_prob
        self.comp_allowed_comparisons = comp_allowed_comparisons
        
        # TODO: allow random chance of whether attribute is used throughout generation (i.e. have mix)
        assert not (use_attribute and use_unit), "Having both attributes and units isn't currently supported"
        self.use_attribute = use_attribute
        self.use_unit = use_unit

    def _request_var(self, property_tracker: PropertyTracker, use_entity: bool|int=True, use_attribute: bool|None|int=False, use_unit: bool|None|int=False):
        entity = None
        if isinstance(use_entity, bool):
            if use_entity == True:
                entity = property_tracker.request_id(PropertyType.ENTITY)
        elif isinstance(use_entity, int):
            entity = use_entity
        
        attribute = None
        if isinstance(use_attribute, bool):
            if use_attribute == True:
                attribute = property_tracker.request_id(PropertyType.ATTRIBUTE)
        elif isinstance(use_attribute, int):
            attribute = use_attribute

        unit = None
        if isinstance(use_unit, bool):
            if use_unit == True:
                unit = property_tracker.request_id(PropertyType.UNIT)
        elif isinstance(use_unit, int):
            unit = use_unit

        return (
            property_tracker.request_id(PropertyType.AGENT),
            entity,
            attribute,
            unit
        )

    def generate(self, seed: int = 14) -> ProofTree:
        random.seed(seed)
        use_attribute, use_unit = self.use_attribute, self.use_unit

        question_type = random.choice(self.start_types)

        property_tracker = PropertyTracker()            
        def var_from_container(cont: Container):
            return (cont.agent, cont.entity, cont.attribute, cont.unit)
        
        def set_parametrization(parametrization: Dict, var_name: str, var):
            parametrization[f"{var_name}_agent"] = var[0] 
            parametrization[f"{var_name}_entity"] = var[1] 
            parametrization[f"{var_name}_attribute"] = var[2] 
            parametrization[f"{var_name}_unit"] = var[3] 

        root = self.create_start_lf(question_type, property_tracker, use_attribute, use_unit)
        tree = ProofTree(root=root, property_tracker=property_tracker)

        part_whole_entities = set([])
        for lf, valid_rules in self.expand_bfs(tree, root, property_tracker):
            rule = self.rule_sampling_policy.sample(lf, tree, valid_rules, self.stopping_criterion)
            parametrization = {}
            if isinstance(rule, ContTransferCont):
                assert isinstance(lf, Container), "Conclusion is expected to be Container"
                vars = [lf.agent]

                # if we start with a part-whole then no other agent should have any such entity
                # e.g. A has 4 apples. B has 3 peaches. C gets 3 peaches from B. How many peaches does everyone combined have? => 7 bc A has 4, B has 0 and C has 3
                if lf.entity not in part_whole_entities:
                    vars.append(property_tracker.request_id(PropertyType.AGENT))
                else:
                    vars.append(None)

                random.shuffle(vars)

                parametrization["sender_agent"] = vars[0]
                parametrization["receiver_agent"] = vars[1]
                parametrization["attribute"] = lf.attribute # TODO: allow introduction of attribute if none and no unit
                parametrization["unit"] = lf.unit
            elif isinstance(rule, ContCompCont):
                assert isinstance(lf, Container), "Conclusion is expected to be Container"
                comp_same_entity = random.random() <= self.comp_same_entity_prob

                ue,ua,uu = True, use_attribute, use_unit
                if comp_same_entity:
                    ue,ua,uu = lf.entity, lf.attribute, lf.unit

                vars = [
                    var_from_container(lf),
                    self._request_var(property_tracker, use_entity=ue, use_attribute=ua, use_unit=uu),
                ]
                random.shuffle(vars)

                set_parametrization(parametrization, "subj", vars[0])
                set_parametrization(parametrization, "obj", vars[1])

                parametrization["comp_type"] = random.choice(self.comp_allowed_comparisons)

            elif isinstance(rule, ContCompCompeqCont):
                assert isinstance(lf, Container), "Conclusion is expected to be Container"

                compeq_same_entity = random.random() <= self.compeq_same_entity_prob

                ue,ua,uu = True, use_attribute, use_unit
                if compeq_same_entity:
                    ue,ua,uu = lf.entity, lf.attribute, lf.unit

                # NOTE: conclusion must match with subj or obj and not other_subj or other_obj 
                vars = [
                    var_from_container(lf),
                    self._request_var(property_tracker, use_entity=ue, use_attribute=ua, use_unit=uu),
                ]
                random.shuffle(vars)
                vars += [
                    self._request_var(property_tracker, use_entity=ue, use_attribute=ua, use_unit=uu),
                    self._request_var(property_tracker, use_entity=ue, use_attribute=ua, use_unit=uu),
                ]

                set_parametrization(parametrization, "subj", vars[0])
                set_parametrization(parametrization, "obj", vars[1])
                set_parametrization(parametrization, "other_subj", vars[2])
                set_parametrization(parametrization, "other_obj", vars[3])

                parametrization["comp_type"] = random.choice([ComparisonType.MORE_THAN]) # , ComparisonType.LESS_THAN
                parametrization["other_comp_type"] = random.choice([ComparisonType.MORE_THAN]) #, ComparisonType.LESS_THAN

            elif isinstance(rule, ContContComp):
                assert isinstance(lf, Comp), "Conclusion is expected to be a Comparison"
                # NOTE: no parametrization

            elif isinstance(rule, ContPartWhole):
                assert isinstance(lf, PartWhole), "Conclusion is expected to be a PartWhole"
                # NOTE: no parametrization

            premises = rule.apply_reverse(lf, parametrization)
            tree.add_derivation(premises, lf, rule)

            assert tree.validate(), "Should not be able to generate invalid trees!"

        tree.compute_symbolically()
        return tree
    
    def create_start_lf(self, typ: Type, property_tracker: PropertyTracker, use_attribute: bool, use_unit: bool) -> LogicalForm:
        if typ == Container:
            var = self._request_var(property_tracker, use_entity=True, use_attribute=use_attribute, use_unit=use_unit)
            return Container(agent=var[0], quantity=None, entity=var[1], attribute=var[2], unit=var[3])
        elif typ == Comp:
            var_subj = self._request_var(property_tracker, use_entity=True, use_attribute=use_attribute, use_unit=use_unit)
            
            comp_same_entity = random.random() <= self.comp_same_entity_prob
            if comp_same_entity:
                var_obj = self._request_var(property_tracker, use_entity=var_subj[1], use_attribute=var_subj[2], use_unit=var_subj[3])
            else:
                var_obj = self._request_var(property_tracker, use_entity=True, use_attribute=use_attribute, use_unit=use_unit)

            comp_type = random.choice(self.comp_allowed_comparisons)
            return Comp(subj_agent = var_subj[0], obj_agent = var_obj[0], 
                 comp_type = comp_type, quantity = None, 
                 subj_entity = var_subj[1], subj_attribute = var_subj[2], subj_unit = var_subj[3], 
                 obj_entity = var_obj[1], obj_attribute = var_obj[2], obj_unit = var_obj[3])            
        elif typ == PartWhole:
            whole_attribute = None if not use_attribute else property_tracker.request_id(PropertyType.ATTRIBUTE)
            whole_unit = None if not use_unit else property_tracker.request_id(PropertyType.UNIT)

            n = random.randint(self.min_part_whole, self.max_part_whole) # NOTE: the current templates only support >1 part
            part_agents = [
                property_tracker.request_id(PropertyType.AGENT)
                for _ in range(n)
            ]
            part_entities = [
                property_tracker.request_id(PropertyType.ENTITY)
                for _ in range(n)
            ]
            part_attributes = [
                whole_attribute if whole_attribute is not None else (None if not use_attribute else property_tracker.request_id(PropertyType.ATTRIBUTE))
                for _ in range(n)
            ]
            part_units = [
                None # TODO: support and then: lf.unit if lf.unit is not None else (None if not use_unit else property_tracker.request_id(PropertyType.UNIT))
                for _ in range(n) 
            ]

            return PartWhole(quantity=None, whole_entity=property_tracker.request_id(PropertyType.ENTITY), whole_attribute=whole_attribute, whole_unit=whole_unit, 
                             part_agents=part_agents, part_entities=part_entities, part_attributes=part_attributes, part_units=part_units)
        else:
            raise ValueError(f"Starting with {typ.__name__} not supported!")

    
    def expand_bfs(self, tree: ProofTree, root: LogicalForm, property_tracker: PropertyTracker) -> GenType[Tuple[LogicalForm, List[InferenceRule]], None, None]:
        """ Gradually tries to expand nodes in a BFS manner """
        leaves_queue = [root]
        while len(leaves_queue) > 0:
            leaf = leaves_queue.pop(0)
            leafnode = tree.nodes_by_lf[leaf]
            if not self.stopping_criterion.satisfied(leafnode, tree):
                valid_rules = [r for r in self.inference_rules if r.is_reverse_applicable(leaf, tree)]
                # try expand the next node
                if len(valid_rules) > 0: # we can actually extend on this node
                    yield (leaf, valid_rules)
                    premises = tree.nodes_by_lf[leaf].premises
                    leaves_queue.extend(premises)
                else:
                    # if we cannot extend => mark it as an axiom
                    leaf.make_axiom(property_tracker)
            else:
                # mark the final nodes as axioms
                leaf.make_axiom(property_tracker)