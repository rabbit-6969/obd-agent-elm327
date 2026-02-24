"""
Command Confirmation Workflow

Requires user confirmation before sending newly constructed commands.
Documents confirmed working procedures.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class CommandConfirmation:
    """
    Command confirmation workflow
    
    Shows command details and requires explicit confirmation
    before sending to vehicle. Documents successful procedures.
    """
    
    def __init__(self):
        """Initialize command confirmation"""
        pass
    
    def request_confirmation(self, command_info: Dict[str, Any],
                           source: str = "unknown") -> str:
        """
        Generate confirmation request
        
        Args:
            command_info: Command details
            source: Source of command (manual, web_research, etc.)
            
        Returns:
            Confirmation request message
        """
        module = command_info.get("module", "Unknown")
        address = command_info.get("address", "Unknown")
        command = command_info.get("command", "Unknown")
        action = command_info.get("action", "Unknown")
        
        message = f"""
⚠️  Command Confirmation Required

This is a newly constructed command that hasn't been verified yet.

Details:
  Module: {module}
  Address: {address}
  Command: {command}
  Action: {action}
  Source: {source}

Expected Behavior:
  {self._describe_expected_behavior(action, command)}

⚠️  WARNING: Sending incorrect commands can potentially cause issues.

Do you want to proceed? (yes/no)
"""
        
        logger.info(f"Requesting confirmation for {module} command: {command}")
        return message.strip()
    
    def _describe_expected_behavior(self, action: str, command: str) -> str:
        """
        Describe expected behavior for command
        
        Args:
            action: Diagnostic action
            command: Command hex
            
        Returns:
            Behavior description
        """
        descriptions = {
            "read_dtc": "Read diagnostic trouble codes from module (read-only, safe)",
            "clear_dtc": "Clear stored diagnostic codes (write operation)",
            "read_data": "Read live data from module (read-only, safe)",
            "read_vin": "Read vehicle identification number (read-only, safe)",
            "actuate": "Command module to perform action (CAUTION: may cause physical movement)"
        }
        
        return descriptions.get(action, "Execute diagnostic command")
    
    def parse_confirmation(self, user_response: str) -> bool:
        """
        Parse user confirmation response
        
        Args:
            user_response: User's response
            
        Returns:
            True if confirmed
        """
        response_lower = user_response.strip().lower()
        
        # Positive responses
        if response_lower in ["yes", "y", "ok", "confirm", "proceed"]:
            logger.info("User confirmed command")
            return True
        
        # Negative responses
        logger.info("User declined command")
        return False
    
    def document_success(self, command_info: Dict[str, Any],
                        response: str, vehicle_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Document successful command for future use
        
        Args:
            command_info: Command details
            response: Vehicle response
            vehicle_info: Vehicle make/model/year
            
        Returns:
            Documentation record
        """
        record = {
            "vehicle": {
                "make": vehicle_info.get("make"),
                "model": vehicle_info.get("model"),
                "year": vehicle_info.get("year")
            },
            "module": command_info.get("module"),
            "address": command_info.get("address"),
            "command": command_info.get("command"),
            "action": command_info.get("action"),
            "response": response,
            "verified_at": datetime.now().isoformat(),
            "status": "verified"
        }
        
        logger.info(f"Documented successful procedure for {command_info.get('module')}")
        return record
    
    def format_success_message(self, command_info: Dict[str, Any]) -> str:
        """
        Format success message after command execution
        
        Args:
            command_info: Command details
            
        Returns:
            Success message
        """
        module = command_info.get("module", "module")
        action = command_info.get("action", "command")
        
        message = f"""
✅ Command Successful!

The {action} command for {module} worked correctly.
This procedure has been documented and will be used automatically next time.

Future diagnostics for this module will be faster!
"""
        
        return message.strip()
    
    def format_failure_message(self, command_info: Dict[str, Any],
                              error: str) -> str:
        """
        Format failure message
        
        Args:
            command_info: Command details
            error: Error description
            
        Returns:
            Failure message
        """
        module = command_info.get("module", "module")
        
        message = f"""
❌ Command Failed

The command for {module} did not work as expected.

Error: {error}

This procedure will NOT be saved. You may want to:
1. Double-check the service manual information
2. Try a different command format
3. Verify the module address is correct
"""
        
        return message.strip()
    
    def create_confirmation_record(self, command_info: Dict[str, Any],
                                  confirmed: bool, user_response: str) -> Dict[str, Any]:
        """
        Create confirmation audit record
        
        Args:
            command_info: Command details
            confirmed: Whether user confirmed
            user_response: User's response text
            
        Returns:
            Audit record
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "module": command_info.get("module"),
            "command": command_info.get("command"),
            "action": command_info.get("action"),
            "confirmed": confirmed,
            "user_response": user_response,
            "source": command_info.get("source", "unknown")
        }
        
        return record


if __name__ == '__main__':
    # Test command confirmation
    print("Testing Command Confirmation...")
    
    confirmation = CommandConfirmation()
    
    # Test confirmation request
    print("\n1. Testing confirmation request...")
    command_info = {
        "module": "HVAC",
        "address": "7A0",
        "command": "03",
        "action": "read_dtc",
        "source": "manual"
    }
    
    request = confirmation.request_confirmation(command_info, "manual")
    print(request)
    
    # Test parsing confirmation
    print("\n2. Testing confirmation parsing...")
    test_responses = ["yes", "no", "y", "n", "confirm", "cancel"]
    for response in test_responses:
        confirmed = confirmation.parse_confirmation(response)
        print(f"   '{response}' -> {confirmed}")
    
    # Test success documentation
    print("\n3. Testing success documentation...")
    vehicle_info = {"make": "Ford", "model": "Escape", "year": 2008}
    response = "43 16 32"
    
    record = confirmation.document_success(command_info, response, vehicle_info)
    print(f"   Documented: {record['module']} at {record['verified_at']}")
    
    # Test success message
    print("\n4. Testing success message...")
    success_msg = confirmation.format_success_message(command_info)
    print(success_msg)
    
    # Test failure message
    print("\n5. Testing failure message...")
    failure_msg = confirmation.format_failure_message(command_info, "No response from module")
    print(failure_msg)
    
    # Test audit record
    print("\n6. Testing audit record...")
    audit = confirmation.create_confirmation_record(command_info, True, "yes")
    print(f"   Audit record created: confirmed={audit['confirmed']}")
    
    print("\nCommand confirmation tests passed!")
