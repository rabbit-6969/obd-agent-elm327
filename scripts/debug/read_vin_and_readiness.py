#!/usr/bin/env python3
"""
Read VIN and Emission Readiness Monitors

Uses standard OBD-II commands:
- Mode 09 PID 02: VIN (Vehicle Identification Number)
- Mode 01 PID 01: Monitor status since DTCs cleared

⚠️ SAFETY: This is READ-ONLY - no messages modify vehicle state.

Usage:
    python scripts/debug/read_vin_and_readiness.py --port COM4
"""

import serial
import time
import sys
from datetime import datetime

class ELM327:
    """ELM327 adapter interface"""
    
    def __init__(self, port='COM4', baudrate=38400, timeout=3):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
    
    def connect(self):
        """Connect and initialize ELM327"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)
            
            # Initialize adapter
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATS0")  # Spaces off
            self.send_command("ATH1")  # Headers on
            self.send_command("ATSP0")  # Auto protocol
            
            # Test communication
            response = self.send_command("0100")
            if not response or "NO DATA" in response:
                return False
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def send_command(self, command):
        """Send command and get response"""
        if not self.ser:
            return None
        
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            self.ser.write((command + '\r').encode())
            
            response = b''
            start_time = time.time()
            
            while time.time() - start_time < self.timeout:
                if self.ser.in_waiting:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response += chunk
                    
                    if b'>' in response:
                        break
                
                time.sleep(0.05)
            
            response_str = response.decode('ascii', errors='ignore')
            response_str = response_str.replace('\r', '').replace('\n', ' ')
            response_str = response_str.replace('>', '').strip()
            
            return response_str
        
        except Exception as e:
            return None
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def read_vin(elm):
    """Read VIN using Mode 09 PID 02"""
    print("Reading VIN...")
    
    # Request VIN (Mode 09, PID 02)
    response = elm.send_command("0902")
    
    if not response or "NO DATA" in response:
        print("  VIN: Not available")
        return None
    
    # Parse VIN from response
    # Response format: 49 02 01 [VIN bytes in ASCII hex]
    try:
        # Remove spaces and extract hex data
        hex_data = response.replace(' ', '')
        
        # Find the start of VIN data (after 4902)
        idx = hex_data.find('4902')
        if idx == -1:
            print("  VIN: Parse error")
            return None
        
        # Skip header (7E8 or similar), length, 49 02, and count byte
        # Extract VIN characters (17 ASCII characters = 34 hex digits)
        vin_start = idx + 6  # Skip "4902" + count byte (2 hex digits)
        vin_hex = hex_data[vin_start:vin_start + 34]
        
        # Convert hex to ASCII
        vin = ''
        for i in range(0, len(vin_hex), 2):
            if i + 1 < len(vin_hex):
                byte_hex = vin_hex[i:i+2]
                try:
                    char = chr(int(byte_hex, 16))
                    if char.isprintable():
                        vin += char
                except:
                    pass
        
        if len(vin) >= 17:
            vin = vin[:17]
            print(f"  VIN: {vin}")
            return vin
        else:
            print(f"  VIN: Incomplete ({vin})")
            return None
    
    except Exception as e:
        print(f"  VIN: Parse error ({e})")
        return None

def read_readiness_monitors(elm):
    """Read emission readiness monitors using Mode 01 PID 01"""
    print("\nReading Emission Readiness Monitors...")
    
    # Request monitor status (Mode 01, PID 01)
    response = elm.send_command("0101")
    
    if not response or "NO DATA" in response:
        print("  Readiness: Not available")
        return None
    
    # Parse readiness data
    # Response format: 41 01 [4 data bytes]
    try:
        # Remove spaces
        hex_data = response.replace(' ', '')
        
        # Find response
        idx = hex_data.find('4101')
        if idx == -1:
            print("  Readiness: Parse error")
            return None
        
        # Extract 4 data bytes after 4101
        data_start = idx + 4
        data_hex = hex_data[data_start:data_start + 8]
        
        if len(data_hex) < 8:
            print("  Readiness: Incomplete data")
            return None
        
        # Parse bytes
        byte_a = int(data_hex[0:2], 16)
        byte_b = int(data_hex[2:4], 16)
        byte_c = int(data_hex[4:6], 16)
        byte_d = int(data_hex[6:8], 16)
        
        # Byte A, bit 7: MIL status
        mil_on = bool(byte_a & 0x80)
        
        # Byte A, bits 0-6: DTC count
        dtc_count = byte_a & 0x7F
        
        print(f"\n  MIL (Check Engine Light): {'ON' if mil_on else 'OFF'}")
        print(f"  DTC Count: {dtc_count}")
        print()
        
        # Determine if spark or compression ignition
        spark_ignition = not bool(byte_a & 0x08)
        
        if spark_ignition:
            print("  Monitor Type: Spark Ignition (Gasoline)")
            print()
            print("  Readiness Monitors:")
            print("  " + "-" * 50)
            
            # Byte B - Supported monitors
            # Byte C - Completion status (0 = complete, 1 = incomplete)
            
            monitors = [
                ("Misfire", 0x01, byte_b, byte_c),
                ("Fuel System", 0x02, byte_b, byte_c),
                ("Components", 0x04, byte_b, byte_c),
            ]
            
            # Byte D - Additional monitors
            additional_monitors = [
                ("Catalyst", 0x01, byte_b, byte_d),
                ("Heated Catalyst", 0x02, byte_b, byte_d),
                ("Evaporative System", 0x04, byte_b, byte_d),
                ("Secondary Air System", 0x08, byte_b, byte_d),
                ("A/C Refrigerant", 0x10, byte_b, byte_d),
                ("Oxygen Sensor", 0x20, byte_b, byte_d),
                ("Oxygen Sensor Heater", 0x40, byte_b, byte_d),
                ("EGR System", 0x80, byte_b, byte_d),
            ]
            
            for name, mask, supported_byte, status_byte in monitors:
                if supported_byte & mask:
                    incomplete = bool(status_byte & mask)
                    status = "INCOMPLETE" if incomplete else "COMPLETE"
                    symbol = "⚠" if incomplete else "✓"
                    print(f"    {symbol} {name:<25} {status}")
            
            for name, mask, supported_byte, status_byte in additional_monitors:
                if supported_byte & mask:
                    incomplete = bool(status_byte & mask)
                    status = "INCOMPLETE" if incomplete else "COMPLETE"
                    symbol = "⚠" if incomplete else "✓"
                    print(f"    {symbol} {name:<25} {status}")
        
        else:
            print("  Monitor Type: Compression Ignition (Diesel)")
            print()
            print("  Readiness Monitors:")
            print("  " + "-" * 50)
            
            # Diesel monitors (different from gasoline)
            monitors = [
                ("Misfire", 0x01, byte_b, byte_c),
                ("Fuel System", 0x02, byte_b, byte_c),
                ("Components", 0x04, byte_b, byte_c),
            ]
            
            additional_monitors = [
                ("EGR/VVT System", 0x01, byte_b, byte_d),
                ("PM Filter", 0x02, byte_b, byte_d),
                ("Exhaust Gas Sensor", 0x04, byte_b, byte_d),
                ("Boost Pressure", 0x08, byte_b, byte_d),
                ("NOx/SCR Monitor", 0x20, byte_b, byte_d),
                ("NMHC Catalyst", 0x40, byte_b, byte_d),
            ]
            
            for name, mask, supported_byte, status_byte in monitors:
                if supported_byte & mask:
                    incomplete = bool(status_byte & mask)
                    status = "INCOMPLETE" if incomplete else "COMPLETE"
                    symbol = "⚠" if incomplete else "✓"
                    print(f"    {symbol} {name:<25} {status}")
            
            for name, mask, supported_byte, status_byte in additional_monitors:
                if supported_byte & mask:
                    incomplete = bool(status_byte & mask)
                    status = "INCOMPLETE" if incomplete else "COMPLETE"
                    symbol = "⚠" if incomplete else "✓"
                    print(f"    {symbol} {name:<25} {status}")
        
        print()
        return {
            'mil_on': mil_on,
            'dtc_count': dtc_count,
            'spark_ignition': spark_ignition
        }
    
    except Exception as e:
        print(f"  Readiness: Parse error ({e})")
        return None

def main(port='COM4'):
    """Main entry point"""
    print("=" * 70)
    print("VIN and Emission Readiness Monitor Reader")
    print("=" * 70)
    print()
    
    elm = ELM327(port=port)
    
    if not elm.connect():
        print("Failed to connect to ELM327")
        print()
        print("Troubleshooting:")
        print("  - Verify adapter is plugged into OBD-II port")
        print("  - Check COM port (use Device Manager)")
        print("  - Ensure vehicle ignition is in RUN position")
        return False
    
    print("✓ Connected to ELM327")
    print()
    print("=" * 70)
    
    # Read VIN
    vin = read_vin(elm)
    
    # Read readiness monitors
    readiness = read_readiness_monitors(elm)
    
    print("=" * 70)
    print()
    
    if readiness:
        if readiness['dtc_count'] > 0:
            print(f"⚠ Vehicle has {readiness['dtc_count']} stored diagnostic trouble code(s)")
            print("  Run Mode 03 (0300) to read DTCs")
        else:
            print("✓ No diagnostic trouble codes stored")
        
        print()
    
    elm.close()
    print("✓ Disconnected")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Read VIN and emission readiness monitors'
    )
    parser.add_argument('--port', default='COM4', 
                       help='Serial port (default: COM4)')
    
    args = parser.parse_args()
    
    success = main(port=args.port)
    sys.exit(0 if success else 1)
