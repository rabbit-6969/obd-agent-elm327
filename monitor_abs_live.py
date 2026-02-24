#!/usr/bin/env python3
"""
Ford Escape 2008 - Live ABS Monitor
Real-time display of ABS module parameters

Monitors DIDs 0x0200 and 0x0202 discovered from ABS module.
Run this while driving to see values change with wheel movement.

Author: AI Diagnostic Agent
"""

import serial
import time
import sys
from datetime import datetime

class ABSMonitor:
    """Real-time ABS parameter monitor"""
    
    def __init__(self, port: str = 'COM3', baudrate: int = 38400):
        """Initialize monitor"""
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        
        # ABS addressing
        self.abs_request = 0x760
        self.abs_response = 0x768
        
        # Known DIDs
        self.dids = {
            0x0200: "ABS Parameter 1",
            0x0202: "ABS Parameter 2"
        }
    
    def connect(self) -> bool:
        """Connect to ELM327"""
        try:
            print("=" * 70)
            print("Ford Escape 2008 - Live ABS Monitor")
            print("=" * 70)
            print("\n⚠ Set adapter switch to HS-CAN position!")
            input("Press Enter when ready...")
            
            print(f"\nConnecting to {self.port}...")
            self.connection = serial.Serial(self.port, self.baudrate, timeout=3)
            time.sleep(2)
            
            # Initialize
            print("Initializing...")
            self._send_command("ATZ")
            time.sleep(1)
            self._send_command("ATE0")
            self._send_command("ATL0")
            self._send_command("ATS0")
            self._send_command("ATH1")
            self._send_command("ATSP6")
            self._send_command("ATCAF0")
            self._send_command(f"ATSH {self.abs_request:03X}")
            self._send_command(f"ATFCSH {self.abs_response:03X}")
            self._send_command("ATFCSD 30 00 00")
            
            print("✓ Connected")
            
            # Test
            print("\nTesting ABS communication...")
            success, _, _ = self.read_did(0x0200)
            if success:
                print("✓ ABS responding")
                return True
            else:
                print("✗ No response from ABS")
                return False
                
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def _send_command(self, cmd: str) -> str:
        """Send command to ELM327"""
        if not self.connection:
            return ""
        
        self.connection.write((cmd + '\r').encode())
        time.sleep(0.1)
        
        response = b''
        while self.connection.in_waiting:
            response += self.connection.read(self.connection.in_waiting)
            time.sleep(0.05)
        
        return response.decode('utf-8', errors='ignore').strip()
    
    def read_did(self, did: int):
        """Read a DID"""
        did_msb = (did >> 8) & 0xFF
        did_lsb = did & 0xFF
        
        cmd = f"03 22 {did_msb:02X} {did_lsb:02X}"
        response = self._send_command(cmd)
        time.sleep(0.15)
        
        if '62' in response:
            parts = response.replace(' ', '').replace('\r', '').replace('\n', '')
            idx = parts.find('62')
            if idx != -1:
                data_start = idx + 2 + 4
                data = parts[data_start:]
                return True, data, None
        
        return False, None, 'NO_RESPONSE'
    
    def decode_value(self, data: str) -> dict:
        """Decode hex data to values"""
        if not data or len(data) < 8:
            return {'raw': data, 'error': 'Invalid data'}
        
        try:
            # Try different interpretations
            raw_hex = data[:8]
            
            # As 32-bit integer
            value_32 = int(raw_hex, 16)
            
            # As 4 bytes
            byte1 = int(raw_hex[0:2], 16)
            byte2 = int(raw_hex[2:4], 16)
            byte3 = int(raw_hex[4:6], 16)
            byte4 = int(raw_hex[6:8], 16)
            
            # As 2x 16-bit integers
            value_16_1 = int(raw_hex[0:4], 16)
            value_16_2 = int(raw_hex[4:8], 16)
            
            return {
                'raw': raw_hex,
                'int32': value_32,
                'bytes': [byte1, byte2, byte3, byte4],
                'int16': [value_16_1, value_16_2],
                'binary': format(value_32, '032b')
            }
        except:
            return {'raw': data, 'error': 'Decode failed'}
    
    def monitor(self, refresh_rate: float = 1.0):
        """Monitor ABS parameters in real-time"""
        print("\n" + "=" * 70)
        print("LIVE ABS MONITOR")
        print("=" * 70)
        print("\nPress Ctrl+C to stop")
        print("\nTIP: Drive the vehicle to see values change")
        print("     Brake activation will show in ABS parameters")
        print("\n" + "=" * 70)
        
        try:
            while True:
                # Clear screen (Windows)
                print("\033[H\033[J", end="")
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'=' * 70}")
                print(f"ABS Monitor - {timestamp}")
                print(f"{'=' * 70}\n")
                
                # Read each DID
                for did, description in self.dids.items():
                    success, data, error = self.read_did(did)
                    
                    print(f"DID 0x{did:04X} - {description}")
                    print("-" * 70)
                    
                    if success and data:
                        decoded = self.decode_value(data)
                        
                        print(f"  Raw Hex:    {decoded.get('raw', 'N/A')}")
                        print(f"  Int32:      {decoded.get('int32', 'N/A')}")
                        
                        if 'int16' in decoded:
                            print(f"  Int16[0]:   {decoded['int16'][0]}")
                            print(f"  Int16[1]:   {decoded['int16'][1]}")
                        
                        if 'bytes' in decoded:
                            bytes_str = ' '.join(f"{b:02X}" for b in decoded['bytes'])
                            print(f"  Bytes:      {bytes_str}")
                        
                        # Check for patterns
                        if decoded.get('int32', 0) == 0:
                            print(f"  Status:     ⚪ All zeros (idle/stationary)")
                        elif decoded.get('int32', 0) > 0:
                            print(f"  Status:     🟢 Active data")
                        
                    else:
                        print(f"  Status:     ✗ {error}")
                    
                    print()
                
                print("=" * 70)
                print(f"Refresh rate: {refresh_rate}s | Press Ctrl+C to stop")
                
                time.sleep(refresh_rate)
                
        except KeyboardInterrupt:
            print("\n\n⚠ Monitoring stopped by user")
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
        print("\n✓ Disconnected")

def main():
    """Main execution"""
    monitor = ABSMonitor(port='COM3')
    
    if not monitor.connect():
        return
    
    try:
        print("\n" + "=" * 70)
        print("MONITOR OPTIONS")
        print("=" * 70)
        print("\n1. Fast refresh (0.5s) - High update rate")
        print("2. Normal refresh (1.0s) - Balanced")
        print("3. Slow refresh (2.0s) - Reduced load")
        
        choice = input("\nSelect refresh rate (1/2/3) [default: 2]: ").strip()
        
        if choice == '1':
            refresh_rate = 0.5
        elif choice == '3':
            refresh_rate = 2.0
        else:
            refresh_rate = 1.0
        
        monitor.monitor(refresh_rate)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        monitor.disconnect()

if __name__ == "__main__":
    main()
