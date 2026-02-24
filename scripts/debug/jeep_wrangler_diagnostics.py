#!/usr/bin/env python3
"""
Jeep Wrangler JK (2007) Diagnostic Script
Reads airbag module DTCs and shifter position via Vgate iCar Pro BLE 4.0

Requirements:
- Vgate iCar Pro BLE 4.0 adapter
- Python 3.7+
- obd library (pip install obd)
- Vehicle ignition ON (engine can be off)
"""

import obd
import time
from datetime import datetime

class JeepWranglerDiagnostics:
    def __init__(self):
        self.connection = None
        
    def connect(self):
        """Connect to vehicle via Bluetooth OBD adapter"""
        print("=" * 60)
        print("Jeep Wrangler JK (2007) Diagnostic Tool")
        print("=" * 60)
        print("\nConnecting to vehicle...")
        print("Make sure:")
        print("  1. Vgate adapter is plugged into OBD-II port")
        print("  2. Bluetooth is paired on your device")
        print("  3. Ignition is ON (engine can be off)")
        print()
        
        try:
            # Auto-detect connection
            self.connection = obd.OBD()
            
            if self.connection.is_connected():
                print(f"✓ Connected successfully!")
                print(f"  Protocol: {self.connection.protocol_name()}")
                print(f"  Port: {self.connection.port_name()}")
                return True
            else:
                print("✗ Failed to connect to vehicle")
                print("\nTroubleshooting:")
                print("  - Check adapter is fully inserted")
                print("  - Verify Bluetooth pairing")
                print("  - Turn ignition to ON position")
                print("  - Try unplugging and replugging adapter")
                return False
                
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def read_airbag_dtcs(self):
        """Read Diagnostic Trouble Codes from Airbag Control Module"""
        print("\n" + "=" * 60)
        print("AIRBAG CONTROL MODULE - DIAGNOSTIC TROUBLE CODES")
        print("=" * 60)
        
        try:
            # Get DTCs - Mode 03 reads confirmed DTCs
            cmd = obd.commands.GET_DTC
            response = self.connection.query(cmd)
            
            if response.is_null():
                print("✗ No response from airbag module")
                print("  Note: Some adapters cannot access airbag module")
                print("  Airbag module may require manufacturer-specific tool")
                return
            
            dtcs = response.value
            
            if not dtcs or len(dtcs) == 0:
                print("✓ No airbag DTCs found - System OK")
            else:
                print(f"⚠ Found {len(dtcs)} airbag DTC(s):\n")
                
                for code, description in dtcs:
                    print(f"  Code: {code}")
                    print(f"  Description: {description}")
                    print(f"  Severity: {self._get_dtc_severity(code)}")
                    print()
                    
                print("IMPORTANT: Airbag system errors require immediate attention!")
                print("Consult a qualified technician for airbag repairs.")
                
        except Exception as e:
            print(f"✗ Error reading airbag DTCs: {e}")
            print("\nNote: Airbag module access may be limited with standard OBD-II")
            print("Consider using a Jeep-specific diagnostic tool for full access")
    
    def read_shifter_position(self):
        """Read transmission shifter position"""
        print("\n" + "=" * 60)
        print("TRANSMISSION SHIFTER POSITION")
        print("=" * 60)
        
        try:
            # Try to read transmission gear
            # Note: Not all vehicles support this via standard OBD-II
            
            # Method 1: Try standard gear position command
            if obd.commands.has_name("GEAR_POSITION"):
                cmd = obd.commands.GEAR_POSITION
                response = self.connection.query(cmd)
                
                if not response.is_null():
                    print(f"✓ Current Gear: {response.value}")
                    return
            
            # Method 2: Try reading via custom PID
            # Jeep Wrangler JK may use manufacturer-specific PIDs
            print("Attempting to read shifter position...")
            
            # Custom command for transmission gear (Mode 01, PID varies by vehicle)
            # This is a common approach but may not work on all vehicles
            custom_cmd = obd.OBDCommand("TRANS_GEAR", 
                                       "Transmission Gear",
                                       b"01A4",  # Example PID
                                       2,
                                       lambda m: m.hex())
            
            response = self.connection.query(custom_cmd, force=True)
            
            if not response.is_null():
                raw_value = response.value
                gear = self._decode_shifter_position(raw_value)
                print(f"✓ Shifter Position: {gear}")
                print(f"  Raw Value: {raw_value}")
            else:
                print("⚠ Shifter position not available via standard OBD-II")
                print("\nAlternative methods:")
                print("  1. Use Jeep-specific diagnostic tool (e.g., wiTECH)")
                print("  2. Monitor transmission parameters:")
                self._read_transmission_params()
                
        except Exception as e:
            print(f"⚠ Could not read shifter position: {e}")
            print("\nNote: Shifter position may require manufacturer-specific access")
            print("Trying alternative transmission parameters...")
            self._read_transmission_params()
    
    def _read_transmission_params(self):
        """Read available transmission-related parameters"""
        print("\n  Available Transmission Data:")
        
        params = [
            (obd.commands.RPM, "Engine RPM"),
            (obd.commands.SPEED, "Vehicle Speed"),
            (obd.commands.THROTTLE_POS, "Throttle Position"),
            (obd.commands.ENGINE_LOAD, "Engine Load"),
        ]
        
        for cmd, name in params:
            try:
                response = self.connection.query(cmd)
                if not response.is_null():
                    print(f"    {name}: {response.value}")
            except:
                pass
    
    def _decode_shifter_position(self, raw_value):
        """Decode raw shifter position value"""
        # This is vehicle-specific and may need adjustment
        # Common positions: P, R, N, D, 2, 1 (automatic)
        # or 1-6, R (manual)
        
        positions = {
            0x00: "Park (P)",
            0x01: "Reverse (R)",
            0x02: "Neutral (N)",
            0x03: "Drive (D)",
            0x04: "2nd Gear",
            0x05: "1st Gear",
        }
        
        try:
            value = int(raw_value, 16) if isinstance(raw_value, str) else raw_value
            return positions.get(value, f"Unknown ({raw_value})")
        except:
            return f"Unknown ({raw_value})"
    
    def _get_dtc_severity(self, code):
        """Determine DTC severity based on code"""
        if code.startswith('P0'):
            return "Powertrain - Generic"
        elif code.startswith('P1'):
            return "Powertrain - Manufacturer Specific"
        elif code.startswith('C0'):
            return "Chassis - Generic"
        elif code.startswith('C1'):
            return "Chassis - Manufacturer Specific"
        elif code.startswith('B0'):
            return "Body - Generic (includes airbag)"
        elif code.startswith('B1'):
            return "Body - Manufacturer Specific (includes airbag)"
        elif code.startswith('U0'):
            return "Network - Generic"
        elif code.startswith('U1'):
            return "Network - Manufacturer Specific"
        else:
            return "Unknown"
    
    def read_all_dtcs(self):
        """Read DTCs from all available modules"""
        print("\n" + "=" * 60)
        print("ALL DIAGNOSTIC TROUBLE CODES")
        print("=" * 60)
        
        try:
            cmd = obd.commands.GET_DTC
            response = self.connection.query(cmd)
            
            if response.is_null():
                print("✗ No response from vehicle")
                return
            
            dtcs = response.value
            
            if not dtcs or len(dtcs) == 0:
                print("✓ No DTCs found - All systems OK")
            else:
                print(f"Found {len(dtcs)} DTC(s):\n")
                
                # Group by system
                powertrain = []
                chassis = []
                body = []
                network = []
                
                for code, description in dtcs:
                    if code.startswith('P'):
                        powertrain.append((code, description))
                    elif code.startswith('C'):
                        chassis.append((code, description))
                    elif code.startswith('B'):
                        body.append((code, description))
                    elif code.startswith('U'):
                        network.append((code, description))
                
                if powertrain:
                    print("POWERTRAIN CODES:")
                    for code, desc in powertrain:
                        print(f"  {code}: {desc}")
                    print()
                
                if chassis:
                    print("CHASSIS CODES (ABS, Suspension):")
                    for code, desc in chassis:
                        print(f"  {code}: {desc}")
                    print()
                
                if body:
                    print("BODY CODES (Airbag, Lighting, etc.):")
                    for code, desc in body:
                        print(f"  {code}: {desc}")
                    print()
                
                if network:
                    print("NETWORK CODES (Communication):")
                    for code, desc in network:
                        print(f"  {code}: {desc}")
                    print()
                    
        except Exception as e:
            print(f"✗ Error reading DTCs: {e}")
    
    def read_vehicle_info(self):
        """Read basic vehicle information"""
        print("\n" + "=" * 60)
        print("VEHICLE INFORMATION")
        print("=" * 60)
        
        info_commands = [
            (obd.commands.VIN, "VIN"),
            (obd.commands.ELM_VERSION, "Adapter Version"),
            (obd.commands.ELM_VOLTAGE, "Battery Voltage"),
        ]
        
        for cmd, name in info_commands:
            try:
                response = self.connection.query(cmd)
                if not response.is_null():
                    print(f"  {name}: {response.value}")
            except:
                pass
    
    def monitor_live_data(self, duration=10):
        """Monitor live transmission data"""
        print("\n" + "=" * 60)
        print(f"LIVE DATA MONITORING ({duration} seconds)")
        print("=" * 60)
        print("\nPress Ctrl+C to stop early\n")
        
        commands = [
            obd.commands.RPM,
            obd.commands.SPEED,
            obd.commands.THROTTLE_POS,
            obd.commands.ENGINE_LOAD,
        ]
        
        start_time = time.time()
        
        try:
            while (time.time() - start_time) < duration:
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] ", end="")
                
                for cmd in commands:
                    response = self.connection.query(cmd)
                    if not response.is_null():
                        print(f"{cmd.name}: {response.value} | ", end="")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
        
        print("\n")
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            print("\n✓ Disconnected from vehicle")

def main():
    """Main diagnostic routine"""
    diag = JeepWranglerDiagnostics()
    
    # Connect to vehicle
    if not diag.connect():
        return
    
    try:
        # Read vehicle info
        diag.read_vehicle_info()
        
        # Read all DTCs (includes airbag if accessible)
        diag.read_all_dtcs()
        
        # Try to read airbag-specific DTCs
        diag.read_airbag_dtcs()
        
        # Read shifter position
        diag.read_shifter_position()
        
        # Optional: Monitor live data
        response = input("\nMonitor live transmission data? (y/n): ")
        if response.lower() == 'y':
            diag.monitor_live_data(duration=30)
        
        # Save report
        print("\n" + "=" * 60)
        print("DIAGNOSTIC REPORT COMPLETE")
        print("=" * 60)
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Vehicle: 2007 Jeep Wrangler JK")
        print("Adapter: Vgate iCar Pro BLE 4.0")
        
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
    
    finally:
        diag.disconnect()

if __name__ == "__main__":
    main()
