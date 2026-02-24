#!/usr/bin/env python3
"""
Convert OBDB batch template to full UDS command documentation.

Usage:
    python scripts/convert_batch_template.py <template_file> [--output <output_file>]
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any


def parse_command(command: str) -> tuple:
    """Parse UDS command into service and DID"""
    command = command.replace(" ", "").upper()
    if len(command) >= 6:
        service = command[:2]
        did = command[2:6]
    else:
        service = "22"
        did = "0000"
    return service, did


def determine_data_type(signal_type: str, bit_length: int) -> str:
    """Determine data type from signal type and bit length"""
    signal_type = signal_type.lower()
    
    if 'bool' in signal_type or bit_length == 1:
        return 'boolean'
    elif 'int8' in signal_type or (bit_length == 8 and 'int' in signal_type):
        return 'int8'
    elif 'uint8' in signal_type or bit_length == 8:
        return 'uint8'
    elif 'int16' in signal_type or (bit_length == 16 and 'int' in signal_type):
        return 'int16'
    elif 'uint16' in signal_type or bit_length == 16:
        return 'uint16'
    elif 'float' in signal_type:
        return 'float'
    else:
        return 'unknown'


def generate_extraction_formula(bit_start: int, bit_length: int) -> tuple:
    """Generate extraction formula and method"""
    if bit_length == 1:
        formula = f"(response_data[0] >> {bit_start}) & 0x01"
        method = "single_bit"
    elif bit_length <= 8:
        mask = (1 << bit_length) - 1
        formula = f"(response_data[0] >> {bit_start}) & 0x{mask:02X}"
        method = "multi_bit"
    elif bit_length == 16:
        formula = "(response_data[0] << 8) | response_data[1]"
        method = "byte_spanning"
    else:
        formula = "Multi-byte extraction - see documentation"
        method = "byte_spanning"
    return formula, method


def generate_python_code(pid: str, bit_start: int, bit_length: int, scaling: str) -> str:
    """Generate Python extraction code"""
    var_name = pid.lower()
    code = f"# Extract {pid}\n"
    
    if bit_length == 1:
        code += f"data_byte = response[3]  # Skip 62 XX XX header\n"
        code += f"{var_name} = (data_byte >> {bit_start}) & 0x01\n"
        code += f"# Result: 0 = off, 1 = on"
    elif bit_length <= 8:
        mask = (1 << bit_length) - 1
        code += f"data_byte = response[3]  # Skip 62 XX XX header\n"
        code += f"raw_value = (data_byte >> {bit_start}) & 0x{mask:02X}\n"
        if scaling:
            code += f"# Apply scaling: {scaling}\n"
            if scaling.startswith('-') or scaling.startswith('+'):
                code += f"{var_name} = raw_value {scaling}\n"
            elif '*' in scaling or '/' in scaling:
                code += f"{var_name} = raw_value {scaling}\n"
            elif '(' in scaling:
                code += f"{var_name} = {scaling.replace('x', 'raw_value')}\n"
            else:
                code += f"{var_name} = raw_value * {scaling}\n"
        else:
            code += f"{var_name} = raw_value\n"
    elif bit_length == 16:
        code += f"high_byte = response[3]  # Skip 62 XX XX header\n"
        code += f"low_byte = response[4]\n"
        code += f"raw_value = (high_byte << 8) | low_byte\n"
        if scaling:
            code += f"# Apply scaling: {scaling}\n"
            if scaling.startswith('-') or scaling.startswith('+'):
                code += f"{var_name} = raw_value {scaling}\n"
            elif '*' in scaling or '/' in scaling:
                code += f"{var_name} = raw_value {scaling}\n"
            elif '(' in scaling:
                code += f"{var_name} = {scaling.replace('x', 'raw_value')}\n"
            else:
                code += f"{var_name} = raw_value * {scaling}\n"
        else:
            code += f"{var_name} = raw_value\n"
    else:
        code += f"# Multi-byte extraction required\n"
        code += f"# See documentation for details\n"
        
    return code


def convert_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Convert template signal to full format"""
    
    service, did = parse_command(signal['command'])
    data_type = determine_data_type(signal['signal_type'], signal['bit_length'])
    formula, method = generate_extraction_formula(signal['bit_start'], signal['bit_length'])
    python_code = generate_python_code(
        signal['pid'], 
        signal['bit_start'], 
        signal['bit_length'],
        signal.get('scaling', '')
    )
    
    entry = {
        'pid': signal['pid'],
        'name': signal['name'],
        'description': signal.get('description', signal['name']),
        'status': signal['status'],
        'command': {
            'service': f"0x{service}",
            'did': f"0x{did}",
            'full_command': f"{service} {did[:2]} {did[2:]}",
            'ecu_address': signal['ecu']
        },
        'response': {
            'format': f"{int(service, 16) + 0x40:02X} {did[:2]} {did[2:]} [DATA...]",
            'data_length': 'Variable'
        },
        'signal_properties': {
            'signal_type': signal['signal_type'],
            'data_type': data_type,
            'bit_position': signal['bit_start'],
            'bit_length': signal['bit_length'],
            'byte_index': 0,
            'unit': signal.get('unit', '')
        },
        'extraction': {
            'method': method,
            'formula': formula,
            'python_code': python_code
        }
    }
    
    if signal.get('scaling'):
        entry['scaling'] = {
            'formula': signal['scaling'],
            'unit': signal.get('unit', '')
        }
        
    if signal.get('suggested_metric'):
        entry['suggested_metric'] = signal['suggested_metric']
        
    return entry


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python convert_batch_template.py <template_file> [--output <output_file>]")
        sys.exit(1)
        
    template_file = sys.argv[1]
    
    output_file = None
    if '--output' in sys.argv:
        output_idx = sys.argv.index('--output')
        if output_idx + 1 < len(sys.argv):
            output_file = sys.argv[output_idx + 1]
            
    if not Path(template_file).exists():
        print(f"Error: Template file '{template_file}' not found")
        sys.exit(1)
        
    # Load template
    with open(template_file, 'r', encoding='utf-8') as f:
        template = yaml.safe_load(f)
        
    if 'signals' not in template:
        print("Error: Template file must contain 'signals' key")
        sys.exit(1)
        
    # Convert signals
    converted_signals = []
    for signal in template['signals']:
        try:
            converted = convert_signal(signal)
            converted_signals.append(converted)
        except Exception as e:
            print(f"Warning: Failed to convert signal {signal.get('pid', 'unknown')}: {e}")
            
    # Generate output
    output = {
        'obdb_extracted_parameters': {
            'description': 'Parameters extracted from OBDB community database',
            'extraction_date': '2026-02-15',
            'source': 'https://obdb.community',
            'note': 'Converted from batch template',
            'parameters': converted_signals
        }
    }
    
    yaml_output = yaml.dump(output, default_flow_style=False, sort_keys=False, width=120)
    
    # Write output
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_output)
        print(f"Converted {len(converted_signals)} signals")
        print(f"Output written to: {output_file}")
    else:
        print(yaml_output)
        print(f"\nConverted {len(converted_signals)} signals")
        
    # Print summary
    ecu_groups = {}
    for signal in converted_signals:
        ecu = signal['command']['ecu_address']
        if ecu not in ecu_groups:
            ecu_groups[ecu] = []
        ecu_groups[ecu].append(signal['pid'])
        
    print("\nSignals by ECU:")
    for ecu, pids in sorted(ecu_groups.items()):
        print(f"  0x{ecu}: {len(pids)} signals")


if __name__ == '__main__':
    main()
