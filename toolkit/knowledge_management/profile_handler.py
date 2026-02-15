"""
Vehicle Profile YAML Handler

Loads and manages human-readable vehicle profiles with DTC descriptions,
repair hints, and diagnostic procedures.
"""

import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class VehicleInfo:
    """Basic vehicle information"""
    make: str
    model: str
    year: int
    vin_pattern: Optional[str] = None
    generation: Optional[str] = None
    engine_options: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class ModuleDescription:
    """Human-readable module description"""
    full_name: str
    location: Optional[str] = None
    part_numbers: List[str] = field(default_factory=list)
    common_issues: List[str] = field(default_factory=list)
    diagnostic_notes: Optional[str] = None
    repair_difficulty: Optional[str] = None


@dataclass
class DTCDescription:
    """DTC description with repair information"""
    code: str
    description: str
    severity: str = "WARNING"
    symptoms: List[str] = field(default_factory=list)
    common_causes: List[str] = field(default_factory=list)
    diagnostic_steps: List[str] = field(default_factory=list)
    repair_hints: List[str] = field(default_factory=list)
    parts_needed: List[str] = field(default_factory=list)
    estimated_repair_time: Optional[str] = None
    estimated_cost: Optional[str] = None
    
    def __repr__(self):
        return f"DTC({self.code}: {self.description})"


@dataclass
class RepairProcedure:
    """Step-by-step repair procedure"""
    title: str
    difficulty: str
    tools_needed: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    time_estimate: Optional[str] = None


@dataclass
class RelatedVehicle:
    """Related vehicle with similar systems"""
    make: str
    model: str
    years: List[int] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class VehicleProfile:
    """Complete vehicle profile"""
    vehicle: VehicleInfo
    modules: Dict[str, ModuleDescription] = field(default_factory=dict)
    dtc_descriptions: Dict[str, DTCDescription] = field(default_factory=dict)
    repair_procedures: Dict[str, RepairProcedure] = field(default_factory=dict)
    related_vehicles: List[RelatedVehicle] = field(default_factory=list)
    
    def __repr__(self):
        return (f"VehicleProfile({self.vehicle.make} {self.vehicle.model} "
                f"{self.vehicle.year}, {len(self.dtc_descriptions)} DTCs)")


class ProfileHandlerError(Exception):
    """Vehicle profile handling error"""
    pass


class VehicleProfileHandler:
    """
    Handler for vehicle profile YAML files
    
    Loads human-readable vehicle profiles with DTC descriptions,
    repair hints, and diagnostic procedures.
    """
    
    def __init__(self):
        self.profile: Optional[VehicleProfile] = None
    
    def load_profile(self, filepath: str) -> VehicleProfile:
        """
        Load vehicle profile from YAML file
        
        Args:
            filepath: Path to YAML profile file
            
        Returns:
            VehicleProfile object
            
        Raises:
            ProfileHandlerError: If file cannot be loaded
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise ProfileHandlerError(f"Profile file not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ProfileHandlerError(f"Invalid YAML syntax: {e}")
        except IOError as e:
            raise ProfileHandlerError(f"Error reading file: {e}")
        
        if not data:
            raise ProfileHandlerError("Profile file is empty")
        
        try:
            self.profile = self._parse_profile(data)
        except Exception as e:
            raise ProfileHandlerError(f"Error parsing profile: {e}")
        
        return self.profile
    
    def _parse_profile(self, data: dict) -> VehicleProfile:
        """Parse profile data into structured objects"""
        
        # Parse vehicle info
        vehicle_data = data.get('vehicle', {})
        vehicle = VehicleInfo(
            make=vehicle_data.get('make', ''),
            model=vehicle_data.get('model', ''),
            year=vehicle_data.get('year', 0),
            vin_pattern=vehicle_data.get('vin_pattern'),
            generation=vehicle_data.get('generation'),
            engine_options=vehicle_data.get('engine_options', []),
            notes=vehicle_data.get('notes')
        )
        
        # Parse modules
        modules = {}
        modules_data = data.get('modules', {})
        for name, mod_data in modules_data.items():
            modules[name] = ModuleDescription(
                full_name=mod_data.get('full_name', name),
                location=mod_data.get('location'),
                part_numbers=mod_data.get('part_numbers', []),
                common_issues=mod_data.get('common_issues', []),
                diagnostic_notes=mod_data.get('diagnostic_notes'),
                repair_difficulty=mod_data.get('repair_difficulty')
            )
        
        # Parse DTC descriptions
        dtc_descriptions = {}
        dtc_data = data.get('dtc_descriptions', {})
        for code, desc_data in dtc_data.items():
            dtc_descriptions[code] = DTCDescription(
                code=code,
                description=desc_data.get('description', ''),
                severity=desc_data.get('severity', 'WARNING'),
                symptoms=desc_data.get('symptoms', []),
                common_causes=desc_data.get('common_causes', []),
                diagnostic_steps=desc_data.get('diagnostic_steps', []),
                repair_hints=desc_data.get('repair_hints', []),
                parts_needed=desc_data.get('parts_needed', []),
                estimated_repair_time=desc_data.get('estimated_repair_time'),
                estimated_cost=desc_data.get('estimated_cost')
            )
        
        # Parse repair procedures
        repair_procedures = {}
        proc_data = data.get('repair_procedures', {})
        for name, proc in proc_data.items():
            repair_procedures[name] = RepairProcedure(
                title=proc.get('title', name),
                difficulty=proc.get('difficulty', 'Unknown'),
                tools_needed=proc.get('tools_needed', []),
                steps=proc.get('steps', []),
                warnings=proc.get('warnings', []),
                time_estimate=proc.get('time_estimate')
            )
        
        # Parse related vehicles
        related_vehicles = []
        related_data = data.get('related_vehicles', [])
        for rel in related_data:
            related_vehicles.append(RelatedVehicle(
                make=rel.get('make', ''),
                model=rel.get('model', ''),
                years=rel.get('years', []),
                notes=rel.get('notes')
            ))
        
        return VehicleProfile(
            vehicle=vehicle,
            modules=modules,
            dtc_descriptions=dtc_descriptions,
            repair_procedures=repair_procedures,
            related_vehicles=related_vehicles
        )
    
    def get_dtc_description(self, code: str) -> Optional[DTCDescription]:
        """
        Get DTC description by code
        
        Args:
            code: DTC code (e.g., "P1632")
            
        Returns:
            DTCDescription object or None if not found
        """
        if not self.profile:
            raise ProfileHandlerError("No profile loaded")
        
        return self.profile.dtc_descriptions.get(code)
    
    def search_dtc_by_symptom(self, symptom: str) -> List[DTCDescription]:
        """
        Search DTCs by symptom keyword
        
        Args:
            symptom: Symptom keyword to search for
            
        Returns:
            List of matching DTCDescription objects
        """
        if not self.profile:
            raise ProfileHandlerError("No profile loaded")
        
        symptom_lower = symptom.lower()
        matches = []
        
        for dtc in self.profile.dtc_descriptions.values():
            # Search in description
            if symptom_lower in dtc.description.lower():
                matches.append(dtc)
                continue
            
            # Search in symptoms list
            for s in dtc.symptoms:
                if symptom_lower in s.lower():
                    matches.append(dtc)
                    break
        
        return matches
    
    def get_module_info(self, module_name: str) -> Optional[ModuleDescription]:
        """
        Get module description by name
        
        Args:
            module_name: Module name (e.g., "HVAC")
            
        Returns:
            ModuleDescription object or None if not found
        """
        if not self.profile:
            raise ProfileHandlerError("No profile loaded")
        
        return self.profile.modules.get(module_name)
    
    def get_repair_procedure(self, procedure_name: str) -> Optional[RepairProcedure]:
        """
        Get repair procedure by name
        
        Args:
            procedure_name: Procedure name
            
        Returns:
            RepairProcedure object or None if not found
        """
        if not self.profile:
            raise ProfileHandlerError("No profile loaded")
        
        return self.profile.repair_procedures.get(procedure_name)
    
    def get_related_vehicles(self) -> List[RelatedVehicle]:
        """
        Get list of related vehicles
        
        Returns:
            List of RelatedVehicle objects
        """
        if not self.profile:
            raise ProfileHandlerError("No profile loaded")
        
        return self.profile.related_vehicles
    
    def get_profile(self) -> VehicleProfile:
        """
        Get loaded profile
        
        Returns:
            VehicleProfile object
            
        Raises:
            ProfileHandlerError: If no profile loaded
        """
        if not self.profile:
            raise ProfileHandlerError("No profile loaded")
        
        return self.profile


def load_vehicle_profile(filepath: str) -> VehicleProfile:
    """
    Convenience function to load vehicle profile
    
    Args:
        filepath: Path to YAML profile file
        
    Returns:
        VehicleProfile object
    """
    handler = VehicleProfileHandler()
    return handler.load_profile(filepath)


if __name__ == '__main__':
    # Test profile handler
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            profile = load_vehicle_profile(filepath)
            print(f"✓ Loaded {profile}")
            print(f"  Vehicle: {profile.vehicle.make} {profile.vehicle.model} {profile.vehicle.year}")
            print(f"  Modules: {len(profile.modules)}")
            print(f"  DTCs: {len(profile.dtc_descriptions)}")
            print(f"  Procedures: {len(profile.repair_procedures)}")
            print(f"  Related vehicles: {len(profile.related_vehicles)}")
            
            if profile.dtc_descriptions:
                print("\n  Sample DTCs:")
                for code, dtc in list(profile.dtc_descriptions.items())[:3]:
                    print(f"    {code}: {dtc.description}")
                    print(f"      Severity: {dtc.severity}")
                    if dtc.common_causes:
                        print(f"      Common causes: {len(dtc.common_causes)}")
        
        except ProfileHandlerError as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python profile_handler.py <profile.yaml>")
