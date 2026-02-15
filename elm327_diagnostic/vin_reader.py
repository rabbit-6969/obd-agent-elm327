"""
VIN (Vehicle Identification Number) Reader
Reads VIN from Ford vehicles via OBD-II
"""

import logging
from typing import Optional
from elm327_adapter import ELM327Adapter

# Configure logging to suppress module name prefixes
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class VINReader:
    """Reads VIN from vehicles using OBD-II protocol"""
    
    def __init__(self, adapter: ELM327Adapter):
        """
        Initialize VIN reader
        
        Args:
            adapter: ELM327Adapter instance
        """
        self.adapter = adapter
    
    def read_vin(self) -> Optional[str]:
        """
        Read VIN from vehicle
        
        For 2008 Ford Escape, VIN is read via OBD-II service 0x09 (Vehicle Info)
        PID 02 = VIN
        
        Returns:
            VIN string (17 characters) or None if failed
        """
        try:
            # Try different CAN bus speeds for 2008 Ford Escape
            # Ford typically uses High CAN (500k) for newer vehicles
            
            logger.info("Reading VIN from vehicle...")
            
            # Request VIN using OBD-II service 09, PID 02
            # Command format: 0902 (service 09, PID 02)
            response = self.adapter.send_obd_command("0902")
            
            if not response:
                logger.warning("No response for VIN on High CAN, trying Low CAN...")
                # Try Low CAN bus
                if self.adapter.set_can_bus(use_high=False):
                    response = self.adapter.send_obd_command("0902")
            
            if response:
                vin = self._parse_vin_response(response)
                if vin and len(vin) == 17:
                    logger.info(f"VIN read successfully: {vin}")
                    return vin
            
            logger.error("Failed to read VIN")
            return None
            
        except Exception as e:
            logger.error(f"Error reading VIN: {e}")
            return None
    
    def _parse_vin_response(self, response: str) -> Optional[str]:
        """
        Parse VIN from OBD-II response
        
        OBD-II response format for VIN:
        49 02 01 + 5 bytes (part 1)
        49 02 02 + 5 bytes (part 2)
        49 02 03 + 5 bytes (part 3)
        49 02 04 + 2 bytes (part 4)
        
        Args:
            response: Raw OBD-II response
            
        Returns:
            17-character VIN or None
        """
        try:
            # Remove spaces and convert to uppercase
            response = response.replace(" ", "").upper()
            
            # Extract VIN bytes (skip response header 49 02)
            if response.startswith("4902"):
                response = response[4:]  # Remove service response header
            
            # Convert hex to ASCII characters
            vin_chars = []
            for i in range(0, len(response), 2):
                if i + 1 < len(response):
                    hex_pair = response[i:i+2]
                    try:
                        char_code = int(hex_pair, 16)
                        if 32 <= char_code <= 126:  # Printable ASCII range
                            vin_chars.append(chr(char_code))
                    except ValueError:
                        continue
            
            vin = ''.join(vin_chars)
            
            # VIN should be exactly 17 characters, alphanumeric
            if len(vin) == 17 and vin.isalnum():
                return vin
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing VIN response: {e}")
            return None
    
    def validate_vin(self, vin: str) -> bool:
        """
        Validate VIN format
        
        Args:
            vin: VIN to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not vin or len(vin) != 17:
            return False
        
        if not vin.isalnum():
            return False
        
        # Check for invalid characters (I, O, Q not allowed in VIN)
        invalid_chars = ['I', 'O', 'Q']
        if any(char in vin for char in invalid_chars):
            return False
        
        return True
