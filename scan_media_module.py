#!/usr/bin/env python3
"""
Ford Escape 2008 - Media Module (ACM) DID Scanner
Scans Audio Control Module on MS-CAN bus

⚠ IMPORTANT: Set adapter switch to MS-CAN position!

The ACM is on MS-CAN (125 kbps), not HS-CAN (500 kbps).
This scanner uses UDS protocol to communicate with the ACM.

Author: AI Diagnostic Agent
"""

import serial
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

class MediaModuleScanner:
    """
    ACM (Audio Control Module) scanner for MS-CAN bus
    """
    
    def __init__(self, port: str = 'COM3', baudrate: int = 38400):
        """Initialize scanner"""
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        
        # ACM addressing
        self.acm_request = 0x726  # Typical ACM request address
        self.acm_response = 0x72E  # Typical ACM response address
        
        # Results storage
        self.discovered_dids: Dict[str, Dict] = {}
        
    def connect(self) -> bool:
        """Connect to ELM327 adapter and configure for MS-CAN"""
        try:
            print("=" * 70)
            print("Ford Escape 2008 - Media Module (ACM) Scanner")
            print("=" * 70)
            print("\n⚠ CRITICAL: Set adapter switch to MS-CAN position!")
            print("   (NOT HS-CAN - this is different from PCM scanning)")
            input("\nPress Enter when switch is in MS-CAN position...")
            
            print(f"\nConnecting to {self.port}...")
            self.connection = serial.Serial(self.port, self.baudrate, timeout=3)
            time.sleep(2)
            
            # Initialize ELM327 for MS-CAN
            print("Initializing ELM327 for MS-CAN...")
            self._send_command("ATZ")  # Reset
            time.sleep(1)
            self._send_command("ATE0")  # Echo off
            self._send_command("ATL0")  # Linefeeds off
            self._send_command("ATS0")  # Spaces off
            self._send_command("ATH1")  # Headers on
            
            # Set protocol for MS-CAN (125 kbps)
            # Try ISO 15765-4 CAN (11 bit ID, 125 kbps)
            response = self._send_command("ATSP6")
            print(f"Protocol set: {response}")
            
            # Set CAN baud rate to 125 kbps (MS-CAN)
            response = self._send_command("ATPB 1F 40")  # 125 kbps
            print(f"Baud rate set: {response}")
            
            self._send_command("ATCAF0")  # CAN Auto Formatting off
            
            # Set header to ACM request address
            self._send_command(f"ATSH {self.acm_request:03X}")
            
            # Set flow control response
            self._send_command(f"ATFCSH {self.acm_response:03X}")
            self._send_command("ATFCSD 30 00 00")  # Flow control: continue, no delay
            
            print("✓ Connected and configured for MS-CAN")
            print(f"  Request address: 0x{self.acm_request:03X}")
            print(f"  Response address: 0x{self.acm_response:03X}")
            
            # Test communication
            print("\nTesting ACM communication...")
            success = self.test_communication()
            if success:
                print("✓ ACM responding!")
            else:
                print("⚠ No response from ACM")
                print("  This could mean:")
                print("  1. Switch is not in MS-CAN position")
                print("  2. ACM uses different address")
                print("  3. ACM requires different protocol")
                
                retry = input("\nContinue anyway? (y/n): ").strip().lower()
                if retry != 'y':
                    return False
            
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def _send_command(self, cmd: str) -> str:
        """Send command to ELM327 and get response"""
        if not self.connection:
            return ""
        
        self.connection.write((cmd + '\r').encode())
        time.sleep(0.1)
        
        response = b''
        while self.connection.in_waiting:
            response += self.connection.read(self.connection.in_waiting)
            time.sleep(0.05)
        
        return response.decode('utf-8', errors='ignore').strip()
    
    def test_communication(self) -> bool:
        """Test if ACM is responding"""
        # Try reading VIN (DID 0xF190)
        success, data, error = self.read_did(0xF190)
        return success and data is not None
    
    def read_did(self, did: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Read a single DID using UDS 0x22 service
        
        Returns:
            (success, data_hex, error_code)
        """
        # Format: 03 22 [DID_MSB] [DID_LSB]
        did_msb = (did >> 8) & 0xFF
        did_lsb = did & 0xFF
        
        cmd = f"03 22 {did_msb:02X} {did_lsb:02X}"
        response = self._send_command(cmd)
        
        # Wait for response
        time.sleep(0.2)  # MS-CAN may be slower
        
        # Check for response
        if response:
            parts = response.replace(' ', '').replace('\r', '').replace('\n', '')
            
            # Look for positive response (62 = 0x22 + 0x40)
            if '62' in parts:
                idx = parts.find('62')
                if idx != -1:
                    # Skip: header, length, 62, DID_MSB, DID_LSB
                    data_start = idx + 2 + 4
                    data = parts[data_start:]
                    return True, data, None
            
            # Check for negative response (7F)
            elif '7F' in parts:
                idx = parts.find('7F')
                if idx != -1:
                    nrc = parts[idx+4:idx+6]
                    if nrc == '33':
                        return True, None, 'SECURITY_LOCKED'
                    elif nrc == '31':
                        return False, None, 'NOT_SUPPORTED'
                    else:
                        return False, None, f'NRC_{nrc}'
        
        return False, None, 'NO_RESPONSE'
    
    def scan_range(self, start: int, end: int, description: str):
        """Scan a DID range"""
        print(f"\n{'=' * 70}")
        print(f"Scanning: {description}")
        print(f"Range: 0x{start:04X} - 0x{end:04X}")
        print(f"{'=' * 70}")
        
        total = end - start + 1
        scanned = 0
        found = 0
        locked = 0
        
        start_time = time.time()
        
        for did in range(start, end + 1):
            scanned += 1
            
            # Progress every 16 DIDs
            if scanned % 16 == 0:
                elapsed = time.time() - start_time
                rate = scanned / elapsed if elapsed > 0 else 0
                eta = (total - scanned) / rate if rate > 0 else 0
                print(f"  Progress: {scanned}/{total} | "
                      f"Rate: {rate:.1f} DID/s | "
                      f"ETA: {eta/60:.1f} min | "
                      f"Found: {found} | Locked: {locked}")
            
            success, data, error = self.read_did(did)
            
            if success:
                if error == 'SECURITY_LOCKED':
                    locked += 1
                    print(f"  🔒 0x{did:04X}: Security locked")
                    self.discovered_dids[f"0x{did:04X}"] = {
                        'status': 'security_locked',
                        'category': description
                    }
                elif data:
                    found += 1
                    print(f"  ✓ 0x{did:04X}: {data}")
                    self.discovered_dids[f"0x{did:04X}"] = {
                        'data': data,
                        'length': len(data) // 2,
                        'status': 'available',
                        'category': description
                    }
            
            time.sleep(0.15)  # MS-CAN may need more time
        
        elapsed = time.time() - start_time
        print(f"\n  Scan complete:")
        print(f"    Time: {elapsed/60:.1f} minutes")
        print(f"    Found: {found} available, {locked} locked")
    
    def scan_quick(self):
        """Quick scan of most common DIDs"""
        print("\n" + "=" * 70)
        print("QUICK SCAN - Common Media Module DIDs")
        print("=" * 70)
        
        common_dids = {
            0xF190: "VIN",
            0xF18C: "ECU Serial Number",
            0xF187: "Spare Part Number",
            0xF188: "ECU Software Number",
            0xF191: "ECU Hardware Number",
            0xF192: "Supplier ID",
            0xF193: "ECU Manufacturing Date",
            0xF194: "System Supplier ID",
            0xF195: "ECU Software Version",
            0xF19E: "ASAM/ODX File Identifier",
        }
        
        for did, description in common_dids.items():
            success, data, error = self.read_did(did)
            
            if success and data:
                print(f"  ✓ 0x{did:04X} ({description}): {data}")
                self.discovered_dids[f"0x{did:04X}"] = {
                    'description': description,
                    'data': data,
                    'length': len(data) // 2
                }
            elif error == 'SECURITY_LOCKED':
                print(f"  🔒 0x{did:04X} ({description}): Security locked")
            else:
                print(f"  ✗ 0x{did:04X} ({description}): {error}")
            
            time.sleep(0.15)
    
    def scan_full(self):
        """Full scan of typical media module ranges"""
        ranges = [
            (0xF100, 0xF1FF, "Module Identification"),
            (0x3000, 0x30FF, "Audio Settings"),
            (0x3100, 0x31FF, "Radio Tuner"),
            (0x3200, 0x32FF, "Media Player"),
            (0x4000, 0x40FF, "Infotainment"),
            (0xD000, 0xD0FF, "Diagnostic Data"),
        ]
        
        for start, end, desc in ranges:
            self.scan_range(start, end, desc)
    
    def save_results(self, filename: str = None):
        """Save results to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ford_escape_acm_scan_{timestamp}.json"
        
        results = {
            'vehicle': {
                'make': 'Ford',
                'model': 'Escape',
                'year': 2008
            },
            'module': {
                'name': 'ACM',
                'description': 'Audio Control Module',
                'bus': 'MS-CAN',
                'request_address': f"0x{self.acm_request:03X}",
                'response_address': f"0x{self.acm_response:03X}"
            },
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'adapter': 'ELM327 v1.5'
            },
            'discovered_dids': self.discovered_dids
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to: {filename}")
    
    def print_summary(self):
        """Print summary"""
        print("\n" + "=" * 70)
        print("SCAN SUMMARY")
        print("=" * 70)
        
        available = len([d for d in self.discovered_dids.values() 
                        if d.get('status') == 'available'])
        locked = len([d for d in self.discovered_dids.values() 
                     if d.get('status') == 'security_locked'])
        
        print(f"\nTotal Available DIDs: {available}")
        print(f"Total Security Locked: {locked}")
        print(f"Total Discovered: {available + locked}")
        
        if available > 0:
            print("\nAvailable DIDs:")
            for did, info in sorted(self.discovered_dids.items()):
                if info.get('status') == 'available':
                    desc = info.get('description', info.get('category', ''))
                    print(f"  {did}: {desc}")
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
        print("\n✓ Disconnected")

def main():
    """Main execution"""
    scanner = MediaModuleScanner(port='COM3')
    
    if not scanner.connect():
        return
    
    try:
        print("\n" + "=" * 70)
        print("SCAN MODE")
        print("=" * 70)
        print("\n1. Quick Scan - Common DIDs (2-3 minutes)")
        print("   Tests standard module identification DIDs")
        print("\n2. Full Scan - All typical ranges (30-40 minutes)")
        print("   Scans all typical media module DID ranges")
        print("\n3. Custom Range")
        print("   Specify your own DID range")
        
        choice = input("\nSelect mode (1/2/3): ").strip()
        
        if choice == '1':
            scanner.scan_quick()
        elif choice == '2':
            scanner.scan_full()
        elif choice == '3':
            start_hex = input("Start DID (hex, e.g., 3000): ").strip()
            end_hex = input("End DID (hex, e.g., 30FF): ").strip()
            desc = input("Description: ").strip()
            start = int(start_hex, 16)
            end = int(end_hex, 16)
            scanner.scan_range(start, end, desc)
        else:
            print("Invalid choice")
            return
        
        scanner.print_summary()
        scanner.save_results()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Scan interrupted")
        scanner.print_summary()
        
        save = input("\nSave partial results? (y/n): ").strip().lower()
        if save == 'y':
            scanner.save_results()
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scanner.disconnect()

if __name__ == "__main__":
    main()
