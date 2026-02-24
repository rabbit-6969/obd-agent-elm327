#!/usr/bin/env python3
"""
Ford Escape 2008 - Complete DID Brute Force Scanner
Scans all possible DIDs (0x0000-0xFFFF) to discover available parameters

Requirements:
- python-can
- can-isotp
- HS-CAN adapter with manual switch

Author: AI Diagnostic Agent
"""

import can
import isotp
import time
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class FordDIDScanner:
    """
    Brute-force DID scanner for Ford PCM
    Discovers all available DIDs and logs responses
    """
    
    # PCM CAN addresses
    PCM_REQUEST_ID = 0x7E0
    PCM_RESPONSE_ID = 0x7E8
    
    # UDS Service IDs
    SID_READ_DATA_BY_ID = 0x22
    SID_TESTER_PRESENT = 0x3E
    SID_DIAGNOSTIC_SESSION = 0x10
    
    # Response codes
    POSITIVE_RESPONSE = 0x62
    NEGATIVE_RESPONSE = 0x7F
    
    # Negative Response Codes
    NRC_REQUEST_OUT_OF_RANGE = 0x31
    NRC_SECURITY_ACCESS_DENIED = 0x33
    NRC_RESPONSE_PENDING = 0x78
    
    def __init__(self, interface='socketcan', channel='can0', bitrate=500000):
        """Initialize scanner"""
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus = None
        self.isotp_socket = None
        
        # Results storage
        self.valid_dids: Dict[int, bytes] = {}
        self.security_locked_dids: List[int] = []
        self.scan_stats = {
            'total_scanned': 0,
            'valid_dids': 0,
            'security_locked': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    def connect(self) -> bool:
        """Connect to CAN bus"""
        try:
            print("=" * 70)
            print("Ford Escape 2008 - DID Brute Force Scanner")
            print("=" * 70)
            print("\n⚠ IMPORTANT: Set adapter switch to HS-CAN position!")
            input("Press Enter when ready...")
            
            print(f"\nConnecting to CAN bus...")
            print(f"  Interface: {self.interface}")
            print(f"  Channel: {self.channel}")
            print(f"  Bitrate: {self.bitrate} bps")
            print(f"  PCM Request: 0x{self.PCM_REQUEST_ID:03X}")
            print(f"  PCM Response: 0x{self.PCM_RESPONSE_ID:03X}")
            
            # Create CAN bus
            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype=self.interface,
                bitrate=self.bitrate
            )
            
            # Setup ISO-TP
            addr = isotp.Address(
                isotp.AddressingMode.Normal_11bits,
                txid=self.PCM_REQUEST_ID,
                rxid=self.PCM_RESPONSE_ID
            )
            
            self.isotp_socket = isotp.socket.socket()
            self.isotp_socket.bind((self.channel, addr))
            self.isotp_socket.settimeout(0.5)  # 500ms timeout for fast scanning
            
            print("✓ Connected to PCM")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def send_uds_request(self, data: bytes) -> Optional[bytes]:
        """Send UDS request and receive response"""
        try:
            self.isotp_socket.send(data)
            response = self.isotp_socket.recv()
            return response
        except Exception:
            return None
    
    def read_did(self, did: int) -> Tuple[bool, Optional[bytes], Optional[int]]:
        """
        Read a single DID
        
        Returns:
            (success, data, nrc)
            - success: True if DID exists
            - data: Response data if positive
            - nrc: Negative Response Code if negative
        """
        did_msb = (did >> 8) & 0xFF
        did_lsb = did & 0xFF
        
        request = bytes([self.SID_READ_DATA_BY_ID, did_msb, did_lsb])
        response = self.send_uds_request(request)
        
        if not response or len(response) < 1:
            return False, None, None
        
        # Positive response
        if response[0] == self.POSITIVE_RESPONSE:
            if len(response) >= 3 and response[1] == did_msb and response[2] == did_lsb:
                return True, response[3:], None
        
        # Negative response
        elif response[0] == self.NEGATIVE_RESPONSE:
            if len(response) >= 3:
                nrc = response[2]
                
                # Security locked = DID exists but requires unlock
                if nrc == self.NRC_SECURITY_ACCESS_DENIED:
                    return True, None, nrc
                
                # Out of range = DID doesn't exist
                elif nrc == self.NRC_REQUEST_OUT_OF_RANGE:
                    return False, None, nrc
                
                # Other NRC
                else:
                    return False, None, nrc
        
        return False, None, None
    
    def scan_range(self, start: int, end: int, description: str = ""):
        """Scan a range of DIDs"""
        print(f"\n{'=' * 70}")
        print(f"Scanning Range: 0x{start:04X} - 0x{end:04X}")
        if description:
            print(f"Purpose: {description}")
        print(f"{'=' * 70}")
        
        range_start_time = time.time()
        range_valid = 0
        range_locked = 0
        
        for did in range(start, end + 1):
            self.scan_stats['total_scanned'] += 1
            
            # Send tester present every 50 DIDs
            if did % 50 == 0:
                self.send_uds_request(bytes([self.SID_TESTER_PRESENT, 0x00]))
            
            # Read DID
            success, data, nrc = self.read_did(did)
            
            if success:
                if nrc == self.NRC_SECURITY_ACCESS_DENIED:
                    # Security locked
                    self.security_locked_dids.append(did)
                    self.scan_stats['security_locked'] += 1
                    range_locked += 1
                    print(f"  🔒 0x{did:04X}: Security locked")
                else:
                    # Valid DID
                    self.valid_dids[did] = data
                    self.scan_stats['valid_dids'] += 1
                    range_valid += 1
                    data_hex = data.hex() if data else "no data"
                    print(f"  ✓ 0x{did:04X}: {data_hex}")
            
            # Progress indicator every 256 DIDs
            if (did - start) % 256 == 0 and did != start:
                elapsed = time.time() - range_start_time
                progress = ((did - start) / (end - start + 1)) * 100
                rate = (did - start) / elapsed if elapsed > 0 else 0
                eta = ((end - did) / rate) if rate > 0 else 0
                
                print(f"\n  Progress: {progress:.1f}% | "
                      f"Rate: {rate:.1f} DID/s | "
                      f"ETA: {eta/60:.1f} min | "
                      f"Found: {range_valid} valid, {range_locked} locked\n")
            
            # Small delay to avoid overwhelming PCM
            time.sleep(0.05)  # 50ms between requests = ~20 req/sec
        
        # Range summary
        elapsed = time.time() - range_start_time
        print(f"\n{'=' * 70}")
        print(f"Range Complete: 0x{start:04X} - 0x{end:04X}")
        print(f"  Time: {elapsed/60:.1f} minutes")
        print(f"  Valid DIDs: {range_valid}")
        print(f"  Security Locked: {range_locked}")
        print(f"  Rate: {(end - start + 1)/elapsed:.1f} DID/s")
        print(f"{'=' * 70}")
    
    def scan_priority_ranges(self):
        """Scan priority ranges first (most likely to have data)"""
        print("\n" + "=" * 70)
        print("PRIORITY SCAN - Most Likely Ranges")
        print("=" * 70)
        
        priority_ranges = [
            (0x0000, 0x00FF, "Basic info, VIN, calibration"),
            (0x2000, 0x2FFF, "Transmission data (CD4E)"),
            (0x1000, 0x1FFF, "Engine data"),
            (0xF000, 0xF3FF, "Engineering data"),
        ]
        
        for start, end, desc in priority_ranges:
            self.scan_range(start, end, desc)
    
    def scan_full(self):
        """Scan entire DID space (0x0000-0xFFFF)"""
        print("\n" + "=" * 70)
        print("FULL SCAN - All Possible DIDs")
        print("=" * 70)
        print("\n⚠ This will take approximately 55-90 minutes")
        print("  Press Ctrl+C to stop at any time")
        input("\nPress Enter to start full scan...")
        
        self.scan_range(0x0000, 0xFFFF, "Complete DID space")
    
    def save_results(self, filename: str = None):
        """Save scan results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ford_escape_dids_{timestamp}.json"
        
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
                'duration_minutes': (self.scan_stats['end_time'] - self.scan_stats['start_time']) / 60 
                    if self.scan_stats['end_time'] else 0,
                'statistics': self.scan_stats
            },
            'valid_dids': {
                f"0x{did:04X}": {
                    'data_hex': data.hex(),
                    'data_length': len(data),
                    'data_bytes': list(data)
                }
                for did, data in self.valid_dids.items()
            },
            'security_locked_dids': [f"0x{did:04X}" for did in self.security_locked_dids]
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to: {filename}")
    
    def print_summary(self):
        """Print scan summary"""
        print("\n" + "=" * 70)
        print("SCAN SUMMARY")
        print("=" * 70)
        
        duration = (self.scan_stats['end_time'] - self.scan_stats['start_time']) / 60 \
            if self.scan_stats['end_time'] else 0
        
        print(f"\nTotal DIDs Scanned: {self.scan_stats['total_scanned']}")
        print(f"Valid DIDs Found: {self.scan_stats['valid_dids']}")
        print(f"Security Locked DIDs: {self.scan_stats['security_locked']}")
        print(f"Scan Duration: {duration:.1f} minutes")
        print(f"Average Rate: {self.scan_stats['total_scanned']/duration/60:.1f} DID/s")
        
        if self.valid_dids:
            print(f"\n{'=' * 70}")
            print("VALID DIDs BY RANGE")
            print(f"{'=' * 70}")
            
            ranges = {
                'Basic Info (0x0000-0x00FF)': [],
                'Engine Data (0x1000-0x1FFF)': [],
                'Transmission Data (0x2000-0x2FFF)': [],
                'Engineering Data (0xF000-0xF3FF)': [],
                'Other': []
            }
            
            for did in sorted(self.valid_dids.keys()):
                if 0x0000 <= did <= 0x00FF:
                    ranges['Basic Info (0x0000-0x00FF)'].append(did)
                elif 0x1000 <= did <= 0x1FFF:
                    ranges['Engine Data (0x1000-0x1FFF)'].append(did)
                elif 0x2000 <= did <= 0x2FFF:
                    ranges['Transmission Data (0x2000-0x2FFF)'].append(did)
                elif 0xF000 <= did <= 0xF3FF:
                    ranges['Engineering Data (0xF000-0xF3FF)'].append(did)
                else:
                    ranges['Other'].append(did)
            
            for range_name, dids in ranges.items():
                if dids:
                    print(f"\n{range_name}: {len(dids)} DIDs")
                    for did in dids:
                        data = self.valid_dids[did]
                        print(f"  0x{did:04X}: {data.hex()}")
    
    def disconnect(self):
        """Close connections"""
        if self.isotp_socket:
            self.isotp_socket.close()
        if self.bus:
            self.bus.shutdown()
        print("\n✓ Disconnected")

def main():
    """Main execution"""
    scanner = FordDIDScanner(
        interface='socketcan',  # Adjust for your system
        channel='can0',         # Adjust for your adapter
        bitrate=500000
    )
    
    if not scanner.connect():
        return
    
    try:
        scanner.scan_stats['start_time'] = time.time()
        
        print("\n" + "=" * 70)
        print("SCAN MODE SELECTION")
        print("=" * 70)
        print("\n1. Priority Scan (recommended first run)")
        print("   Scans most likely ranges: 0x0000-0x00FF, 0x1000-0x2FFF, 0xF000-0xF3FF")
        print("   Duration: ~15-20 minutes")
        print("\n2. Full Scan")
        print("   Scans all possible DIDs: 0x0000-0xFFFF")
        print("   Duration: ~55-90 minutes")
        print("\n3. Custom Range")
        print("   Specify start and end DID")
        
        choice = input("\nSelect mode (1/2/3): ").strip()
        
        if choice == '1':
            scanner.scan_priority_ranges()
        elif choice == '2':
            scanner.scan_full()
        elif choice == '3':
            start_hex = input("Start DID (hex, e.g., 2000): ").strip()
            end_hex = input("End DID (hex, e.g., 2FFF): ").strip()
            start = int(start_hex, 16)
            end = int(end_hex, 16)
            scanner.scan_range(start, end, "Custom range")
        else:
            print("Invalid choice")
            return
        
        scanner.scan_stats['end_time'] = time.time()
        
        # Print summary
        scanner.print_summary()
        
        # Save results
        scanner.save_results()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Scan interrupted by user")
        scanner.scan_stats['end_time'] = time.time()
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
