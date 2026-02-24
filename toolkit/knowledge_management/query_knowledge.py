#!/usr/bin/env python3
"""
Query Knowledge Toolkit Script

Searches technical data files for diagnostic procedures.
Returns matching commands and expected responses.

Usage:
    python query_knowledge.py --vehicle Ford_Escape_2008 --module HVAC --action read_dtc
    python query_knowledge.py --vehicle Ford_Escape_2008 --module PCM --action read_live

Output Format:
    {
        "success": true,
        "module": {"name": "HVAC", "address": "7A0", "protocol": "CAN", "bus": "MS"},
        "commands": [
            {"id": "HVAC.READ_DTC", "mode": "03", "response_pattern": "43[0-9A-F]{4,}"}
        ],
        "response_rules": [
            {"cmd_id": "READ_DTC", "pattern": "43([0-9A-F]{4})+", "extract": ["dtc_hex"]}
        ]
    }
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_knowledge_base_path(vehicle: str) -> Path:
    """
    Get path to vehicle's technical data file
    
    Args:
        vehicle: Vehicle identifier (e.g., "Ford_Escape_2008")
        
    Returns:
        Path to .dat file
    """
    # Try relative to script location first
    script_dir = Path(__file__).parent.parent.parent
    kb_path = script_dir / "knowledge_base" / f"{vehicle}_technical.dat"
    
    if kb_path.exists():
        return kb_path
    
    # Try current directory
    kb_path = Path("knowledge_base") / f"{vehicle}_technical.dat"
    if kb_path.exists():
        return kb_path
    
    return None


def parse_key_values(line: str) -> Dict[str, str]:
    """
    Parse key:value pairs from line
    
    Args:
        line: Line with space-separated key:value pairs
        
    Returns:
        Dictionary of key-value pairs
    """
    import re
    pattern = re.compile(r'(\w+):([^\s]+)')
    matches = pattern.findall(line)
    return {key: value for key, value in matches}


def parse_module_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parse module definition line
    
    Args:
        line: Module line (M:HVAC A:7A0 P:CAN B:HS)
        
    Returns:
        Module dict or None
    """
    if not line.startswith('M:'):
        return None
    
    kv = parse_key_values(line)
    
    if 'M' not in kv or 'A' not in kv:
        return None
    
    return {
        "name": kv['M'],
        "address": kv['A'],
        "protocol": kv.get('P', 'CAN'),
        "bus": kv.get('B', 'HS'),
        "status": kv.get('S', 'unknown')
    }


def parse_command_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parse command definition line
    
    Args:
        line: Command line (C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,})
        
    Returns:
        Command dict or None
    """
    if not line.startswith('C:'):
        return None
    
    kv = parse_key_values(line)
    
    if 'C' not in kv or 'M' not in kv:
        return None
    
    # Extract response pattern (everything after R:)
    response_pattern = ""
    if 'R:' in line:
        response_pattern = line.split('R:', 1)[1].strip()
    
    # Check for UDS command
    uds_did = None
    if 'UDS:' in line:
        uds_did = kv.get('DID', '')
    
    command = {
        "id": kv['C'],
        "mode": kv['M'],
        "response_pattern": response_pattern
    }
    
    if 'PID' in kv:
        command["pid"] = kv['PID']
    if 'D' in kv:
        command["data"] = kv['D']
    if uds_did:
        command["uds_did"] = uds_did
    
    return command


def parse_response_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse response rule line
    
    Args:
        line: Response line (R:READ_DTC PATTERN:43([0-9A-F]{4})+ EXTRACT:dtc_hex)
        
    Returns:
        Response rule dict or None
    """
    if not line.startswith('R:'):
        return None
    
    kv = parse_key_values(line)
    
    if 'R' not in kv:
        return None
    
    rule = {
        "cmd_id": kv['R']
    }
    
    if 'PATTERN' in kv:
        rule["pattern"] = kv['PATTERN']
    
    if 'EXTRACT' in kv:
        rule["extract"] = [f.strip() for f in kv['EXTRACT'].split(',')]
    
    if 'CALC' in kv:
        rule["calculations"] = [f.strip() for f in kv['CALC'].split(',')]
    
    if 'MEANING' in kv:
        rule["meaning"] = kv['MEANING']
    
    return rule


def match_action_to_command(action: str, command_id: str) -> bool:
    """
    Check if action matches command ID
    
    Args:
        action: Action keyword (e.g., "read_dtc", "clear", "actuate")
        command_id: Command ID (e.g., "HVAC.READ_DTC")
        
    Returns:
        True if action matches
    """
    action_lower = action.lower().replace('_', '').replace('-', '')
    command_lower = command_id.lower().replace('_', '').replace('-', '')
    
    # Direct substring match
    if action_lower in command_lower:
        return True
    
    # Action keyword mapping
    action_keywords = {
        'read': ['read', 'get', 'query'],
        'clear': ['clear', 'erase', 'delete'],
        'dtc': ['dtc', 'code', 'fault'],
        'live': ['live', 'data', 'pid'],
        'actuate': ['actuate', 'test', 'activate'],
        'vin': ['vin', 'vehicle'],
        'monitor': ['monitor', 'status']
    }
    
    for keyword, synonyms in action_keywords.items():
        if any(syn in action_lower for syn in synonyms):
            if keyword in command_lower:
                return True
    
    return False


def query_knowledge(vehicle: str, module: str, action: str) -> Dict[str, Any]:
    """
    Query knowledge base for matching procedures
    
    Args:
        vehicle: Vehicle identifier
        module: Module name (e.g., "HVAC", "PCM")
        action: Action keyword (e.g., "read_dtc", "clear")
        
    Returns:
        Result dict with matching procedures
    """
    try:
        filepath = get_knowledge_base_path(vehicle)
        
        if not filepath or not filepath.exists():
            return {
                "success": False,
                "error": f"Knowledge base not found for vehicle: {vehicle}"
            }
        
        module_info = None
        matching_commands = []
        matching_responses = []
        
        # Parse file and find matches
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse module
                if line.startswith('M:'):
                    parsed_module = parse_module_line(line)
                    if parsed_module and parsed_module['name'].upper() == module.upper():
                        module_info = parsed_module
                
                # Parse command
                elif line.startswith('C:'):
                    command = parse_command_line(line)
                    if command:
                        # Check if command matches module and action
                        cmd_id = command['id']
                        cmd_module = cmd_id.split('.')[0] if '.' in cmd_id else ''
                        
                        if cmd_module.upper() == module.upper():
                            if match_action_to_command(action, cmd_id):
                                matching_commands.append(command)
                
                # Parse response rule
                elif line.startswith('R:'):
                    response = parse_response_line(line)
                    if response:
                        # Check if response matches any found command
                        for cmd in matching_commands:
                            cmd_action = cmd['id'].split('.')[-1] if '.' in cmd['id'] else cmd['id']
                            if response['cmd_id'].upper() in cmd_action.upper():
                                matching_responses.append(response)
        
        if not module_info:
            return {
                "success": False,
                "error": f"Module '{module}' not found in knowledge base"
            }
        
        if not matching_commands:
            return {
                "success": False,
                "error": f"No procedures found for module '{module}' with action '{action}'"
            }
        
        return {
            "success": True,
            "module": module_info,
            "commands": matching_commands,
            "response_rules": matching_responses
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Query knowledge base for diagnostic procedures"
    )
    parser.add_argument(
        "--vehicle",
        required=True,
        help="Vehicle identifier (e.g., Ford_Escape_2008)"
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Module name (e.g., HVAC, PCM, ABS)"
    )
    parser.add_argument(
        "--action",
        required=True,
        help="Action keyword (e.g., read_dtc, clear, read_live)"
    )
    
    args = parser.parse_args()
    
    # Query knowledge base
    result = query_knowledge(args.vehicle, args.module, args.action)
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
