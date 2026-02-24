"""
Read Transmission Data from 2008 Ford Escape PCM

This script reads transmission parameters using standard OBD-II Mode 01 PIDs
and discovers which parameters are available.

Usage:
1. Close FORScan
2. Run: python read_transmission_data.py
3. Script will try standard transmission PIDs and report what works

Parameters to read:
- Transmission Fluid Temperature (TFT)
- Transmission Range (gear position)
- Torque Converter Clutch status
- Transmission slip ratio
- And more...
"""

import serial
import time
import sys

# Configuration
COM_PORT = "COM3"
BAUDRATE = 38400

class TransmissionReader:
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
                timeout=2.0
            )
            time.sleep(2)  # Wait for adapter to initialize
            
            # Initialize adapter
            self.send_command("ATZ")  # Reset
            time.sleep(1)
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATSP0")  # Auto protocol
            
            print("✓ Connected to ELM327")
            return True
        except serial.SerialException as e:
            print(f"✗ Error: {e}")
            print("Make sure FORScan is closed and COM3 is available")
            return False
    
    def disconnect(self):
        """Disconnect from adapter"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("\n✓ Disconnected")
    
    def send_command(self, cmd):
        """Send command and get response"""
        if not self.ser or not self.ser.is_open:
            return None
        
        self.ser.write((cmd + "\r").encode())
        time.sleep(0.3)
        
        response = ""
        while self.ser.in_waiting > 0:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        
        # Clean response
        response = response.replace('>', '').replace('\r', ' ').replace('\n', ' ').strip()
        return response if response else None
    
    def read_pid(self, mode, pid):
        """Read a specific PID"""
        cmd = f"{mode:02X}{pid:02X}"
        response = self.send_command(cmd)
        return response
    
    def parse_temperature(self, response, offset=-40):
        """Parse temperature from response (value - 40)"""
        try:
            # Response format: "41 05 XX" where XX is the temperature
            parts = response.replace(' ', '')
            if len(parts) >= 6:
                temp_hex = parts[4:6]
                temp_raw = int(temp_hex, 16)
                temp_c = temp_raw + offset
                temp_f = (temp_c * 9/5) + 32
                return temp_c, temp_f
        except:
            pass
        return None, None
    
    def parse_percentage(self, response):
        """Parse percentage from response (value * 100 / 255)"""
        try:
            parts = response.replace(' ', '')
            if len(parts) >= 6:
                value_hex = parts[4:6]
                value_raw = int(value_hex, 16)
                percentage = (value_raw * 100) / 255
                return percentage
        except:
            pass
        return None
    
    def read_transmission_data(self):
        """Read all available transmission parameters"""
        print("\n" + "="*70)
        print("Reading Transmission Parameters")
        print("="*70 + "\n")
        
        # Standard OBD-II Mode 01 PIDs for transmission
        pids_to_try = [
            (0x01, 0x05, "Engine Coolant Temperature", "temperature"),
            (0x01, 0x0C, "Engine RPM", "rpm"),
            (0x01, 0x0D, "Vehicle Speed", "speed"),
            (0x01, 0x11, "Throttle Position", "percentage"),
            (0x01, 0xA4, "Transmission Fluid Temperature", "temperature"),  # Common TFT PID
            (0x01, 0xA6, "Transmission Range", "hex"),
            (0x01, 0xA7, "Transmission Slip Ratio", "hex"),
            (0x01, 0xA8, "Transmission Torque Converter Clutch", "hex"),
        ]
        
        results = []
        
        for mode, pid, description, parse_type in pids_to_try:
            print(f"Trying PID {mode:02X} {pid:02X}: {description}...", end=" ")
            response = self.read_pid(mode, pid)
            
            if response and "NO DATA" not in response and "?" not in response:
                print(f"✓ Got response: {response}")
                
                # Parse based on type
                parsed_value = None
                if parse_type == "temperature":
                    temp_c, temp_f = self.parse_temperature(response)
                    if temp_c is not None:
                        parsed_value = f"{temp_c}°C ({temp_f:.1f}°F)"
                elif parse_type == "percentage":
                    pct = self.parse_percentage(response)
                    if pct is not None:
                        parsed_value = f"{pct:.1f}%"
                elif parse_type == "rpm":
                    try:
                        parts = response.replace(' ', '')
                        if len(parts) >= 8:
                            rpm_hex = parts[4:8]
                            rpm = int(rpm_hex, 16) / 4
                            parsed_value = f"{rpm:.0f} RPM"
                    except:
                        pass
                elif parse_type == "speed":
                    try:
                        parts = response.replace(' ', '')
                        if len(parts) >= 6:
                            speed_hex = parts[4:6]
                            speed = int(speed_hex, 16)
                            parsed_value = f"{speed} km/h"
                    except:
                        pass
                else:
                    parsed_value = response
                
                if parsed_value:
                    print(f"  → {parsed_value}")
                
                results.append({
                    "mode": mode,
                    "pid": pid,
                    "description": description,
                    "response": response,
                    "parsed": parsed_value
                })
            else:
                print(f"✗ Not supported")
        
        return results
    
    def try_uds_service_22(self):
        """Try UDS Service 0x22 (ReadDataByIdentifier) for transmission data"""
        print("\n" + "="*70)
        print("Trying UDS Service 0x22 (ReadDataByIdentifier)")
        print("="*70 + "\n")
        
        # Common Ford transmission DIDs
        dids_to_try = [
            (0x0100, "Transmission Fluid Temperature"),
            (0x0101, "Transmission Line Pressure"),
            (0x0102, "Current Gear Position"),
            (0x0103, "Shift Solenoid A Status"),
            (0x0104, "Shift Solenoid B Status"),
            (0x0105, "Shift Solenoid C Status"),
            (0x0106, "Shift Solenoid D Status"),
            (0x0107, "Torque Converter Clutch Status"),
            (0x0108, "Input Shaft Speed"),
            (0x0109, "Output Shaft Speed"),
        ]
        
        results = []
        
        for did, description in dids_to_try:
            print(f"Trying DID 0x{did:04X}: {description}...", end=" ")
            cmd = f"22{did:04X}"
            response = self.send_command(cmd)
            
            if response and "NO DATA" not in response and "?" not in response and "7F" not in response:
                print(f"✓ Got response: {response}")
                results.append({
                    "did": did,
                    "description": description,
                    "response": response
                })
            else:
                print(f"✗ Not supported")
        
        return results

def main():
    print("="*70)
    print("2008 Ford Escape - Transmission Data Reader")
    print("="*70)
    print()
    print("This script will:")
    print("1. Connect to your ELM327 adapter")
    print("2. Try standard OBD-II transmission PIDs")
    print("3. Try UDS Service 0x22 for transmission data")
    print("4. Report what works")
    print()
    print("Make sure:")
    print("- FORScan is CLOSED")
    print("- Vehicle ignition is ON")
    print("- ELM327 is connected to COM3")
    print()
    input("Press Enter to continue...")
    
    reader = TransmissionReader(COM_PORT, BAUDRATE)
    
    try:
        if not reader.connect():
            return 1
        
        # Try standard OBD-II PIDs
        obd_results = reader.read_transmission_data()
        
        # Try UDS Service 0x22
        uds_results = reader.try_uds_service_22()
        
        # Summary
        print("\n" + "="*70)
        print("Summary")
        print("="*70)
        print(f"\nOBD-II PIDs that worked: {len(obd_results)}")
        for result in obd_results:
            print(f"  • {result['description']}: Mode {result['mode']:02X} PID {result['pid']:02X}")
            if result['parsed']:
                print(f"    Value: {result['parsed']}")
        
        print(f"\nUDS DIDs that worked: {len(uds_results)}")
        for result in uds_results:
            print(f"  • {result['description']}: DID 0x{result['did']:04X}")
        
        if not obd_results and not uds_results:
            print("\n⚠ No transmission parameters found!")
            print("\nThis could mean:")
            print("1. Vehicle needs to be running (not just ignition ON)")
            print("2. Transmission parameters require extended diagnostic session")
            print("3. Ford uses proprietary DIDs we haven't tried yet")
            print("\nNext step: We need ISO 14229-1 Service 0x22 documentation")
            print("to try more DIDs and enter extended diagnostic mode.")
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        reader.disconnect()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
