#!/usr/bin/env python3
"""
Read DTC Toolkit Script

Reads diagnostic trouble codes from vehicle modules via OBD-II.
Returns JSON output for agent consumption.

Usage:
    python read_dtc.py --port COM3 --module HVAC --address 7A0
    python read_dtc.py --port COM3 --module PCM
"""

import argparse
import json
import sys
from typing import List, Dict
from elm327_base import ELM327Base, ELM327Error


def parse_dtc_response(response: str) -> List[Dict[str, str]]:
    """
    Parse DTC response from Mode 03
    
    Args:
        response: Raw response from vehicle
        
    Returns:
        List of DTC dictionaries with code and raw hex
    """
    dtcs = []
    
    try:
        # Remove spaces and normalize
        data = response.replace(' ', '').replace('\r', '').replace('\n', '').upper()
        
        # Convert to bytes
        bytes_list = []
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                try:
                    bytes_list.append(int(data[i:i+2], 16))
                except ValueError:
                    continue
        
        if not bytes_list:
            return []
        
        # Skip response code (43) if present
        if bytes_list[0] == 0x43:
            data_bytes = bytes_list[1:]
        else:
            data_bytes = bytes_list
        
        # Parse DTC pairs
        for i in range(0, len(data_bytes), 2):
            if i + 1 >= len(data_bytes):
                break
            
            A = data_bytes[i]
            B = data_bytes[i + 1]
            
            # Skip empty DTCs
            if A == 0 and B == 0:
                continue
            
            # Decode DTC
            letter_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
            letter = letter_map.get((A & 0xC0) >> 6, '?')
            code_num = ((A & 0x3F) << 8) | B
            dtc_code = f"{letter}{code_num:04X}"
            
            dtcs.append({
                'code': dtc_code,
                'raw': f"{A:02X}{B:02X}"
            })
    
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': f"Error parsing DTC response: {e}"
        }), file=sys.stderr)
    
    return dtcs


def read_dtc(port: str, module: str = None, address: str = None) -> Dict:
    """
    Read DTCs from vehicle module
    
    Args:
        port: Serial port (e.g., COM3)
        module: Module name (e.g., HVAC, PCM)
        address: CAN address in hex (e.g., 7A0)
        
    Returns:
        Dictionary with success status and DTCs
    """
    result = {
        'success': False,
        'module': module,
        'address': address,
        'dtcs': [],
        'error': None
    }
    
    try:
        with ELM327Base(port) as adapter:
            # Set CAN header if address provided
            if address:
                if not adapter.set_header(address):
                    result['error'] = f"Failed to set CAN header to {address}"
                    return result
            
            # Send Mode 03 command (Read DTCs)
            response = adapter.send_obd_command("03")
            
            if not response:
                result['error'] = "No response from vehicle"
                return result
            
            # Parse DTCs
            dtcs = parse_dtc_response(response)
            
            result['success'] = True
            result['dtcs'] = dtcs
            result['count'] = len(dtcs)
            
            return result
    
    except ELM327Error as e:
        result['error'] = str(e)
        return result
    except Exception as e:
        result['error'] = f"Unexpected error: {e}"
        return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Read diagnostic trouble codes from vehicle module',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Read DTCs from HVAC module
  python read_dtc.py --port COM3 --module HVAC --address 7A0
  
  # Read DTCs from PCM (standard OBD-II)
  python read_dtc.py --port COM3 --module PCM
  
  # Read DTCs without specifying module
  python read_dtc.py --port COM3
        """
    )
    
    parser.add_argument(
        '--port',
        required=True,
        help='Serial port (e.g., COM3, /dev/ttyUSB0)'
    )
    
    parser.add_argument(
        '--module',
        help='Module name (e.g., HVAC, ABS, PCM)'
    )
    
    parser.add_argument(
        '--address',
        help='CAN address in hex (e.g., 7A0 for HVAC)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON only (no human-readable text)'
    )
    
    args = parser.parse_args()
    
    # Read DTCs
    result = read_dtc(args.port, args.module, args.address)
    
    # Output results
    if args.json:
        # JSON output only
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        if result['success']:
            print(f"✓ Successfully read DTCs from {result['module'] or 'vehicle'}")
            if result['dtcs']:
                print(f"\nFound {result['count']} DTC(s):")
                for dtc in result['dtcs']:
                    print(f"  - {dtc['code']} (Raw: {dtc['raw']})")
            else:
                print("\nNo DTCs found")
            
            # Also output JSON for agent
            print(f"\nJSON Output:")
            print(json.dumps(result, indent=2))
        else:
            print(f"✗ Failed to read DTCs: {result['error']}", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
