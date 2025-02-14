from typing import Dict, List, Tuple

from mathgap.natlang.templates.sampling import TemplateSampler, TemplateSelection
from mathgap.trees import ProofTree
from mathgap.instantiate import Instantiation
from mathgap.natlang.templates import ProblemStructureSampler, ProblemStructureAnswersSampler, ProblemStructureRenderer, RenderingMetadata, NEW_LINE, WHITESPACE, TextPart, ReasoningTraceRenderer, ReasoningTraceSampler
from mathgap.problemsample import ProblemOrder

def render_problem(tree: ProofTree, instantiation: Instantiation, problem_structure: ProblemOrder,
                   ps_template_sampler: ProblemStructureSampler, renderer: ProblemStructureRenderer, 
                   preselected_templates: List[TemplateSelection] = None, override_sampler_by_node_id: Dict[int, TemplateSampler] = None,
                   seed: int = 14) -> Tuple[str, RenderingMetadata]:
    """ Renders a problem
        E.g:
            Jacob has 8 beds. Sophia has 5 lamps. Sophia has 2 lamps more than Mia has toy trucks. Jacob has 2 beds more than Christopher has toy bicycles. Sofia has 10 toy buses. Then, Sofia lost 4 toy buses. How many toy vehicles does everybody have together?

        - preselected_templates: list of preselected templates that should not be sampled
        - override_sampler_by_node_id: define the use of special samplers on a node_id basis
    """
    template_selection = ps_template_sampler.sample(tree, problem_structure, preselected_templates=preselected_templates, 
                                                    override_sampler_by_node_id=override_sampler_by_node_id, seed=seed)
    nl, meta = renderer.render(tree, instantiation, template_selection)

    return nl, meta

def render_answers(tree: ProofTree, instantiation: Instantiation, problem_structure: ProblemOrder,
                  ps_answer_template_sampler: ProblemStructureAnswersSampler, renderer: ProblemStructureRenderer, 
                  preselected_templates: List[TemplateSelection] = None, seed: int = 14) -> Tuple[str, RenderingMetadata]:
    """ Renders the corresponding answers to a problem
        E.g:
            Everybody together has 15 toy vehicles.

        - preselected_templates: list of preselected templates that should not be sampled
    """
    assert tree.is_symbolically_computed, "Cannot render answers of an unsolved tree"

    template_selection = ps_answer_template_sampler.sample(tree, problem_structure, preselected_templates=preselected_templates, seed=seed)
    nl, meta = renderer.render(tree, instantiation, template_selection)
    return nl, meta

def render_reasoning_trace(tree: ProofTree, instantiation: Instantiation, problem_structure: ProblemOrder,
               rt_template_sampler: ReasoningTraceSampler, renderer: ReasoningTraceRenderer, 
               preselected_templates: List[TemplateSelection] = None, enforce_premise_axiom_consistency: bool = True, 
               enforce_same_axiom_order: bool = True,
               seed: int = 14) -> Tuple[str, RenderingMetadata]:
    """ Renders the reasoning trace to a problem
        E.g:
            Alice has 2 apples. Bob has 5 apples more than Alice. Therefore, Bob has 7 apples.

        - preselected_templates: list of preselected templates that should not be sampled
        - enforce_premise_axiom_consistency: if preselected templates contains any assignment for any node under any circumstances this template will be reused if possible
    """
    assert tree.is_symbolically_computed, "Cannot render answers of an unsolved tree"

    template_selection = rt_template_sampler.sample(tree, problem_structure, preselected_templates=preselected_templates, 
                                                    enforce_premise_axiom_consistency=enforce_premise_axiom_consistency, 
                                                    enforce_same_axiom_order=enforce_same_axiom_order,
                                                    seed=seed)
    nl, meta = renderer.render(tree, instantiation, template_selection)
    return nl, meta

def join(nl_a: str, meta_a: RenderingMetadata, nl_b: str, meta_b: RenderingMetadata, separator: TextPart = NEW_LINE):
    """ Joins two texts that have been rendered individually """
    joined_txt = f"{nl_a}{separator.content}{nl_b}"
    joined_meta = meta_a.copy()
    joined_meta.join(meta_b, separator=separator, separator_num_characters=len(separator.content))
    return joined_txt, joined_meta

def render_problem_and_answers(tree: ProofTree, instantiation: Instantiation, problem_structure: ProblemOrder,
                   ps_template_sampler: ProblemStructureSampler, ps_answer_template_sampler: ProblemStructureAnswersSampler, 
                   renderer: ProblemStructureRenderer, seed: int = 14) -> Tuple[str, RenderingMetadata]:
    """ Renders a problem
        E.g:
            Jacob has 8 beds. Sophia has 5 lamps. Sophia has 2 lamps more than Mia has toy trucks. Jacob has 2 beds more than Christopher has toy bicycles. Sofia has 10 toy buses. Then, Sofia lost 4 toy buses. How many toy vehicles does everybody have together?
            Everybody together has 15 toy vehicles.
    """
    problem_nl, problem_metadata = render_problem(tree, instantiation, problem_structure, ps_template_sampler, renderer, seed=seed)    
    answers_nl, answers_meta = render_answers(tree, instantiation, problem_structure, ps_answer_template_sampler, renderer, seed=seed)

    return join(problem_nl, problem_metadata, answers_nl, answers_meta, separator=WHITESPACE)