from typing import Dict

from mathgap.properties import PropertyKey, PropertyType

class Instantiation:
    """ Maps agent_id, entity_id etc to a string value and quantity_id to numerical values """
    def __init__(self, instantiations: Dict[PropertyKey, object] = {}) -> None:
        self._instantiations = instantiations

    def __contains__(self, property_key: PropertyKey) -> bool:
        return any([k == property_key for k in self._instantiations.keys()])
    
    def __getitem__(self, key: PropertyKey):
        assert key in self, f"No instantiation for {key} (key-type: {type(key)})!"
        return self._instantiations[key]
    
    def __setitem__(self, key: PropertyKey, value: object):
        assert key not in self._instantiations.keys(), f"Multiple instantiations for {key}! [{self._instantiations[key]}, {value}]"
        self._instantiations[key] = value

    def set_even_if_present(self, key: PropertyKey, value: object):
        self._instantiations[key] = value

    def get_instantiations_of_type(self, property_type: PropertyType) -> Dict[PropertyKey, object]:
        return {k:v for k,v in self._instantiations.items() if k.property_type == property_type}
    
    def remove(self, key: PropertyKey):
        if key in self._instantiations:
            self._instantiations.pop(key)
    
    def copy(self) -> 'Instantiation':
        return Instantiation(self._instantiations.copy())
    
    def __repr__(self):
        from mathgap.renderers import TEXT_RENDERER
        return TEXT_RENDERER(self)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Instantiation): return False        
        return set(self._instantiations.keys()) == set(other._instantiations.keys()) and all(self[k] == other[k] for k in self._instantiations.keys())
    
def delete_all_of_type(instantiation: Instantiation, ptype: PropertyType) -> Instantiation:
    """ Deletes all instantiations of a certain property type (e.g. all agents) """
    result = instantiation.copy()
    for key in instantiation.get_instantiations_of_type(ptype).keys():
        result.remove(key)
    return result