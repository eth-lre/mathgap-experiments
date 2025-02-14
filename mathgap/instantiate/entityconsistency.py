from typing import Dict, List
import random

from mathgap.instantiate.instantiation import Instantiation
from mathgap.instantiate.instantiators import Instantiator

from mathgap.trees import ProofTree
from mathgap.properties import PropertyKey, PropertyType

class PartAndUnitAwareEntityInstantiator(Instantiator):
    """ Instantiates entities while being aware of their units and also their parts """
    def __init__(self, entities_without_units: List[str], entities_with_units: List[str], parts_by_whole: Dict[str, List[str]], enforce_uniqueness: bool = True, enforce_uniqueness_on_parts: bool = True) -> None:
        self.entities_without_units = entities_without_units
        self.entities_with_units = entities_with_units
        self.parts_by_whole = parts_by_whole
        self.enforce_uniqueness = enforce_uniqueness 
        self.enforce_uniqueness_on_parts = enforce_uniqueness_on_parts

    def _instantiate(self, tree: ProofTree, instantiation: Instantiation, skip_existing: bool, seed: int) -> Instantiation:
        available_entities = self.entities_without_units.copy()
        available_entities_with_units = self.entities_with_units.copy()
        available_parts_by_whole = self.parts_by_whole.copy()

        if self.enforce_uniqueness:
            available_entities = [e for e in available_entities if e not in instantiation._instantiations.values()]
            available_entities_with_units = [e for e in available_entities_with_units if e not in instantiation._instantiations.values()]
            available_parts_by_whole = {
                whole:parts 
                for whole,parts in available_parts_by_whole.items() 
                if whole not in instantiation._instantiations.values() 
                    and not any([p in instantiation._instantiations.values() for p in parts])
            }

        # anaylze entity-specs
        unit_by_entity = {}
        parts_by_entity = {}
        for entity_specs in [lf.get_entity_specs() for lf in tree.nodes_by_lf.keys()]:
            for es in entity_specs:
                if es.has_unit:
                    unit_by_entity[es.entity_id] = es.unit_id
                if es.has_part_entities:
                    parts_by_entity[es.entity_id] = es.part_entity_ids

        instantiated_entities = set([])

        # first instantiate all the part_whole entities
        for entity_id, part_ids in parts_by_entity.items():
            assert not entity_id in unit_by_entity, "A whole-entity cannot currently have a unit while also participating in a partwhole"
            entity_name,part_names = random.choice(list(available_parts_by_whole.items()))

            prop_entity = PropertyKey(PropertyType.ENTITY, entity_id)
            if skip_existing and prop_entity in instantiation:
                # if the whole-entity is already assigned, we need to respect the assignment and make sure all parts do too
                entity_name = instantiation[prop_entity]
                part_names = self.parts_by_whole[entity_name].copy()
            else:
                instantiation[prop_entity] = entity_name
            instantiated_entities.add(entity_id)
            
            # instantiate all part-entities
            available_part_names = part_names.copy()
            if self.enforce_uniqueness:
                available_part_names = [p for p in available_part_names if p not in instantiation._instantiations.values()]

            for part_entity_id in part_ids:
                # make sure no part-entity is assigned a unit because we do not support this currently
                assert not part_entity_id in unit_by_entity, "A part-entity cannot currently have a unit while also participating in a partwhole"

                prop_part = PropertyKey(PropertyType.ENTITY, part_entity_id)
                if skip_existing and prop_part in instantiation:
                    # if the part-entity is pre-instantiated, make sure it's consistent with the whole-entity
                    assert instantiation[prop_part] in part_names, f"Invalid whole <-> part mapping ({entity_name} <-> {instantiation[prop_part]}). This is likely due to partial instantiation of partwhole entities"
                    part_name = instantiation[prop_part]
                else:
                    part_name = random.choice(available_part_names)
                    instantiation[prop_part] = part_name
                instantiated_entities.add(part_entity_id)

                if self.enforce_uniqueness_on_parts and part_name in available_part_names:
                    available_part_names.remove(part_name) 

            if self.enforce_uniqueness and entity_name in available_parts_by_whole:
                available_parts_by_whole.pop(entity_name)
        
        # then instantiate the rest
        for entity_id in tree.property_tracker.get_by_type(PropertyType.ENTITY):
            prop_entity = PropertyKey(PropertyType.ENTITY, entity_id)
            if entity_id in instantiated_entities: continue # skip the entities that we've already instantiated
            if skip_existing and prop_entity in instantiation: continue

            if entity_id in unit_by_entity:
                assert len(available_entities_with_units) > 0, "Need at least one entity with a unit to choose from! Maybe you are enforcing uniqueness and the list of provided entities with units is too short?"
                entity_name = random.choice(available_entities_with_units)
            else:
                assert len(available_entities_with_units) > 0, "Need at least one entity without a unit to choose from! Maybe you are enforcing uniqueness and the list of provided entities is too short?"
                entity_name = random.choice(available_entities)
            
            instantiation[prop_entity] = entity_name
            instantiated_entities.add(entity_id)

            if self.enforce_uniqueness:
                if entity_name in available_entities: available_entities.remove(entity_name)
                if entity_name in available_entities_with_units: available_entities_with_units.remove(entity_name)

        return instantiation

class EntityAwareUnitInstantiator(Instantiator):
    """ 
        Instantiates units while being aware of the entities it's used with
        NOTE: this instantiator can only be called after all entities have been instantiated already
    """
    def __init__(self, unit_by_entity: Dict[str, str]) -> None:
        self.entities_with_units = unit_by_entity

    def _instantiate(self, tree: ProofTree, instantiation: Instantiation, skip_existing: bool, seed: int) -> Instantiation:
        # unit -> entity mapping
        entity_by_unit = {}
        for entity_specs in [lf.get_entity_specs() for lf in tree.nodes_by_lf.keys()]:
            for es in entity_specs:
                if es.has_unit:
                    entity_by_unit[es.unit_id] = es.entity_id

        # instantiate
        for unit_id in tree.property_tracker.get_by_type(PropertyType.UNIT):
            prop_unit = PropertyKey(PropertyType.UNIT, unit_id)
            entity_id = entity_by_unit[unit_id]
            prop_entity = PropertyKey(PropertyType.ENTITY, entity_id)
            assert prop_entity in instantiation, "Instantiator expects all entities that are used with units to be initialized already"
            entity_name = instantiation[prop_entity]
            
            if skip_existing and prop_unit in instantiation: 
                assert instantiation[prop_unit] == self.entities_with_units[entity_name], f"Inconsistent entity <-> unit mapping ({entity_name} <-> {instantiation[prop_unit]}) detected! This is likely due to partial instantiation of the units."

            instantiation[prop_unit] = self.entities_with_units[entity_name]

        return instantiation