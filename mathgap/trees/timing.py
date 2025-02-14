from typing import Dict, List, Set, Tuple

from mathgap.properties import PropertyKey

class VariableKey:
    def __init__(self, key: List[PropertyKey]) -> None:
        self.variable_key = key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VariableKey): return False
        if not len(self.variable_key) == len(other.variable_key): return False
        return all([a == b for a,b in zip(self.variable_key, other.variable_key)])

    def __hash__(self) -> int:
        return hash(tuple(self.variable_key))
    
    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)

class VariableTimes:
    """ All the versions of variables involved at some point in time """
    def __init__(self, times_by_var: Dict[VariableKey, Set[int]]):
        self.times_by_var: Dict[VariableKey, Set[int]] = times_by_var
    
    def can_happen_after(self, other: 'VariableTimes') -> bool:
        """ 
            Returns true if self can happen after other, meaning
            there is no variable-key of self at time t1 that is also in other but at time t2 
            where t1 < t2 
        """
        for v_i, v_i_times in self.times_by_var.items():
            if not v_i in other.times_by_var: continue
            
            # only if it contains an entry for the same variable-key
            other_v_j_times = other.times_by_var[v_i]
            for v_i_time in v_i_times:
                for other_v_j_time in other_v_j_times:
                    if v_i_time < other_v_j_time: return False # self has a variable-key that implies it happens before other
        return True
    
    def __getitem__(self, key: VariableKey):
        return self.times_by_var[key]

    def __setitem__(self, key: VariableKey, value: int|Set[int]):
        if isinstance(value, int):
            value = {value}
        elif not isinstance(value, set) or not all(isinstance(i, int) for i in value):
            raise ValueError("Value must be an int or a set of int")
        self.times_by_var[key] = value

    def __contains__(self, key: VariableKey):
        return key in self.times_by_var
    
    def get(self, key: VariableKey, default: Set[int] = None):
        return self.times_by_var.get(key, default)
    
    def merge(self, other: 'VariableTimes') -> List[VariableKey]:
        """ Merges the other into self, returns the keys that were present in both """
        intersection_of_keys = []
        for v_i, v_i_times in self.times_by_var.items():
            if not v_i in other.times_by_var: continue # no information to merge
            
            intersection_of_keys.append(v_i)
            self.times_by_var[v_i] = v_i_times.union(other.times_by_var[v_i])

        for other_v_j, other_v_j_times in other.times_by_var.items():
            if not other_v_j in self.times_by_var:
                # other used variables that aren't present in self
                self.times_by_var[other_v_j] = other_v_j_times
        return intersection_of_keys
    
    def merge_all(self, others: List['VariableTimes']) -> List[VariableKey]:
        """ Merges all others into self, returns the keys that were present in multiple """
        all_conflicts = set([])
        for vts in others:
            conflicts = self.merge(vts)
            all_conflicts = all_conflicts.union(set(conflicts))
        return all_conflicts

    def copy(self):
        return VariableTimes(self.times_by_var.copy())

    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)