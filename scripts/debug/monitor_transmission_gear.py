#!/usr/bin/env python3
"""
Ford Escape 2008 - Transmission Gear Monitor (CAN Bus)

Monitors current transmission gear by reading CAN message 0x228.
This provides real-time gear information without querying any module.

Data Source: CAN message 0x228 (Transmission Status)
- Byte 0: Gear and selector position
- Byte 1: Additional transmission status

Usage:
    python scripts/debug/monitor_transmission_gear.py
    
    Watch gear changes in real-time as you shift.
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
            self.send_command("ATH1")  # Headers on
            self.send_command("ATSP6")  # ISO 15765-4 CAN (500kbaud)
            
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
    
    def monitor_can_message(self, can_id, duration=1.0):
        """
        Monitor a specific CAN message
        
        Args:
            can_id: CAN message ID (e.g., 0x228)
            duration: How long to monitor (seconds)
        
        Returns:
            List of received messages
        """
        # Set CAN filter
        self.send_command(f"ATCF{can_id:03X}")
        self.send_command("ATCM7FF")  # Set mask to match exact ID
        
        # Start monitoring
        self.ser.reset_input_buffer()
        self.ser.write(b'ATMA\r')  # Monitor all
        
        messages = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if self.ser.in_waiting:
                line = self.ser.readline().decode('ascii', errors='ignore').strip()
                
                if line and can_id in [int(line[:3], 16) if len(line) >= 3 else 0]:
                    messages.append(line)
        
        # Stop monitoring
        self.ser.write(b'\r')
        time.sleep(0.1)
        self.ser.reset_input_buffer()
        
        return messages
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def parse_transmission_status(data_hex):
    """
    Parse transmission status from CAN 0x228
    
    Byte 0 format:
    - Bit 0 (0x01): Park/Off
    - Bit 1 (0x02): Reverse
    - Bit 2 (0x04): Drive (Forward)
    - Bit 4 (0x10): 1st Gear
    - Bit 5 (0x20): 2nd Gear
    - Bit 6 (0x40): 3rd Gear
    - Bit 7 (0x80): 4th Gear
    
    Note: 0x03 appears to be Neutral
    
    Byte 1 format:
    - Bit 3 (0x08): Gear Shift in progress
    - Bit 7 (0x80): Manual/Triptronic mode
    
    Args:
        data_hex: String of hex bytes (e.g., "228 04 10 00 00 00 00 00 00")
    
    Returns:
        Dictionary with transmission status
    """
    try:
        parts = data_hex.split()
        
        if len(parts) < 3:
            return None
        
        # Skip CAN ID, get data bytes
        byte0 = int(parts[1], 16)
        byte1 = int(parts[2], 16) if len(parts) > 2 else 0
        
        # Determine selector position
        selector = "Unknown"
        if byte0 == 0x03:
            selector = "Neutral"
        elif byte0 & 0x01:
            selector = "Park"
        elif byte0 & 0x02:
            selector = "Reverse"
        elif byte0 & 0x04:
            selector = "Drive"
        
        # Determine current gear
        gear = None
        if byte0 & 0x10:
            gear = 1
        elif byte0 & 0x20:
            gear = 2
        elif byte0 & 0x40:
            gear = 3
        elif byte0 & 0x80:
            gear = 4
        
        # Additional status
        shifting = bool(byte1 & 0x08)
        manual_mode = bool(byte1 & 0x80)
        
        return {
            'selector': selector,
            'gear': gear,
            'shifting': shifting,
            'manual_mode': manual_mode,
            'byte0': byte0,
            'byte1': byte1,
            'raw_hex': data_hex
        }
    
    except Exception as e:
        print(f"Error parsing transmission status: {e}")
        return None

def format_transmission_status(status):
    """Format transmission status for display"""
    if not status:
        return "No data"
    
    # Build gear display
    if status['gear']:
        gear_str = f"Gear {status['gear']}"
    else:
        gear_str = "No gear"
    
    # Build selector display
    selector_str = status['selector']
    
    # Build status flags
    flags = []
    if status['shifting']:
        flags.append("SHIFTING")
    if status['manual_mode']:
        flags.append("MANUAL")
    
    flags_str = " | ".join(flags) if flags else ""
    
    # Combine
    result = f"{selector_str:10} {gear_str:10}"
    if flags_str:
        result += f" [{flags_str}]"
    
    return result

def main(port='COM3', duration=300, interval=0.5):
    """
    Monitor transmission gear
    
    Args:
        port: Serial port for ELM327
        duration: How long to monitor (seconds)
        interval: Time between readings (seconds)
    """
    print("=" * 80)
    print("Ford Escape 2008 - Transmission Gear Monitor (CAN Bus)")
    print("=" * 80)
    print()
    print("Monitoring CAN message 0x228 (Transmission Status)")
    print()
    print("Gear Information:")
    print("  - Selector Position: Park, Reverse, Neutral, Drive")
    print("  - Current Gear: 1, 2, 3, 4 (when in Drive)")
    print("  - Status Flags: SHIFTING, MANUAL mode")
    print()
    print("Instructions:")
    print("  - Start engine and shift through gears")
    print("  - Watch gear changes in real-time")
    print("  - Press Ctrl+C to stop")
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
    print(f"{'Time':<12} {'Selector':<12} {'Gear':<12} {'Status':<30} {'Raw (Byte0 Byte1)':<20}")
    print("-" * 86)
    
    start_time = time.time()
    sample_count = 0
    last_status = None
    
    try:
        while time.time() - start_time < duration:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Monitor CAN message 0x228
            messages = elm.monitor_can_message(0x228, duration=interval)
            
            if messages:
                # Use the most recent message
                latest_message = messages[-1]
                status = parse_transmission_status(latest_message)
                
                if status:
                    # Only print if status changed or every 10 samples
                    status_changed = (last_status is None or 
                                    status['selector'] != last_status['selector'] or
                                    status['gear'] != last_status['gear'] or
                                    status['shifting'] != last_status['shifting'] or
                                    status['manual_mode'] != last_status['manual_mode'])
                    
                    if status_changed or sample_count % 10 == 0:
                        status_str = format_transmission_status(status)
                        raw_str = f"0x{status['byte0']:02X} 0x{status['byte1']:02X}"
                        
                        print(f"{timestamp:<12} {status_str:<54} {raw_str:<20}")
                        
                        last_status = status
                    
                    sample_count += 1
            else:
                # No data received
                if sample_count % 10 == 0:
                    print(f"{timestamp:<12} No CAN data")
            
            # Small delay before next read
            time.sleep(max(0, interval - 0.1))
    
    except KeyboardInterrupt:
        print()
        print("Monitoring stopped by user")
    
    finally:
        elm.close()
    
    print()
    print("=" * 80)
    print("Transmission Gear Monitoring Complete")
    print("=" * 80)
    print(f"Total samples: {sample_count}")
    print()
    
    if last_status:
        print("Final Status:")
        print(f"  Selector: {last_status['selector']}")
        print(f"  Gear: {last_status['gear'] if last_status['gear'] else 'N/A'}")
        print(f"  Shifting: {last_status['shifting']}")
        print(f"  Manual Mode: {last_status['manual_mode']}")
    
    print()
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor transmission gear from CAN bus'
    )
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    parser.add_argument('--duration', type=int, default=300, 
                       help='Monitoring duration in seconds (default: 300)')
    parser.add_argument('--interval', type=float, default=0.5,
                       help='Time between readings in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, duration=args.duration, interval=args.interval)
    sys.exit(0 if success else 1)
