"""
Serverless Service - Lambda-like function management and execution with IAM integration
"""

import json
import time
import io
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from models.function import Function, InvocationResult
from core.region import get_current_region
from core.iam import IAMManager, Action
from core.events import EventBus, EventType, emit_event
from core.metering import UsageMeter, MetricType


class ServerlessService:
    """Service for managing and executing serverless functions with IAM protection
    
    *** SHARED LOCAL STORAGE ***
    Uses: data/functions/ (single namespace, not per-user)
    """
    
    def __init__(self):
        """Initialize serverless service with IAM integration"""
        # Shared storage: data/functions/
        self.data_root = Path("data/functions")
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.data_root / "metadata.json"
        self._functions = {}
        self._load_functions()
        
        # Initialize core systems
        self.iam = IAMManager()
        self.event_bus = EventBus()
    
    def _check_permission(self, action: str, resource_arn: str):
        """Check IAM permission and raise PermissionError if denied"""
        if not self.iam.check_permission(action, resource_arn):
            username = "local-user"
            raise PermissionError(
                f"User '{username}' does not have permission to perform action '{action}' on resource '{resource_arn}'"
            )
    
    def _load_functions(self):
        """Load function metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for func_data in data:
                        func = Function.from_dict(func_data)
                        self._functions[func.name] = func
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save_functions(self):
        """Save function metadata"""
        data = [func.to_dict() for func in self._functions.values()]
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving function metadata: {e}")
    
    def _save_function_code(self, name: str, code: str):
        """Save function code to file"""
        code_file = self.data_root / f"{name}.py"
        try:
            with open(code_file, 'w') as f:
                f.write(code)
        except IOError as e:
            raise ValueError(f"Failed to save function code: {e}")
    
    def _load_function_code(self, name: str) -> str:
        """Load function code from file"""
        code_file = self.data_root / f"{name}.py"
        if not code_file.exists():
            return ""
        try:
            with open(code_file, 'r') as f:
                return f.read()
        except IOError:
            return ""
    
    def create_function(self, name: str, code: str, handler: str = "handler", 
                       region: Optional[str] = None, tags: Optional[dict] = None) -> Function:
        """
        Create a new serverless function with IAM checks
        
        Args:
            name: Function name
            code: Python code containing the handler function
            handler: Name of the handler function (default: "handler")
            region: Region for function (defaults to current region)
            tags: Optional tags for the function
            
        Returns:
            Created function
            
        Raises:
            ValueError: If name is invalid or function exists
            PermissionError: If user lacks serverless:CreateFunction permission
        """
        region = region or get_current_region()
        resource_arn = f"arn:cloudsim:serverless:{region}:function/{name}"
        
        # IAM permission check
        self._check_permission(Action.SERVERLESS_CREATE_FUNCTION.value, resource_arn)
        
        if not name or not name.strip():
            raise ValueError("Function name cannot be empty")
        
        if not name.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Function name must be alphanumeric with dashes/underscores")
        
        if name in self._functions:
            raise ValueError(f"Function '{name}' already exists")
        
        if not code or not code.strip():
            raise ValueError("Function code cannot be empty")
        
        # Validate code syntax
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"Code syntax error: {e}")
        
        # Create function with region and owner
        func = Function.create_new(name, code, handler)
        func.region = region
        func.tags = tags or {}
        func.owner = "local-user"
        
        self._functions[name] = func
        self._save_function_code(name, code)
        self._save_functions()
        
        # Emit event
        emit_event(
            EventType.FUNCTION_CREATED,
            source="serverless",
            region=region,
            resource_id=name,
            resource_arn=resource_arn,
            details={"handler": handler, "tags": tags or {}}
        )
        
        return func
    
    def update_function(self, name: str, code: str) -> Function:
        """
        Update function code
        
        Args:
            name: Function name
            code: New Python code
            
        Returns:
            Updated function
            
        Raises:
            ValueError: If function doesn't exist or code is invalid
        """
        if name not in self._functions:
            raise ValueError(f"Function '{name}' does not exist")
        
        if not code or not code.strip():
            raise ValueError("Function code cannot be empty")
        
        # Validate code syntax
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"Code syntax error: {e}")
        
        # Update function
        func = self._functions[name]
        func.update_code(code)
        self._save_function_code(name, code)
        self._save_functions()
        
        return func
    
    def delete_function(self, name: str) -> bool:
        """
        Delete a function with IAM checks
        
        Args:
            name: Function name
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If function doesn't exist
            PermissionError: If user lacks serverless:DeleteFunction permission
        """
        if name not in self._functions:
            raise ValueError(f"Function '{name}' does not exist")
        
        func = self._functions[name]
        region = getattr(func, 'region', get_current_region())
        resource_arn = f"arn:cloudsim:serverless:{region}:function/{name}"
        
        # IAM permission check
        self._check_permission(Action.SERVERLESS_DELETE_FUNCTION.value, resource_arn)
        
        # Delete code file
        code_file = self.data_root / f"{name}.py"
        if code_file.exists():
            code_file.unlink()
        
        # Remove from metadata
        del self._functions[name]
        self._save_functions()
        
        # Emit event
        emit_event(
            EventType.FUNCTION_DELETED,
            source="serverless",
            region=region,
            resource_id=name,
            resource_arn=resource_arn,
            details={}
        )
        
        return True
    
    def get_function(self, name: str) -> Optional[Function]:
        """
        Get function by name
        
        Args:
            name: Function name
            
        Returns:
            Function or None if not found
        """
        func = self._functions.get(name)
        if func:
            # Load current code from file
            func.code = self._load_function_code(name)
        return func
    
    def list_functions(self, region: Optional[str] = None) -> List[Function]:
        """
        Get all functions with IAM checks and optional region filtering
        
        Args:
            region: Optional region filter
        
        Returns:
            List of functions
            
        Raises:
            PermissionError: If user lacks serverless:ListFunctions permission
        """
        # IAM permission check
        self._check_permission(Action.SERVERLESS_LIST_FUNCTIONS.value, "arn:cloudsim:serverless:*:function/*")
        
        functions = []
        for func in self._functions.values():
            # Load current code from file
            func.code = self._load_function_code(func.name)
            functions.append(func)
        
        # Filter by region if specified
        if region:
            functions = [f for f in functions if getattr(f, 'region', None) == region]
        
        return functions
    
    def invoke_function(self, name: str, event: Dict[str, Any]) -> InvocationResult:
        """
        Invoke a function with event data and IAM checks
        
        Args:
            name: Function name
            event: Event data (dict)
            
        Returns:
            InvocationResult with output, logs, and errors
            
        Raises:
            ValueError: If function doesn't exist
            PermissionError: If user lacks serverless:InvokeFunction permission
        """
        if name not in self._functions:
            raise ValueError(f"Function '{name}' does not exist")
        
        func = self._functions[name]
        region = getattr(func, 'region', get_current_region())
        resource_arn = f"arn:cloudsim:serverless:{region}:function/{name}"
        
        # IAM permission check
        self._check_permission(Action.SERVERLESS_INVOKE_FUNCTION.value, resource_arn)
        
        func.code = self._load_function_code(name)
        
        # Execute function
        result = self._execute_function(func, event)
        
        # Emit event
        emit_event(
            EventType.FUNCTION_INVOKED,
            source="serverless",
            region=region,
            resource_id=name,
            resource_arn=resource_arn,
            details={
                "duration_ms": result.duration_ms,
                "success": result.error is None
            }
        )
        
        # Update invocation count
        func.increment_invocations()
        self._save_functions()
        
        return result
    
    def _execute_function(self, func: Function, event: Dict[str, Any]) -> InvocationResult:
        """
        Execute a function in a restricted environment
        
        Args:
            func: Function to execute
            event: Event data
            
        Returns:
            InvocationResult
        """
        start_time = time.time()
        
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Create restricted globals
            # Allow basic builtins but restrict dangerous operations
            safe_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'any': any,
                    'all': all,
                    'isinstance': isinstance,
                    'type': type,
                    'json': json,
                },
                'json': json,
            }
            
            # Create context dict for execution
            context = {
                'function_name': func.name,
                'function_version': '1.0',
            }
            
            # Execute the function code to define the handler
            exec(func.code, safe_globals)
            
            # Get the handler function
            if func.handler not in safe_globals:
                raise ValueError(f"Handler function '{func.handler}' not found in code")
            
            handler_func = safe_globals[func.handler]
            
            # Invoke the handler
            result = handler_func(event, context)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000  # milliseconds
            
            # Get logs
            logs = stdout_capture.getvalue()
            errors = stderr_capture.getvalue()
            
            # Format output
            if result is not None:
                try:
                    output = json.dumps(result, indent=2)
                except (TypeError, ValueError):
                    output = str(result)
            else:
                output = "null"
            
            return InvocationResult(
                success=True,
                output=output,
                logs=logs if logs else None,
                error=errors if errors else None,
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logs = stdout_capture.getvalue()
            
            return InvocationResult(
                success=False,
                output=None,
                logs=logs if logs else None,
                error=f"{type(e).__name__}: {str(e)}",
                duration_ms=duration
            )
            
        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def get_default_code_template(self) -> str:
        """
        Get default function code template
        
        Returns:
            Default Python code template
        """
        return '''def handler(event, context):
    """
    Lambda function handler
    
    Args:
        event: Input event data (dict)
        context: Runtime context (dict)
    
    Returns:
        Response data (will be JSON-serialized)
    """
    # Example: Echo the event
    name = event.get('name', 'World')
    
    print(f"Processing request for: {name}")
    
    return {
        'statusCode': 200,
        'body': f'Hello, {name}!'
    }
'''
