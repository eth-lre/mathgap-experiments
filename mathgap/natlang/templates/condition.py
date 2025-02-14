from typing import List

from mathgap.trees import ProofTree

class Condition:
    def is_satisified(self, *args, **kwargs) -> bool:
        ...

class PropertyEqualityCondition(Condition):
    from mathgap.logicalforms import LogicalForm
    """ 
        Equality of an uninstantiated property of the lf and either
        - a constant
        - a query that specifies a property of another lf on the same tree or the name of the rule that has been applied
            - conclusion.agent would refer to the agent of the conclusion that lf is a premise of
            - self.rule would refer to the name of the rule used to derive this node
    """
    def __init__(self, property_identifier: str, const_value: str = None, query: str = None, typ: str = "=="):
        assert query is not None or const_value is not None, "Equality of property must be either with a constant or a query"
        self.property_identifier = property_identifier
        self.const_value = const_value
        self.query = query
        self.typ = typ
    
    def is_satisified(self, lf: LogicalForm, tree: ProofTree, *args, **kwargs) -> bool:
        assert [self.property_identifier, self.const_value, self.query].count(None) == 1, "Comparison must take place between exactly 2 non-null values"
        
        # lhs will be coalesce(property, const)
        if self.property_identifier is not None:
            property_value = lf[self.property_identifier]
        else:
            property_value = self.const_value
        
        # rhs will be coalesce(query, const)
        if self.query is not None:
            # query
            query_parts = self.query.split(".")
            query_str = ".".join(query_parts[:-1])
            attr_str = query_parts[-1]
            node = tree.execute_query(tree.nodes_by_lf[lf], query_str)
            if attr_str == "rule":
                other_property_value = type(node.rule).__name__
            else:
                other_property_value = node.logicalform[attr_str]
        else:
            # constant
            other_property_value = self.const_value

        if self.typ == "==":
            return property_value == other_property_value
        elif self.typ == "!=":
            return property_value != other_property_value

    def __repr__(self):
        all_values = [
            f"[{self.property_identifier}]" if self.property_identifier is not None else None, 
            self.const_value,
            f"[*{self.query}]" if self.query is not None else None
        ]
        left = next(filter(lambda x: x is not None, all_values))
        right = next(filter(lambda x: x is not None and x != left, all_values))
        return f"({left} {self.typ} {right})"

class AndCondition(Condition):
    from mathgap.logicalforms import LogicalForm
    """ All conditions must be satisfied """
    def __init__(self, conditions: List[Condition]):
        self.conditions = conditions

    def is_satisified(self, lf: LogicalForm, tree: ProofTree, *args, **kwargs):
        return all([c.is_satisified(lf=lf, tree=tree, *args, **kwargs) for c in self.conditions])
    
    def __repr__(self):
        return f'({" and ".join([f"({c})" for c in self.conditions])})'
    
class OrCondition(Condition):
    from mathgap.logicalforms import LogicalForm
    """ Any condition must be satisfied """
    def __init__(self, conditions: List[Condition]):
        self.conditions = conditions

    def is_satisified(self, lf: LogicalForm, tree: ProofTree, *args, **kwargs):
        return any([c.is_satisified(lf=lf, tree=tree, *args, **kwargs) for c in self.conditions])
    
    def __repr__(self):
        return f'({" or ".join([f"({c})" for c in self.conditions])})'
    
class NotCondition(Condition):
    from mathgap.logicalforms import LogicalForm
    """ Inverses a condition """
    def __init__(self, condition: Condition):
        self.condition = condition

    def is_satisified(self, lf: LogicalForm, tree: ProofTree, *args, **kwargs):
        return not self.condition.is_satisified(lf=lf, tree=tree, *args, **kwargs)
    
    def __repr__(self):
        return f"(not {self.condition})"
    

class TrueCondition(Condition):
    def is_satisified(self, *args, **kwargs) -> bool:
        return True
    
    def __repr__(self):
        return "True"
    
UNCONDITIONAL = TrueCondition()