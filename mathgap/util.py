from typing import Dict, List, Tuple, TypeVar, Generic
from pydantic import BaseModel, Field

def merge_dicts_with_larger_values(dict1: Dict, dict2: Dict) -> Dict:
    """ Merges two dictionaries, taking the larger value if a key is present in both. """
    merged_dict = dict1.copy()
    for key, value in dict2.items():
        if key in merged_dict:
            merged_dict[key] = max(merged_dict[key], value)
        else:
            merged_dict[key] = value  

    return merged_dict

def pretty_print_dict(dict1: Dict, separator=", ") -> str:
    """ Converts a dict that has objects as keys and values to a string representation """
    kvs_as_str = [f"{str(k)}: {str(v)}" for k,v in dict1.items()]
    return f"{separator.join(kvs_as_str)}"

K = TypeVar('K')
V = TypeVar('V')
class BaseModelDict(BaseModel, Generic[K, V]):
    data: List[Tuple[K, V]] = Field(default=None)
    data_as_dict: Dict[K, V] = Field(default_factory=dict, exclude=True)

    def __init__(self, data: List[Tuple[K, V]]):
        self.data = data
        self.data_as_dict = {k:v for k,v in data}

    def __setitem__(self, key, item):
        if key in self.data_as_dict:
            self.data.remove(self[key])
            
        self.data.append(tuple([key, item]))
        self.data_as_dict[key] = item

    def __getitem__(self, key):
        return self.data_as_dict[key]

    def __repr__(self):
        return repr(self.data_as_dict)

    def __contains__(self, item):
        return item in self.data_as_dict
    
    def items(self):
        return self.data_as_dict.items()
