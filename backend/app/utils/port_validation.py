"""
Port and Protocol Validation Utilities

Utilities for validating security group rule parameters (ports, protocols, CIDR blocks).
"""

from typing import Tuple


# Valid protocols
VALID_PROTOCOLS = ["tcp", "udp", "icmp", "-1"]  # -1 means "all protocols"

# Port ranges
MIN_PORT = 1
MAX_PORT = 65535

# Common ICMP types (for reference)
ICMP_TYPES = {
    0: "Echo Reply",
    3: "Destination Unreachable",
    8: "Echo Request (Ping)",
    11: "Time Exceeded",
}


def validate_protocol(protocol: str) -> Tuple[bool, str]:
    """
    Validate protocol string.
    
    Args:
        protocol: Protocol string (tcp, udp, icmp, -1)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    protocol_lower = protocol.lower()
    
    if protocol_lower not in VALID_PROTOCOLS:
        return False, f"Invalid protocol '{protocol}'. Must be one of: {', '.join(VALID_PROTOCOLS)}"
    
    return True, ""


def validate_port_range(from_port: int, to_port: int, protocol: str) -> Tuple[bool, str]:
    """
    Validate port range for a given protocol.
    
    Args:
        from_port: Starting port
        to_port: Ending port
        protocol: Protocol (tcp, udp, icmp, -1)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    protocol_lower = protocol.lower()
    
    # For 'all protocols' or ICMP, ports should be null/optional
    if protocol_lower in ["-1", "icmp"]:
        # Ports are not required for these protocols
        if from_port is not None or to_port is not None:
            return False, f"Port range should not be specified for protocol '{protocol}'"
        return True, ""
    
    # For TCP/UDP, ports are required
    if from_port is None or to_port is None:
        return False, f"Port range is required for protocol '{protocol}'"
    
    # Validate port numbers
    if from_port < MIN_PORT or from_port > MAX_PORT:
        return False, f"from_port must be between {MIN_PORT} and {MAX_PORT}"
    
    if to_port < MIN_PORT or to_port > MAX_PORT:
        return False, f"to_port must be between {MIN_PORT} and {MAX_PORT}"
    
    # from_port must be <= to_port
    if from_port > to_port:
        return False, f"from_port ({from_port}) must be less than or equal to to_port ({to_port})"
    
    return True, ""


def validate_rule_source(cidr_ipv4: str = None, source_security_group_id: str = None) -> Tuple[bool, str]:
    """
    Validate that exactly one source is specified.
    
    Args:
        cidr_ipv4: CIDR block
        source_security_group_id: Security group ID
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Exactly one source must be specified
    if cidr_ipv4 and source_security_group_id:
        return False, "Cannot specify both cidr_ipv4 and source_security_group_id"
    
    if not cidr_ipv4 and not source_security_group_id:
        return False, "Must specify either cidr_ipv4 or source_security_group_id"
    
    # If CIDR is specified, validate it
    if cidr_ipv4:
        try:
            import ipaddress
            ipaddress.ip_network(cidr_ipv4, strict=False)
        except ValueError as e:
            return False, f"Invalid CIDR block: {str(e)}"
    
    return True, ""


def format_port_range(from_port: int, to_port: int, protocol: str) -> str:
    """
    Format port range for display.
    
    Args:
        from_port: Starting port
        to_port: Ending port
        protocol: Protocol
    
    Returns:
        Formatted string (e.g., "80", "22-22", "1024-65535", "All")
    """
    protocol_lower = protocol.lower()
    
    if protocol_lower in ["-1", "icmp"]:
        return "All"
    
    if from_port == to_port:
        return str(from_port)
    
    return f"{from_port}-{to_port}"


def is_port_in_range(port: int, from_port: int, to_port: int) -> bool:
    """
    Check if a port is within the specified range.
    
    Args:
        port: Port to check
        from_port: Start of range
        to_port: End of range
    
    Returns:
        True if port is in range
    """
    return from_port <= port <= to_port


# Common port definitions (for reference)
WELL_KNOWN_PORTS = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    27017: "MongoDB",
    3389: "RDP",
    8080: "HTTP Alternate",
}


def get_port_description(port: int) -> str:
    """
    Get human-readable description for well-known ports.
    
    Args:
        port: Port number
    
    Returns:
        Description or empty string
    """
    return WELL_KNOWN_PORTS.get(port, "")
