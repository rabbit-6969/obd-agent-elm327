"""
Scan All Vehicle Systems
Try to discover DIDs for different vehicle systems

This scanner tests DID ranges commonly used for different systems:
- 0x0100-0x01FF: Transmission (PCM)
- 0x0200-0x02FF: ABS/Braking
- 0x0300-0x03FF: HVAC/Climate
- 0x0400-0x04FF: Body/Comfort
- 0xF000-0xF0FF: Vehicle identification
- 0xF100-0xF1FF: Manufacturer specific
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

# DID ranges for different systems
SYSTEM_RANGES = [
    (0x0100, 0x01FF, "Transmission/Powertrain"),
    (0x0200, 0x02FF, "ABS/Braking System"),
    (0x0300, 0x03FF, "HVAC/Climate Control"),
    (0x0400, 0x04FF, "Body/Comfort Systems"),
    (0x0500, 0x05FF, "Chassis/Suspension"),
    (0xF000, 0xF0FF, "Vehicle Identification"),
    (0xF100, 0xF1FF, "Manufacturer Specific"),
    (0xF400, 0xF4FF, "Vehicle Manufacturer ECU"),
]


class SystemScanner:
    def __init__(self, port, baudrate=38400):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.found_dids = {}  # Organized by system
        self.stats = {
            'total_tested': 0,
            'positive_responses': 0,
        }
    
    def connect(self):
        """Connect and initialize"""
        print(f"Connecting to {self.port}...")
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=2.0)
            time.sleep(2)
            
            # Initialize
            self.ser.write(b"ATZ\r")
            time.sleep(1)
            self.ser.read(self.ser.in_waiting)
            
            self.ser.write(b"ATE0\r")
            time.sleep(0.3)
            self.ser.read(self.ser.in_waiting)
            
            self.ser.write(b"ATSP0\r")
            time.sleep(0.3)
            self.ser.read(self.ser.in_waiting)
            
            # Test
            self.ser.write(b"03\r")
            time.sleep(0.5)
            response = ""
            while self.ser.in_waiting > 0:
                response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                time.sleep(0.1)
            
            if "43" in response:
                print("✓ Connected and initialized\n")
                return True
            else:
                print(f"✗ Vehicle not responding")
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("\n✓ Disconnected")
    
    def send_command(self, cmd):
        if not self.ser or not self.ser.is_open:
            return None
        
        self.ser.write((cmd + "\r").encode())
        time.sleep(0.5)
        
        response = ""
        while self.ser.in_waiting > 0:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        
        return response.strip()
    
    def test_did(self, did):
        cmd = f"22{did:04X}"
        response = self.send_command(cmd)
        
        self.stats['total_tested'] += 1
        
        if response and response.startswith('62'):
            self.stats['positive_responses'] += 1
            return True, response
        
        return False, None
    
    def scan_system(self, start, end, system_name):
        """Scan a system's DID range"""
        print(f"\n{'='*70}")
        print(f"System: {system_name}")
        print(f"Range: 0x{start:04X} - 0x{end:04X}")
        print(f"{'='*70}\n")
        
        found = []
        total = end - start + 1
        
        for did in range(start, end + 1):
            progress = ((did - start + 1) / total) * 100
            sys.stdout.write(f"\r  Progress: {progress:.1f}% | DID 0x{did:04X} | Found: {len(found)}  ")
            sys.stdout.flush()
            
            success, response = self.test_did(did)
            
            if success:
                print(f"\n  ✓ Found DID 0x{did:04X}: {response}")
                found.append({
                    'did': did,
                    'response': response,
                    'system': system_name,
                    'discovered_at': datetime.now().isoformat()
                })
        
        print(f"\n\n  Found {len(found)} DIDs in {system_name}")
        
        if found:
            self.found_dids[system_name] = found
        
        return found
    
    def scan_all(self):
        """Scan all systems"""
        print("="*70)
        print("Multi-System Vehicle Scanner")
        print("="*70)
        print("\nThis will scan DID ranges for different vehicle systems:")
        for start, end, name in SYSTEM_RANGES:
            print(f"  • {name}: 0x{start:04X}-0x{end:04X}")
        print()
        
        for start, end, system_name in SYSTEM_RANGES:
            self.scan_system(start, end, system_name)
            
            # Ask to continue
            if SYSTEM_RANGES.index((start, end, system_name)) < len(SYSTEM_RANGES) - 1:
                print("\n\nContinue to next system? (Enter=yes, Ctrl+C=stop): ", end="")
                try:
                    input()
                except KeyboardInterrupt:
                    print("\n\nScan stopped")
                    break
    
    def save_results(self):
        """Save results"""
        if not os.path.exists(RESULTS_DIR):
            os.makedirs(RESULTS_DIR)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = os.path.join(RESULTS_DIR, f"all_systems_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump({
                'vehicle': {
                    'make': 'Ford',
                    'model': 'Escape',
                    'year': 2008,
                },
                'scan_date': datetime.now().isoformat(),
                'statistics': self.stats,
                'systems': self.found_dids,
            }, f, indent=2)
        
        print(f"\n✓ Results saved to: {json_file}")
        
        # Text summary
        txt_file = os.path.join(RESULTS_DIR, f"all_systems_summary_{timestamp}.txt")
        with open(txt_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("Multi-System Vehicle Scan - Summary\n")
            f.write("="*70 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Statistics:\n")
            f.write(f"  Total DIDs tested: {self.stats['total_tested']}\n")
            f.write(f"  DIDs found: {self.stats['positive_responses']}\n\n")
            
            for system_name, dids in self.found_dids.items():
                f.write(f"\n{system_name}: {len(dids)} DIDs\n")
                f.write("-"*70 + "\n")
                for item in dids:
                    f.write(f"  DID 0x{item['did']:04X}: {item['response']}\n")
        
        print(f"✓ Summary saved to: {txt_file}")
    
    def print_summary(self):
        """Print summary"""
        print("\n" + "="*70)
        print("Scan Complete - Summary")
        print("="*70)
        print(f"\nTotal DIDs tested: {self.stats['total_tested']}")
        print(f"Total DIDs found: {self.stats['positive_responses']}")
        
        if self.found_dids:
            print("\nDIDs by System:")
            for system_name, dids in self.found_dids.items():
                print(f"\n  {system_name}: {len(dids)} DIDs")
                for item in dids:
                    print(f"    • 0x{item['did']:04X}: {item['response']}")
        else:
            print("\n✗ No DIDs found in any system")


def main():
    print("\nMake sure:")
    print("- Vehicle ignition is ON")
    print("- FORScan is closed")
    print("- ELM327 is connected to COM3")
    print()
    input("Press Enter to start...")
    print()
    
    scanner = SystemScanner(COM_PORT, BAUDRATE)
    
    try:
        if not scanner.connect():
            return 1
        
        scanner.scan_all()
        scanner.print_summary()
        scanner.save_results()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted")
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
