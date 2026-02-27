#!/usr/bin/env python3
"""
Toyota FJ Cruiser / 4Runner - Live ABS Monitoring
Monitor ABS warning lights and individual wheel status in real-time

Based on OBDB signal data:
- Command 0x213D: ABS warning light status
- Command 0x215F: Individual wheel ABS control status

This script continuously polls the ABS module to detect intermittent faults
as they occur, helping diagnose wheel speed sensor issues.

Author: AI Diagnostic Agent
"""

import serial
import time
from datetime import datetime
from typing import Dict, Optional
import sys

class FJCruiserABSMonitor:
    """Monitor live ABS data from FJ Cruiser/4Runner ABS module"""
    
    def __init__(self, port: str = 'COM3', baudrate: int = 38400):
        """Initialize ABS monitor"""
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        
        # Toyota ABS addressing
        self.abs_request = 0x7B0
        self.abs_response = 0x7B8
        
        # Fault detection
        self.fault_detected = False
        self.fault_log = []
        
    def connect(self) -> bool:
        """Connect to ELM327 adapter"""
        try:
            print("=" * 70)
            print("Toyota FJ Cruiser / 4Runner - Live ABS Monitor")
            print("=" * 70)
            print("\nConnecting to ELM327...")
            
            self.connection = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)
            
            # Initialize ELM327
            print("Initializing adapter...")
            self._send_command("ATZ")  # Reset
            time.sleep(1)
            self._send_command("ATE0")  # Echo off
            self._send_command("ATL0")  # Linefeeds off
            self._send_command("ATS0")  # Spaces off
            self._send_command("ATH1")  # Headers on
            self._send_command("ATSP6")  # ISO 15765-4 CAN (11 bit, 500 kbps)
            self._send_command("ATCAF0")  # CAN Auto Formatting off
            
            # Set header to ABS request address
            self._send_command(f"ATSH {self.abs_request:03X}")
            
            # Set flow control
            self._send_command(f"ATFCSH {self.abs_response:03X}")
            self._send_command("ATFCSD 30 00 00")
            
            print(f"✓ Connected")
            print(f"  ABS Module: 0x{self.abs_request:03X} → 0x{self.abs_response:03X}")
            
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def _send_command(self, cmd: str) -> str:
        """Send command to ELM327"""
        if not self.connection:
            return ""
        
        self.connection.write((cmd + '\r').encode())
        time.sleep(0.1)
        
        response = b''
        max_attempts = 5
        for _ in range(max_attempts):
            if self.connection.in_waiting:
                response += self.connection.read(self.connection.in_waiting)
            time.sleep(0.05)
            if b'>' in response:
                break
        
        return response.decode('utf-8', errors='ignore').strip()
    
    def read_warning_lights(self) -> Optional[Dict]:
        """
        Read ABS warning light status (UDS Service 0x22, DID 0x213D)
        
        Returns dict with:
        - abs_warning: bool
        - brake_warning: bool
        - slip_indicator: bool
        - buzzer: bool
        - ecb_warning: bool
        """
        # UDS Service 0x22 (ReadDataByIdentifier) + DID 0x213D
        cmd = "22 21 3D"
        
        response = self._send_command(cmd)
        time.sleep(0.1)
        
        if not response:
            return None
        
        # Clean response
        response = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Positive response: 62 21 3D [DATA...]
        if '62213D' not in response:
            return None
        
        # Extract data bytes after 62 21 3D
        idx = response.find('62213D')
        data = response[idx+6:]
        
        if len(data) < 2:
            return None
        
        # First byte contains the status bits
        try:
            status_byte = int(data[0:2], 16)
            
            return {
                'abs_warning': bool(status_byte & 0x01),      # Bit 0
                'brake_warning': bool(status_byte & 0x02),    # Bit 1
                'slip_indicator': bool(status_byte & 0x04),   # Bit 2
                'buzzer': bool(status_byte & 0x08),           # Bit 3
                'ecb_warning': bool(status_byte & 0x40),      # Bit 6
                'raw': status_byte
            }
        except:
            return None
    
    def read_wheel_status(self) -> Optional[Dict]:
        """
        Read individual wheel ABS status (UDS Service 0x22, DID 0x215F)
        
        Returns dict with:
        - fr_wheel: bool (Front Right)
        - fl_wheel: bool (Front Left)
        - rr_wheel: bool (Rear Right)
        - rl_wheel: bool (Rear Left)
        - brake_assist: bool
        """
        # UDS Service 0x22 (ReadDataByIdentifier) + DID 0x215F
        cmd = "22 21 5F"
        
        response = self._send_command(cmd)
        time.sleep(0.1)
        
        if not response:
            return None
        
        # Clean response
        response = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Positive response: 62 21 5F [DATA...]
        if '62215F' not in response:
            return None
        
        # Extract data bytes after 62 21 5F
        idx = response.find('62215F')
        data = response[idx+6:]
        
        if len(data) < 4:  # Need at least 2 bytes (4 hex chars)
            return None
        
        try:
            # First byte contains wheel status bits 0-7
            byte0 = int(data[0:2], 16)
            # Second byte contains bits 8-15
            byte1 = int(data[2:4], 16) if len(data) >= 4 else 0
            
            return {
                'fr_wheel': bool(byte0 & 0x01),      # Bit 0 - Front Right
                'fl_wheel': bool(byte0 & 0x02),      # Bit 1 - Front Left
                'rr_wheel': bool(byte0 & 0x04),      # Bit 2 - Rear Right
                'rl_wheel': bool(byte0 & 0x08),      # Bit 3 - Rear Left
                'rr_ebs': bool(byte0 & 0x40),        # Bit 6 - Rear Right EBS
                'rl_ebs': bool(byte0 & 0x80),        # Bit 7 - Rear Left EBS
                'brake_assist': bool(byte1 & 0x08),  # Bit 11 (byte1 bit 3)
                'predictive_ba': bool(byte1 & 0x10), # Bit 12 (byte1 bit 4)
                'raw_byte0': byte0,
                'raw_byte1': byte1
            }
        except:
            return None
    
    def monitor_continuous(self, interval: float = 0.5):
        """
        Continuously monitor ABS status
        
        Args:
            interval: Polling interval in seconds (default 0.5s = 2Hz)
        """
        print("\n" + "=" * 70)
        print("LIVE ABS MONITORING")
        print("=" * 70)
        print("\nMonitoring ABS module for faults...")
        print("Press Ctrl+C to stop\n")
        print("Timestamp           | Warnings | Wheel Status")
        print("-" * 70)
        
        last_warning_state = None
        last_wheel_state = None
        
        try:
            while True:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # Read warning lights
                warnings = self.read_warning_lights()
                
                # Read wheel status
                wheels = self.read_wheel_status()
                
                # Check if state changed or fault detected
                warning_changed = warnings != last_warning_state
                wheel_changed = wheels != last_wheel_state
                
                if warnings and (warning_changed or warnings['abs_warning']):
                    # Format warning status
                    warn_str = []
                    if warnings['abs_warning']:
                        warn_str.append("ABS")
                    if warnings['brake_warning']:
                        warn_str.append("BRAKE")
                    if warnings['slip_indicator']:
                        warn_str.append("SLIP")
                    if warnings['ecb_warning']:
                        warn_str.append("ECB")
                    
                    warn_display = ", ".join(warn_str) if warn_str else "OK"
                    
                    # Format wheel status
                    wheel_str = []
                    if wheels:
                        if wheels['fr_wheel']:
                            wheel_str.append("FR")
                        if wheels['fl_wheel']:
                            wheel_str.append("FL")
                        if wheels['rr_wheel']:
                            wheel_str.append("RR")
                        if wheels['rl_wheel']:
                            wheel_str.append("RL")
                    
                    wheel_display = ", ".join(wheel_str) if wheel_str else "All OK"
                    
                    # Print status
                    print(f"{timestamp} | {warn_display:20s} | {wheel_display}")
                    
                    # Log fault if detected
                    if warnings['abs_warning'] and not self.fault_detected:
                        self.fault_detected = True
                        fault_entry = {
                            'timestamp': timestamp,
                            'warnings': warnings,
                            'wheels': wheels
                        }
                        self.fault_log.append(fault_entry)
                        print("\n" + "!" * 70)
                        print("⚠ FAULT DETECTED!")
                        print("!" * 70)
                        self._print_fault_details(fault_entry)
                        print("!" * 70 + "\n")
                    
                    # Reset fault flag if warning cleared
                    if not warnings['abs_warning'] and self.fault_detected:
                        self.fault_detected = False
                        print(f"\n{timestamp} | ✓ Fault cleared\n")
                
                last_warning_state = warnings
                last_wheel_state = wheels
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("MONITORING STOPPED")
            print("=" * 70)
            self._print_summary()
    
    def _print_fault_details(self, fault: Dict):
        """Print detailed fault information"""
        print(f"\nTime: {fault['timestamp']}")
        
        if fault['warnings']:
            print("\nWarning Lights:")
            w = fault['warnings']
            print(f"  ABS Warning:    {'ON' if w['abs_warning'] else 'OFF'}")
            print(f"  Brake Warning:  {'ON' if w['brake_warning'] else 'OFF'}")
            print(f"  Slip Indicator: {'ON' if w['slip_indicator'] else 'OFF'}")
            print(f"  ECB Warning:    {'ON' if w['ecb_warning'] else 'OFF'}")
            print(f"  Raw: 0x{w['raw']:02X}")
        
        if fault['wheels']:
            print("\nWheel Status (ON = fault detected):")
            wh = fault['wheels']
            print(f"  Front Right: {'FAULT' if wh['fr_wheel'] else 'OK'}")
            print(f"  Front Left:  {'FAULT' if wh['fl_wheel'] else 'OK'}")
            print(f"  Rear Right:  {'FAULT' if wh['rr_wheel'] else 'OK'}")
            print(f"  Rear Left:   {'FAULT' if wh['rl_wheel'] else 'OK'}")
            print(f"  Raw: 0x{wh['raw_byte0']:02X} 0x{wh['raw_byte1']:02X}")
    
    def _print_summary(self):
        """Print monitoring summary"""
        if not self.fault_log:
            print("\n✓ No faults detected during monitoring session")
            print("\nThis is good news! Your ABS system appears healthy.")
            print("\nIf you're experiencing intermittent lights:")
            print("  • Run this monitor while driving (passenger operates laptop)")
            print("  • Monitor during conditions when lights typically appear")
            print("  • Try braking, turning, bumps to trigger the fault")
            return
        
        print(f"\n⚠ {len(self.fault_log)} fault(s) detected during session\n")
        
        # Analyze faults
        wheel_faults = {'fr': 0, 'fl': 0, 'rr': 0, 'rl': 0}
        
        for fault in self.fault_log:
            if fault['wheels']:
                wh = fault['wheels']
                if wh['fr_wheel']:
                    wheel_faults['fr'] += 1
                if wh['fl_wheel']:
                    wheel_faults['fl'] += 1
                if wh['rr_wheel']:
                    wheel_faults['rr'] += 1
                if wh['rl_wheel']:
                    wheel_faults['rl'] += 1
        
        print("Fault Summary:")
        print(f"  Front Right: {wheel_faults['fr']} fault(s)")
        print(f"  Front Left:  {wheel_faults['fl']} fault(s)")
        print(f"  Rear Right:  {wheel_faults['rr']} fault(s)")
        print(f"  Rear Left:   {wheel_faults['rl']} fault(s)")
        
        # Identify most likely culprit
        max_faults = max(wheel_faults.values())
        if max_faults > 0:
            culprits = [k for k, v in wheel_faults.items() if v == max_faults]
            wheel_names = {
                'fr': 'Front Right',
                'fl': 'Front Left',
                'rr': 'Rear Right',
                'rl': 'Rear Left'
            }
            
            print("\n" + "=" * 70)
            print("DIAGNOSIS")
            print("=" * 70)
            
            if len(culprits) == 1:
                culprit_name = wheel_names[culprits[0]]
                print(f"\n⚠ Most likely fault: {culprit_name} wheel speed sensor")
                print(f"\nRecommended action:")
                print(f"  1. Inspect {culprit_name} wheel speed sensor")
                print(f"  2. Check wiring and connector for damage/corrosion")
                print(f"  3. Clean sensor tip (remove metal shavings/debris)")
                print(f"  4. Check sensor air gap (should be 0.5-1.5mm)")
                print(f"  5. Test sensor resistance (typically 1-2 kΩ)")
            else:
                print(f"\n⚠ Multiple wheels showing faults")
                print(f"  This could indicate:")
                print(f"    • ABS module issue")
                print(f"    • Wiring harness problem")
                print(f"    • Low battery voltage")
                print(f"    • CAN bus communication issue")
        
        print("\n" + "=" * 70)
        
        # Save log to file
        log_filename = f"abs_fault_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(log_filename, 'w') as f:
                f.write("Toyota FJ Cruiser / 4Runner - ABS Fault Log\n")
                f.write("=" * 70 + "\n\n")
                
                for i, fault in enumerate(self.fault_log, 1):
                    f.write(f"Fault #{i}\n")
                    f.write(f"Time: {fault['timestamp']}\n")
                    
                    if fault['warnings']:
                        f.write("\nWarnings:\n")
                        for key, value in fault['warnings'].items():
                            f.write(f"  {key}: {value}\n")
                    
                    if fault['wheels']:
                        f.write("\nWheel Status:\n")
                        for key, value in fault['wheels'].items():
                            f.write(f"  {key}: {value}\n")
                    
                    f.write("\n" + "-" * 70 + "\n\n")
            
            print(f"\n✓ Fault log saved to: {log_filename}")
        except Exception as e:
            print(f"\n✗ Failed to save log: {e}")
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
        print("\n✓ Disconnected")

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor Toyota FJ Cruiser / 4Runner ABS system in real-time'
    )
    parser.add_argument(
        '--port',
        default='COM3',
        help='Serial port for ELM327 adapter (default: COM3)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=0.5,
        help='Polling interval in seconds (default: 0.5)'
    )
    
    args = parser.parse_args()
    
    monitor = FJCruiserABSMonitor(port=args.port)
    
    if not monitor.connect():
        sys.exit(1)
    
    try:
        monitor.monitor_continuous(interval=args.interval)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        monitor.disconnect()

if __name__ == "__main__":
    main()
