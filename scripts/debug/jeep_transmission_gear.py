#!/usr/bin/env python3
"""
2007 Jeep Wrangler JK - Transmission Gear Reader

Attempts to read current transmission gear using multiple methods:
1. Standard OBD-II commands
2. UDS commands to TCM
3. CAN bus monitoring (if available)

⚠️ SAFETY: This is READ-ONLY - no messages modify vehicle state.

Usage:
    python scripts/debug/jeep_transmission_gear.py --port COM4
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

def try_standard_obd(elm):
    """Try standard OBD-II gear position command"""
    print("Method 1: Standard OBD-II Gear Position")
    print("-" * 60)
    
    # Mode 01, PID A4 - Transmission Actual Gear
    response = elm.send_command("01A4")
    
    if response and "NO DATA" not in response and "?" not in response:
        print(f"  Raw Response: {response}")
        
        # Parse response
        # Expected format: 41 A4 XX (where XX is gear)
        hex_data = response.replace(' ', '')
        idx = hex_data.find('41A4')
        
        if idx != -1:
            gear_byte = hex_data[idx+4:idx+6]
            try:
                gear_value = int(gear_byte, 16)
                gear = decode_gear(gear_value)
                print(f"  ✓ Current Gear: {gear}")
                print(f"  Raw Value: 0x{gear_byte} ({gear_value})")
                return True
            except:
                pass
    
    print("  ✗ Not available via standard OBD-II")
    return False

def try_tcm_uds(elm):
    """Try UDS commands to Transmission Control Module"""
    print("\nMethod 2: UDS Commands to TCM")
    print("-" * 60)
    
    # Set header to TCM (0x7E1 request, 0x7E9 response)
    elm.send_command("ATSH7E1")
    
    # Try common DIDs for gear position
    dids = [
        ("221E00", "Gear Position (Common)"),
        ("221001", "PRNDL Position"),
        ("220100", "Transmission Status"),
        ("220101", "Current Gear"),
    ]
    
    for did, description in dids:
        print(f"\n  Trying DID 0x{did[2:]}: {description}")
        response = elm.send_command(f"22{did[2:]}")
        
        if response and "NO DATA" not in response and "7F22" not in response:
            print(f"    Raw Response: {response}")
            
            # Parse positive response
            hex_data = response.replace(' ', '')
            
            # Look for positive response (62 XX XX ...)
            idx = hex_data.find('62' + did[2:])
            if idx != -1:
                data_start = idx + 2 + len(did[2:])
                data = hex_data[data_start:data_start+4]
                
                if data:
                    print(f"    Data: {data}")
                    try:
                        value = int(data[:2], 16)
                        gear = decode_gear(value)
                        print(f"    ✓ Current Gear: {gear}")
                        return True
                    except:
                        pass
        else:
            print(f"    ✗ No response or negative response")
    
    print("\n  ✗ TCM did not respond to UDS commands")
    return False

def try_can_monitoring(elm):
    """Try monitoring CAN bus for transmission messages"""
    print("\nMethod 3: CAN Bus Monitoring")
    print("-" * 60)
    print("  Monitoring CAN traffic for 5 seconds...")
    print("  (Shift gears if possible to see changes)")
    print()
    
    # Reset to default header
    elm.send_command("ATSH7DF")
    
    # Enable CAN monitoring with filter for transmission-related IDs
    # Common Jeep transmission CAN IDs: 0x1F5, 0x2C1, 0x308
    elm.send_command("ATCRA1F5")  # Filter for 0x1F5
    elm.send_command("ATS1")  # Spaces ON
    
    # Start monitoring
    elm.ser.reset_input_buffer()
    elm.ser.write(b'ATMA\r')
    time.sleep(0.3)
    
    messages = []
    start_time = time.time()
    buffer = ""
    
    try:
        while (time.time() - start_time) < 5:
            if elm.ser.in_waiting:
                chunk = elm.ser.read(elm.ser.in_waiting).decode('ascii', errors='ignore')
                buffer += chunk
                
                while '\r' in buffer or '\n' in buffer:
                    if '\r' in buffer:
                        line, buffer = buffer.split('\r', 1)
                    else:
                        line, buffer = buffer.split('\n', 1)
                    
                    line = line.strip()
                    
                    if line and line != '>' and 'BUFFER' not in line and 'STOPPED' not in line:
                        messages.append(line)
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        pass
    
    finally:
        # Stop monitoring
        elm.ser.write(b'\r')
        time.sleep(0.2)
        elm.ser.reset_input_buffer()
        elm.send_command("ATCRA")  # Clear filter
    
    if messages:
        print(f"  Captured {len(messages)} CAN messages")
        print("\n  Sample messages:")
        for msg in messages[:10]:
            print(f"    {msg}")
        
        print("\n  ⚠ CAN monitoring captured data but gear decoding requires")
        print("    manufacturer-specific knowledge of message format")
        return False
    else:
        print("  ✗ No CAN messages captured")
        print("    (This is normal - Jeep may not broadcast gear on CAN)")
        return False

def try_related_parameters(elm):
    """Read related transmission parameters"""
    print("\nMethod 4: Related Transmission Parameters")
    print("-" * 60)
    
    # Reset to default header
    elm.send_command("ATSH7DF")
    
    params = [
        ("010C", "Engine RPM", lambda x: f"{int(x, 16) / 4:.0f} RPM"),
        ("010D", "Vehicle Speed", lambda x: f"{int(x, 16)} km/h"),
        ("0111", "Throttle Position", lambda x: f"{int(x, 16) * 100 / 255:.1f}%"),
        ("0104", "Engine Load", lambda x: f"{int(x, 16) * 100 / 255:.1f}%"),
    ]
    
    print("\n  Current Vehicle State:")
    for cmd, name, decoder in params:
        response = elm.send_command(cmd)
        
        if response and "NO DATA" not in response:
            hex_data = response.replace(' ', '')
            # Find response (41 XX YY)
            idx = hex_data.find('41' + cmd[2:])
            if idx != -1:
                data_start = idx + 4
                data = hex_data[data_start:data_start+4]
                
                if data:
                    try:
                        value = decoder(data[:2])
                        print(f"    {name}: {value}")
                    except:
                        print(f"    {name}: {data}")
    
    print("\n  ℹ These parameters can help infer gear:")
    print("    - Low RPM + Low Speed = Low gear or Park/Neutral")
    print("    - High Speed + Moderate RPM = High gear")
    print("    - High RPM + Low Speed = Low gear (acceleration)")

def decode_gear(value):
    """Decode gear value to human-readable format"""
    # Common gear encoding for automatic transmissions
    gear_map = {
        0x00: "Park (P)",
        0x01: "Reverse (R)",
        0x02: "Neutral (N)",
        0x03: "Drive (D)",
        0x04: "2nd Gear",
        0x05: "1st Gear",
        0x10: "Park (P)",
        0x20: "Reverse (R)",
        0x30: "Neutral (N)",
        0x40: "Drive (D)",
        0x50: "Sport (S)",
        0x60: "Low (L)",
    }
    
    # Check direct match
    if value in gear_map:
        return gear_map[value]
    
    # Try bit-based decoding
    if value & 0x01:
        return "Park (P)"
    elif value & 0x02:
        return "Reverse (R)"
    elif value & 0x04:
        return "Neutral (N)"
    elif value & 0x08:
        return "Drive (D)"
    elif value & 0x10:
        return "2nd Gear"
    elif value & 0x20:
        return "1st Gear"
    
    return f"Unknown (0x{value:02X})"

def main(port='COM4'):
    """Main entry point"""
    print("=" * 70)
    print("2007 Jeep Wrangler JK - Transmission Gear Reader")
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
        print("  - Try unplugging and replugging adapter")
        return False
    
    print("✓ Connected to ELM327")
    print()
    print("=" * 70)
    print()
    
    # Try multiple methods
    success = False
    
    success = try_standard_obd(elm) or success
    success = try_tcm_uds(elm) or success
    success = try_can_monitoring(elm) or success
    try_related_parameters(elm)
    
    print()
    print("=" * 70)
    
    if not success:
        print()
        print("⚠ RESULT: Gear position not available via standard ELM327")
        print()
        print("EXPLANATION:")
        print("  Jeep/Chrysler vehicles use proprietary protocols for")
        print("  transmission data. Standard OBD-II adapters have limited")
        print("  access to manufacturer-specific parameters.")
        print()
        print("SOLUTION: Use AlfaOBD")
        print("  - Cost: ~$50 (one-time)")
        print("  - Works with your existing ELM327 adapter")
        print("  - Full access to TCM including gear position")
        print("  - Download: https://www.alfaobd.com/")
        print()
        print("ALTERNATIVE: Monitor CAN bus")
        print("  - Requires identifying which CAN ID contains gear data")
        print("  - May require extended monitoring and correlation")
        print("  - See: scripts/debug/explore_can_bus.py")
        print()
    else:
        print()
        print("✓ Successfully read transmission gear!")
        print()
    
    elm.close()
    print("✓ Disconnected")
    
    return success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Read transmission gear from 2007 Jeep Wrangler JK'
    )
    parser.add_argument('--port', default='COM4', 
                       help='Serial port (default: COM4)')
    
    args = parser.parse_args()
    
    success = main(port=args.port)
    sys.exit(0 if success else 1)
