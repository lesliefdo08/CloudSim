"""
Instance State Management

AWS-compatible instance state machine and transitions.
"""

from enum import Enum
from typing import Set


class InstanceState(str, Enum):
    """AWS EC2 instance states"""
    PENDING = "pending"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SHUTTING_DOWN = "shutting-down"
    TERMINATED = "terminated"


# Valid state transitions
STATE_TRANSITIONS = {
    InstanceState.PENDING: {InstanceState.RUNNING, InstanceState.TERMINATED},
    InstanceState.RUNNING: {InstanceState.STOPPING, InstanceState.SHUTTING_DOWN, InstanceState.TERMINATED},
    InstanceState.STOPPING: {InstanceState.STOPPED, InstanceState.TERMINATED},
    InstanceState.STOPPED: {InstanceState.PENDING, InstanceState.TERMINATED},
    InstanceState.SHUTTING_DOWN: {InstanceState.TERMINATED},
    InstanceState.TERMINATED: set(),  # Terminal state
}


def can_transition(from_state: str, to_state: str) -> bool:
    """
    Check if state transition is valid.
    
    Args:
        from_state: Current state
        to_state: Target state
    
    Returns:
        True if transition is valid
    """
    try:
        from_state_enum = InstanceState(from_state)
        to_state_enum = InstanceState(to_state)
        return to_state_enum in STATE_TRANSITIONS[from_state_enum]
    except (ValueError, KeyError):
        return False


def get_valid_transitions(current_state: str) -> Set[str]:
    """
    Get valid next states for current state.
    
    Args:
        current_state: Current instance state
    
    Returns:
        Set of valid next states
    """
    try:
        state_enum = InstanceState(current_state)
        return {s.value for s in STATE_TRANSITIONS[state_enum]}
    except (ValueError, KeyError):
        return set()


def is_terminal_state(state: str) -> bool:
    """
    Check if state is terminal (no transitions allowed).
    
    Args:
        state: Instance state
    
    Returns:
        True if state is terminal
    """
    return state == InstanceState.TERMINATED.value


def can_start(state: str) -> bool:
    """Check if instance can be started"""
    return state == InstanceState.STOPPED.value


def can_stop(state: str) -> bool:
    """Check if instance can be stopped"""
    return state == InstanceState.RUNNING.value


def can_reboot(state: str) -> bool:
    """Check if instance can be rebooted"""
    return state == InstanceState.RUNNING.value


def can_terminate(state: str) -> bool:
    """Check if instance can be terminated"""
    return state not in {InstanceState.TERMINATED.value, InstanceState.SHUTTING_DOWN.value}


# Instance type definitions (for validation)
INSTANCE_TYPES = {
    "t2.micro": {"vcpu": 1, "memory_mb": 1024},
    "t2.small": {"vcpu": 1, "memory_mb": 2048},
    "t2.medium": {"vcpu": 2, "memory_mb": 4096},
    "t2.large": {"vcpu": 2, "memory_mb": 8192},
    "t3.micro": {"vcpu": 2, "memory_mb": 1024},
    "t3.small": {"vcpu": 2, "memory_mb": 2048},
    "t3.medium": {"vcpu": 2, "memory_mb": 4096},
}


def is_valid_instance_type(instance_type: str) -> bool:
    """Check if instance type is valid"""
    return instance_type in INSTANCE_TYPES


def get_instance_type_specs(instance_type: str) -> dict:
    """Get instance type specifications"""
    return INSTANCE_TYPES.get(instance_type, {})
