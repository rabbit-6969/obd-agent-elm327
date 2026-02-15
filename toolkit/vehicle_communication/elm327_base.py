"""
ELM327 Base Communication Module

Core functionality for ELM327 OBD-II adapter communication.
Extracted and refactored from legacy elm327_diagnostic module.
"""

import serial
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ELM327Error(Exception):
    """ELM327 communication error"""
    pass


class ELM327Base:
    """
    Base class for ELM327 OBD-II adapter communication
    
    Provides core functionality:
    - Connection management
    - Command sending/receiving
    - Protocol configuration
    - Error handling
    """
    
    def __init__(self, port: str, baudrate: int = 38400, timeout: float = 2.0):
        """
        Initialize ELM327 adapter
        
        Args:
            port: Serial port (e.g., 'COM3', '/dev/ttyUSB0')
            baudrate: Serial communication speed (default 38400)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Establish connection to ELM327 adapter
        
        Returns:
            True if connection successful
            
        Raises:
            ELM327Error: If connection fails
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            time.sleep(2)  # Wait for adapter to initialize
            
            # Initialize adapter
            if not self.send_command("AT Z"):  # Reset
                raise ELM327Error("Failed to reset adapter")
            
            if not self.send_command("AT E0"):  # Disable echo
                raise ELM327Error("Failed to disable echo")
            
            if not self.send_command("AT L0"):  # Disable linefeeds
                raise ELM327Error("Failed to disable linefeeds")
            
            # Get adapter version
            version = self.send_command("AT I")
            logger.info(f"Connected to ELM327: {version}")
            
            self.connected = True
            return True
            
        except serial.SerialException as e:
            raise ELM327Error(f"Failed to connect to {self.port}: {e}")
    
    def disconnect(self):
        """Close connection to adapter"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.connected = False
            logger.info("Disconnected from adapter")
    
    def send_command(self, command: str) -> Optional[str]:
        """
        Send AT command to adapter
        
        Args:
            command: AT command to send
            
        Returns:
            Response from adapter or None if error
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            raise ELM327Error("Not connected to adapter")
        
        try:
            self.serial_conn.write((command + "\r").encode())
            time.sleep(0.1)
            
            response = self._read_response()
            return response
            
        except serial.SerialException as e:
            raise ELM327Error(f"Serial error sending command '{command}': {e}")
    
    def send_obd_command(self, command: str) -> Optional[str]:
        """
        Send OBD-II command and get response
        
        Args:
            command: OBD-II command (e.g., "03" for read DTCs)
            
        Returns:
            Raw response from vehicle or None if no data
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            raise ELM327Error("Not connected to adapter")
        
        try:
            self.serial_conn.write((command + "\r").encode())
            time.sleep(0.5)  # Wait for response
            
            response = self._read_response()
            
            if response and response not in ["NO DATA", "?", "UNABLE TO CONNECT"]:
                return response
            
            return None
            
        except Exception as e:
            raise ELM327Error(f"Error sending OBD command: {e}")
    
    def _read_response(self) -> Optional[str]:
        """
        Read response from adapter until prompt
        
        Returns:
            Response string without prompts
        """
        response = ""
        prompt = ">"
        
        try:
            while True:
                if self.serial_conn.in_waiting > 0:
                    byte_data = self.serial_conn.read()
                    char = byte_data.decode('utf-8', errors='ignore')
                    response += char
                    
                    if response.endswith(prompt):
                        break
                else:
                    time.sleep(0.01)
                    
                # Timeout protection
                if len(response) > 1000:
                    break
                    
            # Clean response
            clean_response = response.replace(prompt, "").strip()
            return clean_response if clean_response else None
            
        except Exception as e:
            raise ELM327Error(f"Error reading response: {e}")
    
    def set_protocol(self, protocol: str) -> bool:
        """
        Set OBD protocol
        
        Args:
            protocol: Protocol number (e.g., "6" for CAN)
            
        Returns:
            True if successful
        """
        response = self.send_command(f"AT SP{protocol}")
        return response is not None
    
    def set_header(self, header: str) -> bool:
        """
        Set CAN header for specific module addressing
        
        Args:
            header: CAN header in hex (e.g., "7E0" for PCM)
            
        Returns:
            True if successful
        """
        response = self.send_command(f"AT SH {header}")
        return response is not None
    
    def get_voltage(self) -> Optional[float]:
        """
        Get current voltage reading from adapter
        
        Returns:
            Voltage value as float, or None if error
        """
        try:
            voltage_str = self.send_command("AT RV")
            if voltage_str:
                # Clean up response
                voltage_str = voltage_str.replace('\r', ' ').replace('\n', ' ').strip()
                
                if 'V' in voltage_str:
                    voltage_value = voltage_str.replace('V', '').replace('Volts', '').strip()
                    voltage_value = ''.join(c for c in voltage_value if c.isdigit() or c == '.')
                    if voltage_value:
                        return float(voltage_value)
        except Exception as e:
            logger.error(f"Error reading voltage: {e}")
        
        return None
    
    def test_connection(self) -> bool:
        """
        Test if vehicle is connected and responding
        
        Returns:
            True if vehicle is responding
        """
        try:
            # Try to read supported PIDs (mode 1, PID 00)
            response = self.send_obd_command("0100")
            return response is not None
        except Exception:
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


if __name__ == '__main__':
    # Test ELM327 base functionality
    import sys
    
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = "COM3"  # Default port
    
    try:
        print(f"Testing ELM327 connection on {port}...")
        
        with ELM327Base(port) as adapter:
            print("✓ Connected to adapter")
            
            # Test voltage
            voltage = adapter.get_voltage()
            if voltage:
                print(f"✓ Voltage: {voltage:.1f}V")
            
            # Test vehicle connection
            if adapter.test_connection():
                print("✓ Vehicle is responding")
            else:
                print("✗ Vehicle is not responding")
    
    except ELM327Error as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
