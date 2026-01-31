"""
CIDR (Classless Inter-Domain Routing) Utilities
IP address and network validation
"""

import ipaddress
from typing import List, Tuple


def validate_cidr(cidr: str) -> Tuple[bool, str]:
    """
    Validate CIDR block format
    
    Args:
        cidr: CIDR block string (e.g., "10.0.0.0/16")
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        
        # Check if it's IPv4
        if not isinstance(network, ipaddress.IPv4Network):
            return False, "Only IPv4 CIDR blocks are supported"
        
        # Check prefix length (AWS allows /16 to /28 for VPCs)
        if network.prefixlen < 16 or network.prefixlen > 28:
            return False, "VPC CIDR block must be between /16 and /28"
        
        return True, ""
    
    except ValueError as e:
        return False, f"Invalid CIDR block: {str(e)}"


def validate_subnet_cidr(vpc_cidr: str, subnet_cidr: str) -> Tuple[bool, str]:
    """
    Validate that subnet CIDR is within VPC CIDR
    
    Args:
        vpc_cidr: VPC CIDR block
        subnet_cidr: Subnet CIDR block
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        vpc_network = ipaddress.ip_network(vpc_cidr, strict=False)
        subnet_network = ipaddress.ip_network(subnet_cidr, strict=False)
        
        # Check if subnet is within VPC
        if not subnet_network.subnet_of(vpc_network):
            return False, f"Subnet CIDR {subnet_cidr} must be within VPC CIDR {vpc_cidr}"
        
        # Check subnet prefix length (AWS allows /16 to /28 for subnets)
        if subnet_network.prefixlen < 16 or subnet_network.prefixlen > 28:
            return False, "Subnet CIDR block must be between /16 and /28"
        
        # Subnet prefix must be larger or equal to VPC prefix
        if subnet_network.prefixlen < vpc_network.prefixlen:
            return False, f"Subnet prefix /{subnet_network.prefixlen} must be >= VPC prefix /{vpc_network.prefixlen}"
        
        return True, ""
    
    except ValueError as e:
        return False, f"Invalid CIDR block: {str(e)}"


def check_cidr_overlap(cidr1: str, cidr2: str) -> bool:
    """
    Check if two CIDR blocks overlap
    
    Args:
        cidr1: First CIDR block
        cidr2: Second CIDR block
    
    Returns:
        True if CIDRs overlap, False otherwise
    """
    try:
        network1 = ipaddress.ip_network(cidr1, strict=False)
        network2 = ipaddress.ip_network(cidr2, strict=False)
        
        return network1.overlaps(network2)
    
    except ValueError:
        return False


def check_subnet_overlaps(vpc_cidr: str, existing_subnet_cidrs: List[str], new_subnet_cidr: str) -> Tuple[bool, str]:
    """
    Check if new subnet CIDR overlaps with existing subnets
    
    Args:
        vpc_cidr: VPC CIDR block
        existing_subnet_cidrs: List of existing subnet CIDR blocks
        new_subnet_cidr: New subnet CIDR to check
    
    Returns:
        Tuple of (has_overlap, error_message)
    """
    try:
        new_network = ipaddress.ip_network(new_subnet_cidr, strict=False)
        
        for existing_cidr in existing_subnet_cidrs:
            existing_network = ipaddress.ip_network(existing_cidr, strict=False)
            
            if new_network.overlaps(existing_network):
                return True, f"Subnet CIDR {new_subnet_cidr} overlaps with existing subnet {existing_cidr}"
        
        return False, ""
    
    except ValueError as e:
        return True, f"Invalid CIDR block: {str(e)}"


def calculate_available_ips(cidr: str) -> int:
    """
    Calculate number of available IP addresses in CIDR block
    AWS reserves 5 IPs in each subnet (network, router, DNS, future use, broadcast)
    
    Args:
        cidr: CIDR block string
    
    Returns:
        Number of available IP addresses
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        total_ips = network.num_addresses
        
        # AWS reserves 5 IPs per subnet
        # - Network address (.0)
        # - VPC router (.1)
        # - DNS server (.2)
        # - Future use (.3)
        # - Broadcast address (last IP)
        reserved_ips = 5
        
        return max(0, total_ips - reserved_ips)
    
    except ValueError:
        return 0


def get_network_address(cidr: str) -> str:
    """
    Get network address from CIDR block
    
    Args:
        cidr: CIDR block string
    
    Returns:
        Network address (e.g., "10.0.0.0" from "10.0.0.0/16")
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return str(network.network_address)
    except ValueError:
        return ""


def get_broadcast_address(cidr: str) -> str:
    """
    Get broadcast address from CIDR block
    
    Args:
        cidr: CIDR block string
    
    Returns:
        Broadcast address (e.g., "10.0.255.255" from "10.0.0.0/16")
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return str(network.broadcast_address)
    except ValueError:
        return ""


# AWS recommended VPC CIDR blocks
AWS_RECOMMENDED_VPC_CIDRS = [
    "10.0.0.0/16",
    "172.16.0.0/16",
    "192.168.0.0/16"
]


# AWS reserved CIDR blocks (cannot be used)
AWS_RESERVED_CIDRS = [
    "169.254.0.0/16",  # Link-local
    "224.0.0.0/4",     # Multicast
    "240.0.0.0/4",     # Reserved
]


def is_private_cidr(cidr: str) -> bool:
    """
    Check if CIDR block is in private IP range
    
    Args:
        cidr: CIDR block string
    
    Returns:
        True if private, False otherwise
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return network.is_private
    except ValueError:
        return False
