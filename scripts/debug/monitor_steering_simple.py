#!/usr/bin/env python3
"""
Ford Escape 2008 - Steering Wheel Angle Monitor (Simple)

Monitors CAN ID 0x080 byte 6 for steering wheel angle.
Displays angle changes as you turn the steering wheel.

DISCOVERED: Steering angle is in CAN ID 0x080, byte 6
- Raw value: 0-255
- Center position: ~128 (needs calibration)
- Formula: TBD (need to correlate with actual wheel position)

⚠️ SAFETY: This is READ-ONLY passive monitoring - no messages are sent.

Usage:
    python scripts/debug/monitor_steering_simple.py --port COM4
    
    Turn the steering wheel and watch the values.
    Note the center position value when wheel is straight.
    Press Ctrl+C to stop.
"""

import serial
import time
import sys
from datetime import datetime

class ELM327:
    """ELM327 adapter interface"""
    
    def __init__(self, port='COM4', baudrate=38400, timeout=2):
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
            self.send_command("ATE0")
            self.send_command("ATL0")
            self.send_command("ATS1")  # Spaces ON
            self.send_command("ATH1")  # Headers ON
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
    
    def start_monitor(self):
        """Start monitoring CAN ID 0x080"""
        self.send_command("ATCRA080")
        
        self.ser.reset_input_buffer()
        self.ser.write(b'ATMA\r')
        time.sleep(0.3)
    
    def stop_monitor(self):
        """Stop monitoring"""
        self.ser.write(b'\r')
        time.sleep(0.2)
        self.ser.reset_input_buffer()
        self.send_command("ATCRA")
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def monitor_steering(elm, duration=60):
    """Monitor steering angle and display in real-time"""
    print("=" * 80)
    print("Steering Wheel Angle Monitor")
    print("=" * 80)
    print()
    print("Monitoring CAN ID 0x080, Byte 6")
    print()
    print("Turn the steering wheel slowly and watch the values.")
    print("Note the value when wheel is centered (straight ahead).")
    print("Press Ctrl+C to stop.")
    print()
    print("-" * 80)
    print(f"{'Time':<12} {'Byte 6':<10} {'Signed':<10} {'Full Message':<40}")
    print("-" * 80)
    
    elm.start_monitor()
    
    buffer = ""
    start_time = time.time()
    last_value = None
    message_count = 0
    
    try:
        while duration == 0 or (time.time() - start_time < duration):
            if elm.ser.in_waiting:
                chunk = elm.ser.read(elm.ser.in_waiting).decode('ascii', errors='ignore')
                buffer += chunk
                
                while '\r' in buffer or '\n' in buffer:
                    if '\r' in buffer:
                        line, buffer = buffer.split('\r', 1)
                    else:
                        line, buffer = buffer.split('\n', 1)
                    
                    line = line.strip()
                    
                    if not line or line == '>' or 'BUFFER' in line or 'STOPPED' in line:
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 2 and len(parts[0]) == 3:
                        try:
                            can_id = int(parts[0], 16)
                            
                            if can_id == 0x080:
                                # Clean data bytes
                                data_parts = []
                                for p in parts[1:]:
                                    if 'DATA' in p or 'ERROR' in p or '<' in p:
                                        continue
                                    if len(p) == 2:
                                        try:
                                            int(p, 16)
                                            data_parts.append(p)
                                        except ValueError:
                                            break
                                    else:
                                        break
                                
                                if len(data_parts) >= 7:
                                    byte6 = int(data_parts[6], 16)
                                    
                                    # Only display if value changed
                                    if last_value is None or byte6 != last_value:
                                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                        
                                        # Calculate signed value (assuming 128 is center)
                                        signed = byte6 - 128
                                        
                                        data_str = ' '.join(data_parts[:8])
                                        
                                        print(f"{timestamp:<12} {byte6:<10} {signed:+4d}       {data_str:<40}")
                                        
                                        last_value = byte6
                                        message_count += 1
                        
                        except (ValueError, IndexError):
                            pass
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print()
        print("-" * 80)
        print(f"\nMonitoring stopped. Captured {message_count} value changes.")
        print()
        print("NEXT STEPS:")
        print("  1. Note the 'center' value when wheel is straight")
        print("  2. Note the min/max values at full left/right lock")
        print("  3. This will help determine the scaling formula")
        print()
    
    finally:
        elm.stop_monitor()

def main(port='COM4', duration=0):
    """Main entry point"""
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
    
    try:
        monitor_steering(elm, duration=duration)
        return True
    
    finally:
        elm.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor steering wheel angle (CAN ID 0x080, byte 6)'
    )
    parser.add_argument('--port', default='COM4', 
                       help='Serial port (default: COM4)')
    parser.add_argument('--duration', type=int, default=0,
                       help='Duration in seconds (default: infinite)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, duration=args.duration)
    sys.exit(0 if success else 1)
