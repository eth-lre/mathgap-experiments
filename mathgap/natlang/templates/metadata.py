from typing import List, Tuple

from mathgap.logicalforms.logicalform import LogicalForm
from mathgap.natlang.templates.sampling import TemplateSelection
from mathgap.natlang.templates.template import Template
from mathgap.properties import PropertyKey
from mathgap.natlang.templates.origin import Origin

class PropertyKeysOrigin(Origin):
    def __init__(self, property_keys: PropertyKey|Tuple[PropertyKey, ...]):
        self.property_keys=property_keys

class RenderingMetadata:
    def __init__(self, origins: List[Tuple[Origin, int]] = None, units: List[Tuple[Tuple[int, ...], int]] = None, 
                 lfs: List[Tuple[LogicalForm|None, int]] = None, node_ids: List[Tuple[int, int]] = None, templates: List[Tuple[Template, int]] = None, template_selections: TemplateSelection = None):
        self.origins = [] if origins is None else origins 
        self.units = [] if units is None else units
        self.lfs = [] if lfs is None else lfs
        self.node_ids = [] if node_ids is None else node_ids
        self.templates = [] if templates is None else templates
        self.template_selections: List[TemplateSelection] = [] if template_selections is None else template_selections

    @property
    def origin_per_character(self) -> List[Origin]: # [origin1, origin1, origin1, origin2, origin2, ...]
        opc = []
        for origin,times in self.origins:
            opc.extend([origin]*times)
        return opc

    @property
    def unit_per_character(self) -> List[Tuple[int, ...]]: # [unit1, unit1, unit1, unit2, unit2, ...]
        upc = []
        for unit,times in self.units:
            upc.extend([unit]*times)
        return upc
    
    @property
    def lf_per_character(self) -> List[LogicalForm|None]: # [lf1, lf1, lf1, ..., None, ..., lf10, lf10, ...]
        lfpc = []
        for lf,times in self.lfs:
            lfpc.extend([lf]*times)
        return lfpc

    @property
    def node_id_per_character(self) -> List[int|None]: # [id1, id1, id1, ..., None, ..., id5, i5, ...]
        idpc = []
        for node_id,times in self.node_ids:
            idpc.extend([node_id]*times)
        return idpc

    @property
    def template_per_character(self) -> List[Template|None]: # [t1, t1, t1, ..., None, ..., t10, t10, ...]
        tpc = []
        for template,times in self.templates:
            tpc.extend([template]*times)
        return tpc

    def append(self, origin: Origin, unit: List[int], lf: LogicalForm|None, template: Template|None, num_characters: int):
        self.origins.append((origin, num_characters))
        self.units.append((tuple(unit), num_characters))
        self.lfs.append((lf, num_characters))
        self.templates.append((template, num_characters))

    def __add__(self, other):
        assert isinstance(other, RenderingMetadata), "Can only add rendering metadata to rendering metadata"
        return RenderingMetadata(self.origins + other.origins, self.units + other.units, self.lfs + other.lfs, 
                                 self.node_ids + other.node_ids, self.templates + other.templates, self.template_selections + other.template_selections)
    
    def join(self, other: 'RenderingMetadata', separator: Origin, separator_num_characters: int):
        " Similar to addition of metadata but correctly increases the unit-ids of the separator and the other metadata "
        self.origins.append((separator, separator_num_characters))
        self.origins.extend(other.origins)

        self.units = [
            (tuple([0,*unit]), length)
            for unit,length in self.units
        ]
        self.units.append((tuple([1]), separator_num_characters))
        self.units.extend([
            (tuple([2,*unit]), length)
            for unit,length in other.units
        ])

        self.lfs.append((None, separator_num_characters))
        self.lfs.extend(other.lfs)

        self.node_ids.append((None, separator_num_characters))
        self.node_ids.extend(other.node_ids)

        self.templates.append((None, separator_num_characters))
        self.templates.extend(other.templates)

    def copy(self) -> 'RenderingMetadata':
        return RenderingMetadata(origins=self.origins.copy(), units=self.units.copy(), lfs=self.lfs.copy(), 
                                 node_ids=self.node_ids.copy(), templates=self.templates.copy(), template_selections=self.template_selections.copy())
