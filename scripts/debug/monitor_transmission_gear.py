#!/usr/bin/env python3
"""
Ford Escape 2008 - Transmission Status Monitor (CAN Bus)

Monitors transmission parameters by reading CAN message 0x228.
Displays gear, selector position, and transmission status in real-time.

CAN ID 0x228 - Transmission Status (8 bytes):
- Byte 0: Gear and selector position
  - Bit 0 (0x01): Park/Off
  - Bit 1 (0x02): Reverse
  - Bit 2 (0x04): Drive (Forward)
  - Bit 4 (0x10): 1st Gear
  - Bit 5 (0x20): 2nd Gear
  - Bit 6 (0x40): 3rd Gear
  - Bit 7 (0x80): 4th Gear
  - Value 0x03: Neutral
- Byte 1: Status flags
  - Bit 3 (0x08): Gear shift in progress
  - Bit 6 (0x40): Brake pedal related
  - Bit 7 (0x80): Manual/Triptronic mode

⚠️ SAFETY: This is READ-ONLY passive monitoring - no messages are sent.

Usage:
    python scripts/debug/monitor_transmission_gear.py --port COM4
    
    Shift through gears and watch the status update.
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
            print(f"Command error: {e}")
            return None
    
    def start_monitor(self):
        """Start monitoring CAN ID 0x228"""
        self.send_command("ATCRA228")
        
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

def parse_transmission_status(data_parts):
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
    - Value 0x03: Neutral
    
    Byte 1 format:
    - Bit 3 (0x08): Gear shift in progress
    - Bit 6 (0x40): Brake pedal related
    - Bit 7 (0x80): Manual/Triptronic mode
    
    Args:
        data_parts: List of hex byte strings (e.g., ['04', '10', '00', ...])
    
    Returns:
        Dictionary with transmission status
    """
    try:
        if len(data_parts) < 2:
            return None
        
        byte0 = int(data_parts[0], 16)
        byte1 = int(data_parts[1], 16)
        
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
        brake_related = bool(byte1 & 0x40)
        manual_mode = bool(byte1 & 0x80)
        
        return {
            'selector': selector,
            'gear': gear,
            'shifting': shifting,
            'brake_related': brake_related,
            'manual_mode': manual_mode,
            'byte0': byte0,
            'byte1': byte1
        }
    
    except Exception as e:
        return None

def monitor_transmission(elm, duration=60):
    """Monitor transmission status and display in real-time"""
    print("=" * 80)
    print("Transmission Status Monitor")
    print("=" * 80)
    print()
    print("Monitoring CAN ID 0x228 - Transmission Status")
    print()
    print("Shift through gears and watch the status update.")
    print("Press Ctrl+C to stop.")
    print()
    print("-" * 80)
    print(f"{'Time':<12} {'Selector':<10} {'Gear':<6} {'Flags':<20} {'Raw':<20}")
    print("-" * 80)
    
    elm.start_monitor()
    
    buffer = ""
    start_time = time.time()
    last_status = None
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
                            
                            if can_id == 0x228:
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
                                
                                if len(data_parts) >= 2:
                                    status = parse_transmission_status(data_parts)
                                    
                                    if status:
                                        # Only display if status changed
                                        status_changed = (last_status is None or
                                                        status['selector'] != last_status['selector'] or
                                                        status['gear'] != last_status['gear'] or
                                                        status['shifting'] != last_status['shifting'] or
                                                        status['brake_related'] != last_status['brake_related'] or
                                                        status['manual_mode'] != last_status['manual_mode'])
                                        
                                        if status_changed:
                                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                            
                                            # Format gear
                                            if status['gear']:
                                                gear_str = str(status['gear'])
                                            else:
                                                gear_str = "-"
                                            
                                            # Format flags
                                            flags = []
                                            if status['shifting']:
                                                flags.append("SHIFT")
                                            if status['brake_related']:
                                                flags.append("BRAKE")
                                            if status['manual_mode']:
                                                flags.append("MANUAL")
                                            flags_str = " ".join(flags) if flags else "-"
                                            
                                            # Format raw bytes
                                            raw_str = f"{status['byte0']:02X} {status['byte1']:02X}"
                                            
                                            print(f"{timestamp:<12} {status['selector']:<10} {gear_str:<6} {flags_str:<20} {raw_str:<20}")
                                            
                                            last_status = status
                                            message_count += 1
                        
                        except (ValueError, IndexError):
                            pass
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print()
        print("-" * 80)
        print(f"\nMonitoring stopped. Captured {message_count} status changes.")
        print()
        print("ANALYSIS:")
        print("  - Selector shows P/R/N/D position")
        print("  - Gear shows 1-4 when in Drive")
        print("  - SHIFT flag appears during gear changes")
        print("  - BRAKE flag indicates brake pedal state")
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
        monitor_transmission(elm, duration=duration)
        return True
    
    finally:
        elm.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor transmission status (CAN ID 0x228)'
    )
    parser.add_argument('--port', default='COM4', 
                       help='Serial port (default: COM4)')
    parser.add_argument('--duration', type=int, default=0,
                       help='Duration in seconds (default: infinite)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, duration=args.duration)
    sys.exit(0 if success else 1)
