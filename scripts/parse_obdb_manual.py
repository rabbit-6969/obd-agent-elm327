#!/usr/bin/env python3
"""
OBDB Manual Signal Entry Tool
Interactive tool to manually enter OBDB signal details with validation.

Usage:
    python scripts/parse_obdb_manual.py [--output <output_file>]
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List


def get_input(prompt: str, default: str = None, required: bool = True) -> str:
    """Get user input with optional default"""
    if default:
        prompt = f"{prompt} [{default}]"
    prompt += ": "
    
    while True:
        value = input(prompt).strip()
        if not value and default:
            return default
        if value or not required:
            return value
        print("This field is required. Please enter a value.")


def get_int_input(prompt: str, default: int = None) -> int:
    """Get integer input"""
    while True:
        value = get_input(prompt, str(default) if default else None, default is not None)
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid integer.")


def parse_command(command: str) -> tuple:
    """Parse UDS command into service and DID"""
    command = command.replace(" ", "").upper()
    if len(command) >= 6:
        service = command[:2]
        did = command[2:6]
        return service, did
    return "22", "0000"


def generate_extraction_formula(bit_start: int, bit_length: int) -> tuple:
    """Generate extraction formula and method"""
    if bit_length == 1:
        formula = f"(response_data[0] >> {bit_start}) & 0x01"
        method = "single_bit"
    elif bit_length <= 8:
        mask = (1 << bit_length) - 1
        formula = f"(response_data[0] >> {bit_start}) & 0x{mask:02X}"
        method = "multi_bit"
    else:
        formula = "Multi-byte extraction required - see documentation"
        method = "byte_spanning"
    return formula, method


def generate_python_code(pid: str, bit_start: int, bit_length: int) -> str:
    """Generate Python extraction code"""
    var_name = pid.lower()
    code = f"# Extract {pid}\n"
    code += f"data_byte = response[3]  # Skip 62 XX XX header\n"
    
    if bit_length == 1:
        code += f"{var_name} = (data_byte >> {bit_start}) & 0x01\n"
        code += f"# Result: 0 = off, 1 = on"
    elif bit_length <= 8:
        mask = (1 << bit_length) - 1
        code += f"{var_name} = (data_byte >> {bit_start}) & 0x{mask:02X}\n"
        code += f"# Result: 0 to {mask}"
    else:
        code += f"# Multi-byte extraction\n"
        code += f"high_byte = response[3]\n"
        code += f"low_byte = response[4]\n"
        code += f"{var_name} = (high_byte << 8) | low_byte\n"
        code += f"# Result: 0 to 65535"
        
    return code


def enter_signal() -> Dict[str, Any]:
    """Interactive signal entry"""
    print("\n" + "="*60)
    print("Enter OBDB Signal Details")
    print("="*60)
    
    signal = {}
    
    # Basic info
    signal['pid'] = get_input("PID (e.g., ESCAPE_TPMS_WARN)")
    signal['name'] = get_input("Name (e.g., Tire pressure warning)")
    signal['description'] = get_input("Description", signal['name'], required=False)
    
    # Status
    print("\nStatus options: Production, Debugging, Experimental")
    signal['status'] = get_input("Status", "Production")
    
    # Command details
    print("\nCommand Details:")
    signal['ecu_address'] = get_input("ECU Address (e.g., 720)")
    command = get_input("Command (e.g., 2261A5)")
    service, did = parse_command(command)
    
    # Signal properties
    print("\nSignal Properties:")
    print("Signal type options: boolean, uint8, uint16, int8, int16, float, etc.")
    signal['signal_type'] = get_input("Signal Type", "boolean")
    signal['bit_start'] = get_int_input("Bit Position (start)", 0)
    signal['bit_length'] = get_int_input("Bit Length", 1)
    
    # Unit and scaling
    signal['unit'] = get_input("Unit (e.g., psi, celsius, rpm)", "", required=False)
    signal['scaling'] = get_input("Scaling formula (e.g., -40, 0.25)", "", required=False)
    
    # Optional fields
    signal['suggested_metric'] = get_input("Suggested Metric", "", required=False)
    
    # Generate extraction details
    formula, method = generate_extraction_formula(signal['bit_start'], signal['bit_length'])
    python_code = generate_python_code(signal['pid'], signal['bit_start'], signal['bit_length'])
    
    # Build complete entry
    entry = {
        'pid': signal['pid'],
        'name': signal['name'],
        'description': signal['description'] or signal['name'],
        'status': signal['status'],
        'command': {
            'service': f"0x{service}",
            'did': f"0x{did}",
            'full_command': f"{service} {did[:2]} {did[2:]}",
            'ecu_address': signal['ecu_address']
        },
        'response': {
            'format': f"{int(service, 16) + 0x40:02X} {did[:2]} {did[2:]} [DATA...]",
            'data_length': 'Variable'
        },
        'signal_properties': {
            'signal_type': signal['signal_type'],
            'bit_position': signal['bit_start'],
            'bit_length': signal['bit_length'],
            'byte_index': 0,
            'unit': signal['unit']
        },
        'extraction': {
            'method': method,
            'formula': formula,
            'python_code': python_code
        }
    }
    
    if signal['scaling']:
        entry['scaling'] = {
            'formula': signal['scaling'],
            'unit': signal['unit']
        }
        
    if signal['suggested_metric']:
        entry['suggested_metric'] = signal['suggested_metric']
        
    # Show summary
    print("\n" + "-"*60)
    print("Signal Summary:")
    print(f"  PID: {signal['pid']}")
    print(f"  ECU: 0x{signal['ecu_address']}")
    print(f"  Command: {service} {did[:2]} {did[2:]}")
    print(f"  Bit {signal['bit_start']}, Length {signal['bit_length']}")
    print(f"  Extraction: {formula}")
    print("-"*60)
    
    return entry


def main():
    """Main entry point"""
    output_file = None
    if '--output' in sys.argv:
        output_idx = sys.argv.index('--output')
        if output_idx + 1 < len(sys.argv):
            output_file = sys.argv[output_idx + 1]
            
    signals = []
    
    print("OBDB Manual Signal Entry Tool")
    print("Enter signal details from OBDB community database")
    print("Press Ctrl+C to finish\n")
    
    try:
        while True:
            signal = enter_signal()
            signals.append(signal)
            
            another = input("\nAdd another signal? (y/n): ").strip().lower()
            if another != 'y':
                break
                
    except KeyboardInterrupt:
        print("\n\nEntry cancelled.")
        if not signals:
            sys.exit(0)
            
    # Generate output
    output = {
        'obdb_extracted_parameters': {
            'description': 'Parameters extracted from OBDB community database',
            'extraction_date': '2026-02-15',
            'source': 'https://obdb.community',
            'note': 'Manually entered signal details',
            'parameters': signals
        }
    }
    
    yaml_output = yaml.dump(output, default_flow_style=False, sort_keys=False, width=120)
    
    # Write output
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_output)
        print(f"\nYAML output written to: {output_file}")
    else:
        print("\n" + "="*60)
        print("YAML OUTPUT:")
        print("="*60)
        print(yaml_output)
        
    print(f"\nTotal signals entered: {len(signals)}")


if __name__ == '__main__':
    main()
