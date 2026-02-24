"""
Protocol Handlers for Multi-Manufacturer Support

Pluggable protocol handlers for different manufacturers.
Supports Ford, GM, Toyota, Honda, and generic OBD-II protocols.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum


logger = logging.getLogger(__name__)


class Manufacturer(Enum):
    """Supported manufacturers"""
    FORD = "Ford"
    GM = "GM"
    TOYOTA = "Toyota"
    HONDA = "Honda"
    GENERIC = "Generic"


class ProtocolHandler(ABC):
    """
    Abstract base class for protocol handlers
    
    Each manufacturer may have specific:
    - Module addressing schemes
    - Command formats
    - Response parsing
    - Diagnostic session requirements
    """
    
    def __init__(self, manufacturer: Manufacturer):
        """
        Initialize protocol handler
        
        Args:
            manufacturer: Manufacturer enum
        """
        self.manufacturer = manufacturer
        self.name = manufacturer.value
    
    @abstractmethod
    def get_module_address(self, module_name: str) -> Optional[str]:
        """
        Get module address for manufacturer
        
        Args:
            module_name: Module name (e.g., "PCM", "ABS")
            
        Returns:
            Module address in hex or None
        """
        pass
    
    @abstractmethod
    def format_dtc_request(self, module_address: str) -> str:
        """
        Format DTC read request
        
        Args:
            module_address: Module address
            
        Returns:
            Formatted command string
        """
        pass
    
    @abstractmethod
    def parse_dtc_response(self, response: str) -> List[str]:
        """
        Parse DTC codes from response
        
        Args:
            response: Raw response string
            
        Returns:
            List of DTC codes
        """
        pass
    
    def supports_uds(self) -> bool:
        """Check if manufacturer supports UDS"""
        return True
    
    def get_diagnostic_session_command(self) -> Optional[str]:
        """Get command to enter diagnostic session"""
        return None


class FordProtocolHandler(ProtocolHandler):
    """Protocol handler for Ford vehicles"""
    
    def __init__(self):
        super().__init__(Manufacturer.FORD)
        
        # Ford-specific module addresses
        self.module_addresses = {
            "PCM": "7E0",
            "TCM": "7E1",
            "ABS": "760",
            "HVAC": "7A0",
            "BCM": "726",
            "IPC": "720",
            "ACM": "737"  # Audio Control Module
        }
    
    def get_module_address(self, module_name: str) -> Optional[str]:
        """Get Ford module address"""
        return self.module_addresses.get(module_name.upper())
    
    def format_dtc_request(self, module_address: str) -> str:
        """Format Ford DTC request"""
        # Ford uses standard OBD-II mode 03
        return "03"
    
    def parse_dtc_response(self, response: str) -> List[str]:
        """Parse Ford DTC response"""
        dtcs = []
        
        # Remove spaces
        response = response.replace(" ", "").upper()
        
        # Check for response header (43 for mode 03 response)
        if not response.startswith("43"):
            return dtcs
        
        # Skip header
        response = response[2:]
        
        # Parse DTC codes (2 bytes each)
        for i in range(0, len(response), 4):
            if i + 4 <= len(response):
                dtc_hex = response[i:i+4]
                dtc_code = self._hex_to_dtc(dtc_hex)
                if dtc_code:
                    dtcs.append(dtc_code)
        
        return dtcs
    
    def _hex_to_dtc(self, hex_code: str) -> Optional[str]:
        """Convert hex to DTC code"""
        try:
            # First byte determines prefix
            first_byte = int(hex_code[0], 16)
            prefix_map = {0: 'P', 1: 'P', 2: 'P', 3: 'P',
                         4: 'C', 5: 'C', 6: 'C', 7: 'C',
                         8: 'B', 9: 'B', 10: 'B', 11: 'B',
                         12: 'U', 13: 'U', 14: 'U', 15: 'U'}
            
            prefix = prefix_map.get(first_byte, 'P')
            
            # Remaining digits
            digits = hex_code[1:]
            
            return f"{prefix}{digits}"
        except Exception:
            return None
    
    def supports_uds(self) -> bool:
        """Ford supports UDS"""
        return True


class GMProtocolHandler(ProtocolHandler):
    """Protocol handler for GM vehicles"""
    
    def __init__(self):
        super().__init__(Manufacturer.GM)
        
        # GM-specific module addresses
        self.module_addresses = {
            "PCM": "7E0",
            "TCM": "7E1",
            "ABS": "7E8",
            "BCM": "641",
            "IPC": "640"
        }
    
    def get_module_address(self, module_name: str) -> Optional[str]:
        """Get GM module address"""
        return self.module_addresses.get(module_name.upper())
    
    def format_dtc_request(self, module_address: str) -> str:
        """Format GM DTC request"""
        return "03"
    
    def parse_dtc_response(self, response: str) -> List[str]:
        """Parse GM DTC response"""
        # GM uses similar format to Ford
        dtcs = []
        response = response.replace(" ", "").upper()
        
        if not response.startswith("43"):
            return dtcs
        
        response = response[2:]
        
        for i in range(0, len(response), 4):
            if i + 4 <= len(response):
                dtc_hex = response[i:i+4]
                dtc_code = self._hex_to_dtc(dtc_hex)
                if dtc_code:
                    dtcs.append(dtc_code)
        
        return dtcs
    
    def _hex_to_dtc(self, hex_code: str) -> Optional[str]:
        """Convert hex to DTC code"""
        try:
            first_byte = int(hex_code[0], 16)
            prefix_map = {0: 'P', 1: 'P', 2: 'P', 3: 'P',
                         4: 'C', 5: 'C', 6: 'C', 7: 'C',
                         8: 'B', 9: 'B', 10: 'B', 11: 'B',
                         12: 'U', 13: 'U', 14: 'U', 15: 'U'}
            
            prefix = prefix_map.get(first_byte, 'P')
            digits = hex_code[1:]
            
            return f"{prefix}{digits}"
        except Exception:
            return None


class ToyotaProtocolHandler(ProtocolHandler):
    """Protocol handler for Toyota vehicles"""
    
    def __init__(self):
        super().__init__(Manufacturer.TOYOTA)
        
        # Toyota-specific module addresses
        self.module_addresses = {
            "PCM": "7E0",
            "TCM": "7E1",
            "ABS": "7B0",
            "AIRBAG": "7B1",
            "BCM": "750"
        }
    
    def get_module_address(self, module_name: str) -> Optional[str]:
        """Get Toyota module address"""
        return self.module_addresses.get(module_name.upper())
    
    def format_dtc_request(self, module_address: str) -> str:
        """Format Toyota DTC request"""
        return "03"
    
    def parse_dtc_response(self, response: str) -> List[str]:
        """Parse Toyota DTC response"""
        dtcs = []
        response = response.replace(" ", "").upper()
        
        if not response.startswith("43"):
            return dtcs
        
        response = response[2:]
        
        for i in range(0, len(response), 4):
            if i + 4 <= len(response):
                dtc_hex = response[i:i+4]
                dtc_code = self._hex_to_dtc(dtc_hex)
                if dtc_code:
                    dtcs.append(dtc_code)
        
        return dtcs
    
    def _hex_to_dtc(self, hex_code: str) -> Optional[str]:
        """Convert hex to DTC code"""
        try:
            first_byte = int(hex_code[0], 16)
            prefix_map = {0: 'P', 1: 'P', 2: 'P', 3: 'P',
                         4: 'C', 5: 'C', 6: 'C', 7: 'C',
                         8: 'B', 9: 'B', 10: 'B', 11: 'B',
                         12: 'U', 13: 'U', 14: 'U', 15: 'U'}
            
            prefix = prefix_map.get(first_byte, 'P')
            digits = hex_code[1:]
            
            return f"{prefix}{digits}"
        except Exception:
            return None


class HondaProtocolHandler(ProtocolHandler):
    """Protocol handler for Honda vehicles"""
    
    def __init__(self):
        super().__init__(Manufacturer.HONDA)
        
        # Honda-specific module addresses
        self.module_addresses = {
            "PCM": "7E0",
            "TCM": "7E1",
            "ABS": "7D0",
            "AIRBAG": "7D1"
        }
    
    def get_module_address(self, module_name: str) -> Optional[str]:
        """Get Honda module address"""
        return self.module_addresses.get(module_name.upper())
    
    def format_dtc_request(self, module_address: str) -> str:
        """Format Honda DTC request"""
        return "03"
    
    def parse_dtc_response(self, response: str) -> List[str]:
        """Parse Honda DTC response"""
        dtcs = []
        response = response.replace(" ", "").upper()
        
        if not response.startswith("43"):
            return dtcs
        
        response = response[2:]
        
        for i in range(0, len(response), 4):
            if i + 4 <= len(response):
                dtc_hex = response[i:i+4]
                dtc_code = self._hex_to_dtc(dtc_hex)
                if dtc_code:
                    dtcs.append(dtc_code)
        
        return dtcs
    
    def _hex_to_dtc(self, hex_code: str) -> Optional[str]:
        """Convert hex to DTC code"""
        try:
            first_byte = int(hex_code[0], 16)
            prefix_map = {0: 'P', 1: 'P', 2: 'P', 3: 'P',
                         4: 'C', 5: 'C', 6: 'C', 7: 'C',
                         8: 'B', 9: 'B', 10: 'B', 11: 'B',
                         12: 'U', 13: 'U', 14: 'U', 15: 'U'}
            
            prefix = prefix_map.get(first_byte, 'P')
            digits = hex_code[1:]
            
            return f"{prefix}{digits}"
        except Exception:
            return None


class GenericProtocolHandler(ProtocolHandler):
    """Generic OBD-II protocol handler"""
    
    def __init__(self):
        super().__init__(Manufacturer.GENERIC)
        
        # Standard OBD-II addresses
        self.module_addresses = {
            "PCM": "7E0",
            "TCM": "7E1"
        }
    
    def get_module_address(self, module_name: str) -> Optional[str]:
        """Get generic module address"""
        return self.module_addresses.get(module_name.upper())
    
    def format_dtc_request(self, module_address: str) -> str:
        """Format generic DTC request"""
        return "03"
    
    def parse_dtc_response(self, response: str) -> List[str]:
        """Parse generic DTC response"""
        dtcs = []
        response = response.replace(" ", "").upper()
        
        if not response.startswith("43"):
            return dtcs
        
        response = response[2:]
        
        for i in range(0, len(response), 4):
            if i + 4 <= len(response):
                dtc_hex = response[i:i+4]
                dtc_code = self._hex_to_dtc(dtc_hex)
                if dtc_code:
                    dtcs.append(dtc_code)
        
        return dtcs
    
    def _hex_to_dtc(self, hex_code: str) -> Optional[str]:
        """Convert hex to DTC code"""
        try:
            first_byte = int(hex_code[0], 16)
            prefix_map = {0: 'P', 1: 'P', 2: 'P', 3: 'P',
                         4: 'C', 5: 'C', 6: 'C', 7: 'C',
                         8: 'B', 9: 'B', 10: 'B', 11: 'B',
                         12: 'U', 13: 'U', 14: 'U', 15: 'U'}
            
            prefix = prefix_map.get(first_byte, 'P')
            digits = hex_code[1:]
            
            return f"{prefix}{digits}"
        except Exception:
            return None


def get_protocol_handler(manufacturer: str) -> ProtocolHandler:
    """
    Get protocol handler for manufacturer
    
    Args:
        manufacturer: Manufacturer name
        
    Returns:
        ProtocolHandler instance
    """
    manufacturer_upper = manufacturer.upper()
    
    if manufacturer_upper == "FORD":
        return FordProtocolHandler()
    elif manufacturer_upper in ["GM", "CHEVROLET", "GMC", "CADILLAC", "BUICK"]:
        return GMProtocolHandler()
    elif manufacturer_upper == "TOYOTA":
        return ToyotaProtocolHandler()
    elif manufacturer_upper == "HONDA":
        return HondaProtocolHandler()
    else:
        logger.warning(f"Unknown manufacturer '{manufacturer}', using generic handler")
        return GenericProtocolHandler()


if __name__ == '__main__':
    # Test protocol handlers
    print("Testing Protocol Handlers...")
    
    # Test Ford handler
    print("\n1. Testing Ford handler...")
    ford = FordProtocolHandler()
    print(f"   Manufacturer: {ford.name}")
    print(f"   PCM Address: {ford.get_module_address('PCM')}")
    print(f"   DTC Request: {ford.format_dtc_request('7E0')}")
    print(f"   Supports UDS: {ford.supports_uds()}")
    
    # Test DTC parsing
    test_response = "43 16 32 00 00"
    dtcs = ford.parse_dtc_response(test_response)
    print(f"   Parsed DTCs: {dtcs}")
    
    # Test GM handler
    print("\n2. Testing GM handler...")
    gm = GMProtocolHandler()
    print(f"   Manufacturer: {gm.name}")
    print(f"   PCM Address: {gm.get_module_address('PCM')}")
    
    # Test Toyota handler
    print("\n3. Testing Toyota handler...")
    toyota = ToyotaProtocolHandler()
    print(f"   Manufacturer: {toyota.name}")
    print(f"   ABS Address: {toyota.get_module_address('ABS')}")
    
    # Test factory function
    print("\n4. Testing factory function...")
    handler = get_protocol_handler("Ford")
    print(f"   Created handler: {handler.name}")
    
    handler = get_protocol_handler("Unknown")
    print(f"   Fallback handler: {handler.name}")
    
    print("\nProtocol handler tests passed!")
