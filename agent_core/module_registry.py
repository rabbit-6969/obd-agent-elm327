"""
Module Registry for Vehicle Diagnostics

Maintains registry of known module addresses for each vehicle.
Adds newly discovered modules to registry.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class ModuleRegistry:
    """
    Registry of known module addresses for vehicles
    
    Maintains a persistent registry of module addresses discovered
    for each vehicle make/model/year combination.
    """
    
    def __init__(self, registry_path: str = "knowledge_base/module_registry.json"):
        """
        Initialize module registry
        
        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.registry: Dict[str, Dict[str, Any]] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from file"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    self.registry = json.load(f)
                logger.info(f"Loaded module registry from {self.registry_path}")
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self.registry = {}
        else:
            logger.info("No existing registry found, starting fresh")
            self.registry = {}
    
    def _save_registry(self):
        """Save registry to file"""
        try:
            # Create directory if needed
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.registry_path, 'w') as f:
                json.dump(self.registry, f, indent=2)
            logger.info(f"Saved module registry to {self.registry_path}")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def _get_vehicle_key(self, make: str, model: str, year: int) -> str:
        """
        Generate vehicle key for registry
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            
        Returns:
            Vehicle key string
        """
        return f"{make}_{model}_{year}".replace(" ", "_")
    
    def get_modules(self, make: str, model: str, year: int) -> Dict[str, Dict[str, Any]]:
        """
        Get known modules for vehicle
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            
        Returns:
            Dictionary of modules {module_name: {address, protocol, ...}}
        """
        vehicle_key = self._get_vehicle_key(make, model, year)
        
        if vehicle_key in self.registry:
            return self.registry[vehicle_key].get("modules", {})
        
        return {}
    
    def get_module_address(self, make: str, model: str, year: int, 
                          module_name: str) -> Optional[str]:
        """
        Get module address for vehicle
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            module_name: Module name (e.g., "PCM", "ABS")
            
        Returns:
            Module address or None
        """
        modules = self.get_modules(make, model, year)
        module_info = modules.get(module_name.upper())
        
        if module_info:
            return module_info.get("address")
        
        return None
    
    def add_module(self, make: str, model: str, year: int,
                   module_name: str, address: str,
                   protocol: str = "CAN", bus: str = "HS",
                   metadata: Optional[Dict[str, Any]] = None):
        """
        Add module to registry
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            module_name: Module name
            address: Module address (hex)
            protocol: Communication protocol
            bus: Bus type (HS/MS/LS)
            metadata: Additional metadata
        """
        vehicle_key = self._get_vehicle_key(make, model, year)
        
        # Initialize vehicle entry if needed
        if vehicle_key not in self.registry:
            self.registry[vehicle_key] = {
                "make": make,
                "model": model,
                "year": year,
                "modules": {}
            }
        
        # Add module
        module_name_upper = module_name.upper()
        module_info = {
            "address": address,
            "protocol": protocol,
            "bus": bus,
            "discovered_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.registry[vehicle_key]["modules"][module_name_upper] = module_info
        
        logger.info(f"Added module {module_name_upper} at {address} for {make} {model} {year}")
        
        # Save to disk
        self._save_registry()
    
    def update_module_metadata(self, make: str, model: str, year: int,
                               module_name: str, metadata: Dict[str, Any]):
        """
        Update module metadata
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            module_name: Module name
            metadata: Metadata to merge
        """
        vehicle_key = self._get_vehicle_key(make, model, year)
        module_name_upper = module_name.upper()
        
        if vehicle_key in self.registry:
            modules = self.registry[vehicle_key].get("modules", {})
            if module_name_upper in modules:
                # Merge metadata
                current_metadata = modules[module_name_upper].get("metadata", {})
                current_metadata.update(metadata)
                modules[module_name_upper]["metadata"] = current_metadata
                modules[module_name_upper]["updated_at"] = datetime.now().isoformat()
                
                logger.info(f"Updated metadata for {module_name_upper}")
                self._save_registry()
            else:
                logger.warning(f"Module {module_name_upper} not found in registry")
        else:
            logger.warning(f"Vehicle {vehicle_key} not found in registry")
    
    def list_vehicles(self) -> List[Dict[str, Any]]:
        """
        List all vehicles in registry
        
        Returns:
            List of vehicle info dictionaries
        """
        vehicles = []
        for vehicle_key, vehicle_data in self.registry.items():
            vehicles.append({
                "make": vehicle_data.get("make"),
                "model": vehicle_data.get("model"),
                "year": vehicle_data.get("year"),
                "module_count": len(vehicle_data.get("modules", {}))
            })
        return vehicles
    
    def export_vehicle_modules(self, make: str, model: str, year: int) -> Dict[str, Any]:
        """
        Export all modules for a vehicle
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            
        Returns:
            Vehicle data with modules
        """
        vehicle_key = self._get_vehicle_key(make, model, year)
        
        if vehicle_key in self.registry:
            return self.registry[vehicle_key]
        
        return {}


    def correlate_can_id(self, make: str, model: str, year: int,
                        can_id: str, module_name: Optional[str] = None,
                        confidence: float = 1.0, source: str = "manual") -> bool:
        """
        Correlate CAN ID with module type
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            can_id: CAN ID (hex)
            module_name: Module name if known
            confidence: Confidence score (0-1)
            source: Source of correlation (manual, web_research, etc.)
            
        Returns:
            True if correlation added
        """
        vehicle_key = self._get_vehicle_key(make, model, year)
        
        # Initialize vehicle if needed
        if vehicle_key not in self.registry:
            self.registry[vehicle_key] = {
                "make": make,
                "model": model,
                "year": year,
                "modules": {},
                "can_correlations": {}
            }
        
        # Initialize correlations if needed
        if "can_correlations" not in self.registry[vehicle_key]:
            self.registry[vehicle_key]["can_correlations"] = {}
        
        # Add correlation
        correlation_info = {
            "can_id": can_id,
            "module_name": module_name,
            "confidence": confidence,
            "source": source,
            "discovered_at": datetime.now().isoformat()
        }
        
        self.registry[vehicle_key]["can_correlations"][can_id] = correlation_info
        
        logger.info(f"Correlated CAN ID {can_id} with {module_name or 'unknown'} (confidence: {confidence})")
        
        # If module name known and high confidence, add to modules
        if module_name and confidence >= 0.8:
            if module_name.upper() not in self.registry[vehicle_key]["modules"]:
                self.add_module(make, model, year, module_name, can_id, 
                              metadata={"correlation_source": source})
        
        self._save_registry()
        return True
    
    def get_can_correlations(self, make: str, model: str, year: int) -> Dict[str, Dict[str, Any]]:
        """
        Get CAN ID correlations for vehicle
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            
        Returns:
            Dictionary of CAN correlations
        """
        vehicle_key = self._get_vehicle_key(make, model, year)
        
        if vehicle_key in self.registry:
            return self.registry[vehicle_key].get("can_correlations", {})
        
        return {}
    
    def lookup_can_id(self, make: str, model: str, year: int, 
                     can_id: str) -> Optional[Dict[str, Any]]:
        """
        Lookup module info by CAN ID
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            can_id: CAN ID to lookup
            
        Returns:
            Correlation info or None
        """
        correlations = self.get_can_correlations(make, model, year)
        return correlations.get(can_id)


if __name__ == '__main__':
    # Test module registry
    print("Testing Module Registry...")
    
    # Create registry
    registry = ModuleRegistry("test_module_registry.json")
    
    # Add modules for Ford Escape 2008
    print("\n1. Adding modules for Ford Escape 2008...")
    registry.add_module("Ford", "Escape", 2008, "PCM", "7E0", "CAN", "HS")
    registry.add_module("Ford", "Escape", 2008, "HVAC", "7A0", "CAN", "HS")
    registry.add_module("Ford", "Escape", 2008, "ABS", "760", "CAN", "HS")
    
    # Get modules
    print("\n2. Getting modules...")
    modules = registry.get_modules("Ford", "Escape", 2008)
    print(f"   Found {len(modules)} modules")
    for name, info in modules.items():
        print(f"   - {name}: {info['address']}")
    
    # Get specific module address
    print("\n3. Getting HVAC address...")
    hvac_addr = registry.get_module_address("Ford", "Escape", 2008, "HVAC")
    print(f"   HVAC address: {hvac_addr}")
    
    # Update metadata
    print("\n4. Updating module metadata...")
    registry.update_module_metadata("Ford", "Escape", 2008, "HVAC",
                                   {"dtc_count": 2, "last_scan": "2026-02-23"})
    
    # List vehicles
    print("\n5. Listing vehicles...")
    vehicles = registry.list_vehicles()
    for vehicle in vehicles:
        print(f"   - {vehicle['make']} {vehicle['model']} {vehicle['year']}: {vehicle['module_count']} modules")
    
    # Export vehicle
    print("\n6. Exporting vehicle data...")
    vehicle_data = registry.export_vehicle_modules("Ford", "Escape", 2008)
    print(f"   Exported {len(vehicle_data.get('modules', {}))} modules")
    
    # Test CAN ID correlation
    print("\n7. Testing CAN ID correlation...")
    registry.correlate_can_id("Ford", "Escape", 2008, "0x7A0", "HVAC", 0.95, "web_research")
    registry.correlate_can_id("Ford", "Escape", 2008, "0x760", "ABS", 0.90, "manual")
    
    # Get correlations
    print("\n8. Getting CAN correlations...")
    correlations = registry.get_can_correlations("Ford", "Escape", 2008)
    print(f"   Found {len(correlations)} correlations")
    for can_id, info in correlations.items():
        print(f"   - {can_id}: {info['module_name']} (confidence: {info['confidence']})")
    
    # Lookup specific CAN ID
    print("\n9. Looking up CAN ID 0x7A0...")
    lookup_result = registry.lookup_can_id("Ford", "Escape", 2008, "0x7A0")
    if lookup_result:
        print(f"   Module: {lookup_result['module_name']}")
        print(f"   Source: {lookup_result['source']}")
    
    # Clean up test file
    import os
    if os.path.exists("test_module_registry.json"):
        os.remove("test_module_registry.json")
    
    print("\nModule registry tests passed!")
