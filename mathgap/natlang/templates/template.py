from typing import Dict, List, Type, Optional
from enum import Enum

from mathgap.natlang.templates.origin import Origin
from mathgap.natlang.templates.condition import Condition

class TemplateType(Enum):
    STATEMENT = "statement"
    QUESTION = "question"
    CONCLUSION = "conclusion"


class TemplatePart(Origin):
    def __init__(self, content: str):
        self.content = content

class TextPart(TemplatePart):
    def __init__(self, content: str, typ: Optional[str] = None):
        super().__init__(content)
        self.typ = typ

    def __repr__(self):
        return self.content

class ResolvePart(TemplatePart):
    def __init__(self, content: str, method: str, *args, **kwargs):
        super().__init__(content)
        self.method = method
        self.kwargs = {**kwargs}

    def __repr__(self):
        if self.method == "property":
            return f"[{self.content}]"
        elif self.method == "partial":
            return f"{{{self.content}}}"
        else:
            kwargs_str = ";".join([f"{k}={v}" for k,v in self.kwargs.items()])
            return f"[{self.content};{kwargs_str}]"

class Template:
    def __init__(self, parts: List[TemplatePart], template_type: TemplateType, condition: Condition, metadata: Dict) -> None:
        self.parts = parts
        self.template_type = template_type
        self.condition = condition
        self.metadata = metadata
        self.required_properties = [p.content for p in parts if isinstance(p, ResolvePart) and p.method == "property"]

    def get_required_properties(self) -> List[str]:
        return self.required_properties
    
    def __repr__(self):
        return f"Template(parts={''.join([str(p) for p in self.parts])}, template_type={self.template_type}, condition={self.condition})"
    
class TemplateCatalog:
    def __init__(self, templates_by_lf_and_type: Dict[Type, Dict[TemplateType, List[Template]]]) -> None:
        self.templates_by_lf_and_type = templates_by_lf_and_type

    def get_templates_by_lf_and_type(self, lf_type: Type, template_type: TemplateType) -> List[Template]:
        return self.templates_by_lf_and_type[lf_type][template_type]
    
    def merge(self, other: 'TemplateCatalog', exclusive_override: bool = True):
        """ 
            Merges the other templatecatalog into this one 

            - exclusive_override: if true, then for each lf and type that is available in other,
                all of self of the same lf and type combination will be removed 
                (e.g. if other has entries for Transfer-Statements, none of self Transfer-Statements will be present in the final catalog)
        """
        for lf_type,coll in other.templates_by_lf_and_type.items():
            self.templates_by_lf_and_type[lf_type] = self.templates_by_lf_and_type.get(lf_type, {})

            for templ_type,templates in coll.items():
                if exclusive_override:
                    self.templates_by_lf_and_type[lf_type][templ_type] = []
                else:
                    self.templates_by_lf_and_type[lf_type][templ_type] = self.templates_by_lf_and_type[lf_type].get(templ_type, [])
                self.templates_by_lf_and_type[lf_type][templ_type] += templates

NEW_LINE = TextPart("\n")
WHITESPACE = TextPart(" ")