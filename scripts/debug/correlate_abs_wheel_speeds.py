#!/usr/bin/env python3
"""
Ford Escape 2008 - ABS DID and CAN Wheel Speed Correlation Test

This script monitors both:
1. CAN message 0x4B0 (known wheel speeds from CAN bus)
2. ABS DIDs 0x0200 and 0x0202 (unknown parameters)

Purpose: Determine if DIDs 0x0200/0x0202 contain wheel speed data by
comparing them with the known CAN wheel speed data.

Usage:
    python scripts/debug/correlate_abs_wheel_speeds.py
    
    Then slowly roll the vehicle to see which values change together.
"""

import serial
import time
import sys
from datetime import datetime

class ELM327:
    """ELM327 adapter interface"""
    
    def __init__(self, port='COM3', baudrate=38400, timeout=2):
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
            self.send_command("ATH1")  # Headers on (needed for CAN monitoring)
            self.send_command("ATSP6")  # Set protocol to ISO 15765-4 CAN (500kbaud)
            
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
            print(f"Command error: {e}")
            return None
    
    def read_can_message(self, can_id):
        """
        Read a specific CAN message by ID
        
        Args:
            can_id: CAN message ID (e.g., 0x4B0)
        
        Returns:
            Hex string of data bytes, or None if not found
        """
        # Set CAN filter to only receive specific message
        self.send_command(f"ATCF{can_id:03X}")
        
        # Monitor for the message (short timeout)
        old_timeout = self.ser.timeout
        self.ser.timeout = 0.5
        
        response = self.send_command("ATMA")  # Monitor all
        
        self.ser.timeout = old_timeout
        
        # Stop monitoring
        self.ser.write(b'\r')
        time.sleep(0.1)
        
        if response and len(response) > 8:
            # Parse CAN message: format is "4B0 XX XX XX XX XX XX XX XX"
            # Extract just the data bytes
            parts = response.split()
            if len(parts) >= 9:
                return ' '.join(parts[1:9])  # Return 8 data bytes
        
        return None
    
    def read_abs_did(self, did):
        """
        Read ABS module DID
        
        Args:
            did: DID to read (e.g., 0x0200)
        
        Returns:
            Hex string of data, or None if failed
        """
        # Set header for ABS module
        self.send_command("ATSH760")
        
        # Read DID
        did_high = (did >> 8) & 0xFF
        did_low = did & 0xFF
        response = self.send_command(f"22{did_high:02X}{did_low:02X}")
        
        if response and '62' in response:
            # Positive response: 62 XX XX [data]
            # Remove the response header
            data = response.replace('62', '').replace(f'{did_high:02X}', '').replace(f'{did_low:02X}', '').strip()
            return data
        
        return None
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def parse_wheel_speeds_from_can(data_hex):
    """
    Parse wheel speeds from CAN 0x4B0 message
    
    Format (from Mazda CAN Bus Reference):
    - Bytes 0-1: Left Front Wheel Speed
    - Bytes 2-3: Right Front Wheel Speed
    - Bytes 4-5: Left Rear Wheel Speed
    - Bytes 6-7: Right Rear Wheel Speed
    
    Scaling: (value - 10000) / 100 = km/h
    
    Args:
        data_hex: String of hex bytes (e.g., "27 10 27 10 27 10 27 10")
    
    Returns:
        Dictionary with wheel speeds in km/h
    """
    try:
        bytes_list = [int(b, 16) for b in data_hex.split()]
        
        if len(bytes_list) < 8:
            return None
        
        # Parse 16-bit values (big-endian)
        lf_raw = (bytes_list[0] << 8) | bytes_list[1]
        rf_raw = (bytes_list[2] << 8) | bytes_list[3]
        lr_raw = (bytes_list[4] << 8) | bytes_list[5]
        rr_raw = (bytes_list[6] << 8) | bytes_list[7]
        
        # Apply scaling
        lf_speed = (lf_raw - 10000) / 100.0
        rf_speed = (rf_raw - 10000) / 100.0
        lr_speed = (lr_raw - 10000) / 100.0
        rr_speed = (rr_raw - 10000) / 100.0
        
        return {
            'left_front': lf_speed,
            'right_front': rf_speed,
            'left_rear': lr_speed,
            'right_rear': rr_speed,
            'raw_hex': data_hex
        }
    except Exception as e:
        print(f"Error parsing wheel speeds: {e}")
        return None

def format_wheel_speeds(speeds):
    """Format wheel speeds for display"""
    if not speeds:
        return "N/A"
    
    return (f"LF:{speeds['left_front']:6.2f} RF:{speeds['right_front']:6.2f} "
            f"LR:{speeds['left_rear']:6.2f} RR:{speeds['right_rear']:6.2f} km/h")

def main(port='COM3', duration=60, interval=1.0):
    """
    Run correlation test
    
    Args:
        port: Serial port for ELM327
        duration: How long to monitor (seconds)
        interval: Time between readings (seconds)
    """
    print("=" * 80)
    print("Ford Escape 2008 - ABS DID and CAN Wheel Speed Correlation Test")
    print("=" * 80)
    print()
    print("This script will monitor:")
    print("  1. CAN 0x4B0 - Known wheel speeds (broadcast on CAN bus)")
    print("  2. ABS DID 0x0200 - Unknown parameter")
    print("  3. ABS DID 0x0202 - Unknown parameter")
    print()
    print("Instructions:")
    print("  - Keep vehicle stationary initially (baseline)")
    print("  - Then slowly roll vehicle forward/backward")
    print("  - Watch which values change together")
    print("  - Press Ctrl+C to stop early")
    print()
    print(f"Monitoring for {duration} seconds with {interval}s intervals...")
    print()
    
    # Connect to adapter
    elm = ELM327(port=port)
    
    if not elm.connect():
        print("Failed to connect to ELM327")
        return False
    
    print("Connected to ELM327")
    print()
    
    # Print header
    print(f"{'Time':<12} {'CAN Wheel Speeds (km/h)':<60} {'DID 0x0200':<20} {'DID 0x0202':<20}")
    print("-" * 112)
    
    start_time = time.time()
    sample_count = 0
    
    try:
        while time.time() - start_time < duration:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Read CAN wheel speeds
            can_data = elm.read_can_message(0x4B0)
            wheel_speeds = parse_wheel_speeds_from_can(can_data) if can_data else None
            
            # Read ABS DIDs
            did_0200 = elm.read_abs_did(0x0200)
            did_0202 = elm.read_abs_did(0x0202)
            
            # Format output
            can_str = format_wheel_speeds(wheel_speeds) if wheel_speeds else "No data"
            did_0200_str = did_0200 if did_0200 else "No response"
            did_0202_str = did_0202 if did_0202 else "No response"
            
            print(f"{timestamp:<12} {can_str:<60} {did_0200_str:<20} {did_0202_str:<20}")
            
            sample_count += 1
            
            # Wait for next interval
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print()
        print("Monitoring stopped by user")
    
    finally:
        elm.close()
    
    print()
    print("=" * 80)
    print("Correlation Test Complete")
    print("=" * 80)
    print(f"Total samples: {sample_count}")
    print()
    print("Analysis:")
    print("  - If DID 0x0200 or 0x0202 values change when wheel speeds change:")
    print("    → They likely contain wheel speed or related ABS data")
    print("  - If DID values stay constant (all zeros):")
    print("    → They likely contain status flags, pressure, or other parameters")
    print("  - Compare the hex patterns to identify correlations")
    print()
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Correlate ABS DIDs with CAN wheel speed data'
    )
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    parser.add_argument('--duration', type=int, default=60, 
                       help='Monitoring duration in seconds (default: 60)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Time between readings in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, duration=args.duration, interval=args.interval)
    sys.exit(0 if success else 1)
