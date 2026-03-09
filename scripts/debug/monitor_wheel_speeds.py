#!/usr/bin/env python3
"""
Ford Escape 2008 - ABS Wheel Speed Monitor

Monitors CAN ID 0x4B0 for individual wheel speeds from ABS sensors.
Displays real-time wheel speed data as vehicle moves.

CAN ID 0x4B0 - Wheel Speeds (8 bytes):
- Bytes 0-1: Left Front wheel speed
- Bytes 2-3: Right Front wheel speed
- Bytes 4-5: Left Rear wheel speed
- Bytes 6-7: Right Rear wheel speed
- Formula: (value - 10000) / 100 = km/h

⚠️ SAFETY: This is READ-ONLY passive monitoring - no messages are sent.

Usage:
    python scripts/debug/monitor_wheel_speeds.py --port COM4
    
    Roll the vehicle slowly and watch the wheel speeds.
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
            self.send_command("ATS1")  # Spaces ON (required for ATCRA)
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
        """Start monitoring CAN ID 0x4B0"""
        self.send_command("ATCRA4B0")
        
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

def decode_wheel_speed(byte_high, byte_low):
    """Decode wheel speed from 2 bytes
    
    Formula: (value - 10000) / 100 = km/h
    """
    value = (byte_high << 8) | byte_low
    speed_kmh = (value - 10000) / 100.0
    return speed_kmh

def monitor_wheel_speeds(elm, duration=60):
    """Monitor wheel speeds and display in real-time"""
    print("=" * 80)
    print("ABS Wheel Speed Monitor")
    print("=" * 80)
    print()
    print("Monitoring CAN ID 0x4B0 - Individual Wheel Speeds")
    print()
    print("Roll the vehicle slowly and watch the wheel speeds.")
    print("Press Ctrl+C to stop.")
    print()
    print("-" * 80)
    print(f"{'Time':<12} {'LF':<8} {'RF':<8} {'LR':<8} {'RR':<8} {'Raw Data':<30}")
    print("-" * 80)
    
    elm.start_monitor()
    
    buffer = ""
    start_time = time.time()
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
                            
                            if can_id == 0x4B0:
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
                                
                                if len(data_parts) >= 8:
                                    # Decode all 4 wheel speeds
                                    lf_speed = decode_wheel_speed(
                                        int(data_parts[0], 16),
                                        int(data_parts[1], 16)
                                    )
                                    rf_speed = decode_wheel_speed(
                                        int(data_parts[2], 16),
                                        int(data_parts[3], 16)
                                    )
                                    lr_speed = decode_wheel_speed(
                                        int(data_parts[4], 16),
                                        int(data_parts[5], 16)
                                    )
                                    rr_speed = decode_wheel_speed(
                                        int(data_parts[6], 16),
                                        int(data_parts[7], 16)
                                    )
                                    
                                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                    data_str = ' '.join(data_parts[:8])
                                    
                                    print(f"{timestamp:<12} "
                                          f"{lf_speed:>6.2f}  "
                                          f"{rf_speed:>6.2f}  "
                                          f"{lr_speed:>6.2f}  "
                                          f"{rr_speed:>6.2f}  "
                                          f"{data_str:<30}")
                                    
                                    message_count += 1
                        
                        except (ValueError, IndexError):
                            pass
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print()
        print("-" * 80)
        print(f"\nMonitoring stopped. Captured {message_count} messages.")
        print()
        print("ANALYSIS:")
        print("  - All four wheel speeds should be identical when rolling straight")
        print("  - Speeds should be 0.00 km/h when stationary")
        print("  - Individual wheels change during turns (outer wheels faster)")
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
        monitor_wheel_speeds(elm, duration=duration)
        return True
    
    finally:
        elm.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor ABS wheel speeds (CAN ID 0x4B0)'
    )
    parser.add_argument('--port', default='COM4', 
                       help='Serial port (default: COM4)')
    parser.add_argument('--duration', type=int, default=0,
                       help='Duration in seconds (default: infinite)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, duration=args.duration)
    sys.exit(0 if success else 1)
