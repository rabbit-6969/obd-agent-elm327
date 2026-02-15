"""
Working Vehicle Discovery Scanner
Based on successful test_basic_communication.py results

This scanner uses the proven communication pattern that works with your vehicle.
"""

import serial
import time
import sys
import json
import os
from datetime import datetime

COM_PORT = "COM3"
BAUDRATE = 38400
RESULTS_DIR = "vehicle_discovery"

# DID ranges to scan
QUICK_RANGES = [
    (0x0100, 0x01FF, "Transmission parameters"),
    (0x1000, 0x10FF, "Common Ford range"),
    (0xF000, 0xF0FF, "Manufacturer-specific"),
]

FULL_RANGE = [(0x0000, 0xFFFF, "Complete DID space")]


class WorkingScanner:
    def __init__(self, port, baudrate=38400):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.found_dids = []
        self.stats = {
            'total_tested': 0,
            'positive_responses': 0,
            'negative_responses': 0,
            'no_response': 0,
        }
    
    def connect(self):
        """Connect and initialize ELM327"""
        print(f"Connecting to {self.port}...")
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=2.0)
            time.sleep(2)
            print("✓ Serial port opened")
            
            # Initialize - exactly like test_basic_communication.py
            print("Initializing adapter...")
            
            # Reset
            self.ser.write(b"ATZ\r")
            time.sleep(1)
            self.ser.read(self.ser.in_waiting)
            
            # Echo off
            self.ser.write(b"ATE0\r")
            time.sleep(0.3)
            self.ser.read(self.ser.in_waiting)
            
            # Auto protocol
            self.ser.write(b"ATSP0\r")
            time.sleep(0.3)
            self.ser.read(self.ser.in_waiting)
            
            # Test communication with Mode 03
            print("Testing vehicle communication...")
            self.ser.write(b"03\r")
            time.sleep(0.5)
            response = ""
            while self.ser.in_waiting > 0:
                response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                time.sleep(0.1)
            
            if "43" in response:
                print("✓ Vehicle responding")
                print(f"✓ Connected and initialized\n")
                return True
            else:
                print(f"✗ Vehicle not responding: {repr(response)}")
                return False
                
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from adapter"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("\n✓ Disconnected")
    
    def send_command(self, cmd):
        """Send command and get response - exactly like test script"""
        if not self.ser or not self.ser.is_open:
            return None
        
        self.ser.write((cmd + "\r").encode())
        time.sleep(0.5)  # Same timeout as test script
        
        response = ""
        while self.ser.in_waiting > 0:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        
        return response.strip()
    
    def test_did(self, did):
        """Test a single DID"""
        cmd = f"22{did:04X}"
        response = self.send_command(cmd)
        
        self.stats['total_tested'] += 1
        
        if response:
            # Check for positive response (62 = 0x22 + 0x40)
            if response.startswith('62'):
                self.stats['positive_responses'] += 1
                return True, response
            # Check for negative response (7F 22 XX)
            elif '7F 22' in response:
                self.stats['negative_responses'] += 1
                return False, response
            # STOPPED or SEARCHING means no response
            elif 'STOPPED' in response or 'SEARCHING' in response:
                self.stats['no_response'] += 1
                return False, None
        
        self.stats['no_response'] += 1
        return False, None
    
    def scan_range(self, start, end, description):
        """Scan a range of DIDs"""
        print(f"\n{'='*70}")
        print(f"Scanning: {description}")
        print(f"Range: 0x{start:04X} - 0x{end:04X}")
        print(f"{'='*70}\n")
        
        found_in_range = []
        total = end - start + 1
        
        for did in range(start, end + 1):
            # Progress
            progress = ((did - start + 1) / total) * 100
            sys.stdout.write(f"\r  Progress: {progress:.1f}% | DID 0x{did:04X} | Found: {len(found_in_range)}  ")
            sys.stdout.flush()
            
            success, response = self.test_did(did)
            
            if success:
                print(f"\n  ✓ Found DID 0x{did:04X}: {response}")
                found_in_range.append({
                    'did': did,
                    'response': response,
                    'range': description,
                    'discovered_at': datetime.now().isoformat()
                })
                self.found_dids.append(found_in_range[-1])
        
        print(f"\n\n  Found {len(found_in_range)} DIDs in this range")
        return found_in_range
    
    def scan(self, ranges):
        """Scan multiple ranges"""
        print("="*70)
        print("Vehicle DID Discovery Scanner")
        print("="*70)
        print()
        
        for start, end, description in ranges:
            self.scan_range(start, end, description)
            
            # Ask to continue
            if ranges.index((start, end, description)) < len(ranges) - 1:
                print("\n\nContinue to next range? (Enter=yes, Ctrl+C=stop): ", end="")
                try:
                    input()
                except KeyboardInterrupt:
                    print("\n\nScan stopped by user")
                    break
    
    def save_results(self):
        """Save results to file"""
        if not os.path.exists(RESULTS_DIR):
            os.makedirs(RESULTS_DIR)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON results
        json_file = os.path.join(RESULTS_DIR, f"discovered_dids_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump({
                'vehicle': {
                    'make': 'Ford',
                    'model': 'Escape',
                    'year': 2008,
                    'vin': '1FMCU03Z68KB12969',
                },
                'scan_date': datetime.now().isoformat(),
                'statistics': self.stats,
                'dids_found': self.found_dids,
            }, f, indent=2)
        
        print(f"\n✓ Results saved to: {json_file}")
        
        # Text summary
        txt_file = os.path.join(RESULTS_DIR, f"summary_{timestamp}.txt")
        with open(txt_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("Vehicle DID Discovery - Summary\n")
            f.write("="*70 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Vehicle: 2008 Ford Escape\n\n")
            f.write(f"Statistics:\n")
            f.write(f"  Total DIDs tested: {self.stats['total_tested']}\n")
            f.write(f"  Positive responses: {self.stats['positive_responses']}\n")
            f.write(f"  Negative responses: {self.stats['negative_responses']}\n")
            f.write(f"  No response: {self.stats['no_response']}\n\n")
            f.write(f"DIDs Found: {len(self.found_dids)}\n")
            f.write("="*70 + "\n\n")
            
            for item in self.found_dids:
                f.write(f"DID 0x{item['did']:04X}\n")
                f.write(f"  Response: {item['response']}\n")
                f.write(f"  Range: {item['range']}\n")
                f.write(f"  Discovered: {item['discovered_at']}\n")
                f.write("-"*70 + "\n")
        
        print(f"✓ Summary saved to: {txt_file}")
    
    def print_summary(self):
        """Print summary"""
        print("\n" + "="*70)
        print("Scan Complete - Summary")
        print("="*70)
        print(f"\nDIDs tested: {self.stats['total_tested']}")
        print(f"DIDs found: {len(self.found_dids)}")
        print(f"Success rate: {(self.stats['positive_responses'] / max(self.stats['total_tested'], 1) * 100):.2f}%")
        
        if self.found_dids:
            print(f"\nDiscovered DIDs:")
            for item in self.found_dids:
                print(f"  • 0x{item['did']:04X}: {item['response']}")
        else:
            print("\n✗ No DIDs found")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Working vehicle DID scanner')
    parser.add_argument('--quick', action='store_true', help='Quick scan (common ranges)')
    parser.add_argument('--full', action='store_true', help='Full scan (all 65,536 DIDs)')
    args = parser.parse_args()
    
    # Default to quick
    if not args.quick and not args.full:
        args.quick = True
    
    ranges = QUICK_RANGES if args.quick else FULL_RANGE
    
    if args.full:
        print("\n⚠️  FULL SCAN - This will take 2-4 HOURS!")
        print("Press Ctrl+C at any time to stop\n")
    else:
        print("\n✓ Quick scan mode (~30 minutes)\n")
    
    print("Make sure:")
    print("- Vehicle ignition is ON")
    print("- FORScan is closed")
    print("- ELM327 is connected to COM3")
    print()
    input("Press Enter to start...")
    print()
    
    scanner = WorkingScanner(COM_PORT, BAUDRATE)
    
    try:
        if not scanner.connect():
            return 1
        
        scanner.scan(ranges)
        scanner.print_summary()
        scanner.save_results()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        scanner.print_summary()
        scanner.save_results()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scanner.disconnect()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
