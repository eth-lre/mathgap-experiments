# Generates a basic logical form with a couple properties
lf_name = "CompEq"

fields = [
    ("subj_agent", "AGENT"),
    ("subj_entity", "ENTITY"),
    ("subj_attribute", "ATTRIBUTE"),
    ("subj_unit", "UNIT"), 
    ("obj_agent", "AGENT"),
    ("obj_entity", "ENTITY"),
    ("obj_attribute", "ATTRIBUTE"),
    ("obj_unit", "UNIT"), 
    ("comp_type", "COMPARISON"),
    ("other_subj_agent", "AGENT"),
    ("other_subj_entity", "ENTITY"),
    ("other_subj_attribute", "ATTRIBUTE"),
    ("other_subj_unit", "UNIT"), 
    ("other_obj_agent", "AGENT"),
    ("other_obj_entity", "ENTITY"),
    ("other_obj_attribute", "ATTRIBUTE"),
    ("other_obj_unit", "UNIT"),
    ("other_comp_type", "COMPARISON")
]

# LOGICAL FORM
print()
print("LOGICAL FORM:")

def init_param(field):
    cls_types = {
        "AGENT": "int",
        "QUANTITY": "Expr",
        "ENTITY": "int",
        "ATTRIBUTE": "int",
        "UNIT": "int",
        "COMPARISON": "ComparisonType"
    }
    
    name, cls = field
    return f"{name}: {cls_types.get(cls, cls)}"

def init_assign(field):
    name, cls = field
    return f"self.{name} = {name}"

def prop(field):
    name, cls = field
    return f"""    
    @property
    def {name}_prop(self) -> PropertyKey:
        return PropertyKey(PropertyType.{cls}, self.{name})"""

def get_available_properties(field):
    name, cls = field
    return f"if self.{name} is not None: available_properties[\"{name}\"] = self.{name}_prop"


# imports & init
print(f"""
from typing import Dict, List
from mathgap.properties import PropertyTracker
from mathgap.logicalforms.logicalform import LogicalForm, EntitySpec
from mathgap.logicalforms.comp import ComparisonType

from mathgap.properties import PropertyKey, PropertyType
from mathgap.expressions import Expr, Variable

class {lf_name}(LogicalForm):
    def __init__(self, {', '.join([init_param(f) for f in fields])}) -> None:""")

for f in fields:
    print(f"        {init_assign(f)}")

# properties
for f in fields:
    print(prop(f))

# get_available_properties
print(f"""
    def get_available_properties(self) -> def get_available_properties(self) -> Dict[str, PropertyKey|List[PropertyKey]]::
        available_properties = {{}}""")

for f in fields:
    print(f"        {get_available_properties(f)}")

print("        return available_properties")

print(f"""
    def get_quantities(self) -> List[Expr]:
        return [{', '.join(['self.' + str(f[0]) for f in fields if f[1] == 'QUANTITY'])}]""")

# abstract methods
print("""
    def get_entity_specs(self) -> List[EntitySpec]:
        ...""")

print("""
    def get_events(self) -> List[Event]:
        ...""")

print("""
    def make_axiom(self, property_tracker: PropertyTracker) -> None:
        ...""")

print()

# RENDERING AS TEXT
print()
print("RENDERING AS TEXT:")

def render_prop(ref, field):
     name,cls = field
     return f"{name}={{R({ref}.{name})}}"

print(f"""
class {lf_name}Renderer(Renderer):
    def render(self, {lf_name.lower()}: {lf_name}) -> str:
        return f"{lf_name.lower()}({', '.join([render_prop(lf_name.lower(), f) for f in fields])})"
""")