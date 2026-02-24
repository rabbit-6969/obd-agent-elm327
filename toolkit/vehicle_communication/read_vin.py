#!/usr/bin/env python3
"""
VIN Reader Toolkit Script

Reads Vehicle Identification Number (VIN) from vehicle via OBD-II.
Returns JSON output for agent integration.

Usage:
    python read_vin.py --port COM3
    python read_vin.py --port /dev/ttyUSB0

Output Format:
    {"success": true, "vin": "1FAHP551XX8156549"}
    {"success": false, "error": "Failed to read VIN"}
"""

import argparse
import json
import sys
import logging
from typing import Optional
from elm327_base import ELM327Base, ELM327Error


# Suppress logging to stdout (only JSON output)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def parse_vin_response(response: str) -> Optional[str]:
    """
    Parse VIN from OBD-II response
    
    OBD-II response format for VIN (Service 09, PID 02):
    49 02 01 + data bytes (part 1)
    49 02 02 + data bytes (part 2)
    49 02 03 + data bytes (part 3)
    49 02 04 + data bytes (part 4)
    
    Args:
        response: Raw OBD-II response
        
    Returns:
        17-character VIN or None
    """
    try:
        # Remove spaces and convert to uppercase
        response = response.replace(" ", "").replace("\r", "").replace("\n", "").upper()
        
        # Extract VIN bytes (skip response header 49 02)
        if "4902" in response:
            # Find all occurrences of 4902 and extract data after them
            parts = response.split("4902")
            hex_data = ""
            for part in parts[1:]:  # Skip first empty part
                # Skip frame counter byte (01, 02, 03, 04)
                if len(part) >= 2:
                    hex_data += part[2:]  # Skip frame counter
        else:
            hex_data = response
        
        # Convert hex to ASCII characters
        vin_chars = []
        for i in range(0, len(hex_data), 2):
            if i + 1 < len(hex_data):
                hex_pair = hex_data[i:i+2]
                try:
                    char_code = int(hex_pair, 16)
                    if 32 <= char_code <= 126:  # Printable ASCII range
                        vin_chars.append(chr(char_code))
                except ValueError:
                    continue
        
        vin = ''.join(vin_chars)
        
        # VIN should be exactly 17 characters
        if len(vin) >= 17:
            vin = vin[:17]  # Take first 17 characters
            if validate_vin(vin):
                return vin
        
        return None
        
    except Exception as e:
        logger.error(f"Error parsing VIN response: {e}")
        return None


def validate_vin(vin: str) -> bool:
    """
    Validate VIN format
    
    Args:
        vin: VIN to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not vin or len(vin) != 17:
        return False
    
    if not vin.isalnum():
        return False
    
    # Check for invalid characters (I, O, Q not allowed in VIN)
    invalid_chars = ['I', 'O', 'Q']
    if any(char in vin for char in invalid_chars):
        return False
    
    return True


def read_vin(port: str) -> dict:
    """
    Read VIN from vehicle
    
    Args:
        port: Serial port for ELM327 adapter
        
    Returns:
        JSON-serializable dict with success status and VIN or error
    """
    try:
        with ELM327Base(port) as adapter:
            # Request VIN using OBD-II service 09, PID 02
            # Command format: 0902 (service 09, PID 02)
            response = adapter.send_obd_command("0902")
            
            if response:
                vin = parse_vin_response(response)
                if vin:
                    return {
                        "success": True,
                        "vin": vin
                    }
            
            return {
                "success": False,
                "error": "Failed to read VIN from vehicle"
            }
            
    except ELM327Error as e:
        return {
            "success": False,
            "error": f"ELM327 error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Read VIN from vehicle via OBD-II"
    )
    parser.add_argument(
        "--port",
        required=True,
        help="Serial port for ELM327 adapter (e.g., COM3, /dev/ttyUSB0)"
    )
    
    args = parser.parse_args()
    
    # Read VIN and output JSON
    result = read_vin(args.port)
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
