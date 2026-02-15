"""
Scan for Transmission DIDs - 2008 Ford Escape

This script systematically scans UDS Data Identifiers (DIDs) to discover
all available transmission parameters in the PCM.

Usage:
1. Make sure vehicle ignition is ON (engine running is better)
2. Run: python scan_transmission_dids.py
3. Script will scan DID ranges and report what works
4. Results saved to logs/did_scan_[timestamp].txt

Scan Strategy:
- Start with 0x0100-0x01FF (likely transmission range)
- Then try 0x1000-0x10FF (common Ford range)
- Then try 0xF000-0xF0FF (manufacturer-specific range)

This will take 5-10 minutes depending on range.
"""

import serial
import time
import sys
from datetime import datetime
import os

# Configuration
COM_PORT = "COM3"
BAUDRATE = 38400
LOG_DIR = "logs"

class DIDScanner:
    def __init__(self, port, baudrate=38400):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.found_dids = []
    
    def connect(self):
        """Connect to ELM327 adapter"""
        print(f"Connecting to {self.port}...")
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0  # Shorter timeout for scanning
            )
            time.sleep(2)
            
            # Initialize
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")
            self.send_command("ATL0")
            self.send_command("ATSP0")
            self.send_command("ATST32")  # Set timeout to 32ms for faster scanning
            
            print("✓ Connected to ELM327\n")
            return True
        except serial.SerialException as e:
            print(f"✗ Error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from adapter"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def send_command(self, cmd):
        """Send command and get response"""
        if not self.ser or not self.ser.is_open:
            return None
        
        self.ser.write((cmd + "\r").encode())
        time.sleep(0.15)  # Shorter delay for scanning
        
        response = ""
        while self.ser.in_waiting > 0:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.05)
        
        response = response.replace('>', '').replace('\r', ' ').replace('\n', ' ').strip()
        return response if response else None
    
    def try_did(self, did):
        """Try reading a specific DID"""
        cmd = f"22{did:04X}"
        response = self.send_command(cmd)
        
        if response and "NO DATA" not in response and "?" not in response:
            # Check if it's a positive response (starts with 62)
            clean_response = response.replace(' ', '')
            if clean_response.startswith('62'):
                return True, response
            # Check for negative response (7F 22 XX)
            elif clean_response.startswith('7F22'):
                return False, response
        
        return False, None
    
    def scan_range(self, start_did, end_did, description=""):
        """Scan a range of DIDs"""
        print(f"\n{'='*70}")
        print(f"Scanning DID Range: 0x{start_did:04X} - 0x{end_did:04X}")
        if description:
            print(f"Description: {description}")
        print(f"{'='*70}\n")
        
        found_in_range = []
        total = end_did - start_did + 1
        
        for did in range(start_did, end_did + 1):
            # Progress indicator
            progress = ((did - start_did + 1) / total) * 100
            sys.stdout.write(f"\rProgress: {progress:.1f}% (DID 0x{did:04X})  ")
            sys.stdout.flush()
            
            success, response = self.try_did(did)
            
            if success:
                print(f"\n✓ Found: DID 0x{did:04X} → {response}")
                found_in_range.append({
                    'did': did,
                    'response': response
                })
                self.found_dids.append({
                    'did': did,
                    'response': response,
                    'range': description
                })
        
        print(f"\n\nFound {len(found_in_range)} DIDs in this range")
        return found_in_range
    
    def scan_all(self):
        """Scan all interesting DID ranges"""
        print("="*70)
        print("UDS DID Scanner - 2008 Ford Escape Transmission")
        print("="*70)
        print("\nThis will scan multiple DID ranges to discover transmission parameters.")
        print("Estimated time: 5-10 minutes")
        print("\nPress Ctrl+C to stop at any time\n")
        
        input("Press Enter to start scanning...")
        
        # Range 1: 0x0100-0x01FF (likely transmission parameters)
        self.scan_range(0x0100, 0x01FF, "Transmission parameters (likely range)")
        
        # Range 2: 0x1000-0x10FF (common Ford range)
        print("\n\nContinue to next range? (Press Enter or Ctrl+C to stop)")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nScan stopped by user")
            return
        
        self.scan_range(0x1000, 0x10FF, "Common Ford diagnostic range")
        
        # Range 3: 0xF000-0xF0FF (manufacturer-specific)
        print("\n\nContinue to next range? (Press Enter or Ctrl+C to stop)")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nScan stopped by user")
            return
        
        self.scan_range(0xF000, 0xF0FF, "Manufacturer-specific range")
    
    def save_results(self):
        """Save scan results to file"""
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(LOG_DIR, f"did_scan_{timestamp}.txt")
        
        with open(filename, 'w') as f:
            f.write("="*70 + "\n")
            f.write("UDS DID Scan Results - 2008 Ford Escape\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Total DIDs Found: {len(self.found_dids)}\n\n")
            
            if self.found_dids:
                f.write("Found DIDs:\n")
                f.write("-"*70 + "\n")
                for item in self.found_dids:
                    f.write(f"DID: 0x{item['did']:04X}\n")
                    f.write(f"Response: {item['response']}\n")
                    if item['range']:
                        f.write(f"Range: {item['range']}\n")
                    f.write("-"*70 + "\n")
            else:
                f.write("No DIDs found in scanned ranges.\n")
        
        print(f"\n✓ Results saved to: {filename}")
        return filename
    
    def print_summary(self):
        """Print summary of findings"""
        print("\n" + "="*70)
        print("Scan Complete - Summary")
        print("="*70 + "\n")
        
        if self.found_dids:
            print(f"✓ Found {len(self.found_dids)} working DIDs:\n")
            for item in self.found_dids:
                print(f"  • DID 0x{item['did']:04X}: {item['response']}")
                if item['range']:
                    print(f"    Range: {item['range']}")
        else:
            print("✗ No additional DIDs found")
            print("\nPossible reasons:")
            print("1. Vehicle needs to be running (not just ignition ON)")
            print("2. Need to enter extended diagnostic session first (Service 0x10)")
            print("3. Ford uses different DID ranges than scanned")
            print("4. Parameters require security access (Service 0x27)")

def main():
    scanner = DIDScanner(COM_PORT, BAUDRATE)
    
    try:
        if not scanner.connect():
            return 1
        
        scanner.scan_all()
        scanner.print_summary()
        scanner.save_results()
        
    except KeyboardInterrupt:
        print("\n\nScan stopped by user")
        scanner.print_summary()
        scanner.save_results()
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        scanner.disconnect()
        print("\n✓ Disconnected")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
