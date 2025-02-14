from typing import Dict, List, Tuple

from mathgap.logicalforms import LogicalForm
from mathgap.instantiate import Instantiation
from mathgap.properties import PropertyKey, PropertyType
from mathgap.expressions import Expr, Variable
from mathgap.trees import ProofTree

from mathgap.natlang.templates.template import Template, TextPart, ResolvePart, TemplatePart, WHITESPACE, NEW_LINE
from mathgap.natlang.templates.sampling import TemplateSelection
from mathgap.natlang.templates.metadata import PropertyKeysOrigin, RenderingMetadata

class TemplateRenderer:
    """ 
        Renders a logical form given an instantiation using a natural language template.
        Keeps track of metadata.
    """
    def render(self, lf: LogicalForm, instantiation: Instantiation, template: Template, 
               prepend: List[TemplatePart] = [], append: List[TemplatePart] = [], parent_unit: List[int] = []) -> Tuple[str, RenderingMetadata]:
        available_props = lf.get_available_properties()
        out = ""
        metadata = RenderingMetadata()
        for i,part in enumerate(prepend + template.parts + append):
            ref_template = template if part in template.parts else None
            ref_lf = lf if part in template.parts else None
            unit = parent_unit + [i]

            part_str = None
            if isinstance(part, TextPart):
                part_str = part.content
                part_len = len(part_str)
                out += part_str
                metadata.append(part, unit, ref_lf, ref_template, part_len)
            elif isinstance(part, ResolvePart):
                prop_keys = available_props[part.content]
                part_str = ""
                if part.method == "property_list":
                    assert isinstance(prop_keys, list), f"Expecting a list of properties, got {type(prop_keys)}"
                    assert not any([pk.property_type == PropertyType.QUANTITY for pk in prop_keys]), f"Propertykeys of list cannot currently be quantities"
                    
                    join: str = part.kwargs["join"]
                    final_join: str = part.kwargs["final_join"]

                    instantiations = [str(instantiation[pk]) for pk in prop_keys]      
                    if len(instantiations) == 0:
                        part_str = ""
                    elif len(instantiations) == 1:
                        part_str = instantiations[0]
                    else:
                        part_str = join.join(instantiations[:-1])
                        part_str += final_join
                        part_str += instantiations[-1]

                    prop_keys = tuple(prop_keys)
                else:
                    assert isinstance(prop_keys, PropertyKey), f"Expecting a single property, got {type(prop_keys)}"
                    if part.method == "expression":
                        # rendering expressions of some depth
                        depth: int = part.kwargs["depth"]
                        expr: Expr = prop_keys.identifier
                        assert isinstance(expr, Expr), f"Rendering an expression of depth {depth}, requires {expr} to be of type Expr but got {type(expr)} instead"
                        part_str = expr.to_str(instantiation, depth=depth, with_parentheses=(depth > 1))
                    elif prop_keys.property_type == PropertyType.QUANTITY:
                        expr: Expr = prop_keys.identifier
                        assert isinstance(expr, Expr), f"Rendering a quantity, requires {expr} to be of type Expr but got {type(expr)} instead"
                        if isinstance(expr, Variable):
                            # only quantities that are variables can be looked up
                            part_str = str(instantiation[expr.identifier])
                        else:
                            # others are directly evaluated into numerals
                            part_str = str(expr.eval(instantiation))                        
                    else:
                        # default: lookup the instantiation
                        part_str = str(instantiation[prop_keys])
    
                assert part_str is not None, "We require the part to be rendered now"

                part_len = len(part_str)
                out += part_str

                metadata.append(PropertyKeysOrigin(prop_keys), unit, ref_lf, ref_template, part_len)
            else:
                raise ValueError(f"Encountered not supported template part! {part}")
        return out, metadata

class ProblemStructureRenderer:
    def __init__(self, template_renderer: TemplateRenderer):
        self.template_renderer = template_renderer
    
    def render(self, tree: ProofTree, instantiation: Instantiation, template_selections: List[TemplateSelection], append: List[TemplatePart] = []) -> Tuple[str, RenderingMetadata]:
        """ 
            Uses a selection of templates to render a problem structure into natural language.
            NOTE: If you call this with a template_selection generated on a different tree or instantiation,
            make sure it's still valid.
        """
        all_text = ""
        all_metadata = RenderingMetadata(template_selections=template_selections)
        for i,selection in enumerate(template_selections):
            is_last_selection = (len(template_selections) - 1 == i)
            assert len(selection.selection) == 1, "Only supporting rendering of a single template per node in problem-structure rendering."

            node_id, template = selection.selection[0]
            appendix = append if is_last_selection else [WHITESPACE]
            txt, metadata = self.template_renderer.render(tree.node_by_id[node_id].logicalform, instantiation, template, append=appendix, parent_unit=[i])
            metadata.node_ids.append((node_id, len(txt)))

            all_text += txt
            all_metadata += metadata

        return all_text, all_metadata
        
class ReasoningTraceRenderer:
    def __init__(self, template_renderer: TemplateRenderer, end_of_deduction_step_separator: TextPart = NEW_LINE):
        self.template_renderer = template_renderer
        self.eods_separator = end_of_deduction_step_separator
    
    def render(self, tree: ProofTree, instantiation: Instantiation, template_selections: List[TemplateSelection]) -> Tuple[str, RenderingMetadata]:
        """ 
            Uses a selection of templates to render a tree into natural language.
            NOTE: If you call this with a list of template_selections generated on a different tree or instantiation,
            make sure it's still valid.
        """
        assert tree.is_symbolically_computed, "Can only render a reasoning trace on a symbolically computed tree"
        all_text = ""
        all_metadata = RenderingMetadata(template_selections=template_selections)
        visisted_nodes = []
        for i,selection in enumerate(template_selections):
            is_last_selection = (len(template_selections) - 1 == i)
            for j, (node_id, template) in enumerate(selection.selection):
                if node_id in visisted_nodes: continue # skip nodes/facts we already stated

                visisted_nodes.append(node_id)
                is_last_template = (len(selection.selection) - 1 == j)
                node = tree.node_by_id[node_id]

                # NOTE: unfortunately, there's no smart way of automatically converting templates s.t. they are guaranteed to be valid.
                # We expect the user to manually edit the selection beforehand if that's the desired behaviour.
                assert template.condition.is_satisified(node.logicalform, tree), "Template-selection must be valid on the rendered instance!"
                
                # NOTE: this only works as long as the conclusion is rendered last and is always new (generally true for trees)
                appendix = [WHITESPACE] if not is_last_template else ([] if is_last_selection else [self.eods_separator])
                text, metadata = self.template_renderer.render(node.logicalform, instantiation, template, append=appendix, parent_unit=[i,j])
                all_text += text
                all_metadata += metadata
        return all_text, all_metadata
