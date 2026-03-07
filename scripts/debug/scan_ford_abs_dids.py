#!/usr/bin/env python3
"""
Comprehensive Ford Escape 2008 ABS Module DID Scanner

Scans for:
1. Identification DIDs (VIN, serial number, part number, hardware/software versions)
2. Operational DIDs (wheel speeds, brake pressure, sensor data)
3. Status DIDs (system state, fault flags)

Based on ISO 14229-1 (UDS) standard and Ford-specific DIDs
"""

import serial
import time
import sys
import json
from datetime import datetime

class SimpleELM327:
    """Simplified ELM327 adapter for UDS communication"""
    
    def __init__(self, port='COM3', baudrate=38400, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
    
    def connect(self):
        """Connect to ELM327 adapter"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)
            
            # Reset and configure
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")
            self.send_command("ATSP0")
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def send_command(self, command):
        """Send command and get response"""
        if not self.ser:
            return None
        
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            self.ser.write((command + '\r').encode())
            
            response = b''
            start_time = time.time()
            
            while time.time() - start_time < self.timeout:
                if self.ser.in_waiting:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response += chunk
                    
                    if b'>' in response:
                        break
                
                time.sleep(0.05)
            
            response_str = response.decode('ascii', errors='ignore')
            response_str = response_str.replace('\r', '').replace('\n', ' ')
            response_str = response_str.replace('>', '').strip()
            
            return response_str
        
        except Exception as e:
            return None
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def parse_did_response(response, did):
    """Parse DID response and extract data"""
    if not response:
        return None, "NO_RESPONSE"
    
    # Check for negative response (7F)
    if '7F 22' in response:
        parts = response.split()
        if len(parts) >= 3:
            nrc = parts[2]
            nrc_meanings = {
                '11': 'Service Not Supported',
                '12': 'Sub-Function Not Supported',
                '13': 'Incorrect Message Length',
                '22': 'Conditions Not Correct',
                '31': 'Request Out Of Range',
                '33': 'Security Access Denied',
                '78': 'Response Pending'
            }
            return None, f"NEGATIVE_RESPONSE_{nrc}_{nrc_meanings.get(nrc, 'Unknown')}"
    
    # Check for positive response (62)
    if f'62 {did}' in response:
        # Extract data after the DID
        data = response.replace(f'62 {did}', '').strip()
        return data, "SUCCESS"
    
    return None, "INVALID_RESPONSE"

def hex_to_ascii(hex_str):
    """Convert hex string to ASCII (for VIN, part numbers, etc.)"""
    try:
        hex_str = hex_str.replace(' ', '')
        return bytes.fromhex(hex_str).decode('ascii', errors='ignore')
    except:
        return None

def hex_to_int(hex_str):
    """Convert hex string to integer"""
    try:
        return int(hex_str.replace(' ', ''), 16)
    except:
        return None

# Standard UDS Identification DIDs (ISO 14229-1)
STANDARD_IDENTIFICATION_DIDS = {
    'F180': 'Boot Software Identification',
    'F181': 'Application Software Identification',
    'F182': 'Application Data Identification',
    'F183': 'Boot Software Fingerprint',
    'F184': 'Application Software Fingerprint',
    'F185': 'Application Data Fingerprint',
    'F186': 'Active Diagnostic Session',
    'F187': 'Vehicle Manufacturer Spare Part Number',
    'F188': 'Vehicle Manufacturer ECU Software Number',
    'F189': 'Vehicle Manufacturer ECU Software Version Number',
    'F18A': 'System Supplier Identifier',
    'F18B': 'ECU Manufacturing Date and Time',
    'F18C': 'System Supplier ECU Hardware Number',
    'F18D': 'System Supplier ECU Hardware Version Number',
    'F18E': 'System Supplier ECU Software Number',
    'F18F': 'System Supplier ECU Software Version Number',
    'F190': 'Vehicle Identification Number (VIN)',
    'F191': 'Vehicle Manufacturer ECU Hardware Number',
    'F192': 'System Supplier ECU Hardware Version Number',
    'F193': 'System Supplier ECU Software Version Number',
    'F194': 'System Supplier ECU Software Version Number',
    'F195': 'System Name or Engine Type',
    'F196': 'Repair Shop Code or Tester Serial Number',
    'F197': 'Programming Date',
    'F198': 'Calibration Identification',
    'F199': 'Calibration Verification Number',
    'F19A': 'Diagnostic Specification Version',
    'F19B': 'Manufacturer Specific',
    'F19C': 'Manufacturer Specific',
    'F19D': 'ECU Serial Number',
    'F19E': 'Vehicle Manufacturer Kit Assembly Part Number',
    'F19F': 'VIN (Original)',
}

# Ford-specific ABS DIDs (based on common Ford implementations)
FORD_ABS_DIDS = {
    # Wheel Speed Sensors (likely range)
    '0200': 'Unknown Parameter 1 (confirmed working)',
    '0201': 'Possible Wheel Speed FL',
    '0202': 'Unknown Parameter 2 (confirmed working)',
    '0203': 'Possible Wheel Speed FR',
    '0204': 'Possible Wheel Speed RL',
    '0205': 'Possible Wheel Speed RR',
    '0206': 'Possible Wheel Speed Average',
    '0207': 'Possible Vehicle Speed',
    
    # Brake System Parameters
    '0210': 'Possible Brake Pressure FL',
    '0211': 'Possible Brake Pressure FR',
    '0212': 'Possible Brake Pressure RL',
    '0213': 'Possible Brake Pressure RR',
    '0214': 'Possible Master Cylinder Pressure',
    '0215': 'Possible Brake Pedal Position',
    
    # ABS System Status
    '0220': 'Possible ABS System Status',
    '0221': 'Possible Traction Control Status',
    '0222': 'Possible Stability Control Status',
    '0223': 'Possible Pump Motor Status',
    '0224': 'Possible Valve Status',
    
    # Sensor Data
    '0230': 'Possible Lateral Acceleration',
    '0231': 'Possible Yaw Rate',
    '0232': 'Possible Steering Angle',
    '0233': 'Possible Brake Light Switch',
    
    # Module Information (Ford-specific range)
    '0100': 'Possible Module ID',
    '0101': 'Possible Hardware Version',
    '0102': 'Possible Software Version',
    '0103': 'Possible Calibration ID',
    '0104': 'Possible Serial Number',
    '0105': 'Possible Manufacturing Date',
}

def scan_abs_module(port='COM3', quick_scan=False):
    """
    Scan Ford Escape ABS module for all available DIDs
    
    Args:
        port: Serial port for ELM327
        quick_scan: If True, only scan known working DIDs
    """
    
    print("=" * 80)
    print("Ford Escape 2008 - ABS Module DID Scanner")
    print("=" * 80)
    print()
    print("This script will scan the ABS module for:")
    print("  1. Identification DIDs (VIN, serial number, part number, etc.)")
    print("  2. Operational DIDs (wheel speeds, brake pressure, etc.)")
    print("  3. Status DIDs (system state, fault flags)")
    print()
    
    if quick_scan:
        print("QUICK SCAN MODE: Only scanning known working DIDs")
    else:
        print("FULL SCAN MODE: Scanning all standard and Ford-specific DIDs")
        print("This may take several minutes...")
    
    print()
    input("Press Enter to start scan...")
    print()
    
    elm = SimpleELM327(port=port)
    
    try:
        if not elm.connect():
            print("❌ Failed to connect to ELM327 adapter")
            return False
        
        print("✓ Connected to ELM327 adapter")
        
        # Set header for ABS module
        elm.send_command("AT SH 760")
        time.sleep(0.1)
        
        print("✓ Set CAN header to ABS module (0x760)")
        print()
        
        # Test communication with Tester Present
        print("Testing communication...")
        response = elm.send_command("3E 01")
        if '7E' in response:
            print("✓ ABS module responding (Tester Present OK)")
        else:
            print(f"⚠ Unexpected Tester Present response: {response}")
        
        print()
        print("-" * 80)
        print("Scanning DIDs...")
        print("-" * 80)
        print()
        
        results = {
            'scan_date': datetime.now().isoformat(),
            'vehicle': 'Ford Escape 2008',
            'module': 'ABS (0x760)',
            'identification_dids': {},
            'operational_dids': {},
            'failed_dids': {}
        }
        
        # Scan Standard Identification DIDs
        print("📋 SCANNING STANDARD IDENTIFICATION DIDs (ISO 14229-1)")
        print("-" * 80)
        
        for did, description in STANDARD_IDENTIFICATION_DIDS.items():
            # Format DID for command
            did_formatted = f"{did[:2]} {did[2:]}"
            command = f"22 {did_formatted}"
            
            response = elm.send_command(command)
            data, status = parse_did_response(response, did_formatted)
            
            if status == "SUCCESS":
                # Try to decode as ASCII (for VIN, part numbers, etc.)
                ascii_value = hex_to_ascii(data)
                int_value = hex_to_int(data)
                
                print(f"✓ DID 0x{did}: {description}")
                print(f"  Raw: {data}")
                if ascii_value and ascii_value.isprintable():
                    print(f"  ASCII: {ascii_value}")
                if int_value is not None:
                    print(f"  Decimal: {int_value}")
                print()
                
                results['identification_dids'][did] = {
                    'description': description,
                    'raw': data,
                    'ascii': ascii_value,
                    'decimal': int_value
                }
            elif 'NEGATIVE_RESPONSE' in status:
                results['failed_dids'][did] = {
                    'description': description,
                    'status': status
                }
            
            time.sleep(0.1)  # Small delay between requests
        
        # Scan Ford-specific DIDs
        print()
        print("🔧 SCANNING FORD-SPECIFIC ABS DIDs")
        print("-" * 80)
        
        for did, description in FORD_ABS_DIDS.items():
            # Format DID for command
            did_formatted = f"{did[:2]} {did[2:]}"
            command = f"22 {did_formatted}"
            
            response = elm.send_command(command)
            data, status = parse_did_response(response, did_formatted)
            
            if status == "SUCCESS":
                ascii_value = hex_to_ascii(data)
                int_value = hex_to_int(data)
                
                print(f"✓ DID 0x{did}: {description}")
                print(f"  Raw: {data}")
                if ascii_value and ascii_value.isprintable():
                    print(f"  ASCII: {ascii_value}")
                if int_value is not None:
                    print(f"  Decimal: {int_value}")
                print()
                
                results['operational_dids'][did] = {
                    'description': description,
                    'raw': data,
                    'ascii': ascii_value,
                    'decimal': int_value
                }
            elif 'NEGATIVE_RESPONSE' in status:
                results['failed_dids'][did] = {
                    'description': description,
                    'status': status
                }
            
            time.sleep(0.1)
        
        # Save results to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"knowledge_base/captured_data/ford_escape_abs_did_scan_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print()
        print("=" * 80)
        print("SCAN COMPLETE")
        print("=" * 80)
        print()
        print(f"✓ Identification DIDs found: {len(results['identification_dids'])}")
        print(f"✓ Operational DIDs found: {len(results['operational_dids'])}")
        print(f"⚠ Failed DIDs: {len(results['failed_dids'])}")
        print()
        print(f"Results saved to: {filename}")
        print()
        
        # Display summary of key findings
        if results['identification_dids']:
            print("KEY IDENTIFICATION DATA:")
            print("-" * 80)
            
            # VIN
            if 'F190' in results['identification_dids']:
                vin_data = results['identification_dids']['F190']
                print(f"  VIN: {vin_data.get('ascii', 'N/A')}")
            
            # Serial Number
            if 'F19D' in results['identification_dids']:
                serial_data = results['identification_dids']['F19D']
                print(f"  Serial Number: {serial_data.get('ascii', 'N/A')}")
            
            # Part Number
            if 'F187' in results['identification_dids']:
                part_data = results['identification_dids']['F187']
                print(f"  Part Number: {part_data.get('ascii', 'N/A')}")
            
            # Hardware Version
            if 'F191' in results['identification_dids']:
                hw_data = results['identification_dids']['F191']
                print(f"  Hardware Number: {hw_data.get('ascii', 'N/A')}")
            
            # Software Version
            if 'F189' in results['identification_dids']:
                sw_data = results['identification_dids']['F189']
                print(f"  Software Version: {sw_data.get('ascii', 'N/A')}")
            
            print()
        
        if results['operational_dids']:
            print("OPERATIONAL DATA AVAILABLE:")
            print("-" * 80)
            for did, data in results['operational_dids'].items():
                print(f"  DID 0x{did}: {data['description']}")
            print()
        
        return True
    
    except KeyboardInterrupt:
        print("\n\n⚠ Scan interrupted by user")
        return False
    
    except Exception as e:
        print(f"\n❌ Error during scan: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        elm.close()
        print("Connection closed.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scan Ford Escape 2008 ABS module for all available DIDs'
    )
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    parser.add_argument('--quick', action='store_true', 
                       help='Quick scan mode (only known working DIDs)')
    
    args = parser.parse_args()
    
    success = scan_abs_module(port=args.port, quick_scan=args.quick)
    sys.exit(0 if success else 1)
