"""
COM Port Detection Utility
Detects and lists available serial ports for ELM327 adapter connection
"""

import serial
from typing import List, Tuple
from serial.tools import list_ports


class COMPortDetector:
    """Utility for detecting available COM ports"""
    
    @staticmethod
    def get_available_ports() -> List[Tuple[str, str]]:
        """
        Get list of available COM ports
        
        Returns:
            List of tuples (port_name, port_description)
            Example: [('COM3', 'USB Serial Port'), ('COM4', 'Intel ActiveKey')]
        """
        ports = []
        try:
            for port_info in list_ports.comports():
                ports.append((port_info.device, port_info.description))
        except Exception:
            pass
        
        return ports
    
    @staticmethod
    def test_port(port: str, timeout: float = 1.0) -> bool:
        """
        Test if a port is accessible
        
        Args:
            port: COM port name (e.g., 'COM3')
            timeout: Timeout in seconds
            
        Returns:
            True if port is accessible, False otherwise
        """
        try:
            ser = serial.Serial(
                port=port,
                baudrate=38400,
                timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            ser.close()
            return True
        except serial.SerialException:
            return False
    
    @staticmethod
    def get_accessible_ports() -> List[Tuple[str, str]]:
        """
        Get list of accessible (testable) COM ports
        
        Returns:
            List of tuples (port_name, port_description)
        """
        ports = COMPortDetector.get_available_ports()
        accessible = []
        
        for port_name, port_desc in ports:
            if COMPortDetector.test_port(port_name):
                accessible.append((port_name, port_desc))
        
        return accessible
