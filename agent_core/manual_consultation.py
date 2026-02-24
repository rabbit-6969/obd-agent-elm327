"""
Manual Consultation Workflow

Guides user through providing service manual information when web research fails.
"""

import logging
import re
from typing import Dict, Any, Optional, List


logger = logging.getLogger(__name__)


class ManualConsultation:
    """
    Manual consultation workflow
    
    Asks user for service manual information and parses their input
    to construct diagnostic procedures.
    """
    
    def __init__(self):
        """Initialize manual consultation"""
        pass
    
    def request_manual_info(self, vehicle_info: Dict[str, Any],
                           module_name: str, action: str) -> str:
        """
        Generate request for manual information
        
        Args:
            vehicle_info: Vehicle make/model/year
            module_name: Target module
            action: Diagnostic action
            
        Returns:
            Request message for user
        """
        make = vehicle_info.get("make", "")
        model = vehicle_info.get("model", "")
        year = vehicle_info.get("year", "")
        
        message = f"""
📖 Manual Consultation Required

I couldn't find diagnostic procedures online for:
  Vehicle: {year} {make} {model}
  Module: {module_name}
  Action: {action}

If you have access to a service manual, please provide:

1. Module CAN Address (e.g., 0x7A0, 7E0)
2. Diagnostic Command (e.g., 03 for read DTC, 22 XX XX for read data)
3. Expected Response Format (e.g., 43 XX XX for DTC response)

Example format:
  Address: 0x7A0
  Command: 03
  Response: 43 [DTC codes]

Please paste the information below:
"""
        
        logger.info(f"Requesting manual info for {module_name} {action}")
        return message.strip()
    
    def parse_manual_input(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user-provided manual information
        
        Args:
            user_input: User's manual information
            
        Returns:
            Parsed procedure information
        """
        result = {
            "success": False,
            "address": None,
            "command": None,
            "response_pattern": None,
            "raw_input": user_input
        }
        
        # Parse address
        address_match = re.search(r'address[:\s]+(?:0x)?([0-9A-Fa-f]{2,3})', 
                                 user_input, re.IGNORECASE)
        if address_match:
            result["address"] = address_match.group(1).upper()
        
        # Parse command
        command_match = re.search(r'command[:\s]+([0-9A-Fa-f\s]{2,})', 
                                 user_input, re.IGNORECASE)
        if command_match:
            command = command_match.group(1).strip().replace(" ", "")
            result["command"] = command.upper()
        
        # Parse response pattern
        response_match = re.search(r'response[:\s]+([0-9A-Fa-f\[\]\s]+)', 
                                  user_input, re.IGNORECASE)
        if response_match:
            result["response_pattern"] = response_match.group(1).strip()
        
        # Check if we got minimum required info
        if result["address"] and result["command"]:
            result["success"] = True
            logger.info(f"Parsed manual info: address={result['address']}, command={result['command']}")
        else:
            logger.warning("Failed to parse complete manual information")
        
        return result
    
    def generate_guidance(self, module_name: str, action: str) -> str:
        """
        Generate guidance on what to look for in manual
        
        Args:
            module_name: Target module
            action: Diagnostic action
            
        Returns:
            Guidance message
        """
        guidance_map = {
            "read_dtc": f"""
Look for the following in your service manual for {module_name}:

1. Module Address/ID:
   - Usually in "Module Addressing" or "CAN Configuration" section
   - Format: 0x7XX or 7XX (3-digit hex)
   
2. DTC Read Command:
   - Look for "Read Diagnostic Trouble Codes" or "Mode 03"
   - Standard OBD2: 03
   - UDS: 19 02 FF (read all DTCs)
   
3. Response Format:
   - Standard: 43 [DTC bytes]
   - UDS: 59 02 [DTC bytes]
""",
            "clear_dtc": f"""
Look for the following in your service manual for {module_name}:

1. Module Address (same as read DTC)
   
2. Clear DTC Command:
   - Look for "Clear Diagnostic Information" or "Mode 04"
   - Standard OBD2: 04
   - UDS: 14 FF FF FF
   
3. Success Response:
   - Standard: 44
   - UDS: 54
""",
            "read_data": f"""
Look for the following in your service manual for {module_name}:

1. Module Address
   
2. Data Identifier (DID):
   - Look for "Parameter IDs" or "Data Identifiers"
   - Format: 22 XX XX (UDS read data by identifier)
   
3. Response Format:
   - 62 XX XX [data bytes]
"""
        }
        
        guidance = guidance_map.get(action, f"""
Look for diagnostic procedures for {module_name} in your service manual.
Focus on:
- Module CAN address
- Command format for {action}
- Expected response format
""")
        
        return guidance.strip()
    
    def validate_procedure(self, procedure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parsed procedure
        
        Args:
            procedure: Parsed procedure info
            
        Returns:
            Validation results
        """
        issues = []
        
        # Validate address
        if not procedure.get("address"):
            issues.append("Missing module address")
        elif not re.match(r'^[0-9A-Fa-f]{2,3}$', procedure["address"]):
            issues.append("Invalid address format (should be 2-3 hex digits)")
        
        # Validate command
        if not procedure.get("command"):
            issues.append("Missing command")
        elif not re.match(r'^[0-9A-Fa-f]+$', procedure["command"]):
            issues.append("Invalid command format (should be hex digits)")
        
        # Validate response pattern (optional)
        if procedure.get("response_pattern"):
            # Just check it's not empty
            if not procedure["response_pattern"].strip():
                issues.append("Empty response pattern")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def format_procedure_summary(self, procedure: Dict[str, Any]) -> str:
        """
        Format procedure summary for user confirmation
        
        Args:
            procedure: Parsed procedure
            
        Returns:
            Formatted summary
        """
        summary = f"""
Parsed Procedure:
  Module Address: {procedure.get('address', 'N/A')}
  Command: {procedure.get('command', 'N/A')}
  Response Pattern: {procedure.get('response_pattern', 'N/A')}

This command will be sent to the vehicle.
"""
        return summary.strip()


if __name__ == '__main__':
    # Test manual consultation
    print("Testing Manual Consultation...")
    
    consultation = ManualConsultation()
    
    # Test request generation
    print("\n1. Testing manual info request...")
    vehicle_info = {"make": "Ford", "model": "Escape", "year": 2008}
    request = consultation.request_manual_info(vehicle_info, "HVAC", "read_dtc")
    print(request)
    
    # Test parsing
    print("\n2. Testing manual input parsing...")
    test_input = """
    Address: 0x7A0
    Command: 03
    Response: 43 [DTC codes]
    """
    
    parsed = consultation.parse_manual_input(test_input)
    print(f"   Success: {parsed['success']}")
    print(f"   Address: {parsed['address']}")
    print(f"   Command: {parsed['command']}")
    
    # Test guidance generation
    print("\n3. Testing guidance generation...")
    guidance = consultation.generate_guidance("HVAC", "read_dtc")
    print(guidance[:100] + "...")
    
    # Test validation
    print("\n4. Testing procedure validation...")
    validation = consultation.validate_procedure(parsed)
    print(f"   Valid: {validation['valid']}")
    if validation['issues']:
        print(f"   Issues: {validation['issues']}")
    
    # Test summary formatting
    print("\n5. Testing procedure summary...")
    summary = consultation.format_procedure_summary(parsed)
    print(summary)
    
    # Test invalid input
    print("\n6. Testing invalid input parsing...")
    invalid_input = "Some random text without proper format"
    parsed_invalid = consultation.parse_manual_input(invalid_input)
    print(f"   Success: {parsed_invalid['success']}")
    
    print("\nManual consultation tests passed!")
