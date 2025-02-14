# CONCLUSION: Container
# PREMISES: Container, Transfer

# VARIABLE-TIMES: 
# - container(a.e at t1), transfer(a.e at {t1, t1+1}, other.e at 0)
# - conclusion(a.e at t1+1)

# INPUTS:
# - choice of or both:
#   - receiver_agent
#   - sender_agent
# - optionally, if the conclusion has no attribute:
#   - attribute
# - optionally
#   - unit  

from typing import Dict, List
from mathgap.trees.rules.inference_rule import InferenceRule, Parametrization

from mathgap.logicalforms import LogicalForm, Container, Transfer
from mathgap.expressions import Subtraction, Addition
from mathgap.trees.timing import VariableTimes, VariableKey

class ContTransferCont(InferenceRule):
    """ 
        Informal:
            We know how many entities an agent has before the transfer,
            and we know how many are transferred from/to the agent,
            thus, we know how many entities the agent has after the transfer.

        NOTE: If the container and conclusion are without attribute, this permits the transfer to have one.
    """
    def is_reverse_applicable(self, conclusion: LogicalForm, tree) -> bool:
        if isinstance(conclusion, Container): return True
        # NOTE: we don't do sanity checks on the tree because transfer always decreases the time on the affected variable
        #       so, the tree would have to be invalid beforehand already
        return False

    def assert_valid_parametrization(self, conclusion: LogicalForm, parametrization: Parametrization):
        assert isinstance(conclusion, Container), f"Conclusion is expected to be a Container! Got {type(conclusion)} instead."
        receiver_agent = parametrization.get("receiver_agent", None)
        sender_agent = parametrization.get("sender_agent", None)
        assert receiver_agent is not None or sender_agent is not None, f"At least sender_agent or receiver_agent must be passed as parameter!"
        assert (receiver_agent == conclusion.agent) != (sender_agent == conclusion.agent), f"Exactly one of sender_agent ({sender_agent}) or receiver_agent ({receiver_agent}) must match the conclusion.agent ({conclusion.agent})!"

        if conclusion.attribute is None:
            attribute = parametrization.get("attribute", None)
            assert (attribute is None) or (attribute == conclusion.attribute), f"Cannot introduce attribute ({attribute}) different from the attribute of the conclusion ({conclusion.attribute})."
        # otherwise: attribute can be optionally introduced

        unit = parametrization.get("unit", None)
        assert (unit is None) or (unit == conclusion.unit), f"Cannot introduce unit ({unit}) different from the unit of the conclusion ({conclusion.unit})."

        ignored_keys = set(parametrization.keys()).difference(set(["receiver_agent", "sender_agent", "attribute", "unit"]))
        assert len(ignored_keys) == 0, f"Keys {ignored_keys} are provided but are not allowed."

    def apply_reverse(self, conclusion: LogicalForm, parametrization: Parametrization) -> List[LogicalForm]:
        self.assert_valid_parametrization(conclusion, parametrization)
        assert isinstance(conclusion, Container), "Conclusion is expected to be a Container"
        
        receiver_agent = parametrization.get("receiver_agent", None)
        sender_agent = parametrization.get("sender_agent", None)
        entity = conclusion.entity
        attribute = conclusion.attribute
        unit = conclusion.unit

        transfer_attribute = parametrization.get("attribute", attribute)
        transfer_unit = parametrization.get("unit", unit)

        container_agent = receiver_agent if receiver_agent == conclusion.agent else sender_agent

        prem_container = Container(agent=container_agent, quantity=None, 
                                   entity=entity, attribute=attribute, unit=unit)        
        prem_transfer = Transfer(receiver=receiver_agent, sender=sender_agent, quantity=None,
                                entity=entity, attribute=transfer_attribute, unit=transfer_unit)

        # NOTE: no reordering possible because of constraints
        return [prem_container, prem_transfer]
        
    def infer_knowledge(self, premises: List[LogicalForm], conclusion: LogicalForm):
        container, transfer = premises
        assert isinstance(container, Container), "First premise is expected to be a Container"
        assert isinstance(transfer, Transfer), "Second premise is expected to be a Transfer"
        assert isinstance(conclusion, Container), "Conclusion is expected to be a Container"
        assert container.agent == conclusion.agent, "Must operate on the same agent"
        assert container.entity == conclusion.entity, "Must operate on the same entity"
        assert container.attribute == conclusion.attribute, "Must operate on the same attribute"
        assert container.quantity is not None, "Container quantity cannot be None"
        assert transfer.quantity is not None, "Transfer quantity cannot be None"

        if conclusion.agent == transfer.receiver:
            conclusion.quantity = Addition(container.quantity, transfer.quantity)
        elif conclusion.agent == transfer.sender:
            conclusion.quantity = Subtraction(container.quantity, transfer.quantity)

        assert conclusion.quantity is not None, f"Conclusion.quantity must be set after inferring knowledge! conclusion.agent={conclusion.agent}, transfer.receiver={transfer.receiver}, transfer.sender={transfer.sender}"

    def reverse_infer_variable_times(self, premises: List[LogicalForm], conclusion: LogicalForm, conclusion_variable_times: VariableTimes) -> Dict[LogicalForm, VariableTimes]:
        container, transfer = premises
        assert isinstance(container, Container), "First premise is expected to be a Container"
        assert isinstance(transfer, Transfer), "Second premise is expected to be a Transfer"
        assert isinstance(conclusion, Container), "Conclusion is expected to be a Container"

        variable_times_by_premise = {}

        # container
        container_vts = conclusion_variable_times.copy()
        container_vk = container.get_variable_keys()[0]
        container_vts[container_vk] = min(conclusion_variable_times[container_vk]) - 1 # conclusion - 1
        variable_times_by_premise[container] = container_vts

        # transfer
        transfer_vts = conclusion_variable_times.copy()
        receiver_vk = VariableKey((transfer.receiver_prop, transfer.entity_prop, transfer.attribute_prop, transfer.unit_prop))
        sender_vk = VariableKey((transfer.sender_prop, transfer.entity_prop, transfer.attribute_prop, transfer.unit_prop))
        if conclusion.agent == transfer.receiver:
            conc_vt = min(conclusion_variable_times[receiver_vk])
            transfer_vts[receiver_vk] = {conc_vt - 1, conc_vt} # updates receiver_vk at conc_vt with derivative of conc_vt-1
            assert sender_vk not in conclusion_variable_times, "Sender variable-key must be newly introduced"
            transfer_vts[sender_vk] = 0
        elif conclusion.agent == transfer.sender:
            conc_vt = min(conclusion_variable_times[sender_vk])
            transfer_vts[sender_vk] = {conc_vt - 1, conc_vt} # updates sender_vk at conc_vt with derivative of conc_vt-1
            assert receiver_vk not in conclusion_variable_times, "Receiver variable-key must be newly introduced"
            transfer_vts[receiver_vk] = 0
        variable_times_by_premise[transfer] = transfer_vts
        
        return variable_times_by_premise

    def infer_variable_times(self, premises: List[LogicalForm], conclusion: LogicalForm, premises_variable_times: Dict[LogicalForm, VariableTimes]) -> VariableTimes:
        container, transfer = premises
        assert isinstance(container, Container), "First premise is expected to be a Container"
        assert isinstance(transfer, Transfer), "Second premise is expected to be a Transfer"
        assert isinstance(conclusion, Container), "Conclusion is expected to be a Container"

        container_vts = premises_variable_times[container]
        transfer_vts = premises_variable_times[transfer]

        vts = container_vts.copy()
        conflicts = vts.merge(transfer_vts)

        # TODO: sanity checks on conflicts

        container_vk = container.get_variable_keys()[0]
        assert len(container_vts[container_vk]) == 1, "Container can only involve a single value for the key of the conclusion"
        vts[container_vk] = list(container_vts[container_vk])[0] + 1 # conclusion is always the containers time + 1

        return vts        