#!/usr/bin/env python3
"""
Append Procedure Toolkit Script

Appends new diagnostic procedures to technical data files.
Converts JSON input to compact format and appends to .dat file.

Usage:
    python append_procedure.py --vehicle Ford_Escape_2008 --input procedure.json
    echo '{"module": "PCM", "command": {...}}' | python append_procedure.py --vehicle Ford_Escape_2008

Input JSON Format:
    {
        "module": {
            "name": "HVAC",
            "address": "7A0",
            "protocol": "CAN",
            "bus": "MS"
        },
        "command": {
            "id": "HVAC.READ_TEMP",
            "mode": "01",
            "pid": "05",
            "response_pattern": "41 05 [0-9A-F]{2}"
        },
        "response_rule": {
            "cmd_id": "READ_TEMP",
            "pattern": "41 05 ([0-9A-F]{2})",
            "extract": ["temp_hex"],
            "calculations": ["(hex-40)"]
        }
    }

Output Format:
    {"success": true, "appended": ["M:HVAC A:7A0 P:CAN B:MS", "C:HVAC.READ_TEMP M:01 PID:05 R:41 05 [0-9A-F]{2}"]}
    {"success": false, "error": "File not found"}
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List


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
    
    # Create if doesn't exist
    kb_dir = script_dir / "knowledge_base"
    kb_dir.mkdir(exist_ok=True)
    return kb_dir / f"{vehicle}_technical.dat"


def serialize_module(module: Dict[str, str]) -> str:
    """
    Serialize module to compact format
    
    Args:
        module: Module dict with name, address, protocol, bus
        
    Returns:
        Compact format string
    """
    name = module.get("name", "")
    address = module.get("address", "")
    protocol = module.get("protocol", "CAN")
    bus = module.get("bus", "HS")
    
    if not name or not address:
        raise ValueError("Module must have 'name' and 'address' fields")
    
    return f"M:{name} A:{address} P:{protocol} B:{bus}"


def serialize_command(command: Dict[str, str]) -> str:
    """
    Serialize command to compact format
    
    Args:
        command: Command dict with id, mode, optional pid/data/response_pattern
        
    Returns:
        Compact format string
    """
    cmd_id = command.get("id", "")
    mode = command.get("mode", "")
    
    if not cmd_id or not mode:
        raise ValueError("Command must have 'id' and 'mode' fields")
    
    parts = [f"C:{cmd_id}", f"M:{mode}"]
    
    if "pid" in command:
        parts.append(f"PID:{command['pid']}")
    if "data" in command:
        parts.append(f"D:{command['data']}")
    if "response_pattern" in command:
        parts.append(f"R:{command['response_pattern']}")
    
    return " ".join(parts)


def serialize_dtc_rule(dtc_rule: Dict[str, str]) -> str:
    """
    Serialize DTC rule to compact format
    
    Args:
        dtc_rule: DTC rule dict with code, byte_range, bit_range, calculation
        
    Returns:
        Compact format string
    """
    code = dtc_rule.get("code", "")
    byte_range = dtc_rule.get("byte_range", "0-1")
    bit_range = dtc_rule.get("bit_range", "0-15")
    calculation = dtc_rule.get("calculation", "hex")
    
    if not code:
        raise ValueError("DTC rule must have 'code' field")
    
    return f"DTC:{code} B:{byte_range} BITS:{bit_range} CALC:{calculation}"


def serialize_response_rule(response_rule: Dict[str, Any]) -> str:
    """
    Serialize response rule to compact format
    
    Args:
        response_rule: Response rule dict with cmd_id, pattern, extract, calculations
        
    Returns:
        Compact format string
    """
    cmd_id = response_rule.get("cmd_id", "")
    
    if not cmd_id:
        raise ValueError("Response rule must have 'cmd_id' field")
    
    parts = [f"R:{cmd_id}"]
    
    if "pattern" in response_rule:
        parts.append(f"PATTERN:{response_rule['pattern']}")
    if "extract" in response_rule:
        extract_list = response_rule["extract"]
        if isinstance(extract_list, list):
            parts.append(f"EXTRACT:{','.join(extract_list)}")
        else:
            parts.append(f"EXTRACT:{extract_list}")
    if "calculations" in response_rule:
        calc_list = response_rule["calculations"]
        if isinstance(calc_list, list):
            parts.append(f"CALC:{','.join(calc_list)}")
        else:
            parts.append(f"CALC:{calc_list}")
    
    return " ".join(parts)


def check_duplicate(filepath: Path, line: str) -> bool:
    """
    Check if line already exists in file
    
    Args:
        filepath: Path to file
        line: Line to check
        
    Returns:
        True if line exists
    """
    if not filepath.exists():
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for existing_line in f:
            if existing_line.strip() == line:
                return True
    
    return False


def append_procedure(vehicle: str, procedure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append procedure to technical data file
    
    Args:
        vehicle: Vehicle identifier
        procedure: Procedure dict with module, command, response_rule, etc.
        
    Returns:
        Result dict with success status
    """
    try:
        filepath = get_knowledge_base_path(vehicle)
        appended_lines = []
        
        # Serialize each component
        lines_to_append = []
        
        if "module" in procedure:
            line = serialize_module(procedure["module"])
            if not check_duplicate(filepath, line):
                lines_to_append.append(line)
                appended_lines.append(line)
        
        if "command" in procedure:
            line = serialize_command(procedure["command"])
            if not check_duplicate(filepath, line):
                lines_to_append.append(line)
                appended_lines.append(line)
        
        if "dtc_rule" in procedure:
            line = serialize_dtc_rule(procedure["dtc_rule"])
            if not check_duplicate(filepath, line):
                lines_to_append.append(line)
                appended_lines.append(line)
        
        if "response_rule" in procedure:
            line = serialize_response_rule(procedure["response_rule"])
            if not check_duplicate(filepath, line):
                lines_to_append.append(line)
                appended_lines.append(line)
        
        if not lines_to_append:
            return {
                "success": True,
                "appended": [],
                "message": "All entries already exist in knowledge base"
            }
        
        # Append to file
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write("\n")
            for line in lines_to_append:
                f.write(line + "\n")
        
        return {
            "success": True,
            "appended": appended_lines,
            "filepath": str(filepath)
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": f"Validation error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Append diagnostic procedure to knowledge base"
    )
    parser.add_argument(
        "--vehicle",
        required=True,
        help="Vehicle identifier (e.g., Ford_Escape_2008)"
    )
    parser.add_argument(
        "--input",
        help="Input JSON file (if not provided, reads from stdin)"
    )
    
    args = parser.parse_args()
    
    # Read input JSON
    try:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                procedure = json.load(f)
        else:
            procedure = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        result = {
            "success": False,
            "error": f"Invalid JSON input: {str(e)}"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)
    except FileNotFoundError:
        result = {
            "success": False,
            "error": f"Input file not found: {args.input}"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)
    
    # Append procedure
    result = append_procedure(args.vehicle, procedure)
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
