from typing import List
import os
from pathlib import Path

import click
import pandas as pd

from mathgap.renderers import TEXT_RENDERER, ProofTreeRenderer, write_network_utf8, TimeDAGRenderer
from mathgap.trees.generators import GeneralGenerator, UniformPolicy
from mathgap.trees.generators.stoppingcriteria import BranchDepthCriterion
from mathgap.trees.rules import ContTransferCont, ContCompCont, ContPartWhole, ContCompCompeqCont, ContContComp
from mathgap.trees.sampling import CanonicalOrderSampler, VariableTimeBasedSampler
from mathgap.logicalforms import Container, PartWhole
from mathgap.instantiate import PerPropTypeInstantiator, WordListInstantiator, PositiveRandIntInstantiator, PartAndUnitAwareEntityInstantiator, EntityAwareUnitInstantiator
from mathgap.properties import PropertyType, PropertyKey
from mathgap.natlang.templates import TextPart, ResolvePart, TemplateSampler, ReasoningTraceRenderer, ProblemStructureRenderer, TemplateRenderer, ReasoningTraceSampler, ProblemStructureSampler, ProblemStructureAnswersSampler, render_problem_and_answers, Origin, PropertyKeysOrigin
from mathgap.data.util import load_templates, load_agents, load_attributes, load_entities

def save_df_to_csv(df: pd.DataFrame, file_path: str):
    path = Path(file_path)
    folder_name = path.parent.name
    if not path.parent.exists():
        os.makedirs(folder_name, exist_ok=True)
    df.to_csv(file_path, index=False)

@click.group()
def cli():
    pass

def visualize_character_origins(origins: List[Origin]) -> str:
    p_type_rep = {
        PropertyType.AGENT: "a",
        PropertyType.QUANTITY: "n",
        PropertyType.ENTITY: "e",
        PropertyType.ATTRIBUTE: "@",
        PropertyType.UNIT: "u"
    }
    def visualize_origin(origin):
        if isinstance(origin, TextPart): 
            return "t"
        elif isinstance(origin, PropertyKeysOrigin):
            p_keys = origin.property_keys
            if isinstance(p_keys, PropertyKey):
                return p_type_rep[origin.property_keys.property_type]
            elif isinstance(p_keys, tuple):
                return p_type_rep[p_keys[0].property_type]
    return "".join([visualize_origin(o) for o in origins])

@cli.command()
@click.option("--depth", default=3, help="The depth of the tree that should be generated")
@click.option("--graph", default=False, is_flag=True, help="Will generate graphs and open them in the browser if set to true")
@click.option("--dataversion", default="v1", help="Which version of the instantiations and templates should be used?")
@click.option("-s", "--seed", default=140499, help="The seed to be used")
def example_nonlinear(depth, graph, dataversion, seed):
    # 1. generate the tree
    generator = GeneralGenerator(
        start_types=[Container, PartWhole],
        inference_rules=[
            ContTransferCont(),
            ContCompCont(),
            ContCompCompeqCont(),
            ContContComp(),
            ContPartWhole(),
        ], 
        rule_sampling_policy=UniformPolicy(), 
        stopping_criterion= BranchDepthCriterion(depth), # TreeWidthCriterion(preferred_width=10),
        max_part_whole=4,
        comp_same_entity_prob=0.5,
        compeq_same_entity_prob=0.5,
    )

    tree = generator.generate(seed=seed)    

    print("Proof Tree:")
    print(TEXT_RENDERER(tree, include_variable_times=True))
    print()

    # 2. sample the leaves of the tree to generate a problem-structure
    sampler = CanonicalOrderSampler()
    problem = sampler.sample_order(tree, seed=seed)
    print("Problem Sample:")
    print(TEXT_RENDERER(problem))
    print()

    # 3. instantiate the properties of the tree
    agents = load_agents(version=dataversion)
    entities = load_entities(version=dataversion)
    entities_without_units = entities["entities_without_units"]
    entities_with_units = entities["entities_with_units"]
    parts_by_whole = entities["parts_by_whole"]
    attributes = load_attributes(version=dataversion)
    
    instantiator = PerPropTypeInstantiator(
        agent_inst=WordListInstantiator(PropertyType.AGENT, agents, enforce_uniqueness=True),
        number_inst=PositiveRandIntInstantiator(leaf_min_value=2, leaf_max_value=10, inner_min_value=2, inner_max_value=10_000, max_attempts=100_000),
        entity_inst=PartAndUnitAwareEntityInstantiator(entities_without_units, list(entities_with_units.keys()), parts_by_whole, enforce_uniqueness=True, enforce_uniqueness_on_parts=True),
        attribute_inst=WordListInstantiator(PropertyType.ATTRIBUTE, attributes, enforce_uniqueness=True),
        unit_inst=EntityAwareUnitInstantiator(entities_with_units)
    )

    instantiation = instantiator.instantiate(tree, seed=seed)
    print("Instantiation:")
    print(TEXT_RENDERER(instantiation))
    print()

    # 4. convert problem to natural language
    template_catalog = load_templates(version=dataversion)
    template_sampler = TemplateSampler(template_catalog)
    template_renderer = TemplateRenderer()
    ps_template_sampler = ProblemStructureSampler(template_sampler)
    ps_answer_template_sampler = ProblemStructureAnswersSampler(template_sampler)
    ps_renderer = ProblemStructureRenderer(template_renderer)
    rt_template_sampler = ReasoningTraceSampler(template_sampler)
    rt_renderer = ReasoningTraceRenderer(template_renderer)

    print("Natural Language:")
    nl, metadata = render_problem_and_answers(tree, instantiation, problem, ps_template_sampler, ps_answer_template_sampler, ps_renderer, seed)
    print(nl)
    print(visualize_character_origins(metadata.origin_per_character))
    print()

    print("Reorderings:")
    print(problem.body_node_ids)
    vt_reorder_sampler = VariableTimeBasedSampler()
        
    for i in range(10):
        reordered_problem = vt_reorder_sampler.sample_order(tree, seed=seed+i)
        print(reordered_problem.body_node_ids)
        template_selection = ps_template_sampler.sample(tree, reordered_problem, seed=seed)
        problem_nl, problem_metadata = ps_renderer.render(tree, instantiation, template_selection)

        print(problem_nl)
        print(visualize_character_origins(problem_metadata.origin_per_character))
        print()

    # 5. generate CoT reasoning trace as natural language
    print("Reasoning Trace:")
    template_selection = rt_template_sampler.sample(tree, problem, seed=seed)
    cot_nl, cot_metadata = rt_renderer.render(tree, instantiation, template_selection)
    print(cot_nl)
    print(visualize_character_origins(cot_metadata.origin_per_character))
    print()
    
    if graph:
        print("Rendering as Graph...")
        network = ProofTreeRenderer().render(tree, problem.body_node_ids)
        time_dag = tree.build_time_dag()
        TimeDAGRenderer().render(time_dag, tree, network, transitive=True)
        write_network_utf8(network, filename="graph.html", open_browser=True)

        network = ProofTreeRenderer().render(tree, reordered_problem.body_node_ids)
        write_network_utf8(network, filename="graph_reordered.html", open_browser=True)

if __name__ == "__main__":
    cli()