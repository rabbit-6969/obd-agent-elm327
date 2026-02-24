"""
Read Transmission Live Data - 2008 Ford Escape

This script reads the two discovered transmission DIDs and displays them
in human-readable format with proper parsing.

Usage:
1. Make sure vehicle is running (for accurate readings)
2. Run: python read_transmission_live.py
3. Script will continuously display transmission parameters

Discovered DIDs:
- 0x0100: Transmission Fluid Temperature
- 0x0101: Transmission Line Pressure
"""

import serial
import time
import sys
from datetime import datetime

# Configuration
COM_PORT = "COM3"
BAUDRATE = 38400
REFRESH_INTERVAL = 2.0  # seconds between readings

class TransmissionMonitor:
    def __init__(self, port, baudrate=38400):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
    
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
        if self.ser and self.ser.is_open:
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
    
    def read_did(self, did):
        """Read a specific DID using UDS Service 0x22"""
        cmd = f"22{did:04X}"
        response = self.send_command(cmd)
        
        if response and "NO DATA" not in response and "?" not in response:
            clean_response = response.replace(' ', '')
            if clean_response.startswith('62') or '62' in clean_response:
                return response
        
        return None
    
    def parse_temperature(self, response):
        """Parse transmission fluid temperature from DID 0x0100"""
        try:
            # Response format: "62 01 00 XX" where XX is temperature
            clean = response.replace(' ', '')
            
            # Find the response data after "620100"
            idx = clean.find('620100')
            if idx >= 0:
                temp_hex = clean[idx+6:idx+8]
                temp_raw = int(temp_hex, 16)
                temp_c = temp_raw - 40
                temp_f = (temp_c * 9/5) + 32
                return temp_c, temp_f, temp_hex
        except Exception as e:
            pass
        
        return None, None, None
    
    def parse_pressure(self, response):
        """Parse transmission line pressure from DID 0x0101"""
        try:
            # Response format: "62 01 01 XX XX" where XX XX is pressure (2 bytes)
            clean = response.replace(' ', '')
            
            # Find the response data after "620101"
            idx = clean.find('620101')
            if idx >= 0:
                pressure_hex = clean[idx+6:idx+10]
                pressure_raw = int(pressure_hex, 16)
                
                # Formula TBD - for now just show raw value
                # Possible units: PSI, kPa, or arbitrary units
                # Need to compare with known gauge reading to determine
                return pressure_raw, pressure_hex
        except Exception as e:
            pass
        
        return None, None
    
    def read_all_parameters(self):
        """Read all transmission parameters"""
        data = {}
        
        # Read temperature
        temp_response = self.read_did(0x0100)
        if temp_response:
            temp_c, temp_f, temp_hex = self.parse_temperature(temp_response)
            data['temperature'] = {
                'celsius': temp_c,
                'fahrenheit': temp_f,
                'hex': temp_hex,
                'raw_response': temp_response
            }
        
        # Read pressure
        pressure_response = self.read_did(0x0101)
        if pressure_response:
            pressure_raw, pressure_hex = self.parse_pressure(pressure_response)
            data['pressure'] = {
                'raw': pressure_raw,
                'hex': pressure_hex,
                'raw_response': pressure_response
            }
        
        return data
    
    def display_data(self, data):
        """Display transmission data in formatted output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] Transmission Parameters:")
        print("=" * 60)
        
        if 'temperature' in data:
            temp = data['temperature']
            if temp['celsius'] is not None:
                print(f"  Fluid Temperature: {temp['celsius']}°C ({temp['fahrenheit']:.1f}°F)")
                print(f"    Raw hex: 0x{temp['hex']}")
                
                # Temperature status
                if temp['celsius'] < 60:
                    print(f"    Status: COLD (normal operating: 70-90°C)")
                elif temp['celsius'] < 70:
                    print(f"    Status: WARMING UP")
                elif temp['celsius'] <= 90:
                    print(f"    Status: NORMAL")
                elif temp['celsius'] <= 110:
                    print(f"    Status: HOT (monitor closely)")
                else:
                    print(f"    Status: OVERHEATING! (>110°C)")
        else:
            print(f"  Fluid Temperature: NOT AVAILABLE")
        
        print()
        
        if 'pressure' in data:
            pressure = data['pressure']
            if pressure['raw'] is not None:
                print(f"  Line Pressure: {pressure['raw']} (units unknown)")
                print(f"    Raw hex: 0x{pressure['hex']}")
                print(f"    Note: Formula needs calibration with known gauge")
                print(f"          Possible units: PSI, kPa, or arbitrary")
        else:
            print(f"  Line Pressure: NOT AVAILABLE")
        
        print("=" * 60)
    
    def monitor_continuous(self):
        """Continuously monitor transmission parameters"""
        print("="*60)
        print("Transmission Live Data Monitor")
        print("="*60)
        print("\nReading transmission parameters every 2 seconds...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                data = self.read_all_parameters()
                self.display_data(data)
                time.sleep(REFRESH_INTERVAL)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
    
    def read_once(self):
        """Read parameters once and exit"""
        print("="*60)
        print("Transmission Parameters - Single Reading")
        print("="*60)
        
        data = self.read_all_parameters()
        self.display_data(data)
        
        # Show raw responses for debugging
        print("\nRaw Responses (for debugging):")
        print("-" * 60)
        if 'temperature' in data:
            print(f"  DID 0x0100: {data['temperature']['raw_response']}")
        if 'pressure' in data:
            print(f"  DID 0x0101: {data['pressure']['raw_response']}")
        print("-" * 60)

def main():
    print("="*60)
    print("2008 Ford Escape - Transmission Live Data")
    print("="*60)
    print()
    print("This script reads transmission parameters:")
    print("  • Transmission Fluid Temperature (DID 0x0100)")
    print("  • Transmission Line Pressure (DID 0x0101)")
    print()
    print("Make sure:")
    print("  - Vehicle is RUNNING (for accurate readings)")
    print("  - ELM327 is connected to COM3")
    print()
    
    mode = input("Mode: [C]ontinuous or [O]nce? (C/O): ").strip().upper()
    
    monitor = TransmissionMonitor(COM_PORT, BAUDRATE)
    
    try:
        if not monitor.connect():
            return 1
        
        if mode == 'O':
            monitor.read_once()
        else:
            monitor.monitor_continuous()
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        monitor.disconnect()
        print("\n✓ Disconnected")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
