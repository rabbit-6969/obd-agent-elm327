#!/usr/bin/env python3
"""
Toyota FJ Cruiser - ABS Address Scanner
Test multiple possible CAN IDs to find the correct ABS module address

This script tests:
- 0x750/0x758 (common Toyota ABS)
- 0x7B0/0x7B8 (from OBDB data)
- 0x760/0x768 (alternate)
- Diagnostic session entry (0x10 0x03)
- VIN read (0x22 0xF190)
- DTC read (0x19 0x02 0xFF)

Author: AI Diagnostic Agent
"""

import serial
import time
from typing import Optional, Tuple

class ToyotaABSAddressScanner:
    """Scan for Toyota ABS module on different CAN IDs"""
    
    def __init__(self, port: str = 'COM3', baudrate: int = 38400):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        
        # Possible Toyota ABS addresses to test
        self.addresses_to_test = [
            (0x750, 0x758, "Common Toyota ABS"),
            (0x7B0, 0x7B8, "OBDB Data (4Runner)"),
            (0x760, 0x768, "Alternate Toyota"),
            (0x7E0, 0x7E8, "PCM (for comparison)"),
        ]
    
    def connect(self) -> bool:
        """Connect to ELM327"""
        try:
            print("=" * 70)
            print("Toyota FJ Cruiser - ABS Address Scanner")
            print("=" * 70)
            print(f"\nConnecting to {self.port}...")
            
            self.connection = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)
            
            # Initialize ELM327
            print("Initializing ELM327...")
            self._send_command("ATZ")  # Reset
            time.sleep(1)
            self._send_command("ATE0")  # Echo off
            self._send_command("ATL0")  # Linefeeds off
            self._send_command("ATS0")  # Spaces off
            self._send_command("ATH1")  # Headers on
            self._send_command("ATSP6")  # ISO 15765-4 CAN (11 bit, 500 kbps)
            self._send_command("ATCAF0")  # CAN Auto Formatting off
            
            print("✓ Connected\n")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def _send_command(self, cmd: str, wait_time: float = 0.1) -> str:
        """Send command to ELM327"""
        if not self.connection:
            return ""
        
        self.connection.write((cmd + '\r').encode())
        time.sleep(wait_time)
        
        response = b''
        max_attempts = 10
        for _ in range(max_attempts):
            if self.connection.in_waiting:
                response += self.connection.read(self.connection.in_waiting)
            time.sleep(0.05)
            if b'>' in response:
                break
        
        return response.decode('utf-8', errors='ignore').strip()
    
    def test_address(self, request: int, response: int, description: str) -> dict:
        """Test a specific CAN address"""
        print(f"\n{'=' * 70}")
        print(f"Testing: {description}")
        print(f"Request: 0x{request:03X} → Response: 0x{response:03X}")
        print(f"{'=' * 70}")
        
        results = {
            'address': (request, response),
            'description': description,
            'diagnostic_session': False,
            'vin_read': False,
            'dtc_read': False,
            'responses': {}
        }
        
        # Set header
        print(f"\n1. Setting header to 0x{request:03X}...")
        self._send_command(f"ATSH {request:03X}")
        self._send_command(f"ATFCSH {response:03X}")
        self._send_command("ATFCSD 30 00 00")
        time.sleep(0.2)
        
        # Test 1: Diagnostic Session Control (0x10 0x03)
        print("2. Testing Diagnostic Session (0x10 0x03)...")
        cmd = "10 03"
        resp = self._send_command(cmd, wait_time=0.3)
        print(f"   Request:  {cmd}")
        print(f"   Response: {resp[:80]}")
        
        resp_clean = resp.replace(' ', '').replace('\r', '').replace('\n', '').upper()
        if '5003' in resp_clean:
            print("   ✓ Positive response (50 03) - Module responded!")
            results['diagnostic_session'] = True
            results['responses']['session'] = resp
        elif '7F' in resp_clean:
            print("   ⚠ Negative response (7F) - Module present but rejected")
            results['responses']['session'] = resp
        else:
            print("   ✗ No response")
        
        time.sleep(0.3)
        
        # Test 2: Read VIN (0x22 0xF190)
        print("3. Testing VIN Read (0x22 0xF190)...")
        cmd = "22 F1 90"
        resp = self._send_command(cmd, wait_time=0.5)
        print(f"   Request:  {cmd}")
        print(f"   Response: {resp[:80]}")
        
        resp_clean = resp.replace(' ', '').replace('\r', '').replace('\n', '').upper()
        if '62F190' in resp_clean:
            print("   ✓ Positive response (62 F1 90) - Module responded!")
            results['vin_read'] = True
            results['responses']['vin'] = resp
            # Try to decode VIN
            idx = resp_clean.find('62F190')
            if idx != -1:
                vin_hex = resp_clean[idx+6:idx+40]  # VIN is 17 chars = 34 hex
                try:
                    vin = bytes.fromhex(vin_hex).decode('ascii', errors='ignore')
                    print(f"   VIN: {vin}")
                except:
                    pass
        elif '7F' in resp_clean:
            print("   ⚠ Negative response (7F) - Module present but rejected")
            results['responses']['vin'] = resp
        else:
            print("   ✗ No response")
        
        time.sleep(0.3)
        
        # Test 3: Read DTCs (0x19 0x02 0xFF)
        print("4. Testing DTC Read (0x19 0x02 0xFF)...")
        cmd = "19 02 FF"
        resp = self._send_command(cmd, wait_time=0.5)
        print(f"   Request:  {cmd}")
        print(f"   Response: {resp[:80]}")
        
        resp_clean = resp.replace(' ', '').replace('\r', '').replace('\n', '').upper()
        if '5902' in resp_clean:
            print("   ✓ Positive response (59 02) - Module responded!")
            results['dtc_read'] = True
            results['responses']['dtc'] = resp
        elif '7F' in resp_clean:
            print("   ⚠ Negative response (7F) - Module present but rejected")
            results['responses']['dtc'] = resp
        else:
            print("   ✗ No response (normal if no DTCs on Toyota)")
        
        time.sleep(0.3)
        
        # Test 4: Tester Present (0x3E 0x00)
        print("5. Testing Tester Present (0x3E 0x00)...")
        cmd = "3E 00"
        resp = self._send_command(cmd, wait_time=0.3)
        print(f"   Request:  {cmd}")
        print(f"   Response: {resp[:80]}")
        
        resp_clean = resp.replace(' ', '').replace('\r', '').replace('\n', '').upper()
        if '7E' in resp_clean:
            print("   ✓ Positive response (7E) - Module responded!")
            results['responses']['tester_present'] = resp
        elif '7F' in resp_clean:
            print("   ⚠ Negative response (7F) - Module present but rejected")
            results['responses']['tester_present'] = resp
        else:
            print("   ✗ No response")
        
        return results
    
    def scan_all_addresses(self):
        """Scan all possible addresses"""
        print("\n" + "=" * 70)
        print("SCANNING ALL POSSIBLE ABS ADDRESSES")
        print("=" * 70)
        print("\nThis will test multiple CAN IDs to find your ABS module...")
        print("Each test takes ~5 seconds\n")
        
        all_results = []
        
        for request, response, description in self.addresses_to_test:
            result = self.test_address(request, response, description)
            all_results.append(result)
            time.sleep(0.5)
        
        # Print summary
        print("\n\n" + "=" * 70)
        print("SCAN RESULTS SUMMARY")
        print("=" * 70)
        
        found_modules = []
        
        for result in all_results:
            req, resp = result['address']
            desc = result['description']
            
            # Check if module responded to anything
            responded = (
                result['diagnostic_session'] or
                result['vin_read'] or
                result['dtc_read'] or
                any('7F' in str(r).upper() for r in result['responses'].values())
            )
            
            if responded:
                found_modules.append(result)
                print(f"\n✓ FOUND: {desc} (0x{req:03X}/0x{resp:03X})")
                print(f"  Diagnostic Session: {'✓' if result['diagnostic_session'] else '✗'}")
                print(f"  VIN Read:           {'✓' if result['vin_read'] else '✗'}")
                print(f"  DTC Read:           {'✓' if result['dtc_read'] else '✗'}")
            else:
                print(f"\n✗ No response: {desc} (0x{req:03X}/0x{resp:03X})")
        
        # Recommendations
        print("\n" + "=" * 70)
        print("RECOMMENDATIONS")
        print("=" * 70)
        
        if not found_modules:
            print("\n⚠ NO MODULES RESPONDED")
            print("\nPossible causes:")
            print("  1. ABS module on secondary CAN bus (gateway required)")
            print("  2. Module in deep sleep mode")
            print("  3. Ignition not ON")
            print("  4. ELM327 adapter issue")
            print("  5. Wrong protocol (try ATSP7 for 29-bit CAN)")
            print("\nTroubleshooting:")
            print("  • Verify ignition is ON (engine doesn't need to run)")
            print("  • Try with engine running")
            print("  • Disconnect battery for 30 seconds, reconnect, try again")
            print("  • Test with professional scan tool")
        
        elif len(found_modules) == 1:
            result = found_modules[0]
            req, resp = result['address']
            print(f"\n✓ FOUND YOUR ABS MODULE!")
            print(f"\nCorrect address: 0x{req:03X} (request) / 0x{resp:03X} (response)")
            print(f"Description: {result['description']}")
            print(f"\nUpdate your scripts to use:")
            print(f"  self.abs_request = 0x{req:03X}")
            print(f"  self.abs_response = 0x{resp:03X}")
            
            if result['vin_read']:
                print(f"\n✓ Module supports VIN read - communication is working!")
            
            if not result['dtc_read']:
                print(f"\n⚠ No response to DTC read - this is NORMAL for Toyota")
                print(f"  Toyota ABS modules don't respond when no DTCs are present")
        
        else:
            print(f"\n⚠ MULTIPLE MODULES RESPONDED ({len(found_modules)})")
            print("\nThis is unusual. Modules found:")
            for result in found_modules:
                req, resp = result['address']
                print(f"  • {result['description']}: 0x{req:03X}/0x{resp:03X}")
            print("\nThe PCM (0x7E0) responding is normal.")
            print("Use the ABS-specific address (0x750 or 0x7B0) for ABS diagnostics.")
        
        print("\n" + "=" * 70)
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
        print("\n✓ Disconnected")

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scan for Toyota ABS module on different CAN addresses'
    )
    parser.add_argument(
        '--port',
        default='COM3',
        help='Serial port for ELM327 adapter (default: COM3)'
    )
    
    args = parser.parse_args()
    
    scanner = ToyotaABSAddressScanner(port=args.port)
    
    if not scanner.connect():
        return
    
    try:
        scanner.scan_all_addresses()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scanner.disconnect()

if __name__ == "__main__":
    main()
