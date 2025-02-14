from typing import Dict, List, Tuple
import random
from collections import Counter

from mathgap.natlang.templates.template import Template, TemplateType, TemplateCatalog

from mathgap.problemsample import ProblemOrder
from mathgap.trees.prooftree import ProofTree, TraversalOrder, TreeNode

class TemplateSelection:
    def __init__(self, primary_node_id: int, selection: List[Tuple[int, Template]]):
        self.primary_node_id = primary_node_id
        self.selection = selection

class TemplateSampler():
    from mathgap.logicalforms.logicalform import LogicalForm
    
    # TODO: extend this with context (i.e. different template based on context)
    def __init__(self, template_catalog: TemplateCatalog) -> None:
        self.template_catalog = template_catalog

    def choose_template(self, lf: LogicalForm, template_type: TemplateType, tree: ProofTree, seed: int = 14) -> Template:
        random.seed(seed)
        available_props = lf.get_available_properties()

        templates = self.template_catalog.get_templates_by_lf_and_type(type(lf), template_type)
        assert len(templates) > 0, f"Requires template for {type(lf)} of type {template_type}"
        templates = [t for t in templates if t.condition.is_satisified(lf=lf, tree=tree)]
        assert len(templates) > 0, f"None of the templates for {type(lf)} of type {template_type} have their conditions satisified: {lf}"
        # group the templates by the amount of information they use
        template_by_info: Dict[int, List[Template]] = {}
        for t in templates:
            required_properties = t.get_required_properties()
            required_prop_ids = set(required_properties)
            available_prop_ids = set(available_props.keys())

            # ignore templates for which we are missing information
            if not required_prop_ids.issubset(available_prop_ids): continue
            
            info_used = len(required_properties)
            template_by_info[info_used] = template_by_info.get(info_used, []) + [t]

        # select a template from the group that has the most overlap
        assert len(template_by_info.keys()) > 0, f"Requires at least 1 template but none found for available_prop_ids={set(available_props.keys())}, template_type={template_type}, lf={lf}"
        max_overlap = max(template_by_info.keys())
        template = random.choice(template_by_info[max_overlap])
        return template
    
class ReasoningTraceSampler:
    def __init__(self, template_sampler: TemplateSampler):
        self.sampler = template_sampler

    def sample(self, tree: ProofTree, problem: ProblemOrder, 
               preselected_templates: List[TemplateSelection] = None, 
               enforce_premise_axiom_consistency: bool = True,
               enforce_same_axiom_order: bool = True,
               seed: int = 14) -> List[TemplateSelection]:
        """ 
            Picks a template to express each conclusion and all premises in natural language. 

            - tree: the underlying prooftree
            - problem: the underlying problem(-order)
            - preselected_templates: for any conclusion-node or premise-node for which a template has been preselected, said template will be used 
                (only for non-preselected nodes, new templates will be selected)
            - enforce_premise_axiom_consistency: if true, then will try to enforce consistency between rendering of axioms as premises or standalone axioms in the problem formulation
            - enforce_same_axiom_order: if true, will render the axioms in the same order as they are given in the problem text
            - seed
        """
        assert tree.is_symbolically_computed, "Can only choose templates for a symbolically computed tree"
        
        preselected_templates_by_primary_node_id = {} if preselected_templates is None else {s.primary_node_id: {i:t for i,t in s.selection} for s in preselected_templates}
        template_selections = []

        for node in tree.traverse_reasoning_trace(problem.body_node_ids):
            selection: List[Tuple[int, Template]] = []
            if node.is_leaf and not enforce_same_axiom_order: continue # no need to provide reasoning for axioms
            
            node_id = tree.id_by_node[node]
            lf = node.logicalform
            
            # leaf nodes
            if node.is_leaf and enforce_same_axiom_order:
                if enforce_premise_axiom_consistency and (node_id in preselected_templates_by_primary_node_id):
                    # enforce consistency between premise and axiom
                    template = preselected_templates_by_primary_node_id[node_id][node_id]
                else:
                    # sample new template
                    template = self.sampler.choose_template(lf, TemplateType.STATEMENT, tree, seed)
                assert template.template_type == TemplateType.STATEMENT, f"Template should be a statement and not {template.template_type.name}"
                assert template.condition.is_satisified(lf=lf, tree=tree), "Template should still be valid!"
                selection.append((node_id, template))
                template_selections.append(TemplateSelection(node_id, selection))
                seed += 1

                continue

            # premises
            if not enforce_same_axiom_order:
                for premise_node in node.child_nodes:
                    premise_node_id = tree.id_by_node[premise_node]
                    premise_lf = premise_node.logicalform
                    if (node_id in preselected_templates_by_primary_node_id) and (premise_node_id in preselected_templates_by_primary_node_id[node_id]):
                        # try using preselected template
                        template = preselected_templates_by_primary_node_id[node_id][premise_node_id]
                    elif premise_node.is_leaf and enforce_premise_axiom_consistency and (premise_node_id in preselected_templates_by_primary_node_id):
                        # enforce consistency between premise and axiom
                        template = preselected_templates_by_primary_node_id[premise_node_id][premise_node_id]
                    else:
                        # sample new template
                        template = self.sampler.choose_template(premise_lf, TemplateType.STATEMENT, tree, seed)
                    assert template.template_type == TemplateType.STATEMENT, f"Template should be a statement and not {template.template_type.name}"
                    assert template.condition.is_satisified(lf=premise_lf, tree=tree), "Template should still be valid!"
                    selection.append((premise_node_id, template))
                    seed += 1

            # conclusion
            if node_id in preselected_templates_by_primary_node_id and node_id in preselected_templates_by_primary_node_id[node_id]:
                # try using preselected template
                template = preselected_templates_by_primary_node_id[node_id][node_id]
                assert template.template_type == TemplateType.CONCLUSION, f"Preselected template should be a conclusion and not {template.template_type.name}"
                assert template.condition.is_satisified(lf=lf, tree=tree), "Preselected template should still be valid!"
            else:
                # sample new template
                template = self.sampler.choose_template(lf, TemplateType.CONCLUSION, tree, seed)
            selection.append((node_id, template))

            template_selections.append(TemplateSelection(node_id, selection))
            seed += 1

        return template_selections

class ProblemStructureSampler:
    def __init__(self, template_sampler: TemplateSampler):
        self.sampler = template_sampler

    def sample(self, tree: ProofTree, problem: ProblemOrder, 
               preselected_templates: List[TemplateSelection] = None, 
               override_sampler_by_node_id: Dict[int, TemplateSampler] = None, 
               seed: int = 14) -> List[TemplateSelection]:
        """ 
            Picks a template to express each logical form of the problem structure in natural language 
            
            - tree: underlying prooftree
            - problem: problem structure specifying the exact problem given the tree
            - preselected_templates: for any node for which a template has been preselected, said template will be used 
                (only for non-preselected nodes, new templates will be selected)
            - override_sampler_by_node_id: if a sampler is specified for a node-id then that one will be used, otherwise the standard template sampler is used
            - seed
        """
        preselected_templates_by_primary_node_id = {} if preselected_templates is None else {s.primary_node_id: {i:t for i,t in s.selection} for s in preselected_templates}
        override_sampler_by_node_id = override_sampler_by_node_id if override_sampler_by_node_id is not None else {}
        template_selections = []

        # body
        for lf in problem.get_body(tree):
            node = tree.nodes_by_lf[lf]
            node_id = tree.id_by_node[node]
            if node_id in preselected_templates_by_primary_node_id:
                # try use preselected template
                template = preselected_templates_by_primary_node_id[node_id][node_id]
                assert template.template_type == TemplateType.STATEMENT, f"Preselected template should be a statement and not {template.template_type.name}"
                assert template.condition.is_satisified(lf=lf, tree=tree), "Preselected template should still be valid!"
            else:
                # sample new template
                sampler = override_sampler_by_node_id.get(node_id, self.sampler)
                template = sampler.choose_template(lf, TemplateType.STATEMENT, tree, seed)
            template_selections.append(TemplateSelection(node_id, [(node_id, template)]))
            seed += 1 # NOTE: otherwise we continuously choose the same template for a type of lf

        # questions
        for lf in problem.get_questions(tree):
            node = tree.nodes_by_lf[lf]
            node_id = tree.id_by_node[node]

            if node_id in preselected_templates_by_primary_node_id:
                # try use preselected template
                template = preselected_templates_by_primary_node_id[node_id][node_id]
                assert template.template_type == TemplateType.QUESTION, f"Preselected template should be a questino and not {template.template_type.name}"
                assert template.condition.is_satisified(lf=lf, tree=tree), "Preselected template should still be valid!"
            else:
                # sample new template
                sampler = override_sampler_by_node_id.get(node_id, self.sampler)
                template = sampler.choose_template(lf, TemplateType.QUESTION, tree, seed)

            template_selections.append(TemplateSelection(node_id, [(node_id, template)]))
            seed += 1 # NOTE: otherwise we continuously choose the same template for a type of lf

        return template_selections
    
class ProblemStructureAnswersSampler:
    def __init__(self, template_sampler: TemplateSampler):
        self.sampler = template_sampler

    def sample(self, tree: ProofTree, problem: ProblemOrder, 
               preselected_templates: List[TemplateSelection] = None, 
               seed: int = 14) -> List[TemplateSelection]:
        """ 
            Picks a template to express each answer to the questions asked in the problem structure in natural language 

            - tree: underlying prooftree
            - problem: problem structure specifying the exact problem given the tree
            - preselected_templates: for any node for which a template has been preselected, said template will be used 
                (only for non-preselected nodes, new templates will be selected)
            - seed
        """
        assert tree.is_symbolically_computed, "We require the tree to be solved in order to select templates for answering."
        
        preselected_templates_by_primary_node_id = {} if preselected_templates is None else {s.primary_node_id: {i:t for i,t in s.selection} for s in preselected_templates}

        template_selections = []
        for lf in problem.get_questions(tree):
            node = tree.nodes_by_lf[lf]
            node_id = tree.id_by_node[node]
            
            if node_id in preselected_templates_by_primary_node_id:
                # try use preselected template
                template = preselected_templates_by_primary_node_id[node_id][node_id]
                assert template.template_type == TemplateType.STATEMENT, f"Preselected template should be a statement and not {template.template_type.name}"
                assert template.condition.is_satisified(lf=lf, tree=tree), "Preselected template should still be valid!"
            else:
                # sample new template
                template = self.sampler.choose_template(lf, TemplateType.STATEMENT, tree, seed)

            template_selections.append(TemplateSelection(node_id, [(node_id, template)]))
            seed += 1 # NOTE: otherwise we continuously choose the same template for a type of lf

        return template_selections
