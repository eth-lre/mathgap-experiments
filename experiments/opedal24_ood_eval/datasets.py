from typing import List, Dict

from mathgap.logicalforms.logicalform import LogicalForm
from mathgap.natlang.templates.template import WHITESPACE
from mathgap.trees.generators import MultiGenerator
from mathgap.trees.sampling.order import OrderSampler
from mathgap.generation_util import *

from data.util import DATA_FOLDER


def generate_linear_comparison(nr_problems: int, min_depth: int, max_depth: int, seed: int = None, data_folder: str = DATA_FOLDER) -> List[Dict[str, str]]:
    """ 
        Generates a dataset of linear mwps with comparison inference rules, where the underlying proof tree is of depth between min_depth and max_depth.
    """

    # 1. Define the generators for generating the proof-trees
    #    In our case, we want a mixture of depths, where each depth is equally likely to occur 
    #    (hence all sub-generators have weight 1.0)
    weights_by_generator = {
        default_generator(use_attribute=atrr_unit[0], use_unit=atrr_unit[1], 
                          comp_same_entity_prob=1.0, compeq_same_entity_prob=1.0,
                          stopping_criterion=BranchDepthCriterion(i), 
                          start_types=CONT_START_TYPE, inference_rules=COMP_RULESET): 1.0
        for i in range(min_depth, max_depth+1) for atrr_unit in [[False, False], [True, False], [False, True]]
    }
    generator = MultiGenerator(weights_by_generator)

    # 2. Load the default instantiator but use the agents, entities etc specified in the data-folder of this experiment
    #    The instantiator will be used to instantiate properties with values (e.g. agent1 -> Alice, quantity1 -> 4)
    instantiator = default_instantiator(data_folder=data_folder, dataversion="v1", leaf_min_value=2, leaf_max_value=20, 
                                        inner_min_value=2, inner_max_value=10_000)
    
    # 3. Load template renderers and samplers
    #    They will be used to express logical forms and deduction steps as natural language
    ps_template_sampler, ps_answers_template_sampler, ps_renderer, rt_template_sampler, rt_renderer \
        = default_templates_and_samplers(data_folder, "v1", WHITESPACE)

    # 4. Now, we actually generate the mwps
    mwps = generate_mwps(nr_problems, generator, instantiator, CANONICAL_ORDER_SAMPLER, 
                         ps_template_sampler, ps_answers_template_sampler, ps_renderer, 
                         rt_template_sampler, rt_renderer, seed)

    # 5. extract the required information from the mwps
    return [{
        "problem": mwp.ps_nl,
        "reasoning_trace": mwp.rt_nl,
        "answer": mwp.numerical_answers[-1],
        "answer_nl": mwp.answers_nl,
        "depth": mwp.tree.depth,
        "width": len(mwp.tree.leaf_nodes)
    } for mwp in mwps]

def generate_linear_transfer(nr_problems: int, min_depth: int, max_depth: int, seed: int = None, data_folder: str = DATA_FOLDER) -> List[Dict[str, str]]:
    """ 
        Generates a dataset of linear mwps with transfer inference rules, where the underlying proof tree is of depth between min_depth and max_depth.
    """
    weights_by_generator = {
        default_generator(use_attribute=atrr_unit[0], use_unit=atrr_unit[1], 
                          comp_same_entity_prob=1.0, compeq_same_entity_prob=1.0, 
                          stopping_criterion=BranchDepthCriterion(i), 
                          start_types=CONT_START_TYPE, inference_rules=TRANSFER_RULESET): 1.0
        for i in range(min_depth, max_depth+1) for atrr_unit in [[False, False], [True, False], [False, True]]
    }
    generator = MultiGenerator(weights_by_generator)

    instantiator = default_instantiator(data_folder=data_folder, dataversion="v1", leaf_min_value=2, leaf_max_value=20, 
                                        inner_min_value=2, inner_max_value=10_000)
    
    ps_template_sampler, ps_answers_template_sampler, ps_renderer, rt_template_sampler, rt_renderer \
        = default_templates_and_samplers(data_folder, "v1", WHITESPACE)

    mwps = generate_mwps(nr_problems, generator, instantiator, CANONICAL_ORDER_SAMPLER, 
                         ps_template_sampler, ps_answers_template_sampler, ps_renderer, 
                         rt_template_sampler, rt_renderer, seed)

    return [{
        "problem": mwp.ps_nl,
        "reasoning_trace": mwp.rt_nl,
        "answer": mwp.numerical_answers[-1],
        "answer_nl": mwp.answers_nl,
        "depth": mwp.tree.depth,
        "width": len(mwp.tree.leaf_nodes)
    } for mwp in mwps]

def generate_linear_depth(nr_problems: int, min_depth: int, max_depth: int, seed: int = None, data_folder: str = DATA_FOLDER) -> List[Dict[str, str]]:
    """ 
        Generates a dataset of linear mwps with transfer and commparison inference rules, where the underlying proof tree is of depth between min_depth and max_depth.
    """
    weights_by_generator = {
        default_generator(use_attribute=atrr_unit[0], use_unit=atrr_unit[1], 
                          comp_same_entity_prob=1.0, compeq_same_entity_prob=1.0, 
                          stopping_criterion=BranchDepthCriterion(i), 
                          start_types=CONT_START_TYPE, inference_rules=COMP_TRANSFER_RULESET): 1.0
        for i in range(min_depth, max_depth+1) for atrr_unit in [[False, False], [True, False], [False, True]]
    }
    generator = MultiGenerator(weights_by_generator)

    instantiator = default_instantiator(data_folder=data_folder, dataversion="v1", leaf_min_value=2, leaf_max_value=20, 
                                        inner_min_value=2, inner_max_value=10_000)
    
    ps_template_sampler, ps_answers_template_sampler, ps_renderer, rt_template_sampler, rt_renderer \
        = default_templates_and_samplers(data_folder, "v1", WHITESPACE)

    mwps = generate_mwps(nr_problems, generator, instantiator, CANONICAL_ORDER_SAMPLER, 
                         ps_template_sampler, ps_answers_template_sampler, ps_renderer, 
                         rt_template_sampler, rt_renderer, seed)

    return [{
        "problem": mwp.ps_nl,
        "reasoning_trace": mwp.rt_nl,
        "answer": mwp.numerical_answers[-1],
        "answer_nl": mwp.answers_nl,
        "depth": mwp.tree.depth,
        "width": len(mwp.tree.leaf_nodes)
    } for mwp in mwps]


def generate_linear_partwhole(nr_problems: int, min_width: int, max_width: int, seed: int = None, data_folder: str = DATA_FOLDER) -> List[Dict[str, str]]:
    """ 
        Generates a dataset of linear mwps with part-whole inference rules, where the underlying proof tree is of depth 1 and has width between min_width and max_width.
    """
    weights_by_generator = {
        default_generator(use_attribute=attr, use_unit=False, 
                          comp_same_entity_prob=1.0, compeq_same_entity_prob=1.0, 
                          min_part_whole=min_width, max_part_whole=max_width, stopping_criterion=BranchDepthCriterion(1), 
                          start_types=PARTWHOLE_START_TYPE, inference_rules=PARTWHOLE_RULESET): 1.0
        for attr in [True, False]
    }
    generator = MultiGenerator(weights_by_generator)

    instantiator = default_instantiator(data_folder=data_folder, dataversion="v1", leaf_min_value=2, leaf_max_value=20, 
                                        inner_min_value=2, inner_max_value=10_000)
    
    ps_template_sampler, ps_answers_template_sampler, ps_renderer, rt_template_sampler, rt_renderer \
        = default_templates_and_samplers(data_folder, "v1", WHITESPACE)

    mwps = generate_mwps(nr_problems, generator, instantiator, CANONICAL_ORDER_SAMPLER, 
                         ps_template_sampler, ps_answers_template_sampler, ps_renderer, 
                         rt_template_sampler, rt_renderer, seed)

    return [{
        "problem": mwp.ps_nl,
        "reasoning_trace": mwp.rt_nl,
        "answer": mwp.numerical_answers[-1],
        "answer_nl": mwp.answers_nl,
        "depth": mwp.tree.depth,
        "width": len(mwp.tree.leaf_nodes)
    } for mwp in mwps]

def generate_nonlinear_comparison(nr_problems: int, min_depth: int, max_depth: int, seed: int = None, data_folder: str = DATA_FOLDER) -> List[Dict[str, str]]:
    """ 
        Generates a dataset of nonlinear mwps with comparison inference rules, where the underlying proof tree is of depth between min_depth and max_depth.
    """

    weights_by_generator = {
        default_generator(use_attribute=atrr_unit[0], use_unit=atrr_unit[1], 
                          comp_same_entity_prob=1.0, compeq_same_entity_prob=1.0,
                          stopping_criterion=BranchDepthCriterion(i), 
                          rule_sampling_policy = NONLINEAR_POLICY,
                          #start_types=NONLINEAR_START_TYPE, 
                          start_types=[Container],
                          inference_rules=NONLINEAR_RULESET): 1.0
        for i in range(min_depth, max_depth+1) for atrr_unit in [[False, False], [True, False], [False, True]]
    }
    generator = MultiGenerator(weights_by_generator)

    instantiator = default_instantiator(data_folder=data_folder, dataversion="long", leaf_min_value=2, leaf_max_value=20, 
                                        inner_min_value=2, inner_max_value=10_000, strategy="cpga")
    
    ps_template_sampler, ps_answers_template_sampler, ps_renderer, rt_template_sampler, rt_renderer \
        = default_templates_and_samplers(data_folder, "v1", WHITESPACE)

    mwps = generate_mwps(nr_problems, generator, instantiator, CANONICAL_ORDER_SAMPLER, 
                         ps_template_sampler, ps_answers_template_sampler, ps_renderer, 
                         rt_template_sampler, rt_renderer, seed)

    return [{
        "problem": mwp.ps_nl,
        "reasoning_trace": mwp.rt_nl,
        "answer": mwp.numerical_answers[-1],
        "answer_nl": mwp.answers_nl,
        "depth": mwp.tree.depth,
        "width": len(mwp.tree.leaf_nodes)
    } for mwp in mwps] 

def generate_moved_linear_comparison(nr_problems: int, depth: int, move_idx: int = 0, seed: int = None, data_folder: str = DATA_FOLDER) -> List[Dict[str, str]]:
    """ 
        Generates a dataset of linear mwps with comparison inference rules, 
        where the sentences indexed by move_idx has been moved to the front in relation to canonical order
        move_idx = 0 defaults to no movement
    """
    assert 0 <= move_idx <= depth

    # 1. Define the generators for generating the proof-trees
    #    In our case, we want a mixture of depths, where each depth is equally likely to occur 
    #    (hence all sub-generators have weight 1.0)
    weights_by_generator = {
        default_generator(use_attribute=atrr_unit[0], use_unit=atrr_unit[1], 
                          comp_same_entity_prob=1.0, compeq_same_entity_prob=1.0,
                          stopping_criterion=BranchDepthCriterion(depth), 
                          start_types=CONT_START_TYPE, inference_rules=COMP_RULESET): 1.0
        for atrr_unit in [[False, False], [True, False], [False, True]]
    }
    generator = MultiGenerator(weights_by_generator)

    # 2. Load the default instantiator but use the agents, entities etc specified in the data-folder of this experiment
    #    The instantiator will be used to instantiate properties with values (e.g. agent1 -> Alice, quantity1 -> 4)
    instantiator = default_instantiator(data_folder=data_folder, dataversion="v1", leaf_min_value=2, leaf_max_value=20, 
                                        inner_min_value=2, inner_max_value=10_000)
    
    # 3. Load template renderers and samplers
    #    They will be used to express logical forms and deduction steps as natural language
    ps_template_sampler, ps_answers_template_sampler, ps_renderer, rt_template_sampler, rt_renderer \
        = default_templates_and_samplers(data_folder, "v1", WHITESPACE)

    # 4. Now, we actually generate the mwps
    mwps = generate_mwps(nr_problems, generator, instantiator, FrontMovementOrderSampler(move_idx), 
                         ps_template_sampler, ps_answers_template_sampler, ps_renderer, 
                         rt_template_sampler, rt_renderer, seed)

    # 5. extract the required information from the mwps
    return [{
        "problem": mwp.ps_nl,
        "reasoning_trace": mwp.rt_nl,
        "answer": mwp.numerical_answers[-1],
        "answer_nl": mwp.answers_nl,
        "depth": mwp.tree.depth,
        "width": len(mwp.tree.leaf_nodes)
    } for mwp in mwps]