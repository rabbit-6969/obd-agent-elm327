#!/usr/bin/env python3
"""
Ford Escape 2008 - Steering Wheel Angle Monitor

Monitors CAN ID 0x4DA and decodes steering wheel angle in real-time.
Displays angle changes as you turn the steering wheel.

Based on Mazda CAN Bus Reference:
- CAN ID: 0x4DA
- Bytes 0-1: Steering angle (16-bit big-endian)
- Formula: (value - 32768) / 10 degrees
- Clockwise = positive

⚠️ SAFETY: This is READ-ONLY passive monitoring - no messages are sent.

Usage:
    python scripts/debug/monitor_steering_angle.py
    
    Then turn the steering wheel and watch the angle values update.
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
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATS1")  # Spaces ON (required for ATCRA)
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
    
    def start_steering_monitor(self, can_id=0x080):
        """Start monitoring specified CAN ID for steering angle"""
        # Set filter for steering angle CAN ID
        can_id_hex = f"{can_id:03X}"
        self.send_command(f"ATCRA{can_id_hex}")
        
        # Start monitoring
        self.ser.reset_input_buffer()
        self.ser.write(b'ATMA\r')
        time.sleep(0.3)
    
    def stop_monitoring(self):
        """Stop monitoring and clear filter"""
        self.ser.write(b'\r')
        time.sleep(0.2)
        self.ser.reset_input_buffer()
        self.send_command("ATCRA")  # Clear filter
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def decode_steering_angle_0x080(data_bytes):
    """
    Decode steering wheel angle from CAN ID 0x080
    
    Testing hypothesis: Bytes 6-7 might contain steering angle
    
    Args:
        data_bytes: String like "4E 0D 4E 22 01 C3 54 FF"
    
    Returns:
        Dict with multiple interpretations or None if invalid
    """
    try:
        parts = data_bytes.split()
        
        # Remove <DATA ERROR if present
        parts = [p for p in parts if 'DATA' not in p and 'ERROR' not in p and '<' not in p]
        
        if len(parts) < 8:
            return None
        
        # Try different byte positions and formulas
        results = {}
        
        # Hypothesis 1: Bytes 6-7 (changed from 0x54FF to 0x97FF)
        byte6 = int(parts[6], 16)
        byte7 = int(parts[7], 16)
        raw_67 = (byte6 << 8) | byte7
        results['bytes_6_7_raw'] = raw_67
        results['bytes_6_7_signed'] = raw_67 - 32768 if raw_67 >= 32768 else raw_67
        results['bytes_6_7_div10'] = (raw_67 - 32768) / 10.0
        
        # Hypothesis 2: Byte 6 only
        results['byte_6_raw'] = byte6
        results['byte_6_signed'] = byte6 - 128 if byte6 >= 128 else byte6
        
        # Hypothesis 3: Bytes 0-1 (RPM area but might have steering mixed in)
        byte0 = int(parts[0], 16)
        byte1 = int(parts[1], 16)
        raw_01 = (byte0 << 8) | byte1
        results['bytes_0_1_raw'] = raw_01
        
        return results
    
    except (ValueError, IndexError):
        return None

def decode_steering_angle_0x420(data_bytes):
    """
    Decode steering wheel angle from CAN ID 0x420
    
    Testing hypothesis: Bytes 0-1 changed from 0x8035 to 0x7F35
    
    Args:
        data_bytes: String like "80 35 C2 00 00 00 03 00"
    
    Returns:
        Dict with multiple interpretations or None if invalid
    """
    try:
        parts = data_bytes.split()
        
        # Remove <DATA ERROR if present
        parts = [p for p in parts if 'DATA' not in p and 'ERROR' not in p and '<' not in p]
        
        if len(parts) < 2:
            return None
        
        # Try different interpretations
        results = {}
        
        # Bytes 0-1
        byte0 = int(parts[0], 16)
        byte1 = int(parts[1], 16)
        raw_01 = (byte0 << 8) | byte1
        results['bytes_0_1_raw'] = raw_01
        results['bytes_0_1_signed'] = raw_01 - 32768 if raw_01 >= 32768 else raw_01
        results['bytes_0_1_div10'] = (raw_01 - 32768) / 10.0
        
        # Byte 0 only
        results['byte_0_raw'] = byte0
        results['byte_0_signed'] = byte0 - 128 if byte0 >= 128 else byte0
        
        # Byte 2 (the counter we saw)
        if len(parts) >= 3:
            byte2 = int(parts[2], 16)
            results['byte_2_counter'] = byte2
        
        return results
    
    except (ValueError, IndexError):
        return None

def monitor_steering(elm, can_id=0x080, duration=60):
    """
    Monitor steering angle and display in real-time
    
    Args:
        elm: ELM327 instance
        can_id: CAN ID to monitor (0x080 or 0x420)
        duration: How long to monitor (seconds), 0 = infinite
    """
    print("=" * 80)
    print("Steering Wheel Angle Monitor - Experimental Decoder")
    print("=" * 80)
    print()
    print(f"Monitoring CAN ID 0x{can_id:03X}")
    print("Testing multiple byte positions and formulas")
    print()
    print("Turn the steering wheel and watch for values that correlate with angle.")
    print("Press Ctrl+C to stop.")
    print()
    print("-" * 80)
    
    elm.start_steering_monitor(can_id)
    
    buffer = ""
    start_time = time.time()
    message_count = 0
    
    try:
        while duration == 0 or (time.time() - start_time < duration):
            if elm.ser.in_waiting:
                chunk = elm.ser.read(elm.ser.in_waiting).decode('ascii', errors='ignore')
                buffer += chunk
                
                # Process complete lines
                while '\r' in buffer or '\n' in buffer:
                    if '\r' in buffer:
                        line, buffer = buffer.split('\r', 1)
                    else:
                        line, buffer = buffer.split('\n', 1)
                    
                    line = line.strip()
                    
                    # Skip empty lines, prompts, and status messages
                    if not line or line == '>' or 'BUFFER' in line or 'STOPPED' in line:
                        continue
                    
                    # Parse message
                    parts = line.split()
                    if len(parts) >= 2 and len(parts[0]) == 3:
                        try:
                            msg_can_id = int(parts[0], 16)
                            
                            if msg_can_id == can_id:
                                # Clean up data bytes - remove any non-hex parts
                                data_parts = []
                                for p in parts[1:]:
                                    # Skip <DATA ERROR and other non-hex strings
                                    if 'DATA' in p or 'ERROR' in p or '<' in p:
                                        continue
                                    # Only keep valid 2-digit hex bytes
                                    if len(p) == 2:
                                        try:
                                            int(p, 16)
                                            data_parts.append(p)
                                        except ValueError:
                                            break
                                    else:
                                        break
                                
                                # Need at least 8 bytes for 0x080
                                if len(data_parts) < 8:
                                    continue
                                
                                data_bytes = ' '.join(data_parts)
                                
                                # Decode based on CAN ID
                                if can_id == 0x080:
                                    decoded = decode_steering_angle_0x080(data_bytes)
                                elif can_id == 0x420:
                                    decoded = decode_steering_angle_0x420(data_bytes)
                                else:
                                    decoded = None
                                
                                if decoded:
                                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                    
                                    # Display all interpretations
                                    print(f"\n{timestamp} - Raw: {data_bytes}")
                                    for key, value in decoded.items():
                                        if isinstance(value, float):
                                            print(f"  {key}: {value:+8.2f}")
                                        else:
                                            print(f"  {key}: 0x{value:04X} ({value})")
                                    
                                    message_count += 1
                                    
                                    # Limit output rate
                                    if message_count % 5 == 0:
                                        print("-" * 80)
                        
                        except (ValueError, IndexError):
                            pass
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print()
        print("-" * 80)
        print(f"\nMonitoring stopped. Captured {message_count} messages.")
        print()
        print("ANALYSIS INSTRUCTIONS:")
        print("  Look for values that change smoothly as you turn the wheel")
        print("  Steering angle should:")
        print("    - Increase when turning clockwise")
        print("    - Decrease when turning counter-clockwise")
        print("    - Return to same value when wheel returns to center")
        print()
    
    finally:
        elm.stop_monitoring()

def main(port='COM4', can_id=0x080, duration=0):
    """
    Main entry point
    
    Args:
        port: Serial port for ELM327
        can_id: CAN ID to monitor (0x080 or 0x420)
        duration: How long to monitor (0 = infinite)
    """
    # Connect
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
        monitor_steering(elm, can_id=can_id, duration=duration)
        return True
    
    finally:
        elm.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor steering wheel angle in real-time - experimental decoder'
    )
    parser.add_argument('--port', default='COM3', 
                       help='Serial port (default: COM3)')
    parser.add_argument('--can-id', type=lambda x: int(x, 16), default=0x080,
                       help='CAN ID to monitor in hex (default: 0x080)')
    parser.add_argument('--duration', type=int, default=0,
                       help='Duration in seconds (default: infinite)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, can_id=args.can_id, duration=args.duration)
    sys.exit(0 if success else 1)
