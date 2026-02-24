"""
Error Handler and Recovery

Implements error recovery strategies and graceful degradation.
Provides fallback approaches when operations fail.
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur"""
    CONNECTION_ERROR = "connection_error"
    COMMAND_FAILURE = "command_failure"
    PARSE_ERROR = "parse_error"
    TIMEOUT_ERROR = "timeout_error"
    PROTOCOL_ERROR = "protocol_error"
    WEB_RESEARCH_FAILURE = "web_research_failure"
    AI_BACKEND_UNAVAILABLE = "ai_backend_unavailable"
    KNOWLEDGE_BASE_ERROR = "knowledge_base_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryStrategy:
    """Base class for recovery strategies"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute recovery strategy
        
        Args:
            context: Error context with details
            
        Returns:
            Recovery result dict with success status and message
        """
        raise NotImplementedError


class RetryStrategy(RecoveryStrategy):
    """Retry the failed operation"""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        super().__init__(
            "retry",
            f"Retry operation up to {max_retries} times"
        )
        self.max_retries = max_retries
        self.delay = delay
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute retry strategy"""
        return {
            "success": False,
            "strategy": self.name,
            "message": f"Retry operation (max {self.max_retries} attempts)",
            "action": "retry"
        }


class FallbackCommandStrategy(RecoveryStrategy):
    """Try alternative command"""
    
    def __init__(self):
        super().__init__(
            "fallback_command",
            "Try alternative command or protocol"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fallback command strategy"""
        suggestions = []
        
        # Suggest alternative protocols
        if context.get("protocol") == "UDS":
            suggestions.append("Try standard OBD-II mode instead of UDS")
        elif context.get("protocol") == "OBD2":
            suggestions.append("Try manufacturer-specific UDS commands")
        
        # Suggest alternative addressing
        if context.get("address"):
            suggestions.append("Try broadcast address (7DF) instead of module-specific")
        
        return {
            "success": True,
            "strategy": self.name,
            "message": "Alternative approaches available",
            "suggestions": suggestions
        }


class ManualConsultationStrategy(RecoveryStrategy):
    """Ask user to consult manual"""
    
    def __init__(self):
        super().__init__(
            "manual_consultation",
            "Request user to consult service manual"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute manual consultation strategy"""
        vehicle = context.get("vehicle_info", {})
        module = context.get("module", "unknown")
        
        message = (
            f"Unable to find procedure for {vehicle.get('make', '')} "
            f"{vehicle.get('model', '')} {vehicle.get('year', '')} {module} module. "
            f"Please consult the service manual for the correct diagnostic procedure."
        )
        
        return {
            "success": True,
            "strategy": self.name,
            "message": message,
            "action": "request_user_input"
        }


class ErrorHandler:
    """
    Handles errors and implements recovery strategies
    
    Features:
    - Error classification
    - Recovery strategy selection
    - Fallback suggestions
    - Graceful degradation
    """
    
    def __init__(self):
        self.strategies: Dict[ErrorType, List[RecoveryStrategy]] = {
            ErrorType.CONNECTION_ERROR: [
                RetryStrategy(max_retries=3, delay=2.0),
                ManualConsultationStrategy()
            ],
            ErrorType.COMMAND_FAILURE: [
                FallbackCommandStrategy(),
                ManualConsultationStrategy()
            ],
            ErrorType.TIMEOUT_ERROR: [
                RetryStrategy(max_retries=2, delay=3.0)
            ],
            ErrorType.WEB_RESEARCH_FAILURE: [
                ManualConsultationStrategy()
            ],
            ErrorType.AI_BACKEND_UNAVAILABLE: [],
            ErrorType.KNOWLEDGE_BASE_ERROR: [
                ManualConsultationStrategy()
            ]
        }
    
    def handle_error(self, error_type: ErrorType, 
                    context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle error and suggest recovery
        
        Args:
            error_type: Type of error
            context: Error context with details
            
        Returns:
            Recovery suggestion dict
        """
        logger.error(f"Handling error: {error_type.value}")
        logger.debug(f"Error context: {context}")
        
        # Get recovery strategies for this error type
        strategies = self.strategies.get(error_type, [])
        
        if not strategies:
            return {
                "success": False,
                "error_type": error_type.value,
                "message": "No recovery strategies available",
                "suggestions": []
            }
        
        # Try first strategy
        strategy = strategies[0]
        result = strategy.execute(context)
        result["error_type"] = error_type.value
        
        # Add alternative strategies
        if len(strategies) > 1:
            result["alternative_strategies"] = [
                {"name": s.name, "description": s.description}
                for s in strategies[1:]
            ]
        
        return result
    
    def suggest_can_bus_fixes(self, error_context: Dict[str, Any]) -> List[str]:
        """
        Suggest fixes for CAN bus communication failures
        
        Args:
            error_context: Error context
            
        Returns:
            List of suggestions
        """
        suggestions = [
            "Check ELM327 adapter connection to OBD-II port",
            "Verify vehicle ignition is ON (not ACC)",
            "Ensure adapter is compatible with vehicle CAN protocol",
            "Try different baud rate settings (38400, 115200)",
            "Check for blown OBD-II port fuse",
            "Verify adapter firmware is up to date"
        ]
        
        # Add protocol-specific suggestions
        protocol = error_context.get("protocol")
        if protocol == "CAN":
            suggestions.append("Try setting protocol manually (AT SP 6 for CAN 11-bit)")
            suggestions.append("Try auto protocol detection (AT SP 0)")
        
        return suggestions
    
    def get_degraded_mode_message(self, unavailable_feature: str) -> str:
        """
        Get message for degraded mode operation
        
        Args:
            unavailable_feature: Feature that is unavailable
            
        Returns:
            User-friendly message
        """
        messages = {
            "ai_backend": (
                "AI backend is unavailable. Operating in manual mode. "
                "You can still execute diagnostic commands, but AI-assisted "
                "interpretation and web research are not available."
            ),
            "web_research": (
                "Web research is unavailable. You can provide manual information "
                "from service manuals or online resources."
            ),
            "knowledge_base": (
                "Knowledge base is unavailable. Using generic OBD-II commands only. "
                "Vehicle-specific procedures may not be available."
            )
        }
        
        return messages.get(
            unavailable_feature,
            f"Feature '{unavailable_feature}' is unavailable. "
            "Operating with reduced functionality."
        )


def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any, Optional[str]]:
    """
    Safely execute function with error handling
    
    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Tuple of (success, result, error_message)
    """
    try:
        result = func(*args, **kwargs)
        return (True, result, None)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        return (False, None, str(e))


if __name__ == '__main__':
    # Test error handler
    print("Testing Error Handler...")
    
    handler = ErrorHandler()
    
    # Test connection error
    print("\n1. Testing connection error handling...")
    result = handler.handle_error(
        ErrorType.CONNECTION_ERROR,
        {"port": "COM3", "adapter": "ELM327"}
    )
    print(f"   Strategy: {result.get('strategy')}")
    print(f"   Message: {result.get('message')}")
    
    # Test command failure
    print("\n2. Testing command failure handling...")
    result = handler.handle_error(
        ErrorType.COMMAND_FAILURE,
        {"command": "22 1E 1C", "module": "PCM", "protocol": "UDS"}
    )
    print(f"   Strategy: {result.get('strategy')}")
    print(f"   Suggestions: {len(result.get('suggestions', []))}")
    
    # Test CAN bus suggestions
    print("\n3. Testing CAN bus fix suggestions...")
    suggestions = handler.suggest_can_bus_fixes({"protocol": "CAN"})
    print(f"   Suggestions: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"   {i}. {suggestion}")
    
    # Test degraded mode
    print("\n4. Testing degraded mode messages...")
    message = handler.get_degraded_mode_message("ai_backend")
    print(f"   Message: {message[:80]}...")
    
    # Test safe execute
    print("\n5. Testing safe execute...")
    success, result, error = safe_execute(lambda x: x * 2, 5)
    print(f"   Success: {success}, Result: {result}")
    
    success, result, error = safe_execute(lambda: 1/0)
    print(f"   Success: {success}, Error: {error}")
    
    print("\nError handler tests passed!")
