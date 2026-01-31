"""
IAM Policy Evaluation Engine
AWS-like policy evaluation with proper precedence and wildcard matching
"""

import json
from typing import List, Optional, Literal
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iam_user import User
from app.models.iam_group import Group
from app.models.iam_role import Role
from app.models.iam_policy import Policy
from app.schemas.iam_policy import PolicyDocument, PolicyStatement
from app.utils.wildcard import matches_action, matches_resource


class EvaluationResult(str, Enum):
    """Policy evaluation result"""
    ALLOW = "Allow"
    DENY = "Deny"
    IMPLICIT_DENY = "ImplicitDeny"


class PolicyEvaluationDecision(BaseModel):
    """
    Result of policy evaluation
    """
    result: EvaluationResult
    reason: str
    matching_statements: List[dict] = []
    
    @property
    def is_allowed(self) -> bool:
        """Check if access is allowed"""
        return self.result == EvaluationResult.ALLOW
    
    @property
    def is_denied(self) -> bool:
        """Check if access is explicitly denied"""
        return self.result == EvaluationResult.DENY


class PolicyEvaluator:
    """
    IAM Policy Evaluation Engine
    
    Implements AWS IAM policy evaluation logic:
    1. By default, all requests are denied (implicit deny)
    2. An explicit allow overrides the implicit deny
    3. An explicit deny overrides any allows
    
    Evaluation order:
    1. Check for explicit Deny → if found, return Deny
    2. Check for explicit Allow → if found, return Allow
    3. If no Allow found, return ImplicitDeny (default deny)
    
    Policy sources (evaluated in order):
    - User inline policies
    - Group policies (for all groups user belongs to)
    - User attached policies
    - Role policies (if assuming role)
    """
    
    @staticmethod
    def evaluate_statement(
        statement: PolicyStatement,
        action: str,
        resource: str
    ) -> bool:
        """
        Check if a statement applies to the requested action/resource
        
        Args:
            statement: Policy statement to evaluate
            action: Requested action (e.g., "ec2:StartInstances")
            resource: Requested resource ARN
            
        Returns:
            True if statement applies to this request
        """
        # Check if action matches
        action_matches = matches_action(statement.action, action)
        
        # Check if resource matches
        resource_matches = matches_resource(statement.resource, resource)
        
        return action_matches and resource_matches
    
    @staticmethod
    def evaluate_policy_document(
        policy_doc: PolicyDocument,
        action: str,
        resource: str
    ) -> tuple[Optional[Literal["Allow", "Deny"]], List[PolicyStatement]]:
        """
        Evaluate a single policy document
        
        Returns:
            Tuple of (Effect or None, matching statements)
        """
        deny_statements = []
        allow_statements = []
        
        for statement in policy_doc.statement:
            if PolicyEvaluator.evaluate_statement(statement, action, resource):
                if statement.effect == "Deny":
                    deny_statements.append(statement)
                elif statement.effect == "Allow":
                    allow_statements.append(statement)
        
        # Explicit deny takes precedence
        if deny_statements:
            return ("Deny", deny_statements)
        
        # Then explicit allow
        if allow_statements:
            return ("Allow", allow_statements)
        
        # No matching statements
        return (None, [])
    
    @staticmethod
    async def get_user_policies(db: AsyncSession, user_id: str) -> List[PolicyDocument]:
        """
        Get all policies applicable to a user
        
        Collects policies from:
        - User inline policy
        - User attached policies
        - Group attached policies (for all groups user belongs to)
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of PolicyDocument objects
        """
        policies = []
        
        # Get user with relationships
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return policies
        
        # 1. User inline policy
        if user.inline_policy:
            try:
                policy_dict = json.loads(user.inline_policy)
                policies.append(PolicyDocument(**policy_dict))
            except (json.JSONDecodeError, ValueError):
                pass  # Invalid policy, skip
        
        # 2. User attached policies
        for policy in user.attached_policies:
            try:
                policy_dict = json.loads(policy.policy_document)
                policies.append(PolicyDocument(**policy_dict))
            except (json.JSONDecodeError, ValueError):
                pass
        
        # 3. Group policies
        for group in user.groups:
            # Group inline policy
            if group.inline_policy:
                try:
                    policy_dict = json.loads(group.inline_policy)
                    policies.append(PolicyDocument(**policy_dict))
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # Group attached policies
            for policy in group.attached_policies:
                try:
                    policy_dict = json.loads(policy.policy_document)
                    policies.append(PolicyDocument(**policy_dict))
                except (json.JSONDecodeError, ValueError):
                    pass
        
        return policies
    
    @staticmethod
    async def evaluate(
        db: AsyncSession,
        user_id: str,
        action: str,
        resource: str
    ) -> PolicyEvaluationDecision:
        """
        Evaluate IAM policies for a user's access request
        
        AWS Evaluation Logic:
        1. By default, all requests are implicitly denied
        2. An explicit allow in any policy overrides the default deny
        3. An explicit deny in any policy overrides any allows
        
        Args:
            db: Database session
            user_id: User making the request
            action: Action being requested (e.g., "ec2:StartInstances")
            resource: Resource ARN being accessed
            
        Returns:
            PolicyEvaluationDecision with result and reason
            
        Example:
            decision = await PolicyEvaluator.evaluate(
                db=db,
                user_id="AIDACKCEVSQ6C2EXAMPLE",
                action="ec2:StartInstances",
                resource="arn:aws:ec2:us-east-1:123456789012:instance/i-abc123"
            )
            
            if decision.is_allowed:
                # Allow action
                pass
            else:
                # Deny action
                raise PermissionError(decision.reason)
        """
        # Get all applicable policies
        policies = await PolicyEvaluator.get_user_policies(db, user_id)
        
        if not policies:
            return PolicyEvaluationDecision(
                result=EvaluationResult.IMPLICIT_DENY,
                reason="No policies attached to user",
                matching_statements=[]
            )
        
        # Track all matching statements
        all_deny_statements = []
        all_allow_statements = []
        
        # Evaluate each policy
        for policy_doc in policies:
            effect, statements = PolicyEvaluator.evaluate_policy_document(
                policy_doc, action, resource
            )
            
            if effect == "Deny":
                all_deny_statements.extend(statements)
            elif effect == "Allow":
                all_allow_statements.extend(statements)
        
        # AWS Evaluation Order:
        # 1. Explicit Deny wins
        if all_deny_statements:
            return PolicyEvaluationDecision(
                result=EvaluationResult.DENY,
                reason=f"Explicit Deny found for action '{action}' on resource '{resource}'",
                matching_statements=[
                    {"effect": "Deny", "sid": stmt.sid, "action": stmt.action, "resource": stmt.resource}
                    for stmt in all_deny_statements
                ]
            )
        
        # 2. Explicit Allow required
        if all_allow_statements:
            return PolicyEvaluationDecision(
                result=EvaluationResult.ALLOW,
                reason=f"Explicit Allow found for action '{action}' on resource '{resource}'",
                matching_statements=[
                    {"effect": "Allow", "sid": stmt.sid, "action": stmt.action, "resource": stmt.resource}
                    for stmt in all_allow_statements
                ]
            )
        
        # 3. Default Deny (no matching Allow)
        return PolicyEvaluationDecision(
            result=EvaluationResult.IMPLICIT_DENY,
            reason=f"No Allow statement found for action '{action}' on resource '{resource}'",
            matching_statements=[]
        )
    
    @staticmethod
    async def check_permission(
        db: AsyncSession,
        user_id: str,
        action: str,
        resource: str
    ) -> bool:
        """
        Quick permission check (returns boolean)
        
        Args:
            db: Database session
            user_id: User ID
            action: Action to check
            resource: Resource ARN
            
        Returns:
            True if allowed, False otherwise
        """
        decision = await PolicyEvaluator.evaluate(db, user_id, action, resource)
        return decision.is_allowed


# Import BaseModel for PolicyEvaluationDecision
from pydantic import BaseModel

