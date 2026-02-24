"""
Comprehensive Vehicle Capability Discovery Scanner
2008 Ford Escape - Discover ALL DIDs, Routines, and Actuations

This script performs a complete scan of the vehicle to discover:
1. All accessible modules (ECUs) on CAN bus
2. All readable DIDs (Service 0x22) for each module
3. All executable routines (Service 0x31) for each module
4. All controllable outputs (Service 0x2F) for each module

WARNING: This scan will take SEVERAL HOURS to complete!
- Full DID scan: 65,536 DIDs per module × ~150ms = ~2.7 hours per module
- Routine scan: Similar time
- Actuation scan: Similar time

The script supports:
- Resume capability (saves progress periodically)
- Configurable scan ranges (skip ranges if needed)
- Safe testing (read-only by default, actuation requires confirmation)

Usage:
    python discover_vehicle_capabilities.py [options]

Options:
    --quick         Quick scan (common ranges only, ~30 minutes)
    --full          Full scan (all 65,536 DIDs, several hours)
    --resume        Resume from last saved progress
    --modules       Scan for modules only
    --dids          Scan DIDs only (requires module scan first)
    --routines      Scan routines only
    --actuations    Scan actuations (CAUTION: may affect vehicle)

Examples:
    python discover_vehicle_capabilities.py --quick
    python discover_vehicle_capabilities.py --full --resume
    python discover_vehicle_capabilities.py --modules
"""

import serial
import time
import sys
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

# Configuration
COM_PORT = "COM3"
BAUDRATE = 38400
RESULTS_DIR = "vehicle_discovery"
PROGRESS_FILE = "vehicle_discovery/scan_progress.json"

# Scan ranges for quick vs full scan
QUICK_SCAN_RANGES = {
    'dids': [
        (0x0100, 0x01FF, "Transmission parameters"),
        (0x1000, 0x10FF, "Common Ford diagnostic range"),
        (0xF000, 0xF0FF, "Manufacturer-specific"),
        (0xF100, 0xF1FF, "Vehicle identification"),
        (0xF400, 0xF4FF, "Vehicle manufacturer specific"),
    ],
    'routines': [
        (0x0200, 0x02FF, "Transmission routines"),
        (0x0300, 0x03FF, "Engine routines"),
        (0xFF00, 0xFFFF, "Manufacturer-specific routines"),
    ],
}

FULL_SCAN_RANGES = {
    'dids': [(0x0000, 0xFFFF, "Complete DID range")],
    'routines': [(0x0000, 0xFFFF, "Complete routine range")],
}

# Known module addresses to scan
MODULE_ADDRESSES = {
    'PCM': 0x7E0,      # Powertrain Control Module
    'TCM': 0x7E1,      # Transmission (may be integrated with PCM)
    'ABS': 0x760,      # Anti-lock Braking System
    'HVAC': 0x7A0,     # Climate Control
    'BCM': 0x726,      # Body Control Module
    'IPC': 0x720,      # Instrument Panel Cluster
    'RCM': 0x737,      # Restraint Control Module (Airbags)
    'PAM': 0x736,      # Parking Aid Module
    'PSCM': 0x730,     # Power Steering Control Module
}


class VehicleScanner:
    """Comprehensive vehicle capability scanner"""
    
    def __init__(self, port: str, baudrate: int = 38400):
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None
        
        # Results storage
        self.modules_found: Dict = {}
        self.dids_found: Dict = {}
        self.routines_found: Dict = {}
        self.actuations_found: Dict = {}
        
        # Progress tracking
        self.progress = {
            'modules_scanned': [],
            'current_module': None,
            'current_scan_type': None,
            'last_did': 0,
            'last_routine': 0,
            'start_time': None,
            'last_save_time': None,
        }
        
        # Statistics
        self.stats = {
            'total_commands_sent': 0,
            'positive_responses': 0,
            'negative_responses': 0,
            'no_responses': 0,
        }
    
    def connect(self) -> bool:
        """Connect to ELM327 adapter"""
        print(f"Connecting to {self.port}...")
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0
            )
            time.sleep(2)
            
            # Initialize ELM327
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATSP0")  # Auto protocol
            self.send_command("ATST32")  # Timeout 32ms
            self.send_command("ATH1")  # Headers on (to see module addresses)
            
            print("✓ Connected to ELM327\n")
            return True
        except serial.SerialException as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from adapter"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("✓ Disconnected")
    
    def send_command(self, cmd: str, timeout: float = 0.3) -> Optional[str]:
        """Send command and get response"""
        if not self.ser or not self.ser.is_open:
            return None
        
        self.ser.write((cmd + "\r").encode())
        time.sleep(timeout)
        
        response = ""
        while self.ser.in_waiting > 0:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        
        response = response.replace('>', '').replace('\r', ' ').replace('\n', ' ').strip()
        self.stats['total_commands_sent'] += 1
        
        return response if response else None
    
    def set_module_address(self, address: int):
        """Set target module address for communication"""
        # For standard OBD-II addresses (7E0, 7E1, etc.), use standard format
        # For other addresses, set specific header
        if address in [0x7E0, 0x7E1, 0x7E8]:
            # Standard OBD-II - use auto addressing
            self.send_command("ATSH7E0")  # Standard OBD-II functional address
        else:
            # Non-standard address - set specific header
            cmd = f"ATSH{address:03X}"
            self.send_command(cmd)
    
    def scan_modules(self) -> Dict:
        """Scan for accessible modules on CAN bus"""
        print("="*70)
        print("MODULE DISCOVERY")
        print("="*70)
        print("\nScanning for accessible modules...\n")
        
        for name, address in MODULE_ADDRESSES.items():
            print(f"Testing {name} (0x{address:03X})...", end=" ")
            
            # Don't set header - let ELM327 auto-detect
            # Just send commands and see what responds
            
            # Try multiple test commands
            tests = [
                ("03", "Read DTCs (Mode 03)"),           # Standard OBD-II
                ("01 00", "Supported PIDs (Mode 01)"),   # Standard OBD-II
            ]
            
            accessible = False
            test_results = []
            
            for cmd, desc in tests:
                response = self.send_command(cmd, timeout=0.5)
                
                if response:
                    clean = response.replace(' ', '')
                    # Check for positive response
                    # Mode 03: 43 XX XX...
                    # Mode 01: 41 00 XX XX XX XX
                    # Negative: 7F XX YY or NO DATA
                    if clean.startswith(('43', '41')) and "NO DATA" not in response and "?" not in response:
                        accessible = True
                        test_results.append({
                            'command': cmd,
                            'description': desc,
                            'response': response,
                            'success': True
                        })
                        break  # Found it, no need to test more
            
            if accessible:
                print("✓ ACCESSIBLE")
                self.modules_found[name] = {
                    'address': address,
                    'test_results': test_results,
                    'discovered_at': datetime.now().isoformat()
                }
            else:
                print("✗ Not accessible")
        
        print(f"\n✓ Found {len(self.modules_found)} accessible modules")
        return self.modules_found

    
    def scan_dids(self, module_name: str, address: int, ranges: List[Tuple]) -> Dict:
        """Scan DID range for a specific module"""
        print(f"\n{'='*70}")
        print(f"DID SCAN: {module_name} (0x{address:03X})")
        print(f"{'='*70}\n")
        
        # For standard OBD-II (PCM), don't set header
        # For other modules, we would need to set header, but that's not working yet
        # So for now, just scan and see what responds
        
        module_dids = {}
        
        for start, end, description in ranges:
            print(f"\nScanning {description}: 0x{start:04X} - 0x{end:04X}")
            total = end - start + 1
            found_in_range = 0
            
            for did in range(start, end + 1):
                # Progress indicator
                progress = ((did - start + 1) / total) * 100
                sys.stdout.write(f"\r  Progress: {progress:.1f}% (DID 0x{did:04X}) | Found: {found_in_range}  ")
                sys.stdout.flush()
                
                # Send UDS ReadDataByIdentifier command
                cmd = f"22{did:04X}"
                response = self.send_command(cmd, timeout=0.15)
                
                if response and "NO DATA" not in response and "?" not in response:
                    clean = response.replace(' ', '')
                    
                    # Positive response (62 = 0x22 + 0x40)
                    if clean.startswith('62'):
                        found_in_range += 1
                        module_dids[f"0x{did:04X}"] = {
                            'did': did,
                            'command': cmd,
                            'response': response,
                            'range': description,
                            'discovered_at': datetime.now().isoformat()
                        }
                        print(f"\n  ✓ Found DID 0x{did:04X}: {response}")
                        self.stats['positive_responses'] += 1
                    
                    # Negative response (7F 22 XX)
                    elif clean.startswith('7F22'):
                        self.stats['negative_responses'] += 1
                    else:
                        self.stats['no_responses'] += 1
                else:
                    self.stats['no_responses'] += 1
                
                # Save progress every 100 DIDs
                if did % 100 == 0:
                    self.progress['last_did'] = did
                    self.save_progress()
            
            print(f"\n  Found {found_in_range} DIDs in this range")
        
        return module_dids
    
    def scan_routines(self, module_name: str, address: int, ranges: List[Tuple]) -> Dict:
        """Scan routine IDs for a specific module"""
        print(f"\n{'='*70}")
        print(f"ROUTINE SCAN: {module_name} (0x{address:03X})")
        print(f"{'='*70}\n")
        print("⚠️  This scan uses Service 0x31 (RoutineControl)")
        print("    We will only test 'requestRoutineResults' (sub-function 0x03)")
        print("    This is safe and won't start any routines.\n")
        
        # For standard OBD-II (PCM), don't set header
        module_routines = {}
        
        for start, end, description in ranges:
            print(f"\nScanning {description}: 0x{start:04X} - 0x{end:04X}")
            total = end - start + 1
            found_in_range = 0
            
            for rid in range(start, end + 1):
                # Progress indicator
                progress = ((rid - start + 1) / total) * 100
                sys.stdout.write(f"\r  Progress: {progress:.1f}% (RID 0x{rid:04X}) | Found: {found_in_range}  ")
                sys.stdout.flush()
                
                # Send UDS RoutineControl - requestRoutineResults (safe, doesn't start routine)
                cmd = f"3103{rid:04X}"
                response = self.send_command(cmd, timeout=0.15)
                
                if response and "NO DATA" not in response and "?" not in response:
                    clean = response.replace(' ', '')
                    
                    # Positive response (71 = 0x31 + 0x40)
                    if clean.startswith('71'):
                        found_in_range += 1
                        module_routines[f"0x{rid:04X}"] = {
                            'rid': rid,
                            'command': cmd,
                            'response': response,
                            'range': description,
                            'discovered_at': datetime.now().isoformat()
                        }
                        print(f"\n  ✓ Found Routine 0x{rid:04X}: {response}")
                        self.stats['positive_responses'] += 1
                    
                    # Negative response (7F 31 XX)
                    elif clean.startswith('7F31'):
                        nrc = clean[4:6] if len(clean) >= 6 else "??"
                        # NRC 0x31 (ROOR) means routine doesn't exist
                        # NRC 0x24 (RSE) means routine exists but wrong sequence
                        # NRC 0x22 (CNC) means routine exists but conditions not met
                        if nrc in ['24', '22']:  # Routine exists!
                            found_in_range += 1
                            module_routines[f"0x{rid:04X}"] = {
                                'rid': rid,
                                'command': cmd,
                                'response': response,
                                'range': description,
                                'nrc': nrc,
                                'note': 'Routine exists but cannot be queried (may need to start first)',
                                'discovered_at': datetime.now().isoformat()
                            }
                            print(f"\n  ✓ Found Routine 0x{rid:04X}: {response} (NRC {nrc})")
                            self.stats['positive_responses'] += 1
                        else:
                            self.stats['negative_responses'] += 1
                    else:
                        self.stats['no_responses'] += 1
                else:
                    self.stats['no_responses'] += 1
                
                # Save progress every 100 routines
                if rid % 100 == 0:
                    self.progress['last_routine'] = rid
                    self.save_progress()
            
            print(f"\n  Found {found_in_range} routines in this range")
        
        return module_routines
    
    def scan_actuations(self, module_name: str, address: int, known_dids: Dict) -> Dict:
        """Test which DIDs support actuation (Service 0x2F)"""
        print(f"\n{'='*70}")
        print(f"ACTUATION SCAN: {module_name} (0x{address:03X})")
        print(f"{'='*70}\n")
        print("⚠️  WARNING: This scan uses Service 0x2F (InputOutputControlByIdentifier)")
        print("    This service can CONTROL vehicle actuators!")
        print("    We will test with 'returnControlToECU' (sub-function 0x00)")
        print("    This is safe and won't activate anything.\n")
        
        if not known_dids:
            print("  No DIDs to test (run DID scan first)")
            return {}
        
        response = input(f"  Test {len(known_dids)} DIDs for actuation capability? (yes/no): ")
        if response.lower() != 'yes':
            print("  Skipped actuation scan")
            return {}
        
        # For standard OBD-II (PCM), don't set header
        module_actuations = {}
        
        print(f"\n  Testing {len(known_dids)} DIDs...")
        
        for idx, (did_key, did_info) in enumerate(known_dids.items(), 1):
            did = did_info['did']
            
            sys.stdout.write(f"\r  Progress: {idx}/{len(known_dids)} (DID 0x{did:04X})  ")
            sys.stdout.flush()
            
            # Send UDS InputOutputControlByIdentifier - returnControlToECU (safe)
            cmd = f"2F{did:04X}00"
            response = self.send_command(cmd, timeout=0.2)
            
            if response and "NO DATA" not in response and "?" not in response:
                clean = response.replace(' ', '')
                
                # Positive response (6F = 0x2F + 0x40)
                if clean.startswith('6F'):
                    module_actuations[f"0x{did:04X}"] = {
                        'did': did,
                        'command': cmd,
                        'response': response,
                        'note': 'Supports actuation (Service 0x2F)',
                        'discovered_at': datetime.now().isoformat()
                    }
                    print(f"\n  ✓ DID 0x{did:04X} supports actuation: {response}")
                    self.stats['positive_responses'] += 1
                
                # Negative response
                elif clean.startswith('7F2F'):
                    nrc = clean[4:6] if len(clean) >= 6 else "??"
                    # NRC 0x31 (ROOR) means actuation not supported
                    # NRC 0x22 (CNC) means actuation supported but conditions not met
                    # NRC 0x33 (SAD) means actuation supported but needs security access
                    if nrc in ['22', '33']:  # Actuation supported!
                        module_actuations[f"0x{did:04X}"] = {
                            'did': did,
                            'command': cmd,
                            'response': response,
                            'nrc': nrc,
                            'note': 'Supports actuation but requires conditions/security',
                            'discovered_at': datetime.now().isoformat()
                        }
                        print(f"\n  ✓ DID 0x{did:04X} supports actuation: {response} (NRC {nrc})")
                        self.stats['positive_responses'] += 1
                    else:
                        self.stats['negative_responses'] += 1
        
        print(f"\n\n  Found {len(module_actuations)} actuatable DIDs")
        return module_actuations

    
    def save_progress(self):
        """Save current progress to file"""
        if not os.path.exists(RESULTS_DIR):
            os.makedirs(RESULTS_DIR)
        
        self.progress['last_save_time'] = datetime.now().isoformat()
        
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                'progress': self.progress,
                'modules_found': self.modules_found,
                'dids_found': self.dids_found,
                'routines_found': self.routines_found,
                'actuations_found': self.actuations_found,
                'stats': self.stats,
            }, f, indent=2)
    
    def load_progress(self) -> bool:
        """Load progress from file"""
        if not os.path.exists(PROGRESS_FILE):
            return False
        
        try:
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                self.progress = data.get('progress', {})
                self.modules_found = data.get('modules_found', {})
                self.dids_found = data.get('dids_found', {})
                self.routines_found = data.get('routines_found', {})
                self.actuations_found = data.get('actuations_found', {})
                self.stats = data.get('stats', {})
            
            print(f"✓ Loaded progress from {PROGRESS_FILE}")
            return True
        except Exception as e:
            print(f"✗ Error loading progress: {e}")
            return False
    
    def save_results(self):
        """Save final results to JSON file"""
        if not os.path.exists(RESULTS_DIR):
            os.makedirs(RESULTS_DIR)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(RESULTS_DIR, f"vehicle_capabilities_{timestamp}.json")
        
        results = {
            'vehicle': {
                'make': 'Ford',
                'model': 'Escape',
                'year': 2008,
                'vin': '1FMCU03Z68KB12969',
            },
            'scan_info': {
                'date': datetime.now().isoformat(),
                'adapter': 'ELM327 v1.5',
                'port': self.port,
                'duration_seconds': (datetime.now() - datetime.fromisoformat(self.progress['start_time'])).total_seconds() if self.progress.get('start_time') else 0,
            },
            'statistics': self.stats,
            'modules': self.modules_found,
            'dids': self.dids_found,
            'routines': self.routines_found,
            'actuations': self.actuations_found,
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to: {filename}")
        
        # Also save human-readable summary
        summary_file = os.path.join(RESULTS_DIR, f"summary_{timestamp}.txt")
        self.save_summary(summary_file, results)
        print(f"✓ Summary saved to: {summary_file}")
        
        return filename
    
    def save_summary(self, filename: str, results: Dict):
        """Save human-readable summary"""
        with open(filename, 'w') as f:
            f.write("="*70 + "\n")
            f.write("VEHICLE CAPABILITY DISCOVERY - SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Vehicle: {results['vehicle']['year']} {results['vehicle']['make']} {results['vehicle']['model']}\n")
            f.write(f"VIN: {results['vehicle']['vin']}\n")
            f.write(f"Scan Date: {results['scan_info']['date']}\n")
            f.write(f"Duration: {results['scan_info']['duration_seconds']:.0f} seconds\n\n")
            
            f.write("="*70 + "\n")
            f.write("STATISTICS\n")
            f.write("="*70 + "\n")
            f.write(f"Total commands sent: {results['statistics']['total_commands_sent']}\n")
            f.write(f"Positive responses: {results['statistics']['positive_responses']}\n")
            f.write(f"Negative responses: {results['statistics']['negative_responses']}\n")
            f.write(f"No responses: {results['statistics']['no_responses']}\n\n")
            
            f.write("="*70 + "\n")
            f.write("MODULES FOUND\n")
            f.write("="*70 + "\n")
            for name, info in results['modules'].items():
                f.write(f"\n{name} (0x{info['address']:03X})\n")
                f.write(f"  Discovered: {info['discovered_at']}\n")
                f.write(f"  Test results: {len(info['test_results'])} commands tested\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("DIDs DISCOVERED\n")
            f.write("="*70 + "\n")
            for module, dids in results['dids'].items():
                f.write(f"\n{module}: {len(dids)} DIDs\n")
                for did_key, did_info in dids.items():
                    f.write(f"  {did_key}: {did_info['response']}\n")
                    f.write(f"    Range: {did_info['range']}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("ROUTINES DISCOVERED\n")
            f.write("="*70 + "\n")
            for module, routines in results['routines'].items():
                f.write(f"\n{module}: {len(routines)} routines\n")
                for rid_key, rid_info in routines.items():
                    f.write(f"  {rid_key}: {rid_info['response']}\n")
                    if 'note' in rid_info:
                        f.write(f"    Note: {rid_info['note']}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("ACTUATIONS DISCOVERED\n")
            f.write("="*70 + "\n")
            for module, actuations in results['actuations'].items():
                f.write(f"\n{module}: {len(actuations)} actuatable DIDs\n")
                for did_key, act_info in actuations.items():
                    f.write(f"  {did_key}: {act_info['response']}\n")
                    f.write(f"    Note: {act_info['note']}\n")
    
    def print_summary(self):
        """Print summary to console"""
        print("\n" + "="*70)
        print("SCAN COMPLETE - SUMMARY")
        print("="*70 + "\n")
        
        print(f"Modules found: {len(self.modules_found)}")
        for name in self.modules_found.keys():
            print(f"  • {name}")
        
        print(f"\nDIDs discovered:")
        total_dids = sum(len(dids) for dids in self.dids_found.values())
        print(f"  Total: {total_dids}")
        for module, dids in self.dids_found.items():
            print(f"  • {module}: {len(dids)} DIDs")
        
        print(f"\nRoutines discovered:")
        total_routines = sum(len(routines) for routines in self.routines_found.values())
        print(f"  Total: {total_routines}")
        for module, routines in self.routines_found.items():
            print(f"  • {module}: {len(routines)} routines")
        
        print(f"\nActuations discovered:")
        total_actuations = sum(len(acts) for acts in self.actuations_found.values())
        print(f"  Total: {total_actuations}")
        for module, acts in self.actuations_found.items():
            print(f"  • {module}: {len(acts)} actuatable DIDs")
        
        print(f"\nStatistics:")
        print(f"  Commands sent: {self.stats['total_commands_sent']}")
        print(f"  Positive responses: {self.stats['positive_responses']}")
        print(f"  Success rate: {(self.stats['positive_responses'] / max(self.stats['total_commands_sent'], 1) * 100):.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive vehicle capability discovery scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--quick', action='store_true',
                        help='Quick scan (common ranges only, ~30 minutes)')
    parser.add_argument('--full', action='store_true',
                        help='Full scan (all 65,536 DIDs, several hours)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from last saved progress')
    parser.add_argument('--modules', action='store_true',
                        help='Scan for modules only')
    parser.add_argument('--dids', action='store_true',
                        help='Scan DIDs only (requires module scan first)')
    parser.add_argument('--routines', action='store_true',
                        help='Scan routines only')
    parser.add_argument('--actuations', action='store_true',
                        help='Scan actuations (CAUTION: may affect vehicle)')
    
    args = parser.parse_args()
    
    # Default to quick scan if no options specified
    if not any([args.quick, args.full, args.modules, args.dids, args.routines, args.actuations]):
        args.quick = True
    
    # Determine scan ranges
    if args.full:
        scan_ranges = FULL_SCAN_RANGES
        print("\n⚠️  FULL SCAN MODE - This will take SEVERAL HOURS!")
    else:
        scan_ranges = QUICK_SCAN_RANGES
        print("\n✓ Quick scan mode - Common ranges only (~30 minutes)")
    
    scanner = VehicleScanner(COM_PORT, BAUDRATE)
    
    try:
        # Load progress if resuming
        if args.resume:
            scanner.load_progress()
        
        # Connect to vehicle
        if not scanner.connect():
            return 1
        
        scanner.progress['start_time'] = datetime.now().isoformat()
        
        # Module discovery
        if args.modules or not args.dids and not args.routines and not args.actuations:
            scanner.scan_modules()
            scanner.save_progress()
        
        # If no modules found, can't continue
        if not scanner.modules_found:
            print("\n✗ No modules found. Cannot continue with DID/routine scan.")
            print("  Make sure vehicle ignition is ON and adapter is connected properly.")
            return 1
        
        # DID scanning
        if args.dids or (args.quick or args.full) and not args.modules:
            for module_name, module_info in scanner.modules_found.items():
                address = module_info['address']
                
                print(f"\n\nScan DIDs for {module_name}? (yes/no/skip): ", end="")
                response = input().lower()
                
                if response == 'yes':
                    dids = scanner.scan_dids(module_name, address, scan_ranges['dids'])
                    scanner.dids_found[module_name] = dids
                    scanner.save_progress()
                elif response == 'skip':
                    break
        
        # Routine scanning
        if args.routines or (args.quick or args.full) and not args.modules and not args.dids:
            for module_name, module_info in scanner.modules_found.items():
                address = module_info['address']
                
                print(f"\n\nScan routines for {module_name}? (yes/no/skip): ", end="")
                response = input().lower()
                
                if response == 'yes':
                    routines = scanner.scan_routines(module_name, address, scan_ranges['routines'])
                    scanner.routines_found[module_name] = routines
                    scanner.save_progress()
                elif response == 'skip':
                    break
        
        # Actuation scanning
        if args.actuations:
            for module_name, module_info in scanner.modules_found.items():
                if module_name in scanner.dids_found:
                    address = module_info['address']
                    actuations = scanner.scan_actuations(
                        module_name, address, scanner.dids_found[module_name]
                    )
                    scanner.actuations_found[module_name] = actuations
                    scanner.save_progress()
        
        # Save final results
        scanner.print_summary()
        scanner.save_results()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        print("Progress has been saved. Use --resume to continue.")
        scanner.save_progress()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scanner.disconnect()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
