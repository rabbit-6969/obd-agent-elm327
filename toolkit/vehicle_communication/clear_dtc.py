#!/usr/bin/env python3
"""
Clear DTC Toolkit Script

Clears diagnostic trouble codes from vehicle modules via OBD-II.
Returns JSON output for agent consumption.

Usage:
    python clear_dtc.py --port COM3 --module HVAC --address 7A0
    python clear_dtc.py --port COM3 --module PCM
"""

import argparse
import json
import sys
from typing import Dict
from elm327_base import ELM327Base, ELM327Error


def clear_dtc(port: str, module: str = None, address: str = None) -> Dict:
    """
    Clear DTCs from vehicle module
    
    Args:
        port: Serial port (e.g., COM3)
        module: Module name (e.g., HVAC, PCM)
        address: CAN address in hex (e.g., 7A0)
        
    Returns:
        Dictionary with success status
    """
    result = {
        'success': False,
        'module': module,
        'address': address,
        'cleared': False,
        'error': None
    }
    
    try:
        with ELM327Base(port) as adapter:
            # Set CAN header if address provided
            if address:
                if not adapter.set_header(address):
                    result['error'] = f"Failed to set CAN header to {address}"
                    return result
            
            # Send Mode 04 command (Clear DTCs)
            response = adapter.send_obd_command("04")
            
            if not response:
                result['error'] = "No response from vehicle"
                return result
            
            # Check for success response (44 = Mode 04 response)
            if '44' in response.upper():
                result['success'] = True
                result['cleared'] = True
            else:
                result['error'] = f"Unexpected response: {response}"
            
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
        description='Clear diagnostic trouble codes from vehicle module',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clear DTCs from HVAC module
  python clear_dtc.py --port COM3 --module HVAC --address 7A0
  
  # Clear DTCs from PCM (standard OBD-II)
  python clear_dtc.py --port COM3 --module PCM
  
  # Clear DTCs without specifying module
  python clear_dtc.py --port COM3

WARNING: Clearing DTCs will reset emissions monitors and may cause
vehicle to fail emissions testing until monitors complete.
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
    
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt (use with caution)'
    )
    
    args = parser.parse_args()
    
    # Confirmation prompt (unless --confirm flag)
    if not args.confirm and not args.json:
        print("⚠ WARNING: Clearing DTCs will reset emissions monitors!")
        print("This may cause your vehicle to fail emissions testing.")
        response = input("\nAre you sure you want to clear DTCs? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Operation cancelled")
            sys.exit(0)
    
    # Clear DTCs
    result = clear_dtc(args.port, args.module, args.address)
    
    # Output results
    if args.json:
        # JSON output only
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        if result['success']:
            print(f"✓ Successfully cleared DTCs from {result['module'] or 'vehicle'}")
            print("\nNote: Emissions monitors have been reset.")
            print("Drive vehicle normally to allow monitors to complete.")
            
            # Also output JSON for agent
            print(f"\nJSON Output:")
            print(json.dumps(result, indent=2))
        else:
            print(f"✗ Failed to clear DTCs: {result['error']}", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
