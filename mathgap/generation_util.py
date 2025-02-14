from typing import List, Tuple, Generator as GeneratorType
import random

from mathgap.logicalforms.comp import ADDITIVE_COMP_TYPES, ComparisonType
from mathgap.natlang.templates.template import NEW_LINE, TextPart
from mathgap.trees.generators import Generator, GeneralGenerator, UniformPolicy, RuleSamplingPolicy, Criterion, BranchDepthCriterion
from mathgap.trees.generators.policies.nonlinearpolicy import NonlinearPolicy
from mathgap.trees.rules import ContTransferCont, ContCompCont, ContCompCompeqCont, ContContComp, ContPartWhole, InferenceRule
from mathgap.logicalforms import Container, PartWhole, LogicalForm, Comp
from mathgap.instantiate import PerPropTypeInstantiator, WordListInstantiator, PositiveRandIntInstantiator, PartAndUnitAwareEntityInstantiator, EntityAwareUnitInstantiator, Instantiator
from mathgap.properties import PropertyType
from mathgap.natlang.templates import TemplateSampler, ProblemStructureSampler, ProblemStructureRenderer, TemplateRenderer, ProblemStructureAnswersSampler, ReasoningTraceSampler, ReasoningTraceRenderer
from mathgap.data.util import load_templates, load_agents, load_attributes, load_entities, DATA_FOLDER
from mathgap import MathWordProblem
from mathgap.trees.sampling.canonical import CanonicalOrderSampler
from mathgap.trees.sampling.order import OrderSampler
from mathgap.trees.sampling.movement import FrontMovementOrderSampler

CONT_START_TYPE = [
    Container
]

NONLINEAR_START_TYPE = [
    Container,
    Comp
]

FULL_START_TYPES = [
    Container,
    PartWhole,
    Comp
]

PARTWHOLE_START_TYPE = [
    PartWhole
]

NONLINEAR_RULESET = [
    ContCompCont(),
    ContCompCompeqCont(),
    ContContComp(),
]

FULL_NONLINEAR_RULESET = [
    ContTransferCont(),
    ContCompCont(),
    ContCompCompeqCont(),
    ContContComp(),
    ContPartWhole(),
]

TRANSFER_PARTWHOLE_RULESET = [
    ContTransferCont(),
    ContPartWhole(),
]

COMP_RULESET = [
    ContCompCont(),
]

TRANSFER_RULESET = [
    ContTransferCont(),
]

PARTWHOLE_RULESET = [
    ContPartWhole(),
]

COMP_PARTWHOLE_RULESET = [
    ContCompCont(),
    ContPartWhole(),
]

COMPEQ_PARTWHOLE_RULESET = [
    ContCompCont(),
    ContCompCompeqCont(),
    ContContComp(),
    ContPartWhole(),
]

UNIFORM_POLICY = UniformPolicy()
NONLINEAR_POLICY = NonlinearPolicy()
DEPTH_3_CRITERION = BranchDepthCriterion(3)

CANONICAL_ORDER_SAMPLER = CanonicalOrderSampler()

def default_generator(start_types: List[LogicalForm] = FULL_START_TYPES, inference_rules: List[InferenceRule] = FULL_NONLINEAR_RULESET,
                      rule_sampling_policy: RuleSamplingPolicy = UNIFORM_POLICY, stopping_criterion: Criterion = DEPTH_3_CRITERION, 
                      use_attribute: bool = False, use_unit: bool = False, min_part_whole: int = 2, max_part_whole: int = 4,
                      comp_same_entity_prob: float = 0.5, compeq_same_entity_prob: float = 0.5, 
                      comp_allowed_comparisons: List[ComparisonType] = ADDITIVE_COMP_TYPES) -> Generator:
    generator = GeneralGenerator(
        start_types=start_types,
        inference_rules=inference_rules, 
        rule_sampling_policy=rule_sampling_policy, 
        stopping_criterion=stopping_criterion,
        use_attribute=use_attribute,
        use_unit=use_unit,
        min_part_whole=min_part_whole,
        max_part_whole=max_part_whole,
        comp_same_entity_prob=comp_same_entity_prob,
        compeq_same_entity_prob=compeq_same_entity_prob,
        comp_allowed_comparisons=comp_allowed_comparisons
    )

    return generator

def default_instantiator(data_folder: str = DATA_FOLDER, dataversion: str = "v1", leaf_min_value: int = 2, leaf_max_value: int = 10, 
                         inner_min_value: int = 2, inner_max_value: int = 10_000, max_attempts: int = 100_000, 
                         strategy: str = "random", validate_preselected: bool = True,
                         agents: List[str] = None) -> Instantiator:
    if agents is None:
        agents = load_agents(data_folder=data_folder, version=dataversion)

    entities = load_entities(data_folder=data_folder, version=dataversion)
    entities_without_units = entities["entities_without_units"]
    entities_with_units = entities["entities_with_units"]
    parts_by_whole = entities["parts_by_whole"]
    attributes = load_attributes(data_folder=data_folder, version=dataversion)

    instantiator = PerPropTypeInstantiator(
        agent_inst=WordListInstantiator(PropertyType.AGENT, agents, enforce_uniqueness=True),
        number_inst=PositiveRandIntInstantiator(leaf_min_value=leaf_min_value, leaf_max_value=leaf_max_value, 
                                                inner_min_value=inner_min_value, inner_max_value=inner_max_value, 
                                                max_attempts=max_attempts, strategy=strategy, validate_preselected=validate_preselected),
        entity_inst=PartAndUnitAwareEntityInstantiator(entities_without_units, list(entities_with_units.keys()), parts_by_whole, enforce_uniqueness=True, enforce_uniqueness_on_parts=False),
        attribute_inst=WordListInstantiator(PropertyType.ATTRIBUTE, attributes, enforce_uniqueness=True),
        unit_inst=EntityAwareUnitInstantiator(entities_with_units)
    )

    return instantiator

def default_templates_and_samplers(data_folder: str = DATA_FOLDER, dataversion: str = "v1", end_of_deduction_step_separator: TextPart = NEW_LINE) \
    -> Tuple[ProblemStructureSampler, ProblemStructureAnswersSampler, ProblemStructureRenderer, ReasoningTraceSampler, ReasoningTraceRenderer]:
    template_catalog = load_templates(data_folder=data_folder, version=dataversion)
    template_sampler = TemplateSampler(template_catalog)
    template_renderer = TemplateRenderer()
    ps_template_sampler = ProblemStructureSampler(template_sampler)
    ps_answers_template_sampler = ProblemStructureAnswersSampler(template_sampler)
    ps_renderer = ProblemStructureRenderer(template_renderer)
    rt_template_sampler = ReasoningTraceSampler(template_sampler)
    rt_renderer = ReasoningTraceRenderer(template_renderer, end_of_deduction_step_separator)

    return ps_template_sampler, ps_answers_template_sampler, ps_renderer, rt_template_sampler, rt_renderer

def generate_mwps(nr_problems: int, generator: Generator, instantiator: Instantiator, order_sampler: OrderSampler,
                  ps_template_sampler: ProblemStructureSampler, ps_answers_template_sampler: ProblemStructureAnswersSampler,
                  ps_renderer: ProblemStructureRenderer, rt_template_sampler: ReasoningTraceSampler, rt_renderer: ReasoningTraceRenderer, 
                  seed: int = 14) -> List[MathWordProblem]:
    """ Generates a list of mathwordproblems """
    mwp_iter = generate_mwps_iter(generator, instantiator, order_sampler, 
                                  ps_template_sampler, ps_answers_template_sampler, ps_renderer, 
                                  rt_template_sampler, rt_renderer, seed)
    return [
        next(mwp_iter)
        for i in range(nr_problems)
    ]

def generate_mwps_iter(generator: Generator, instantiator: Instantiator, order_sampler: OrderSampler,
                       ps_template_sampler: ProblemStructureSampler, ps_answers_template_sampler: ProblemStructureAnswersSampler,
                       ps_renderer: ProblemStructureRenderer, rt_template_sampler: ReasoningTraceSampler, rt_renderer: ReasoningTraceRenderer, 
                       seed: int = 14) -> GeneratorType[MathWordProblem, None, None]:
    """ Generates a list of mathwordproblems iteratively """
    _seed = seed
    while True:
        random.seed(_seed)
        _seed = random.randint(0, 2**32 - 1)
            
        # 1. generate the tree
        tree = generator.generate(seed=_seed)
        
        # 2. try to instantiate the properties of the tree ...
        try:
            instantiation = instantiator.instantiate(tree, seed=_seed)
            mwp = MathWordProblem(tree=tree, instantiation=instantiation, 
                                  ps_template_sampler=ps_template_sampler, answers_template_sampler=ps_answers_template_sampler, 
                                  ps_renderer=ps_renderer, rt_template_sampler=rt_template_sampler, rt_renderer=rt_renderer)
            
            # ... if successful:
            
            # 3. sample the leaf nodes of the tree in some specific order
            mwp.sample_problem_order(order_sampler, seed=_seed)

            # 4. compute the actual answers of the mwp given the problem order and instantiation
            mwp.compute_answers()

            # 5. render the problem, its reasoning trace and answer into natural language
            mwp.problem_as_nl(seed=_seed)
            mwp.reasoning_trace_as_nl(seed=_seed)
            mwp.answers_as_nl(seed=_seed)

            yield mwp
        except ValueError as e:
            # NOTE: instantiation can fail, in this case we simply retry with a different structure
            print(e)
