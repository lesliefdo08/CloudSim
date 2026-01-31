"""
Wildcard Matching Utilities
Pattern matching for IAM actions and resource ARNs with wildcard support
"""

import re
from typing import List


def wildcard_to_regex(pattern: str) -> re.Pattern:
    """
    Convert wildcard pattern to regex pattern
    
    AWS wildcard rules:
    - * matches zero or more characters
    - ? matches exactly one character
    
    Examples:
        ec2:* → matches ec2:StartInstances, ec2:StopInstances, etc.
        ec2:*Instances → matches ec2:StartInstances, ec2:DescribeInstances, etc.
        arn:aws:s3:::bucket/* → matches arn:aws:s3:::bucket/file.txt, etc.
    
    Args:
        pattern: Wildcard pattern string
        
    Returns:
        Compiled regex pattern
    """
    # Escape special regex characters except * and ?
    escaped = re.escape(pattern)
    
    # Replace escaped wildcards with regex equivalents
    regex_pattern = escaped.replace(r'\*', '.*').replace(r'\?', '.')
    
    # Anchor to match entire string
    regex_pattern = f'^{regex_pattern}$'
    
    return re.compile(regex_pattern, re.IGNORECASE)


def matches_wildcard(pattern: str, value: str) -> bool:
    """
    Check if value matches wildcard pattern
    
    Examples:
        matches_wildcard("ec2:*", "ec2:StartInstances") → True
        matches_wildcard("ec2:Start*", "ec2:StartInstances") → True
        matches_wildcard("ec2:Stop*", "ec2:StartInstances") → False
        matches_wildcard("*", "anything") → True
    
    Args:
        pattern: Wildcard pattern
        value: Value to match
        
    Returns:
        True if value matches pattern
    """
    # Fast path for exact match
    if pattern == value:
        return True
    
    # Fast path for universal wildcard
    if pattern == "*":
        return True
    
    # Convert to regex and match
    regex = wildcard_to_regex(pattern)
    return bool(regex.match(value))


def matches_any_wildcard(patterns: List[str], value: str) -> bool:
    """
    Check if value matches any of the wildcard patterns
    
    Args:
        patterns: List of wildcard patterns
        value: Value to match
        
    Returns:
        True if value matches at least one pattern
    """
    return any(matches_wildcard(pattern, value) for pattern in patterns)


def matches_action(policy_actions: List[str], requested_action: str) -> bool:
    """
    Check if requested action matches any policy action pattern
    
    Examples:
        matches_action(["ec2:*"], "ec2:StartInstances") → True
        matches_action(["ec2:Start*"], "ec2:StartInstances") → True
        matches_action(["ec2:Stop*"], "ec2:StartInstances") → False
        matches_action(["*"], "ec2:StartInstances") → True
    
    Args:
        policy_actions: List of action patterns from policy
        requested_action: Action being requested
        
    Returns:
        True if requested action matches any policy action
    """
    return matches_any_wildcard(policy_actions, requested_action)


def matches_resource(policy_resources: List[str], requested_resource: str) -> bool:
    """
    Check if requested resource ARN matches any policy resource pattern
    
    Examples:
        matches_resource(["*"], "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123") → True
        matches_resource(
            ["arn:aws:ec2:*:*:instance/*"],
            "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123"
        ) → True
        matches_resource(
            ["arn:aws:s3:::bucket/*"],
            "arn:aws:s3:::bucket/file.txt"
        ) → True
        matches_resource(
            ["arn:aws:s3:::other-bucket/*"],
            "arn:aws:s3:::bucket/file.txt"
        ) → False
    
    Args:
        policy_resources: List of resource ARN patterns from policy
        requested_resource: Resource ARN being requested
        
    Returns:
        True if requested resource matches any policy resource
    """
    return matches_any_wildcard(policy_resources, requested_resource)


# Unit tests (inline examples for verification)
if __name__ == "__main__":
    # Test action matching
    assert matches_action(["ec2:*"], "ec2:StartInstances") is True
    assert matches_action(["ec2:Start*"], "ec2:StartInstances") is True
    assert matches_action(["ec2:Stop*"], "ec2:StartInstances") is False
    assert matches_action(["*"], "anything") is True
    assert matches_action(["ec2:StartInstances", "ec2:StopInstances"], "ec2:StartInstances") is True
    
    # Test resource matching
    assert matches_resource(["*"], "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123") is True
    assert matches_resource(
        ["arn:aws:ec2:*:*:instance/*"],
        "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123"
    ) is True
    assert matches_resource(
        ["arn:aws:s3:::bucket/*"],
        "arn:aws:s3:::bucket/file.txt"
    ) is True
    assert matches_resource(
        ["arn:aws:s3:::other-bucket/*"],
        "arn:aws:s3:::bucket/file.txt"
    ) is False
    
    # Test wildcard patterns
    assert matches_wildcard("ec2:*", "ec2:StartInstances") is True
    assert matches_wildcard("ec2:*Instances", "ec2:StartInstances") is True
    assert matches_wildcard("ec2:Start*", "ec2:StartInstances") is True
    assert matches_wildcard("*:*", "ec2:StartInstances") is True
    assert matches_wildcard("ec2:?tart*", "ec2:StartInstances") is True
    
    print("✅ All wildcard matching tests passed")
