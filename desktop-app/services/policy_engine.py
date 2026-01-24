"""
Policy Engine - Evaluates IAM policies and checks permissions
"""
from typing import List, Optional, Tuple
import fnmatch
from models.iam_policy import Policy, PolicyStatement


class PolicyEngine:
    """
    Evaluates IAM policies to determine if an action is allowed.
    
    Permission evaluation follows AWS IAM logic:
    1. By default, all requests are denied (implicit deny)
    2. An explicit Allow overrides the default deny
    3. An explicit Deny overrides any Allow
    """
    
    @staticmethod
    def evaluate_action(
        action: str,
        resource: str,
        policies: List[Policy]
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate if an action is allowed based on policies.
        
        Args:
            action: Action to check (e.g., "ec2:RunInstance")
            resource: Resource identifier (e.g., "*", "bucket:my-bucket")
            policies: List of policies to evaluate
        
        Returns:
            (allowed: bool, reason: Optional[str])
        """
        if not policies:
            return False, "No policies attached"
        
        # Check for explicit deny first (deny always wins)
        for policy in policies:
            for statement in policy.statements:
                if statement.effect == "Deny":
                    if PolicyEngine._matches_action(action, statement.actions):
                        if PolicyEngine._matches_resource(resource, statement.resources):
                            return False, f"Explicitly denied by policy '{policy.name}'"
        
        # Check for explicit allow
        for policy in policies:
            for statement in policy.statements:
                if statement.effect == "Allow":
                    if PolicyEngine._matches_action(action, statement.actions):
                        if PolicyEngine._matches_resource(resource, statement.resources):
                            return True, None
        
        # Implicit deny (no explicit allow found)
        return False, "No policy allows this action"
    
    @staticmethod
    def _matches_action(action: str, policy_actions: List[str]) -> bool:
        """
        Check if action matches any policy action pattern.
        Supports wildcards like "ec2:*" or "*"
        """
        for policy_action in policy_actions:
            if policy_action == "*":
                return True
            if fnmatch.fnmatch(action, policy_action):
                return True
        return False
    
    @staticmethod
    def _matches_resource(resource: str, policy_resources: List[str]) -> bool:
        """
        Check if resource matches any policy resource pattern.
        Supports wildcards like "*" or specific resources
        """
        for policy_resource in policy_resources:
            if policy_resource == "*":
                return True
            if fnmatch.fnmatch(resource, policy_resource):
                return True
        return False
    
    @staticmethod
    def simulate_action(
        action: str,
        resource: str,
        policies: List[Policy]
    ) -> dict:
        """
        Simulate policy evaluation and return detailed results.
        Useful for testing and debugging permissions.
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "matched_policies": List[str],
                "evaluation_order": List[dict]
            }
        """
        result = {
            "allowed": False,
            "reason": "",
            "matched_policies": [],
            "evaluation_order": []
        }
        
        if not policies:
            result["reason"] = "No policies attached"
            return result
        
        # Check for explicit deny
        for policy in policies:
            for statement in policy.statements:
                if statement.effect == "Deny":
                    matches_action = PolicyEngine._matches_action(action, statement.actions)
                    matches_resource = PolicyEngine._matches_resource(resource, statement.resources)
                    
                    eval_step = {
                        "policy": policy.name,
                        "effect": "Deny",
                        "matches_action": matches_action,
                        "matches_resource": matches_resource,
                        "result": "deny" if matches_action and matches_resource else "skip"
                    }
                    result["evaluation_order"].append(eval_step)
                    
                    if matches_action and matches_resource:
                        result["allowed"] = False
                        result["reason"] = f"Explicitly denied by policy '{policy.name}'"
                        result["matched_policies"].append(policy.name)
                        return result
        
        # Check for explicit allow
        for policy in policies:
            for statement in policy.statements:
                if statement.effect == "Allow":
                    matches_action = PolicyEngine._matches_action(action, statement.actions)
                    matches_resource = PolicyEngine._matches_resource(resource, statement.resources)
                    
                    eval_step = {
                        "policy": policy.name,
                        "effect": "Allow",
                        "matches_action": matches_action,
                        "matches_resource": matches_resource,
                        "result": "allow" if matches_action and matches_resource else "skip"
                    }
                    result["evaluation_order"].append(eval_step)
                    
                    if matches_action and matches_resource:
                        result["allowed"] = True
                        result["reason"] = f"Allowed by policy '{policy.name}'"
                        result["matched_policies"].append(policy.name)
        
        if not result["allowed"]:
            result["reason"] = "No policy allows this action (implicit deny)"
        
        return result
    
    @staticmethod
    def get_effective_permissions(policies: List[Policy]) -> dict:
        """
        Get summary of effective permissions from policies.
        
        Returns:
            {
                "allowed_actions": List[str],
                "denied_actions": List[str],
                "policies_count": int
            }
        """
        allowed_actions = set()
        denied_actions = set()
        
        for policy in policies:
            for statement in policy.statements:
                if statement.effect == "Allow":
                    allowed_actions.update(statement.actions)
                elif statement.effect == "Deny":
                    denied_actions.update(statement.actions)
        
        return {
            "allowed_actions": sorted(list(allowed_actions)),
            "denied_actions": sorted(list(denied_actions)),
            "policies_count": len(policies)
        }


# Global policy engine instance
policy_engine = PolicyEngine()
