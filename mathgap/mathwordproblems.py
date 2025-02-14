from typing import Dict, List, Optional
import os
import pickle

from pydantic import BaseModel, Field
from mathgap.natlang.templates.sampling import TemplateSampler, TemplateSelection
from mathgap.trees import ProofTree
from mathgap.instantiate import Instantiation
from mathgap.natlang.templates import ReasoningTraceRenderer, ReasoningTraceSampler, ProblemStructureSampler, ProblemStructureRenderer, ProblemStructureAnswersSampler, RenderingMetadata, render_answers, render_problem, render_reasoning_trace
from mathgap.problemsample import ProblemOrder
from mathgap.trees.sampling import OrderSampler

class MathWordProblem(BaseModel):
    ps_nl: Optional[str] = Field(default=None) # problem with questions only
    answers_nl: Optional[str] = Field(default=None) # answers only
    rt_nl: Optional[str] = Field(default=None) # reasoning trace only
    ps_meta: Optional[RenderingMetadata] = Field(default=None, exclude=True)
    answers_meta: Optional[RenderingMetadata] = Field(default=None, exclude=True)
    rt_meta: Optional[RenderingMetadata] = Field(default=None, exclude=True)
    
    tree: Optional[ProofTree] = Field(default=None, exclude=True)
    instantiation: Optional[Instantiation] = Field(default=None, exclude=True)
    
    ps_template_sampler: Optional[ProblemStructureSampler] = Field(default=None, exclude=True)
    answers_template_sampler: Optional[ProblemStructureAnswersSampler] = Field(default=None, exclude=True)
    ps_renderer: Optional[ProblemStructureRenderer] = Field(default=None, exclude=True)
    rt_template_sampler: Optional[ReasoningTraceSampler] = Field(default=None, exclude=True)
    rt_renderer: Optional[ReasoningTraceRenderer] = Field(default=None, exclude=True)

    problem_order: Optional[ProblemOrder] = Field(default=None, exclude=True)
    numerical_answers: Optional[List[int]] = Field(default=None) # numerical answers to each subquestion
    

    def sample_problem_order(self, order_sampler: OrderSampler, seed: int = 14) -> ProblemOrder:
        """ Samples the problem, returns the visitation order """
        self.problem_order = order_sampler.sample_order(self.tree, seed)    

    def problem_as_nl(self, override_sampler_by_node_id: Dict[int, TemplateSampler] = None, preselected_templates: List[TemplateSelection] = None, seed: int = 14):
        """ Renders the problem structure as natural language """
        assert self.problem_order is not None, "Need to sample a problem structure first!"

        self.ps_nl, self.ps_meta = render_problem(self.tree, self.instantiation, self.problem_order, self.ps_template_sampler, self.ps_renderer, 
                                                  preselected_templates=preselected_templates, override_sampler_by_node_id=override_sampler_by_node_id, seed=seed)
        
    def reasoning_trace_as_nl(self, preselected_templates: List[TemplateSelection] = None, 
                              enforce_premise_axiom_consistency: bool = True, enforce_same_axiom_order: bool = True, seed: int = 14):
        """ Renders the reasoning trace for the problem structure as natural language """
        assert self.problem_order is not None, "Need to sample a problem structure first!"
        
        if self.ps_meta is not None:
            if preselected_templates is None and enforce_premise_axiom_consistency:
                # use the same way of expressing axioms as in the problem formulation
                preselected_templates = [ts for ts in self.ps_meta.template_selections if self.tree.node_by_id[ts.primary_node_id].is_leaf]
            else:
                raise NotImplementedError("Having both preselected templates while enforcing premise-axiom-consistency is not supported!")

        self.rt_nl, self.rt_meta = render_reasoning_trace(self.tree, self.instantiation, self.problem_order, self.rt_template_sampler, self.rt_renderer, 
                                                          preselected_templates=preselected_templates, enforce_premise_axiom_consistency=enforce_premise_axiom_consistency,
                                                          enforce_same_axiom_order=enforce_same_axiom_order, seed=seed)

    def answers_as_nl(self, preselected_templates: List[TemplateSelection] = None, seed: int = 14):
        """ Renders the answer(s) to the problem structure as natural language """
        assert self.problem_order is not None, "Need to sample a problem structure first!"

        self.answers_nl, self.answers_meta = render_answers(self.tree, self.instantiation, self.problem_order, self.answers_template_sampler, self.ps_renderer, 
                                                            preselected_templates=preselected_templates, seed=seed)

    def compute_answers(self):
        """ Compute the numerical answer(s) based on the instantiation and problem structure """
        assert self.problem_order is not None, "Requires problem structure to have been sampled"

        question_lfs = [self.tree.node_by_id[i].logicalform for i in self.problem_order.question_node_ids]
        self.numerical_answers = self.tree.instantiated_quantities(question_lfs, self.instantiation)
    
    def update_instantiation(self, instantiation: Instantiation):
        self.instantiation = instantiation

        self.ps_nl = None
        self.answers_nl = None
        self.rt_nl = None
        self.ps_meta = None
        self.answers_meta = None
        self.rt_meta = None
        self.numerical_answers = None

    def save(self, folder: str, name: str, include_metadata: bool = True, include_trees: bool = True, include_instantiation: bool = True):
        os.makedirs(folder, exist_ok=True)

        self_file = os.path.join(folder, f"{name}.json")
        with open(self_file, "w") as f:
            f.write(self.model_dump_json())

        if include_metadata:
            if self.ps_meta is not None:
                ps_meta_file = os.path.join(folder, f"{name}_ps_meta.pkz")
                with open(ps_meta_file, "wb") as f:
                    pickle.dump(self.ps_meta, f)

            if self.answers_meta is not None:
                answers_meta_file = os.path.join(folder, f"{name}_answers_meta.pkz")
                with open(answers_meta_file, "wb") as f:
                    pickle.dump(self.answers_meta, f)

            if self.rt_meta is not None:
                rt_meta_file = os.path.join(folder, f"{name}_rt_meta.pkz")
                with open(rt_meta_file, "wb") as f:
                    pickle.dump(self.rt_meta, f)

        if include_trees:
            tree_file = os.path.join(folder, f"{name}_tree.pkz")
            with open(tree_file, "wb") as f:
                pickle.dump(self.tree, f)

        if include_instantiation:
            instantiation_file = os.path.join(folder, f"{name}_instantiation.pkz")
            with open(instantiation_file, "wb") as f:
                pickle.dump(self.instantiation, f)

    def load(folder: str, name: str, sub_cls: type = None) -> 'MathWordProblem':
        self_file = os.path.join(folder, f"{name}.json")
        with open(self_file, "r") as f:
            sub_cls = MathWordProblem if sub_cls is None else sub_cls
            assert issubclass(sub_cls, MathWordProblem), "sub_cls needs to be either MathWordProblem or subtype thereof"
            model = sub_cls.model_validate_json(f.read())

        ps_meta_file = os.path.join(folder, f"{name}_ps_meta.pkz")
        if os.path.exists(ps_meta_file):
            with open(ps_meta_file, "rb") as f:
                model.ps_meta = pickle.load(f)

        answers_meta_file = os.path.join(folder, f"{name}_answers_meta.pkz")
        if os.path.exists(answers_meta_file):
            with open(answers_meta_file, "rb") as f:
                model.answers_meta = pickle.load(f)

        rt_meta_file = os.path.join(folder, f"{name}_rt_meta.pkz")
        if os.path.exists(rt_meta_file):
            with open(rt_meta_file, "rb") as f:
                model.rt_meta = pickle.load(f)

        tree_file = os.path.join(folder, f"{name}_tree.pkz")
        if os.path.exists(tree_file):
            with open(tree_file, "rb") as f:
                model.tree = pickle.load(f)

        instantiation_file = os.path.join(folder, f"{name}_instantiation.pkz")
        if os.path.exists(instantiation_file):
            with open(instantiation_file, "rb") as f:
                model.instantiation = pickle.load(f)

        return model

    class Config:
        arbitrary_types_allowed = True