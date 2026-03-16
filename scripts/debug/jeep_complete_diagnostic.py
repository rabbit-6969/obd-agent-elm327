#!/usr/bin/env python3
"""
2007 Jeep Wrangler JK - Complete Diagnostic Workflow

Workflow:
1. Read VIN via standard OBD-II
2. Connect to PCM and scan supported DIDs + read DTCs
3. Connect to SRS/Airbag module and scan supported DIDs + read DTCs

⚠️ SAFETY: This is READ-ONLY - no messages modify vehicle state.

Usage:
    python scripts/debug/jeep_complete_diagnostic.py --port COM4
"""

import serial
import time
import sys
from datetime import datetime

# Allow running from repo root or scripts/debug directly
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'toolkit', 'vehicle_communication'))

try:
    from adapter_checker import check_adapter, AdapterCheckResult
    _CHECKER_AVAILABLE = True
except ImportError:
    _CHECKER_AVAILABLE = False

class ELM327:
    """ELM327 adapter interface"""
    
    def __init__(self, port='COM4', baudrate=38400, timeout=3):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
    
    def connect(self):
        """Connect and initialize ELM327"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)
            
            # Initialize adapter
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATS0")  # Spaces off
            self.send_command("ATH1")  # Headers on
            self.send_command("ATSP0")  # Auto protocol
            
            # Test communication
            response = self.send_command("0100")
            if not response or "NO DATA" in response:
                return False
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def send_command(self, command, timeout=None):
        """Send command and get response"""
        if not self.ser:
            return None
        
        if timeout is None:
            timeout = self.timeout
        
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            self.ser.write((command + '\r').encode())
            
            response = b''
            start_time = time.time()
            
            while time.time() - start_time < timeout:
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

def read_vin(elm):
    """Step 1: Read VIN using Mode 09 PID 02"""
    print("=" * 70)
    print("STEP 1: READ VIN")
    print("=" * 70)
    print()
    
    # Request VIN (Mode 09, PID 02)
    response = elm.send_command("0902")
    
    if not response or "NO DATA" in response:
        print("  ✗ VIN: Not available")
        return None
    
    # Parse VIN from response
    try:
        hex_data = response.replace(' ', '')
        
        # Find the start of VIN data (after 4902)
        idx = hex_data.find('4902')
        if idx == -1:
            print("  ✗ VIN: Parse error")
            return None
        
        # Extract VIN characters (17 ASCII characters = 34 hex digits)
        vin_start = idx + 6  # Skip "4902" + count byte
        vin_hex = hex_data[vin_start:vin_start + 34]
        
        # Convert hex to ASCII
        vin = ''
        for i in range(0, len(vin_hex), 2):
            if i + 1 < len(vin_hex):
                byte_hex = vin_hex[i:i+2]
                try:
                    char = chr(int(byte_hex, 16))
                    if char.isprintable():
                        vin += char
                except:
                    pass
        
        if len(vin) >= 17:
            vin = vin[:17]
            print(f"  ✓ VIN: {vin}")
            print()
            return vin
        else:
            print(f"  ✗ VIN: Incomplete ({vin})")
            return None
    
    except Exception as e:
        print(f"  ✗ VIN: Parse error ({e})")
        return None

def scan_pcm(elm):
    """Step 2: Connect to PCM and scan DIDs + read DTCs"""
    print("=" * 70)
    print("STEP 2: PCM (POWERTRAIN CONTROL MODULE)")
    print("=" * 70)
    print()
    
    # Set header to PCM (0x7E0 request, 0x7E8 response)
    elm.send_command("ATSH7E0")
    
    print("2.1: Testing PCM Communication")
    print("-" * 70)
    
    # Test with Tester Present
    response = elm.send_command("3E00")
    
    if response and "7E8" in response and "7E00" in response:
        print("  ✓ PCM is responding")
    else:
        print(f"  ⚠ PCM response: {response}")
    
    print()
    
    # Scan supported DIDs
    print("2.2: Scanning Supported DIDs")
    print("-" * 70)
    
    supported_dids = scan_supported_dids(elm, "PCM")
    
    if supported_dids:
        print(f"  ✓ Found {len(supported_dids)} supported DIDs")
        print()
        print("  Supported DIDs:")
        for did in supported_dids[:20]:  # Show first 20
            print(f"    0x{did}")
        if len(supported_dids) > 20:
            print(f"    ... and {len(supported_dids) - 20} more")
    else:
        print("  ⚠ No supported DIDs found (may require extended session)")
    
    print()
    
    # Read DTCs
    print("2.3: Reading DTCs from PCM")
    print("-" * 70)
    
    dtcs = read_dtcs_uds(elm, "PCM")
    
    if dtcs:
        print(f"  ⚠ Found {len(dtcs)} DTC(s):")
        print()
        for dtc in dtcs:
            print(f"    {dtc['code']} - {dtc['status']}")
    elif dtcs is not None:
        print("  ✓ No DTCs stored in PCM")
    else:
        print("  ⚠ Could not read DTCs (may require extended session)")
    
    print()

def scan_srs_airbag(elm):
    """Step 3: Connect to SRS/Airbag module and scan DIDs + read DTCs"""
    print("=" * 70)
    print("STEP 3: SRS/AIRBAG CONTROL MODULE")
    print("=" * 70)
    print()
    
    # Common Jeep/Chrysler airbag module addresses
    airbag_addresses = [
        ("740", "758", "Primary Airbag Address"),
        ("738", "758", "Alternative Airbag Address"),
        ("750", "758", "Body Control (may include airbag)"),
    ]
    
    airbag_found = False
    
    for req_addr, resp_addr, description in airbag_addresses:
        print(f"3.1: Testing {description} (0x{req_addr})")
        print("-" * 70)
        
        # Set header to airbag module
        elm.send_command(f"ATSH{req_addr}")
        
        # Test with Tester Present
        response = elm.send_command("3E00", timeout=2)
        
        if response and resp_addr in response and "7E00" in response:
            print(f"  ✓ Airbag module responding at 0x{req_addr}")
            airbag_found = True
            
            print()
            
            # Scan supported DIDs
            print(f"3.2: Scanning Supported DIDs (0x{req_addr})")
            print("-" * 70)
            
            supported_dids = scan_supported_dids(elm, "Airbag")
            
            if supported_dids:
                print(f"  ✓ Found {len(supported_dids)} supported DIDs")
                print()
                print("  Supported DIDs:")
                for did in supported_dids[:20]:
                    print(f"    0x{did}")
                if len(supported_dids) > 20:
                    print(f"    ... and {len(supported_dids) - 20} more")
            else:
                print("  ⚠ No supported DIDs found")
            
            print()
            
            # Read DTCs
            print(f"3.3: Reading DTCs from Airbag Module (0x{req_addr})")
            print("-" * 70)
            
            dtcs = read_dtcs_uds(elm, "Airbag")
            
            if dtcs:
                print(f"  ⚠ Found {len(dtcs)} DTC(s):")
                print()
                for dtc in dtcs:
                    print(f"    {dtc['code']} - {dtc['status']}")
            elif dtcs is not None:
                print("  ✓ No DTCs stored in Airbag module")
            else:
                print("  ⚠ Could not read DTCs")
            
            print()
            break
        
        elif response and "7F" in response:
            print(f"  ✗ Negative response from 0x{req_addr}: {response}")
            print()
        else:
            print(f"  ✗ No response from 0x{req_addr}")
            print()
    
    if not airbag_found:
        print("=" * 70)
        print("⚠ AIRBAG MODULE NOT ACCESSIBLE")
        print("=" * 70)
        print()
        print("EXPLANATION:")
        print("  Jeep/Chrysler airbag modules use proprietary protocols")
        print("  that are not accessible via standard OBD-II/UDS.")
        print()
        print("  The airbag module likely uses:")
        print("    - CCD bus (Chrysler Collision Detection)")
        print("    - SCI bus (Serial Communication Interface)")
        print("    - Manufacturer-specific security/authentication")
        print()
        print("SOLUTION:")
        print("  Use AlfaOBD (~$50) for full airbag module access")
        print("  Download: https://www.alfaobd.com/")
        print()

def scan_supported_dids(elm, module_name):
    """Scan for supported DIDs using Service 0x22"""
    supported = []
    
    # Common DID ranges to scan
    did_ranges = [
        (0xF100, 0xF1FF),  # Identification DIDs
        (0xF200, 0xF2FF),  # Diagnostic DIDs
        (0x0100, 0x01FF),  # Live data DIDs
    ]
    
    print(f"  Scanning common DID ranges...")
    
    for start, end in did_ranges:
        # Sample every 16th DID for speed
        for did in range(start, min(start + 0x20, end), 0x10):
            did_hex = f"{did:04X}"
            response = elm.send_command(f"22{did_hex}", timeout=1)
            
            if response and f"62{did_hex}" in response.replace(' ', ''):
                supported.append(did_hex)
            
            # Small delay to avoid overwhelming module
            time.sleep(0.05)
    
    return supported

def read_dtcs_uds(elm, module_name):
    """Read DTCs using UDS Service 0x19"""
    
    # Service 0x19, Sub-function 0x02 (DTCs by status mask)
    # Status mask 0xFF = all DTCs
    response = elm.send_command("1902FF", timeout=2)
    
    if not response:
        return None
    
    # Check for negative response
    if "7F19" in response.replace(' ', ''):
        return None
    
    # Check for positive response (59 02)
    hex_data = response.replace(' ', '')
    idx = hex_data.find('5902')
    
    if idx == -1:
        return None
    
    # Parse DTCs
    dtcs = []
    
    try:
        # Skip to DTC data (after 5902 and status availability mask)
        data_start = idx + 6  # Skip "5902" + status byte
        
        # Each DTC is 4 bytes: 3 bytes DTC + 1 byte status
        while data_start + 8 <= len(hex_data):
            dtc_bytes = hex_data[data_start:data_start+6]
            status_byte = hex_data[data_start+6:data_start+8]
            
            if dtc_bytes == "000000":
                break
            
            # Decode DTC
            dtc_code = decode_dtc(dtc_bytes)
            status = decode_dtc_status(status_byte)
            
            if dtc_code:
                dtcs.append({
                    'code': dtc_code,
                    'status': status,
                    'raw': dtc_bytes
                })
            
            data_start += 8
    
    except Exception as e:
        print(f"  ⚠ DTC parse error: {e}")
        return None
    
    return dtcs

def decode_dtc(dtc_bytes):
    """Decode 3-byte DTC to standard format (e.g., P0420)"""
    try:
        # Convert to integer
        dtc_int = int(dtc_bytes, 16)
        
        # Extract components
        first_byte = (dtc_int >> 16) & 0xFF
        second_byte = (dtc_int >> 8) & 0xFF
        third_byte = dtc_int & 0xFF
        
        # Determine DTC type from first 2 bits
        dtc_type_bits = (first_byte >> 6) & 0x03
        dtc_types = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
        dtc_type = dtc_types.get(dtc_type_bits, 'P')
        
        # Extract digits
        digit1 = (first_byte >> 4) & 0x03
        digit2 = first_byte & 0x0F
        digit3 = (second_byte >> 4) & 0x0F
        digit4 = second_byte & 0x0F
        digit5 = (third_byte >> 4) & 0x0F
        
        dtc_code = f"{dtc_type}{digit1}{digit2:X}{digit3:X}{digit4:X}"
        
        return dtc_code
    
    except:
        return None

def decode_dtc_status(status_byte):
    """Decode DTC status byte"""
    try:
        status = int(status_byte, 16)
        
        flags = []
        
        if status & 0x01:
            flags.append("Test Failed")
        if status & 0x02:
            flags.append("Test Failed This Cycle")
        if status & 0x04:
            flags.append("Pending")
        if status & 0x08:
            flags.append("Confirmed")
        if status & 0x10:
            flags.append("Test Not Complete Since Clear")
        if status & 0x20:
            flags.append("Test Failed Since Clear")
        if status & 0x40:
            flags.append("Test Not Complete This Cycle")
        if status & 0x80:
            flags.append("Warning Indicator Requested")
        
        if flags:
            return ", ".join(flags)
        else:
            return "Stored"
    
    except:
        return "Unknown"

def main(port='COM4'):
    """Main entry point"""
    print("=" * 70)
    print("2007 Jeep Wrangler JK - Complete Diagnostic Workflow")
    print("=" * 70)
    print()
    print("Workflow:")
    print("  1. Read VIN via standard OBD-II")
    print("  2. Connect to PCM and scan DIDs + read DTCs")
    print("  3. Connect to SRS/Airbag and scan DIDs + read DTCs")
    print()
    print("=" * 70)
    print()
    
    elm = ELM327(port=port)
    
    if not elm.connect():
        print("✗ Failed to connect to ELM327")
        print()
        print("Troubleshooting:")
        print("  - Verify adapter is plugged into OBD-II port")
        print("  - Check COM port (use Device Manager)")
        print("  - Ensure vehicle ignition is in RUN position")
        print("  - Try unplugging and replugging adapter")
        return False
    
    print("✓ Connected to ELM327")
    print()

    # ── Adapter quality check (every session) ──────────────────────────────
    if _CHECKER_AVAILABLE:
        print("Checking adapter quality...")
        adapter_result = check_adapter(elm.ser)
        print(adapter_result.user_message())
        print()
    else:
        print("⚠ Adapter checker not available (toolkit not in path)")
        print()

    # Step 1: Read VIN
    vin = read_vin(elm)
    
    # Step 2: Scan PCM
    scan_pcm(elm)
    
    # Step 3: Scan SRS/Airbag
    scan_srs_airbag(elm)
    
    # Summary
    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print()
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Vehicle: 2007 Jeep Wrangler JK")
    if vin:
        print(f"VIN: {vin}")
    print()
    
    elm.close()
    print("✓ Disconnected")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Complete diagnostic workflow for 2007 Jeep Wrangler JK'
    )
    parser.add_argument('--port', default='COM4', 
                       help='Serial port (default: COM4)')
    
    args = parser.parse_args()
    
    success = main(port=args.port)
    sys.exit(0 if success else 1)
