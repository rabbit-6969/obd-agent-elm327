#!/usr/bin/env python3
"""
Test connection to 2008 Ford Escape ABS Module
Tests module presence and basic communication
"""

import serial
import time
import sys

class SimpleELM327:
    """Simplified ELM327 adapter for testing"""
    
    def __init__(self, port='COM3', baudrate=38400, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
    
    def connect(self):
        """Connect to ELM327 adapter"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for adapter to initialize
            
            # Reset adapter
            self.send_command("ATZ")
            time.sleep(1)
            
            # Turn off echo
            self.send_command("ATE0")
            
            # Set protocol to auto
            self.send_command("ATSP0")
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def send_command(self, command):
        """Send command and get response"""
        if not self.ser:
            return None
        
        try:
            # Clear buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # Send command
            self.ser.write((command + '\r').encode())
            
            # Read response
            response = b''
            start_time = time.time()
            
            while time.time() - start_time < self.timeout:
                if self.ser.in_waiting:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response += chunk
                    
                    if b'>' in response:
                        break
                
                time.sleep(0.05)
            
            # Decode and clean response
            response_str = response.decode('ascii', errors='ignore')
            response_str = response_str.replace('\r', '').replace('\n', ' ')
            response_str = response_str.replace('>', '').strip()
            
            return response_str
        
        except Exception as e:
            print(f"Command error: {e}")
            return None
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def test_abs_connection(port='COM3'):
    """Test connection to Ford Escape ABS module"""
    
    print("=" * 60)
    print("Ford Escape 2008 - ABS Module Connection Test")
    print("=" * 60)
    print()
    
    # Initialize adapter
    print(f"Connecting to ELM327 adapter on {port}...")
    elm = SimpleELM327(port=port)
    
    try:
        if not elm.connect():
            print("❌ Failed to connect to ELM327 adapter")
            return False
        
        print("✓ Connected to ELM327 adapter")
        print()
        
        # ABS module address for Ford Escape 2008
        abs_request = 0x760
        abs_response = 0x768
        
        print(f"ABS Module Address: 0x{abs_request:03X} (Request) / 0x{abs_response:03X} (Response)")
        print()
        
        # Set header for ABS module
        print("Setting CAN header for ABS module...")
        elm.send_command(f"AT SH {abs_request:03X}")
        time.sleep(0.1)
        
        # Test 1: Tester Present (all three variants)
        print("-" * 60)
        print("Test 1: Tester Present (Module Presence Detection)")
        print("-" * 60)
        
        tester_present_variants = [
            ("3E 01", "Tester Present with response suppression disabled"),
            ("3E 00", "Tester Present with response suppression enabled"),
            ("3E", "Tester Present (minimal format)")
        ]
        
        module_responding = False
        working_variant = None
        
        for command, description in tester_present_variants:
            print(f"\nTrying: {command} - {description}")
            response = elm.send_command(command)
            print(f"Response: {response}")
            
            if response and '7E' in response:
                print("✓ Module responded! (7E = positive response)")
                module_responding = True
                working_variant = command
                break
            elif response and '7F' in response:
                print("⚠ Negative response (module present but service not supported)")
                module_responding = True
                working_variant = command
            else:
                print("✗ No response")
        
        if not module_responding:
            print("\n❌ ABS module not responding to any Tester Present variant")
            print("\nPossible causes:")
            print("1. Wrong CAN address (try 0x750 as alternative)")
            print("2. Module requires extended diagnostic session")
            print("3. Module on secondary CAN bus (ELM327 cannot reach)")
            print("4. Adapter limitation")
            print("5. Vehicle not in correct state (try ignition ON, engine OFF)")
            return False
        
        print(f"\n✓ ABS module is responding (working variant: {working_variant})")
        
        # Test 2: Read VIN
        print("\n" + "-" * 60)
        print("Test 2: Read VIN (DID 0xF190)")
        print("-" * 60)
        
        response = elm.send_command("22 F1 90")
        print(f"Command: 22 F1 90")
        print(f"Response: {response}")
        
        if response and '62 F1 90' in response:
            print("✓ VIN read successful")
            # Parse VIN from response
            vin_hex = response.replace('62 F1 90', '').strip().replace(' ', '')
            if len(vin_hex) >= 34:  # 17 bytes = 34 hex chars
                try:
                    vin = bytes.fromhex(vin_hex[:34]).decode('ascii', errors='ignore')
                    print(f"VIN: {vin}")
                except:
                    print(f"VIN (hex): {vin_hex[:34]}")
        else:
            print("⚠ VIN read failed or not supported")
        
        # Test 3: Try extended diagnostic session
        print("\n" + "-" * 60)
        print("Test 3: Extended Diagnostic Session")
        print("-" * 60)
        
        response = elm.send_command("10 03")
        print(f"Command: 10 03 (Enter Extended Session)")
        print(f"Response: {response}")
        
        if response and '50 03' in response:
            print("✓ Extended diagnostic session entered")
        else:
            print("⚠ Extended session not supported or failed")
        
        # Test 4: Read module identification DIDs
        print("\n" + "-" * 60)
        print("Test 4: Module Identification DIDs")
        print("-" * 60)
        
        dids = [
            ("F181", "Calibration ID"),
            ("F18C", "ECU Serial Number"),
            ("F187", "Spare Part Number"),
            ("F191", "ECU Hardware Number")
        ]
        
        for did, description in dids:
            print(f"\nReading DID 0x{did} ({description})...")
            response = elm.send_command(f"22 {did}")
            print(f"Response: {response}")
            
            if response and f'62 {did}' in response:
                print(f"✓ {description} read successful")
            else:
                print(f"✗ {description} not available")
        
        # Test 5: Try reading DTCs
        print("\n" + "-" * 60)
        print("Test 5: Read DTCs (Service 0x19)")
        print("-" * 60)
        
        response = elm.send_command("19 02 FF")
        print(f"Command: 19 02 FF (Read DTCs by status)")
        print(f"Response: {response}")
        
        if response and '59 02' in response:
            print("✓ DTC read successful")
            # Parse DTCs
            dtc_data = response.replace('59 02', '').strip()
            if dtc_data and dtc_data != '00':
                print(f"DTCs present: {dtc_data}")
            else:
                print("No DTCs stored")
        elif response and '7F 19' in response:
            print("⚠ Service not supported (normal for some Ford ABS modules)")
            print("Note: Ford Escape 2008 ABS may not support standard DTC reading")
        else:
            print("✗ No response to DTC read")
        
        # Test 6: Try known working DIDs from knowledge base
        print("\n" + "-" * 60)
        print("Test 6: Known ABS DIDs (from knowledge base)")
        print("-" * 60)
        
        known_dids = [
            ("0200", "Unknown ABS Parameter"),
            ("0202", "Unknown ABS Parameter")
        ]
        
        for did, description in known_dids:
            print(f"\nReading DID 0x{did} ({description})...")
            response = elm.send_command(f"22 {did}")
            print(f"Response: {response}")
            
            if response and f'62 {did}' in response:
                print(f"✓ {description} read successful")
                # Show hex data
                data = response.replace(f'62 {did}', '').strip()
                print(f"Data: {data}")
            else:
                print(f"✗ {description} not available")
        
        print("\n" + "=" * 60)
        print("Connection Test Complete")
        print("=" * 60)
        print("\n✓ ABS module is accessible and responding")
        print(f"✓ Working Tester Present variant: {working_variant}")
        print("\nNext steps:")
        print("1. Use working variant for future communication")
        print("2. Explore additional DIDs for ABS parameters")
        print("3. Document which services are supported")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        elm.close()
        print("\nConnection closed.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Ford Escape 2008 ABS module connection')
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    
    args = parser.parse_args()
    
    success = test_abs_connection(port=args.port)
    sys.exit(0 if success else 1)
