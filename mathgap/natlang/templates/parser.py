from typing import Any, Dict, List
import re
import ast

from mathgap.natlang.templates.template import Template, TemplatePart, TextPart, ResolvePart, TemplateType
from mathgap.natlang.templates.condition import Condition, OrCondition, PropertyEqualityCondition, AndCondition, NotCondition, UNCONDITIONAL

class TemplateParser:
    """ 
        Default parser for templates that supports:
        - string based templates "[agent] has [quantity] {ent}."
        - partials (e.g. instead of {ent}, you could have any of ["[entity]", "[unit]s of [entity]", "[attribute] [entity]"])
        - conditions (e.g. instead of "[subj_agent] has [quantity] more [subj_entity] than [obj_agent] has [obj_entity]", 
            you might want to say "[subj_agent] has [quantity] more [subj_entity] than [obj_agent]" if subj_entity == obj_entity)
    """
    def parse(self, data: Dict) -> Dict[TemplateType, List[Template]]:
        """ Parses all templates in a template-file """                
        named_conditions = data.get("named_conditions", {})

        # 1. create unresolved templates (creates pointers to partials and named conditions)
        unresolved_templates_by_type = {
            TemplateType.STATEMENT: self._parse_templates_of_type(data["statements"], TemplateType.STATEMENT, named_conditions),
            TemplateType.QUESTION: self._parse_templates_of_type(data["questions"], TemplateType.QUESTION, named_conditions),
            TemplateType.CONCLUSION: self._parse_templates_of_type(data["conclusions"], TemplateType.CONCLUSION, named_conditions),
        }

        # 2. parse partials & named conditions
        partials = self._parse_partials(data["partials"])
        
        # 3. resolve templates recursively (follow pointers)
        resolved_templates_by_type: Dict[TemplateType, List[Template]] = {}
        for typ,templates in unresolved_templates_by_type.items():
            resolved_templates_by_type[typ] = self._resolve_rec(templates, partials)
        
        return resolved_templates_by_type

    def _parse_partials(self, partials_data: Dict) -> Dict[str, List[List[TemplatePart]]]:
        partials = {}
        for partial_name, partial_data in partials_data.items():
            partials[partial_name] = []
            # parse a single partial
            for tdata in partial_data:
                # parse a single template of that partial
                parts = self._parse_template_into_parts(tdata)
                partials[partial_name].append(parts)
        return partials
    
    def _parse_condition_from_ast(self, node) -> Condition:
        def _parse_variable(node):
            if isinstance(node, ast.List): # [] => property
                assert len(node.elts) == 1
                if isinstance(node.elts[0], ast.Name):
                    return "prop", node.elts[0].id
                elif isinstance(node.elts[0], ast.Attribute):
                    query_parts = []
                    attr = node.elts[0]
                    while isinstance(attr, ast.Attribute):
                        query_parts.append(attr.value.id) 
                        attr = attr.attr
                    query_parts.append(attr)
                    return "query", ".".join(query_parts)
                else:
                    raise ValueError(f"Unsupported structure: {ast.dump(node.elts[0])}")
            elif isinstance(node, ast.Name): # => constant
                return "const", node.id
            else:
                raise ValueError(f"Unsupported variable type {type(node)}")

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return AndCondition([self._parse_condition_from_ast(value) for value in node.values])
            elif isinstance(node.op, ast.Or):
                return OrCondition([self._parse_condition_from_ast(value) for value in node.values])
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return NotCondition(self._parse_condition_from_ast(node.operand))
        elif isinstance(node, ast.Compare):
            if isinstance(node.ops[0], ast.Eq):
                property_identifier = None
                const_value = None
                query = None
                
                # parse left and right to check if 
                ltype,lval = _parse_variable(node.left)
                rtype,rval = _parse_variable(node.comparators[0])

                if ltype == "const":
                    const_value = lval
                elif ltype == "query":
                    query = lval
                elif ltype == "prop":
                    property_identifier = lval
                
                if rtype == "const":
                    assert const_value is None, "Cannot have both sides of comparison be constants!"
                    const_value = rval
                elif rtype == "query":
                    assert query is None, "Comparing query with query currently not supported!"
                    query = rval
                elif rtype == "prop":
                    if query is None: # NOTE: query also supports properties
                        query = rval
                    else:
                        assert property_identifier is None
                        property_identifier = rval
                return PropertyEqualityCondition(property_identifier=property_identifier, const_value=const_value, query=query, typ="==")
        else:
            raise ValueError(f"Unsupported node: {ast.dump(node)}")

    def _parse_condition(self, cdata: str, named_conditions: Dict[str, str]):
        # substitute all {cname} until there are no more {
        def replacement(match):
            cname = match.group(1)
            return named_conditions.get(cname, "True")
        while "{" in cdata:
            cdata = re.sub(r'\{([^}]+)\}', replacement, cdata)
        
        # parse the condition that is free from substitutions
        tree = ast.parse(cdata, mode='eval')
        return self._parse_condition_from_ast(tree.body)

    def _parse_template_into_parts(self, template_data: str) -> List[TemplatePart]:
        assert isinstance(template_data, str), f"Expects {template_data} to be a string! Make sure you are using the correct template parser"
        pattern = r"(\[.*?\]|\{.*?\}|\s+)"
        part_datas = [part for part in re.split(pattern, template_data) if part]

        parts = []
        for pdata in part_datas:
            if pdata.startswith("["):
                prop_identifier = pdata[1:-1]
                # can append parameters with ;param_name=param_value;param2_name=param2_value etc
                if ";" in prop_identifier:
                    split_identifier = prop_identifier.split(";")
                    kwargs = {s.split("=")[0]:s.split("=")[1] for s in split_identifier[1:]}
                    if "depth" in kwargs:
                        kwargs["method"] = "expression"
                        kwargs["depth"] = int(kwargs["depth"])
                    elif "join" in kwargs:
                        kwargs["method"] = "property_list"
                    parts.append(ResolvePart(split_identifier[0], **kwargs))
                else:
                    parts.append(ResolvePart(prop_identifier, method="property"))

            elif pdata.startswith("{"):
                parts.append(ResolvePart(pdata[1:-1], method="partial"))
            else:
                parts.append(TextPart(content=pdata))
        return parts

    def _parse_templates_of_type(self, tdata: List, typ: TemplateType, named_conditions: Dict[str, str]) -> List[Template]:
        all_templates = []
        for group_data in tdata:
            # parse condition
            condition = UNCONDITIONAL
            if "condition" in group_data:
                condition = self._parse_condition(group_data["condition"], named_conditions)

            # parse a group
            templates_data = group_data["templates"]
            for template_data in templates_data:
                # parse a template
                parts = self._parse_template_into_parts(template_data)
                all_templates.append(Template(parts, typ, condition, {}))

        return all_templates
    
    def _resolve_rec(self, templates: List[Template], partials: Dict[str, List[TemplatePart]]) -> List[Template]:
        resolved_templates = []

        resolved_any_template = False
        for template in templates:
            resolved_any_part = False
            for i,part in enumerate(template.parts):
                if isinstance(part, ResolvePart) and part.method == "partial":
                    # resolve the first non-constant part with all potential substitutions
                    for sub in partials[part.content]:
                        sub_parts = template.parts[:i] + sub + template.parts[i+1:] # substitute the i-th part with the parts from the partial
                        resolved_templates.extend(self._resolve_rec([Template(sub_parts, template.template_type, template.condition, template.metadata)], partials))
                    resolved_any_part = True
                    resolved_any_template = True
                    break
            if not resolved_any_part:
                resolved_templates.append(template)

        if not resolved_any_template:
            # all templates are already resolved
            resolved_templates.extend(templates) 
        
        return resolved_templates
            

class TemplateWithMetadataParser(TemplateParser):
    """ Parses templates that contain metadata (per template but also per template part) """
    def _parse_template_into_parts(self, template_data: str|List) -> List[TemplatePart]:
        if isinstance(template_data, str):
            return super()._parse_template_into_parts(template_data)
        else:
            return [self._parse_part(pdata) for pdata in template_data]
    
    def _parse_templates_of_type(self, tdata: List, typ: TemplateType, named_conditions: Dict[str, str]) -> List[Template]:
        all_templates = super()._parse_templates_of_type(tdata, typ, named_conditions)

        # parse template metadata
        for group_data,template in zip(tdata, all_templates):
            metadata = {}
            if "metadata" in group_data:
                metadata = self._parse_metadata(group_data["metadata"])
            template.metadata = metadata

        return all_templates
    
    def _parse_metadata(self, gdata: Dict) -> Dict[str, Any]:
        return gdata
            
    def _parse_part(self, pdata: Dict) -> TemplatePart:
        content = pdata["content"]
        typ = pdata.get("type", None)
        if "resolve" in pdata:
            method = pdata["resolve"]
            # pass the rest of the properties on this part as a dict
            kwargs = { k:v for k,v in pdata.items() if k != "content" and k != "resolve" and k != "type" }
            return ResolvePart(content, method, **kwargs)
        return TextPart(content=content, typ=typ)