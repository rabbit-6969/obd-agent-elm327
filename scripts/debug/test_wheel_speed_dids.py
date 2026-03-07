#!/usr/bin/env python3
"""
Test if DIDs 0x0200 and 0x0202 are wheel speed sensors
Read them continuously and watch for changes when vehicle moves
"""

import serial
import time
import sys

class SimpleELM327:
    """Simplified ELM327 adapter"""
    
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
            time.sleep(2)
            
            # Reset and configure
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")
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

def parse_hex_response(response, did):
    """Parse hex response and extract data bytes"""
    if not response or f'62 {did}' not in response:
        return None
    
    # Remove the response header (62 DDDD)
    data = response.replace(f'62 {did}', '').strip().replace(' ', '')
    return data

def hex_to_int(hex_str):
    """Convert hex string to integer"""
    try:
        return int(hex_str, 16)
    except:
        return None

def test_wheel_speed_dids(port='COM3'):
    """Test DIDs 0x0200 and 0x0202 for wheel speed data"""
    
    print("=" * 70)
    print("Ford Escape 2008 - Wheel Speed DID Test")
    print("=" * 70)
    print()
    print("This script will continuously read DIDs 0x0200 and 0x0202")
    print("to see if they change when you roll the vehicle.")
    print()
    print("INSTRUCTIONS:")
    print("1. Start with vehicle stationary (in Park, engine can be on or off)")
    print("2. Watch the values - they should be stable")
    print("3. Put vehicle in Neutral and slowly roll it forward/backward")
    print("4. If values change, we've found wheel speed sensors!")
    print("5. Press Ctrl+C to stop")
    print()
    input("Press Enter when ready to start...")
    print()
    
    elm = SimpleELM327(port=port)
    
    try:
        if not elm.connect():
            print("❌ Failed to connect to ELM327 adapter")
            return False
        
        print("✓ Connected to ELM327 adapter")
        
        # Set header for ABS module
        elm.send_command("AT SH 760")
        time.sleep(0.1)
        
        print("✓ Set CAN header to ABS module (0x760)")
        print()
        print("-" * 70)
        print("Reading DIDs... (Press Ctrl+C to stop)")
        print("-" * 70)
        print()
        
        # Track previous values to detect changes
        prev_0200 = None
        prev_0202 = None
        
        # Track statistics
        read_count = 0
        change_count_0200 = 0
        change_count_0202 = 0
        
        while True:
            read_count += 1
            
            # Read DID 0x0200
            response_0200 = elm.send_command("22 0200")
            data_0200 = parse_hex_response(response_0200, "0200")
            
            # Read DID 0x0202
            response_0202 = elm.send_command("22 0202")
            data_0202 = parse_hex_response(response_0202, "0202")
            
            # Check for changes
            changed_0200 = (prev_0200 is not None and data_0200 != prev_0200)
            changed_0202 = (prev_0202 is not None and data_0202 != prev_0202)
            
            if changed_0200:
                change_count_0200 += 1
            if changed_0202:
                change_count_0202 += 1
            
            # Display current values
            timestamp = time.strftime("%H:%M:%S")
            
            print(f"[{timestamp}] Read #{read_count}")
            
            if data_0200:
                value_0200 = hex_to_int(data_0200)
                change_indicator = " ← CHANGED!" if changed_0200 else ""
                print(f"  DID 0x0200: {data_0200} (decimal: {value_0200}){change_indicator}")
            else:
                print(f"  DID 0x0200: No response")
            
            if data_0202:
                value_0202 = hex_to_int(data_0202)
                change_indicator = " ← CHANGED!" if changed_0202 else ""
                print(f"  DID 0x0202: {data_0202} (decimal: {value_0202}){change_indicator}")
            else:
                print(f"  DID 0x0202: No response")
            
            print(f"  Changes: 0x0200={change_count_0200}, 0x0202={change_count_0202}")
            print()
            
            # Update previous values
            prev_0200 = data_0200
            prev_0202 = data_0202
            
            # Wait before next read
            time.sleep(0.5)  # Read twice per second
    
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Test stopped by user")
        print("=" * 70)
        print()
        print("RESULTS:")
        print(f"  Total reads: {read_count}")
        print(f"  DID 0x0200 changes: {change_count_0200}")
        print(f"  DID 0x0202 changes: {change_count_0202}")
        print()
        
        if change_count_0200 > 0 or change_count_0202 > 0:
            print("✓ VALUES CHANGED! These DIDs likely contain dynamic data.")
            print()
            if change_count_0200 > 0:
                print("  DID 0x0200 changed - could be wheel speed or other sensor")
            if change_count_0202 > 0:
                print("  DID 0x0202 changed - could be wheel speed or other sensor")
            print()
            print("NEXT STEPS:")
            print("1. Note which DID(s) changed when you rolled the vehicle")
            print("2. Test again with different wheel movements to confirm")
            print("3. Try scanning more DIDs (0x0201, 0x0203, 0x0204, etc.)")
        else:
            print("⚠ No changes detected")
            print()
            print("POSSIBLE REASONS:")
            print("1. Vehicle didn't move enough")
            print("2. These DIDs are not wheel speeds")
            print("3. Wheel speeds are in different DIDs")
            print()
            print("NEXT STEPS:")
            print("1. Try rolling vehicle more")
            print("2. Scan more DIDs in 0x0200-0x02FF range")
        
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
    
    parser = argparse.ArgumentParser(description='Test Ford Escape ABS DIDs for wheel speed data')
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    
    args = parser.parse_args()
    
    success = test_wheel_speed_dids(port=args.port)
    sys.exit(0 if success else 1)
