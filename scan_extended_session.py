"""
Scan for Transmission DIDs in Extended Diagnostic Session - 2008 Ford Escape

This script enters UDS extended diagnostic session (0x10 03) and then
re-scans for transmission DIDs that may be hidden in the default session.

Usage:
1. Make sure vehicle is running
2. Run: python scan_extended_session.py
3. Script will enter extended session and scan for DIDs
4. Results saved to logs/extended_scan_[timestamp].txt

Based on ISO 14229-1 Service 0x10: DiagnosticSessionControl
"""

import serial
import time
import sys
from datetime import datetime
import os
import threading

# Configuration
COM_PORT = "COM3"
BAUDRATE = 38400
LOG_DIR = "logs"

class ExtendedSessionScanner:
    def __init__(self, port, baudrate=38400):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.found_dids = []
        self.session_active = False
        self.tester_present_thread = None
        self.stop_tester_present = False
    
    def connect(self):
        """Connect to ELM327 adapter"""
        print(f"Connecting to {self.port}...")
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0
            )
            time.sleep(2)
            
            # Initialize
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")
            self.send_command("ATL0")
            self.send_command("ATSP0")
            self.send_command("ATH1")  # Show headers
            
            print("✓ Connected to ELM327\n")
            return True
        except serial.SerialException as e:
            print(f"✗ Error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from adapter"""
        self.stop_tester_present = True
        if self.tester_present_thread:
            self.tester_present_thread.join(timeout=2)
        
        if self.ser and self.ser.is_open:
            # Return to default session before disconnecting
            if self.session_active:
                print("\nReturning to default session...")
                self.send_command("1001")  # Return to defaultSession
                time.sleep(0.5)
            self.ser.close()
    
    def send_command(self, cmd):
        """Send command and get response"""
        if not self.ser or not self.ser.is_open:
            return None
        
        self.ser.write((cmd + "\r").encode())
        time.sleep(0.2)
        
        response = ""
        while self.ser.in_waiting > 0:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.05)
        
        response = response.replace('>', '').replace('\r', ' ').replace('\n', ' ').strip()
        return response if response else None
    
    def enter_extended_session(self):
        """Enter extended diagnostic session (0x10 03)"""
        print("="*70)
        print("Entering Extended Diagnostic Session")
        print("="*70)
        print("\nSending: 10 03 (DiagnosticSessionControl - extendedDiagnosticSession)")
        
        response = self.send_command("1003")
        
        if response:
            print(f"Response: {response}\n")
            
            # Check for positive response (50 03)
            clean = response.replace(' ', '')
            if '5003' in clean:
                print("✓ Extended diagnostic session ACTIVE")
                
                # Parse timing parameters
                idx = clean.find('5003')
                if idx >= 0 and len(clean) >= idx + 12:
                    timing_data = clean[idx+4:idx+12]
                    p2_high = timing_data[0:2]
                    p2_low = timing_data[2:4]
                    p2star_high = timing_data[4:6]
                    p2star_low = timing_data[6:8]
                    
                    p2_ms = int(p2_high + p2_low, 16)
                    p2star_ms = int(p2star_high + p2star_low, 16) * 10
                    
                    print(f"  P2Server_max: {p2_ms} ms")
                    print(f"  P2*Server_max: {p2star_ms} ms")
                    print(f"\n  Session will timeout without TesterPresent messages")
                    print(f"  Starting TesterPresent keepalive thread...\n")
                
                self.session_active = True
                self.start_tester_present()
                return True
            elif '7F' in clean:
                # Negative response
                print("✗ Extended session REJECTED")
                print(f"  Negative response: {response}")
                print(f"\n  Possible reasons:")
                print(f"  - Vehicle conditions not met (e.g., must be stationary)")
                print(f"  - Session not supported by this ECU")
                print(f"  - Security access required first")
                return False
        
        print("✗ No response from ECU")
        return False
    
    def start_tester_present(self):
        """Start background thread to send TesterPresent messages"""
        self.stop_tester_present = False
        self.tester_present_thread = threading.Thread(target=self._tester_present_loop, daemon=True)
        self.tester_present_thread.start()
    
    def _tester_present_loop(self):
        """Background loop to keep session alive"""
        while not self.stop_tester_present and self.session_active:
            time.sleep(2)  # Send every 2 seconds
            if not self.stop_tester_present:
                # Send TesterPresent with suppressPosRspMsgIndicationBit set (0x3E 80)
                self.send_command("3E80")
    
    def try_did(self, did):
        """Try reading a specific DID"""
        cmd = f"22{did:04X}"
        response = self.send_command(cmd)
        
        if response and "NO DATA" not in response and "?" not in response:
            clean_response = response.replace(' ', '')
            if clean_response.startswith('62') or '62' in clean_response:
                return True, response
            elif clean_response.startswith('7F22') or '7F22' in clean_response:
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
        """Scan all interesting DID ranges in extended session"""
        print("="*70)
        print("UDS DID Scanner - Extended Diagnostic Session")
        print("="*70)
        print("\nThis will scan for transmission DIDs in extended session.")
        print("Estimated time: 5-10 minutes")
        print("\nPress Ctrl+C to stop at any time\n")
        
        input("Press Enter to start scanning...")
        
        # Range 1: 0x0100-0x01FF (transmission parameters)
        self.scan_range(0x0100, 0x01FF, "Transmission parameters (extended session)")
        
        # Range 2: 0x1000-0x10FF (common Ford range)
        print("\n\nContinue to next range? (Press Enter or Ctrl+C to stop)")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nScan stopped by user")
            return
        
        self.scan_range(0x1000, 0x10FF, "Common Ford diagnostic range (extended session)")
        
        # Range 3: 0xF000-0xF0FF (manufacturer-specific)
        print("\n\nContinue to next range? (Press Enter or Ctrl+C to stop)")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nScan stopped by user")
            return
        
        self.scan_range(0xF000, 0xF0FF, "Manufacturer-specific range (extended session)")
    
    def save_results(self):
        """Save scan results to file"""
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(LOG_DIR, f"extended_scan_{timestamp}.txt")
        
        with open(filename, 'w') as f:
            f.write("="*70 + "\n")
            f.write("UDS DID Scan Results - Extended Diagnostic Session\n")
            f.write("2008 Ford Escape\n")
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
                f.write("No additional DIDs found in extended session.\n")
        
        print(f"\n✓ Results saved to: {filename}")
        return filename
    
    def print_summary(self):
        """Print summary of findings"""
        print("\n" + "="*70)
        print("Scan Complete - Summary")
        print("="*70 + "\n")
        
        if self.found_dids:
            print(f"✓ Found {len(self.found_dids)} working DIDs in extended session:\n")
            for item in self.found_dids:
                print(f"  • DID 0x{item['did']:04X}: {item['response']}")
                if item['range']:
                    print(f"    Range: {item['range']}")
        else:
            print("✗ No additional DIDs found in extended session")
            print("\nPossible reasons:")
            print("1. Ford uses different DID ranges than scanned")
            print("2. Parameters require security access (Service 0x27) first")
            print("3. Ford uses manufacturer-specific session types (0x40-0x5F)")
            print("4. Parameters only available during specific vehicle states")

def main():
    scanner = ExtendedSessionScanner(COM_PORT, BAUDRATE)
    
    try:
        if not scanner.connect():
            return 1
        
        # Enter extended diagnostic session
        if not scanner.enter_extended_session():
            print("\n✗ Failed to enter extended session")
            print("Cannot proceed with scan")
            return 1
        
        # Wait a moment for session to stabilize
        time.sleep(1)
        
        # Scan for DIDs
        scanner.scan_all()
        scanner.print_summary()
        scanner.save_results()
        
    except KeyboardInterrupt:
        print("\n\nScan stopped by user")
        scanner.print_summary()
        scanner.save_results()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scanner.disconnect()
        print("\n✓ Disconnected")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
