#!/usr/bin/env python3
"""
Ford Escape 2008 - Real-Time Transmission Monitor
Displays live transmission data using discovered DIDs

Uses the 4 confirmed working transmission DIDs:
- 0x221E1C: ATF Temperature
- 0x221E10: ATF Temperature (alt)
- 0x221E14: Turbine Speed
- 0x221E16: Output Shaft Speed

Author: AI Diagnostic Agent
"""

import serial
import time
from datetime import datetime
from typing import Dict, Optional
import sys


class TransmissionMonitor:
    """Real-time transmission data monitor"""
    
    # Known working DIDs
    DID_ATF_TEMP = 0x221E1C
    DID_ATF_TEMP_ALT = 0x221E10
    DID_TURBINE_SPEED = 0x221E14
    DID_OUTPUT_SPEED = 0x221E16
    
    # PCM addresses
    PCM_REQUEST = 0x7E0
    PCM_RESPONSE = 0x7E8
    
    def __init__(self, port: str = 'COM3', baudrate: int = 38400):
        """Initialize monitor"""
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.running = False
        
        # Data storage
        self.current_data = {
            'atf_temp': None,
            'turbine_rpm': None,
            'output_rpm': None,
            'gear_ratio': None,
            'timestamp': None
        }
    
    def connect(self) -> bool:
        """Connect to ELM327 adapter"""
        try:
            print(f"Connecting to {self.port}...")
            self.connection = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)
            
            # Initialize ELM327
            self._send_command("ATZ")  # Reset
            time.sleep(1)
            self._send_command("ATE0")  # Echo off
            self._send_command("ATL0")  # Linefeeds off
            self._send_command("ATS0")  # Spaces off
            self._send_command("ATH1")  # Headers on
            self._send_command("ATSP6")  # ISO 15765-4 CAN (11 bit, 500 kbps)
            self._send_command("ATCAF0")  # CAN Auto Formatting off
            
            print("✓ Connected and configured")
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
        while self.connection.in_waiting:
            response += self.connection.read(self.connection.in_waiting)
            time.sleep(0.05)
        
        return response.decode('utf-8', errors='ignore').strip()
    
    def read_did(self, did: int) -> Optional[bytes]:
        """
        Read a DID from PCM
        
        Args:
            did: Data Identifier (e.g., 0x221E1C)
        
        Returns:
            Data bytes or None if failed
        """
        did_msb = (did >> 8) & 0xFF
        did_lsb = did & 0xFF
        
        cmd = f"7E0 03 22 {did_msb:02X} {did_lsb:02X}"
        response = self._send_command(cmd)
        
        time.sleep(0.1)
        
        # Parse response
        if '7E8' in response and '62' in response:
            # Extract hex data
            parts = response.replace(' ', '').replace('\r', '').replace('\n', '')
            
            # Find positive response (62)
            idx = parts.find('62')
            if idx != -1:
                # Skip: 7E8, length, 62, DID_MSB, DID_LSB
                data_start = idx + 2 + 4  # 62 + 2 bytes for DID
                data_hex = parts[data_start:]
                
                # Convert to bytes
                try:
                    data_bytes = bytes.fromhex(data_hex)
                    return data_bytes
                except:
                    pass
        
        return None
    
    def read_atf_temperature(self) -> Optional[float]:
        """Read ATF temperature in °C"""
        data = self.read_did(self.DID_ATF_TEMP)
        
        if data and len(data) >= 1:
            temp_raw = data[0]
            temp_celsius = temp_raw - 40
            return temp_celsius
        
        # Try alternative DID
        data = self.read_did(self.DID_ATF_TEMP_ALT)
        if data and len(data) >= 1:
            temp_raw = data[0]
            temp_celsius = temp_raw - 40
            return temp_celsius
        
        return None
    
    def read_turbine_speed(self) -> Optional[int]:
        """Read turbine speed in RPM"""
        data = self.read_did(self.DID_TURBINE_SPEED)
        
        if data and len(data) >= 2:
            high_byte = data[0]
            low_byte = data[1]
            rpm = (high_byte << 8) | low_byte
            return rpm
        
        return None
    
    def read_output_speed(self) -> Optional[int]:
        """Read output shaft speed in RPM"""
        data = self.read_did(self.DID_OUTPUT_SPEED)
        
        if data and len(data) >= 2:
            high_byte = data[0]
            low_byte = data[1]
            rpm = (high_byte << 8) | low_byte
            return rpm
        
        return None
    
    def calculate_gear_ratio(self, turbine_rpm: int, output_rpm: int) -> Optional[float]:
        """Calculate current gear ratio"""
        if output_rpm > 0:
            ratio = turbine_rpm / output_rpm
            return ratio
        return None
    
    def estimate_gear(self, ratio: Optional[float]) -> str:
        """Estimate current gear from ratio"""
        if ratio is None:
            return "Unknown"
        
        # CD4E gear ratios
        gear_ratios = {
            'P/N': (0.0, 0.1),
            '1st': (2.2, 2.7),
            '2nd': (1.3, 1.6),
            '3rd': (0.9, 1.1),
            '4th': (0.6, 0.8)
        }
        
        for gear, (min_ratio, max_ratio) in gear_ratios.items():
            if min_ratio <= ratio <= max_ratio:
                return gear
        
        return f"~{ratio:.2f}:1"
    
    def update_data(self):
        """Update all transmission data"""
        self.current_data['timestamp'] = datetime.now()
        
        # Read ATF temperature
        self.current_data['atf_temp'] = self.read_atf_temperature()
        
        # Read speeds
        self.current_data['turbine_rpm'] = self.read_turbine_speed()
        self.current_data['output_rpm'] = self.read_output_speed()
        
        # Calculate gear ratio
        if self.current_data['turbine_rpm'] and self.current_data['output_rpm']:
            self.current_data['gear_ratio'] = self.calculate_gear_ratio(
                self.current_data['turbine_rpm'],
                self.current_data['output_rpm']
            )
    
    def display_data(self):
        """Display current data"""
        # Clear screen (Windows)
        print('\033[2J\033[H', end='')
        
        print("=" * 70)
        print("Ford Escape 2008 - Real-Time Transmission Monitor")
        print("=" * 70)
        print(f"Time: {self.current_data['timestamp'].strftime('%H:%M:%S') if self.current_data['timestamp'] else 'N/A'}")
        print()
        
        # ATF Temperature
        temp = self.current_data['atf_temp']
        if temp is not None:
            temp_f = (temp * 9/5) + 32
            temp_status = self._get_temp_status(temp)
            print(f"ATF Temperature:  {temp:>6.1f}°C ({temp_f:>6.1f}°F) {temp_status}")
        else:
            print(f"ATF Temperature:  {'N/A':>6}")
        
        # Turbine Speed
        turbine = self.current_data['turbine_rpm']
        if turbine is not None:
            print(f"Turbine Speed:    {turbine:>6} RPM")
        else:
            print(f"Turbine Speed:    {'N/A':>6}")
        
        # Output Speed
        output = self.current_data['output_rpm']
        if output is not None:
            print(f"Output Speed:     {output:>6} RPM")
        else:
            print(f"Output Speed:     {'N/A':>6}")
        
        # Gear Ratio
        ratio = self.current_data['gear_ratio']
        if ratio is not None:
            gear = self.estimate_gear(ratio)
            print(f"Gear Ratio:       {ratio:>6.2f}:1 (Estimated: {gear})")
        else:
            print(f"Gear Ratio:       {'N/A':>6}")
        
        print()
        print("=" * 70)
        print("Press Ctrl+C to stop monitoring")
        print("=" * 70)
    
    def _get_temp_status(self, temp_c: float) -> str:
        """Get temperature status indicator"""
        if temp_c < 40:
            return "[COLD]"
        elif temp_c < 70:
            return "[WARMING UP]"
        elif temp_c < 95:
            return "[NORMAL]"
        elif temp_c < 110:
            return "[WARM]"
        elif temp_c < 130:
            return "[HOT ⚠]"
        else:
            return "[CRITICAL ⚠⚠]"
    
    def monitor_loop(self, interval: float = 1.0):
        """Main monitoring loop"""
        self.running = True
        
        print("\nStarting transmission monitor...")
        print(f"Update interval: {interval} seconds")
        print()
        
        try:
            while self.running:
                self.update_data()
                self.display_data()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n✓ Monitoring stopped by user")
            self.running = False
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
        print("✓ Disconnected")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Ford Escape 2008 - Real-Time Transmission Monitor'
    )
    parser.add_argument(
        '--port',
        default='COM3',
        help='Serial port (default: COM3)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Update interval in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = TransmissionMonitor(port=args.port)
    
    # Connect
    if not monitor.connect():
        sys.exit(1)
    
    # Start monitoring
    try:
        monitor.monitor_loop(interval=args.interval)
    finally:
        monitor.disconnect()


if __name__ == "__main__":
    main()
