#!/usr/bin/env python3
"""
Ford Escape 2008 - Module-Focused DID Scanner
Optimized for slower ELM327 adapters - scans only known DID ranges by module

This scanner is designed for ELM327 v1.5 adapters and focuses on:
- Known Ford DID ranges
- Module-specific parameters
- Practical diagnostic data

Author: AI Diagnostic Agent
"""

import serial
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

class FordModuleScanner:
    """
    Module-focused DID scanner optimized for ELM327 adapters
    Scans only known useful DID ranges instead of brute-forcing everything
    """
    
    def __init__(self, port: str = 'COM4', baudrate: int = 38400):
        """Initialize scanner"""
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        
        # Results storage
        self.discovered_dids: Dict[str, Dict] = {}
        self.module_results: Dict[str, List] = {
            'PCM_Engine': [],
            'PCM_Transmission': [],
            'PCM_Basic': [],
            'PCM_Engineering': []
        }
        
    def connect(self) -> bool:
        """Connect to ELM327 adapter"""
        try:
            print("=" * 70)
            print("Ford Escape 2008 - Module-Focused DID Scanner")
            print("=" * 70)
            print("\n⚠ IMPORTANT: Set adapter switch to HS-CAN position!")
            input("Press Enter when ready...")
            
            print(f"\nConnecting to {self.port}...")
            self.connection = serial.Serial(self.port, self.baudrate, timeout=3)
            time.sleep(2)
            
            # Initialize ELM327
            print("Initializing ELM327...")
            self._send_command("ATZ")  # Reset
            time.sleep(1)
            self._send_command("ATE0")  # Echo off
            self._send_command("ATL0")  # Linefeeds off
            self._send_command("ATS0")  # Spaces off
            self._send_command("ATH1")  # Headers on
            self._send_command("ATSP6")  # Set protocol ISO 15765-4 CAN (11 bit, 500 kbps)
            self._send_command("ATCAF0")  # CAN Auto Formatting off
            
            print("✓ Connected and configured")
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
    
    def read_did(self, did: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Read a single DID using UDS 0x22 service
        
        Returns:
            (success, data_hex, error_code)
        """
        # Format: 7E0 03 22 [DID_MSB] [DID_LSB]
        did_msb = (did >> 8) & 0xFF
        did_lsb = did & 0xFF
        
        cmd = f"7E0 03 22 {did_msb:02X} {did_lsb:02X}"
        response = self._send_command(cmd)
        
        # Wait for response
        time.sleep(0.15)  # Give PCM time to respond
        
        # Check for response from 7E8 (PCM response ID)
        if '7E8' in response:
            # Extract data after header
            parts = response.replace(' ', '').replace('\r', '').replace('\n', '')
            
            # Look for positive response (62 = 0x22 + 0x40)
            if '62' in parts:
                # Find the 62 and extract data after DID
                idx = parts.find('62')
                if idx != -1:
                    # Skip: 7E8, length byte, 62, DID_MSB, DID_LSB
                    data_start = idx + 2 + 4  # 62 + 2 bytes for DID
                    data = parts[data_start:]
                    return True, data, None
            
            # Check for negative response (7F)
            elif '7F' in parts:
                idx = parts.find('7F')
                if idx != -1:
                    nrc = parts[idx+4:idx+6]  # Negative Response Code
                    if nrc == '33':
                        return True, None, 'SECURITY_LOCKED'
                    elif nrc == '31':
                        return False, None, 'NOT_SUPPORTED'
                    else:
                        return False, None, f'NRC_{nrc}'
        
        return False, None, 'NO_RESPONSE'
    
    def scan_module(self, module_name: str, did_ranges: List[Tuple[int, int, str]]):
        """
        Scan specific DID ranges for a module
        
        Args:
            module_name: Name of module (e.g., "PCM_Transmission")
            did_ranges: List of (start, end, description) tuples
        """
        print(f"\n{'=' * 70}")
        print(f"Scanning Module: {module_name}")
        print(f"{'=' * 70}")
        
        total_dids = sum(end - start + 1 for start, end, _ in did_ranges)
        scanned = 0
        found = 0
        locked = 0
        
        start_time = time.time()
        
        for range_start, range_end, description in did_ranges:
            print(f"\n  Range: 0x{range_start:04X} - 0x{range_end:04X} ({description})")
            
            for did in range(range_start, range_end + 1):
                scanned += 1
                
                # Progress indicator every 16 DIDs
                if scanned % 16 == 0:
                    elapsed = time.time() - start_time
                    rate = scanned / elapsed if elapsed > 0 else 0
                    eta = (total_dids - scanned) / rate if rate > 0 else 0
                    print(f"    Progress: {scanned}/{total_dids} | "
                          f"Rate: {rate:.1f} DID/s | "
                          f"ETA: {eta/60:.1f} min | "
                          f"Found: {found} | Locked: {locked}")
                
                success, data, error = self.read_did(did)
                
                if success:
                    if error == 'SECURITY_LOCKED':
                        locked += 1
                        print(f"    🔒 0x{did:04X}: Security locked")
                        self.module_results[module_name].append({
                            'did': f"0x{did:04X}",
                            'status': 'security_locked'
                        })
                    elif data:
                        found += 1
                        print(f"    ✓ 0x{did:04X}: {data}")
                        self.module_results[module_name].append({
                            'did': f"0x{did:04X}",
                            'data': data,
                            'length': len(data) // 2,
                            'status': 'available'
                        })
                
                # Small delay between requests
                time.sleep(0.1)
        
        elapsed = time.time() - start_time
        print(f"\n  Module scan complete:")
        print(f"    Time: {elapsed/60:.1f} minutes")
        print(f"    Scanned: {scanned} DIDs")
        print(f"    Found: {found} available")
        print(f"    Locked: {locked} security-locked")
        print(f"    Rate: {scanned/elapsed:.1f} DID/s")
    
    def scan_all_modules(self):
        """Scan all known Ford module DID ranges"""
        
        # Define focused DID ranges based on Ford documentation
        modules = {
            'PCM_Basic': [
                (0x0000, 0x000F, "VIN and basic info"),
                (0x0080, 0x008F, "Calibration IDs"),
            ],
            'PCM_Engine': [
                (0x1000, 0x1020, "Engine RPM, load, timing"),
                (0x1100, 0x1110, "Fuel system"),
                (0x1200, 0x1210, "Sensors (MAF, MAP, IAT)"),
            ],
            'PCM_Transmission': [
                (0x2000, 0x2020, "Transmission status"),
                (0x2100, 0x2110, "Speed sensors"),
                (0x221E, 0x221F, "Known transmission DIDs"),
            ],
            'PCM_Engineering': [
                (0xF000, 0xF020, "Diagnostic counters"),
                (0xF100, 0xF110, "Engineering data"),
            ]
        }
        
        for module_name, ranges in modules.items():
            self.scan_module(module_name, ranges)
    
    def scan_known_dids(self):
        """Scan only the confirmed working DIDs from documentation"""
        print(f"\n{'=' * 70}")
        print("Scanning Known Working DIDs")
        print(f"{'=' * 70}")
        
        known_dids = {
            0x221E1C: "ATF Temperature",
            0x221E10: "ATF Temperature (alt)",
            0x221E14: "Turbine Speed",
            0x221E16: "Output Shaft Speed",
        }
        
        for did, description in known_dids.items():
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
            
            time.sleep(0.1)
    
    def save_results(self, filename: str = None):
        """Save scan results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ford_escape_module_scan_{timestamp}.json"
        
        results = {
            'vehicle': {
                'make': 'Ford',
                'model': 'Escape',
                'year': 2008,
                'engine': '2.3L',
                'transmission': 'CD4E'
            },
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'scan_type': 'module_focused',
                'adapter': 'ELM327 v1.5'
            },
            'modules': self.module_results,
            'known_dids': self.discovered_dids
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to: {filename}")
    
    def print_summary(self):
        """Print scan summary"""
        print("\n" + "=" * 70)
        print("SCAN SUMMARY")
        print("=" * 70)
        
        total_found = 0
        total_locked = 0
        
        for module, results in self.module_results.items():
            available = len([r for r in results if r.get('status') == 'available'])
            locked = len([r for r in results if r.get('status') == 'security_locked'])
            
            if available > 0 or locked > 0:
                print(f"\n{module}:")
                print(f"  Available: {available}")
                print(f"  Security Locked: {locked}")
                
                total_found += available
                total_locked += locked
        
        print(f"\nTotal Available DIDs: {total_found}")
        print(f"Total Security Locked: {total_locked}")
        print(f"Total Discovered: {total_found + total_locked}")
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
        print("\n✓ Disconnected")

def main():
    """Main execution"""
    scanner = FordModuleScanner(port='COM3')  # Adjust port as needed
    
    if not scanner.connect():
        return
    
    try:
        print("\n" + "=" * 70)
        print("SCAN MODE SELECTION")
        print("=" * 70)
        print("\n1. Quick Scan - Known DIDs only (2 minutes)")
        print("   Tests only the 4 confirmed working transmission DIDs")
        print("\n2. Module Scan - Focused ranges (15-20 minutes)")
        print("   Scans known useful DID ranges for each module")
        print("\n3. Custom Range")
        print("   Specify your own DID range to scan")
        
        choice = input("\nSelect mode (1/2/3): ").strip()
        
        if choice == '1':
            scanner.scan_known_dids()
        elif choice == '2':
            scanner.scan_all_modules()
        elif choice == '3':
            start_hex = input("Start DID (hex, e.g., 2000): ").strip()
            end_hex = input("End DID (hex, e.g., 2020): ").strip()
            desc = input("Description: ").strip()
            start = int(start_hex, 16)
            end = int(end_hex, 16)
            scanner.scan_module("Custom", [(start, end, desc)])
        else:
            print("Invalid choice")
            return
        
        # Print summary
        scanner.print_summary()
        
        # Save results
        scanner.save_results()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Scan interrupted by user")
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
