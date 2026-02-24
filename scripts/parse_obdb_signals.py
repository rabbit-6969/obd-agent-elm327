#!/usr/bin/env python3
"""
OBDB Signal Parser
Extracts UDS command details from OBDB signal data and generates knowledge base entries.

Usage:
    python scripts/parse_obdb_signals.py <input_file> [--output <output_file>]
    
Input format: Text file with OBDB signal details (copy/paste from OBDB website)
Output: YAML formatted UDS command documentation
"""

import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any


class OBDBSignalParser:
    """Parse OBDB signal details into structured format"""
    
    def __init__(self):
        self.signals = []
        
    def parse_signal_block(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single signal block from OBDB text
        
        Expected format:
        ECU Parameter ID Name Status Years Suggested Metric
        720 ESCAPE_TPMS_WARN Tire pressure warning Debugging -- --
        Signal Details...
        Command Invocation ECU:720 Command:2261A5
        Bit Position:2 to 2 Bit Length:1
        """
        signal = {}
        
        # Extract PID name (ESCAPE_XXX pattern)
        pid_match = re.search(r'(ESCAPE_[A-Z0-9_]+)', text)
        if pid_match:
            signal['pid'] = pid_match.group(1)
        else:
            return None
            
        # Extract human-readable name
        # Look for pattern: PID_NAME followed by description
        name_match = re.search(r'ESCAPE_[A-Z0-9_]+\s+([^—\n]+?)(?:Debugging|Production|—)', text)
        if name_match:
            signal['name'] = name_match.group(1).strip()
            
        # Extract status
        status_match = re.search(r'(Debugging|Production|Experimental)', text)
        if status_match:
            signal['status'] = status_match.group(1)
        else:
            signal['status'] = 'Unknown'
            
        # Extract ECU address
        ecu_match = re.search(r'ECU:\s*([0-9A-Fa-f]+)', text)
        if ecu_match:
            signal['ecu_address'] = ecu_match.group(1).upper()
            
        # Extract command
        cmd_match = re.search(r'Command:\s*([0-9A-Fa-f]+)', text)
        if cmd_match:
            signal['command'] = cmd_match.group(1).upper()
            
        # Extract bit position
        bit_pos_match = re.search(r'Bit Position:\s*(\d+)\s+to\s+(\d+)', text)
        if bit_pos_match:
            signal['bit_start'] = int(bit_pos_match.group(1))
            signal['bit_end'] = int(bit_pos_match.group(2))
            
        # Extract bit length
        bit_len_match = re.search(r'Bit Length:\s*(\d+)', text)
        if bit_len_match:
            signal['bit_length'] = int(bit_len_match.group(1))
            
        # Extract signal type
        type_match = re.search(r'Signal Type:\s*([^\n]+)', text)
        if type_match:
            signal['signal_type'] = type_match.group(1).strip()
            
        # Extract unit
        unit_match = re.search(r'Unit:\s*([^\n]+)', text)
        if unit_match:
            signal['unit'] = unit_match.group(1).strip()
            
        # Extract scaling if present
        scaling_match = re.search(r'Scaling:\s*([^\n]+)', text)
        if scaling_match and scaling_match.group(1).strip():
            signal['scaling'] = scaling_match.group(1).strip()
            
        # Extract suggested metric
        metric_match = re.search(r'Suggested Metric[:\s]+([a-zA-Z]+)', text)
        if metric_match:
            signal['suggested_metric'] = metric_match.group(1)
            
        return signal if signal.get('pid') else None
        
    def parse_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Parse entire file containing multiple signal blocks"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split by signal blocks (look for PID patterns)
        blocks = re.split(r'(?=\d+ESCAPE_[A-Z0-9_]+)', content)
        
        for block in blocks:
            if not block.strip():
                continue
                
            signal = self.parse_signal_block(block)
            if signal:
                self.signals.append(signal)
                
        return self.signals
        
    def generate_yaml_entry(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate YAML-formatted entry for a signal"""
        
        # Parse command into service and DID
        cmd = signal.get('command', '')
        if len(cmd) >= 6:
            service = cmd[:2]
            did = cmd[2:6]
        else:
            service = '22'  # Default to ReadDataByIdentifier
            did = '0000'
            
        # Determine data type from signal type and bit length
        signal_type = signal.get('signal_type', '').lower()
        bit_length = signal.get('bit_length', 1)
        
        if 'on' in signal_type or 'off' in signal_type or bit_length == 1:
            data_type = 'boolean'
        elif bit_length <= 8:
            data_type = 'uint8'
        elif bit_length <= 16:
            data_type = 'uint16'
        elif bit_length <= 32:
            data_type = 'uint32'
        else:
            data_type = 'unknown'
            
        # Generate extraction formula
        bit_start = signal.get('bit_start', 0)
        bit_len = signal.get('bit_length', 1)
        
        if bit_len == 1:
            formula = f"(response_data[0] >> {bit_start}) & 0x01"
            method = "single_bit"
        elif bit_len <= 8:
            mask = (1 << bit_len) - 1
            formula = f"(response_data[0] >> {bit_start}) & 0x{mask:02X}"
            method = "multi_bit"
        else:
            formula = "Multi-byte extraction required"
            method = "byte_spanning"
            
        entry = {
            'pid': signal['pid'],
            'name': signal.get('name', 'Unknown'),
            'description': signal.get('name', 'Unknown'),
            'status': signal.get('status', 'Unknown'),
            'command': {
                'service': f"0x{service}",
                'did': f"0x{did}",
                'full_command': f"{service} {did[:2]} {did[2:]}",
                'ecu_address': signal.get('ecu_address', 'Unknown')
            },
            'response': {
                'format': f"{int(service, 16) + 0x40:02X} {did[:2]} {did[2:]} [DATA...]",
                'data_length': 'Variable'
            },
            'signal_properties': {
                'signal_type': signal.get('signal_type', 'unknown'),
                'data_type': data_type,
                'bit_position': bit_start,
                'bit_length': bit_len,
                'byte_index': 0,
                'unit': signal.get('unit', '')
            },
            'extraction': {
                'method': method,
                'formula': formula,
                'python_code': self._generate_python_code(signal)
            }
        }
        
        # Add scaling if present
        if signal.get('scaling'):
            entry['scaling'] = {
                'formula': signal['scaling'],
                'unit': signal.get('unit', '')
            }
            
        # Add suggested metric if present
        if signal.get('suggested_metric'):
            entry['suggested_metric'] = signal['suggested_metric']
            
        return entry
        
    def _generate_python_code(self, signal: Dict[str, Any]) -> str:
        """Generate Python extraction code"""
        pid = signal['pid']
        bit_start = signal.get('bit_start', 0)
        bit_len = signal.get('bit_length', 1)
        
        code = f"# Extract {pid}\n"
        code += f"data_byte = response[3]  # Skip header bytes\n"
        
        if bit_len == 1:
            code += f"{pid.lower()} = (data_byte >> {bit_start}) & 0x01\n"
            code += f"# Result: 0 or 1"
        else:
            mask = (1 << bit_len) - 1
            code += f"{pid.lower()} = (data_byte >> {bit_start}) & 0x{mask:02X}\n"
            code += f"# Result: 0 to {mask}"
            
        return code
        
    def generate_yaml_output(self) -> str:
        """Generate complete YAML output for all signals"""
        output = {
            'obdb_extracted_parameters': {
                'description': 'Parameters extracted from OBDB community database',
                'extraction_date': '2026-02-15',
                'source': 'https://obdb.community',
                'parameters': []
            }
        }
        
        for signal in self.signals:
            entry = self.generate_yaml_entry(signal)
            output['obdb_extracted_parameters']['parameters'].append(entry)
            
        return yaml.dump(output, default_flow_style=False, sort_keys=False, width=120)
        
    def generate_summary(self) -> str:
        """Generate summary statistics"""
        summary = f"\n=== OBDB Signal Extraction Summary ===\n"
        summary += f"Total signals parsed: {len(self.signals)}\n\n"
        
        # Group by ECU
        ecu_groups = {}
        for signal in self.signals:
            ecu = signal.get('ecu_address', 'Unknown')
            if ecu not in ecu_groups:
                ecu_groups[ecu] = []
            ecu_groups[ecu].append(signal['pid'])
            
        summary += "Signals by ECU:\n"
        for ecu, pids in sorted(ecu_groups.items()):
            summary += f"  {ecu}: {len(pids)} signals\n"
            
        # Group by status
        status_groups = {}
        for signal in self.signals:
            status = signal.get('status', 'Unknown')
            if status not in status_groups:
                status_groups[status] = 0
            status_groups[status] += 1
            
        summary += "\nSignals by status:\n"
        for status, count in sorted(status_groups.items()):
            summary += f"  {status}: {count} signals\n"
            
        return summary


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python parse_obdb_signals.py <input_file> [--output <output_file>]")
        print("\nInput file should contain OBDB signal details (copy/paste from website)")
        print("Output will be YAML formatted UDS command documentation")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    # Parse output file argument
    output_file = None
    if '--output' in sys.argv:
        output_idx = sys.argv.index('--output')
        if output_idx + 1 < len(sys.argv):
            output_file = sys.argv[output_idx + 1]
            
    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
        
    # Parse signals
    parser = OBDBSignalParser()
    print(f"Parsing signals from {input_file}...")
    signals = parser.parse_file(input_file)
    
    if not signals:
        print("Warning: No signals found in input file")
        print("Make sure the file contains OBDB signal details in the expected format")
        sys.exit(1)
        
    # Generate output
    yaml_output = parser.generate_yaml_output()
    summary = parser.generate_summary()
    
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
        
    # Print summary
    print(summary)
    
    # Print example usage
    print("\n=== Example Usage ===")
    if signals:
        example = signals[0]
        print(f"\nTo read {example['pid']}:")
        print(f"  ECU Address: 0x{example.get('ecu_address', 'XXX')}")
        print(f"  Command: {example.get('command', 'XX XX XX')}")
        print(f"  Bit Position: {example.get('bit_start', 0)}")
        print(f"  Bit Length: {example.get('bit_length', 1)}")


if __name__ == '__main__':
    main()
