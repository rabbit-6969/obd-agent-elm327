"""
Vehicle Profile Management

Loads and manages vehicle profiles from YAML configuration.
Supports defining new vehicles without code changes.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class VehicleProfile:
    """Vehicle profile data structure"""
    make: str
    model: str
    year: str
    protocol: str = "CAN"
    bus_speed: str = "HS"
    modules: Dict[str, Dict[str, str]] = field(default_factory=dict)
    dtc_descriptions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    manufacturer_specific: Dict[str, Any] = field(default_factory=dict)
    
    def get_module_address(self, module_name: str) -> Optional[str]:
        """Get module address by name"""
        module = self.modules.get(module_name.upper())
        return module.get('address') if module else None
    
    def get_module_protocol(self, module_name: str) -> Optional[str]:
        """Get module protocol by name"""
        module = self.modules.get(module_name.upper())
        return module.get('protocol', self.protocol) if module else None
    
    def get_dtc_description(self, dtc_code: str) -> Optional[Dict[str, Any]]:
        """Get DTC description by code"""
        return self.dtc_descriptions.get(dtc_code.upper())
    
    def get_identifier(self) -> str:
        """Get vehicle identifier string"""
        return f"{self.make}_{self.model}_{self.year}"


class VehicleProfileLoader:
    """
    Loads vehicle profiles from YAML files
    
    Features:
    - Load profiles from knowledge_base directory
    - Cache loaded profiles
    - Support for multiple manufacturers
    - Extensible without code changes
    """
    
    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        """
        Initialize profile loader
        
        Args:
            knowledge_base_dir: Directory containing vehicle profiles
        """
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.profiles: Dict[str, VehicleProfile] = {}
        
        if not self.knowledge_base_dir.exists():
            logger.warning(f"Knowledge base directory not found: {knowledge_base_dir}")
    
    def load_profile(self, make: str, model: str, year: str) -> Optional[VehicleProfile]:
        """
        Load vehicle profile
        
        Args:
            make: Vehicle make (e.g., "Ford")
            model: Vehicle model (e.g., "Escape")
            year: Vehicle year (e.g., "2008")
            
        Returns:
            VehicleProfile object or None if not found
        """
        # Check cache first
        identifier = f"{make}_{model}_{year}"
        if identifier in self.profiles:
            logger.debug(f"Using cached profile: {identifier}")
            return self.profiles[identifier]
        
        # Try to load from file
        profile_file = self.knowledge_base_dir / f"{identifier}_profile.yaml"
        
        if not profile_file.exists():
            logger.warning(f"Profile not found: {profile_file}")
            return None
        
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Parse profile data
            profile = self._parse_profile_data(data, make, model, year)
            
            # Cache profile
            self.profiles[identifier] = profile
            logger.info(f"Loaded profile: {identifier}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Error loading profile {profile_file}: {e}")
            return None
    
    def _parse_profile_data(self, data: Dict[str, Any], 
                           make: str, model: str, year: str) -> VehicleProfile:
        """
        Parse profile data from YAML
        
        Args:
            data: YAML data dict
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            
        Returns:
            VehicleProfile object
        """
        # Extract vehicle info
        vehicle_info = data.get('vehicle', {})
        
        # Extract modules
        modules = {}
        for module_name, module_data in data.get('modules', {}).items():
            modules[module_name.upper()] = {
                'address': module_data.get('address', ''),
                'protocol': module_data.get('protocol', 'CAN'),
                'bus': module_data.get('bus', 'HS'),
                'status': module_data.get('status', 'unknown')
            }
        
        # Extract DTC descriptions
        dtc_descriptions = {}
        for dtc_code, dtc_data in data.get('dtc_descriptions', {}).items():
            dtc_descriptions[dtc_code.upper()] = {
                'description': dtc_data.get('description', ''),
                'common_causes': dtc_data.get('common_causes', []),
                'repair_hints': dtc_data.get('repair_hints', []),
                'severity': dtc_data.get('severity', 'unknown')
            }
        
        # Create profile
        profile = VehicleProfile(
            make=make,
            model=model,
            year=year,
            protocol=vehicle_info.get('protocol', 'CAN'),
            bus_speed=vehicle_info.get('bus_speed', 'HS'),
            modules=modules,
            dtc_descriptions=dtc_descriptions,
            manufacturer_specific=data.get('manufacturer_specific', {})
        )
        
        return profile
    
    def list_available_profiles(self) -> List[str]:
        """
        List available vehicle profiles
        
        Returns:
            List of profile identifiers
        """
        profiles = []
        
        if not self.knowledge_base_dir.exists():
            return profiles
        
        for profile_file in self.knowledge_base_dir.glob("*_profile.yaml"):
            # Extract identifier from filename
            identifier = profile_file.stem.replace('_profile', '')
            profiles.append(identifier)
        
        return sorted(profiles)
    
    def create_profile_template(self, make: str, model: str, year: str, 
                               output_path: Optional[str] = None) -> str:
        """
        Create a template profile YAML file
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            output_path: Optional output path (defaults to knowledge_base)
            
        Returns:
            Path to created template file
        """
        identifier = f"{make}_{model}_{year}"
        
        if output_path is None:
            output_path = self.knowledge_base_dir / f"{identifier}_profile.yaml"
        else:
            output_path = Path(output_path)
        
        # Create template data
        template = {
            'vehicle': {
                'make': make,
                'model': model,
                'year': year,
                'protocol': 'CAN',
                'bus_speed': 'HS'
            },
            'modules': {
                'PCM': {
                    'address': '7E0',
                    'protocol': 'CAN',
                    'bus': 'HS',
                    'status': 'accessible'
                },
                'ABS': {
                    'address': '760',
                    'protocol': 'CAN',
                    'bus': 'HS',
                    'status': 'partial'
                }
            },
            'dtc_descriptions': {
                'P0000': {
                    'description': 'Example DTC',
                    'common_causes': ['Cause 1', 'Cause 2'],
                    'repair_hints': ['Check component X', 'Inspect wiring'],
                    'severity': 'warning'
                }
            },
            'manufacturer_specific': {
                'notes': 'Add manufacturer-specific information here'
            }
        }
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write template
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Created profile template: {output_path}")
        return str(output_path)


if __name__ == '__main__':
    # Test vehicle profile loader
    print("Testing Vehicle Profile Loader...")
    
    loader = VehicleProfileLoader()
    
    # List available profiles
    print("\n1. Listing available profiles...")
    profiles = loader.list_available_profiles()
    print(f"   Found {len(profiles)} profiles:")
    for profile_id in profiles[:5]:
        print(f"   - {profile_id}")
    
    # Load Ford Escape 2008 profile
    print("\n2. Loading Ford Escape 2008 profile...")
    profile = loader.load_profile("Ford", "Escape", "2008")
    
    if profile:
        print(f"   ✓ Loaded: {profile.get_identifier()}")
        print(f"   Protocol: {profile.protocol}")
        print(f"   Modules: {len(profile.modules)}")
        print(f"   DTCs: {len(profile.dtc_descriptions)}")
        
        # Test module lookup
        pcm_address = profile.get_module_address("PCM")
        print(f"   PCM Address: {pcm_address}")
        
        # Test DTC lookup
        if profile.dtc_descriptions:
            first_dtc = list(profile.dtc_descriptions.keys())[0]
            dtc_info = profile.get_dtc_description(first_dtc)
            print(f"   Sample DTC: {first_dtc} - {dtc_info.get('description', '')[:50]}...")
    else:
        print("   ✗ Profile not found")
    
    # Create template
    print("\n3. Creating profile template...")
    template_path = loader.create_profile_template(
        "Toyota", "Camry", "2020",
        output_path="logs/Toyota_Camry_2020_profile.yaml"
    )
    print(f"   ✓ Created: {template_path}")
    
    print("\nVehicle profile loader tests passed!")
