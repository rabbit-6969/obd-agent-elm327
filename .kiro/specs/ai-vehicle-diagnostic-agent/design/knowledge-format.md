# Knowledge Document Format

## Knowledge Document Format

## Directory Organization

### `knowledge_base/` vs `reference/`

The system maintains two distinct knowledge directories:

**`knowledge_base/`** - Vehicle-Specific Operational Data
- Vehicle profiles (YAML): DTC descriptions, repair hints
- Technical data (DAT): Module addresses, commands
- CAN databases (KCD): Signal definitions
- Captured data (JSON): Diagnostic session logs
- Learned procedures: Successful workflows

**`reference/`** - Universal Protocol Documentation
- ISO 14229-1 UDS specifications
- OBD-II protocol documentation
- CAN bus standards
- Example implementations
- Industry standards

**Key Difference**: `knowledge_base/` grows through learning and is vehicle-specific, while `reference/` contains static protocol documentation that applies universally.

## Overview

Knowledge is split into two file types for optimal performance and usability:

1. **Technical Data** (.dat): Machine-optimized, ultra-compact, fast parsing
2. **Vehicle Profiles** (.yaml): Human-readable, rich context, easy editing

## Technical Data Format

### File Location
`knowledge/technical/{make}_{model}_{year}_technical.dat`

Example: `knowledge/technical/Ford_Escape_2008_technical.dat`

### Format Specification

**Design Goals**:
- Parse entire file in < 50ms
- Single procedure lookup in < 5ms
- Minimal file size (no redundancy)
- No human descriptions (pure technical data)

**Format**: Line-based, space-separated key:value pairs

### Module Definitions

```
M:name A:address P:protocol B:bus
```

**Example**:
```
M:HVAC A:7A0 P:CAN B:HS
M:ABS A:760 P:CAN B:HS
M:PCM A:7E0 P:CAN B:HS
M:BCM A:726 P:CAN B:HS
M:IPC A:720 P:CAN B:HS
```

**Fields**:
- `M:` Module name (short identifier)
- `A:` CAN address (hex, no 0x prefix)
- `P:` Protocol (CAN, LIN, etc.)
- `B:` Bus type (HS=High-Speed 500kbps, LS=Low-Speed 125kbps)

### Command Sequences

```
C:id M:mode [PID:pid] [D:data] R:response_pattern
```

**Example**:
```
C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,}
C:HVAC.CLEAR_DTC M:04 R:44
C:HVAC.READ_LIVE M:01 PID:05 R:41 05 [0-9A-F]{2}
C:HVAC.ACTUATE_BLEND M:31 PID:01 D:FF R:71 01
```

**Fields**:
- `C:` Command identifier (module.action)
- `M:` OBD Mode (hex)
- `PID:` Parameter ID (optional, hex)
- `D:` Data bytes (optional, hex)
- `R:` Expected response pattern (regex)

### DTC Parsing Rules

```
DTC:code B:byte_range BITS:bit_range CALC:formula
```

**Example**:
```
DTC:P1632 B:0-1 BITS:0-15 CALC:hex
DTC:P1635 B:0-1 BITS:0-15 CALC:hex
DTC:C1234 B:0-1 BITS:0-15 CALC:hex
```

**Fields**:
- `DTC:` DTC code
- `B:` Byte position(s) in response
- `BITS:` Bit range within bytes
- `CALC:` Calculation formula (hex, dec, (hex-40), etc.)

### Response Parsing Rules

```
R:cmd_id PATTERN:regex EXTRACT:field_names CALC:formulas
```

**Example**:
```
R:READ_DTC PATTERN:43([0-9A-F]{4})+ EXTRACT:dtc_hex
R:LIVE_TEMP PATTERN:41 05 ([0-9A-F]{2}) EXTRACT:temp_hex CALC:(hex-40)
R:VOLTAGE PATTERN:41 42 ([0-9A-F]{4}) EXTRACT:volt_hex CALC:(hex/1000)
```

**Fields**:
- `R:` Response rule for command
- `PATTERN:` Regex to match response
- `EXTRACT:` Field names from capture groups
- `CALC:` Calculation formulas for extracted values

### Bit Mappings

```
BM:field BYTE:pos BIT:range MEANING:values
```

**Example**:
```
BM:monitor_status BYTE:1 BIT:0 MEANING:0=incomplete,1=complete
BM:dtc_pending BYTE:1 BIT:2 MEANING:0=no,1=yes
BM:mil_status BYTE:1 BIT:7 MEANING:0=off,1=on
```

**Fields**:
- `BM:` Bit mapping name
- `BYTE:` Byte position in response
- `BIT:` Bit position (0-7)
- `MEANING:` Value interpretations

### Complete Example

```
# Ford Escape 2008 - Technical Data
# Generated: 2024-01-15
# Version: 1.0

## Modules
M:HVAC A:7A0 P:CAN B:HS
M:ABS A:760 P:CAN B:HS
M:PCM A:7E0 P:CAN B:HS

## Commands
C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,}
C:HVAC.CLEAR_DTC M:04 R:44
C:ABS.READ_DTC M:03 R:43[0-9A-F]{4,}
C:PCM.READ_LIVE M:01 PID:05 R:41 05 [0-9A-F]{2}

## DTC Parsing
DTC:P1632 B:0-1 BITS:0-15 CALC:hex
DTC:P1635 B:0-1 BITS:0-15 CALC:hex

## Response Parsing
R:READ_DTC PATTERN:43([0-9A-F]{4})+ EXTRACT:dtc_hex
R:LIVE_TEMP PATTERN:41 05 ([0-9A-F]{2}) EXTRACT:temp_hex CALC:(hex-40)

## Bit Mappings
BM:monitor_status BYTE:1 BIT:0 MEANING:0=incomplete,1=complete
```

### Parsing Implementation

```python
class TechnicalDataParser:
    """Fast parser for technical data format"""
    
    def parse_file(self, filepath: str) -> TechnicalKnowledge:
        """Parse entire file in < 50ms"""
        modules = {}
        commands = {}
        dtc_rules = {}
        response_rules = {}
        bit_mappings = {}
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('M:'):
                    module = self._parse_module(line)
                    modules[module.name] = module
                elif line.startswith('C:'):
                    command = self._parse_command(line)
                    commands[command.id] = command
                elif line.startswith('DTC:'):
                    rule = self._parse_dtc_rule(line)
                    dtc_rules[rule.code] = rule
                elif line.startswith('R:'):
                    rule = self._parse_response_rule(line)
                    response_rules[rule.cmd_id] = rule
                elif line.startswith('BM:'):
                    mapping = self._parse_bit_mapping(line)
                    bit_mappings[mapping.field] = mapping
        
        return TechnicalKnowledge(
            modules=modules,
            commands=commands,
            dtc_rules=dtc_rules,
            response_rules=response_rules,
            bit_mappings=bit_mappings
        )
    
    def _parse_module(self, line: str) -> ModuleInfo:
        """Parse: M:HVAC A:7A0 P:CAN B:HS"""
        parts = line.split()
        return ModuleInfo(
            name=parts[0].split(':')[1],
            address=parts[1].split(':')[1],
            protocol=parts[2].split(':')[1],
            bus=parts[3].split(':')[1]
        )
```

## Vehicle Profile Format

### File Location
`knowledge/vehicles/{make}_{model}_{year}_profile.yaml`

Example: `knowledge/vehicles/Ford_Escape_2008_profile.yaml`

### Format Specification

**Design Goals**:
- Human-readable and editable
- Rich context and descriptions
- Repair hints and common issues
- Easy to extend

**Format**: YAML with structured sections

### Complete Example

```yaml
# Ford Escape 2008 - Vehicle Profile
# Human-readable descriptions and context

vehicle:
  make: Ford
  model: Escape
  year: 2008
  vin_pattern: "1FM.*"
  generation: "Second Generation (2008-2012)"
  engine_options:
    - "2.3L I4"
    - "3.0L V6"
  notes: "Uses CAN 2.0b protocol, HS-CAN for powertrain, LS-CAN for comfort systems"

modules:
  HVAC:
    full_name: "Heating, Ventilation, and Air Conditioning Control Module"
    location: "Behind dashboard, center console area"
    part_numbers:
      - "8L8Z-19980-A"
      - "8L8Z-19980-B"
    common_issues:
      - "Blend door actuator failure (clicking noise)"
      - "Mode door stuck (airflow direction issues)"
      - "Temperature sensor drift"
    diagnostic_notes: |
      HVAC module responds quickly on HS-CAN.
      Blend door actuator is a common failure point.
      Listen for clicking sounds when changing temperature.
    repair_difficulty: "Moderate (requires dashboard removal)"
    
  ABS:
    full_name: "Anti-Lock Braking System Module"
    location: "Engine bay, driver side near brake master cylinder"
    part_numbers:
      - "8L8Z-2C219-A"
    common_issues:
      - "Wheel speed sensor failure"
      - "ABS pump motor failure"
      - "Hydraulic unit internal leak"
    diagnostic_notes: |
      ABS module requires vehicle stationary for some tests.
      Wheel speed sensors are common failure points.
    repair_difficulty: "Difficult (requires brake bleeding)"

dtc_descriptions:
  P1632:
    description: "HVAC Mix Door Actuator Circuit - Stuck"
    severity: "WARNING"
    symptoms:
      - "Temperature control not working"
      - "Clicking noise from dashboard"
      - "Air temperature doesn't change"
    common_causes:
      - "Blend door actuator motor failure"
      - "Mechanical obstruction in blend door"
      - "Wiring harness damage to actuator"
      - "Actuator gear stripped"
    diagnostic_steps:
      - "Listen for clicking noise when changing temperature"
      - "Test actuator motor resistance (should be 200-400 ohms)"
      - "Check for binding in door mechanism"
      - "Verify 12V power supply to actuator"
      - "Check actuator feedback signal"
    repair_hints:
      - "Actuator located behind glove box"
      - "Remove glove box for access (4 screws)"
      - "Disconnect electrical connector before removing actuator"
      - "Test new actuator before full installation"
    parts_needed:
      - "Blend door actuator (Motorcraft YH-1800 or equivalent)"
      - "Electrical connector (if damaged)"
    estimated_repair_time: "1-2 hours"
    estimated_cost: "$150-300 (parts + labor)"
    
  P1635:
    description: "HVAC Blend Door Actuator - Stuck/Malfunction"
    severity: "WARNING"
    symptoms:
      - "No temperature control"
      - "Constant clicking from dashboard"
    common_causes:
      - "Actuator gear stripped"
      - "Door linkage broken"
      - "Actuator motor burned out"
    diagnostic_steps:
      - "Remove actuator and test manually"
      - "Check door movement without actuator"
      - "Inspect actuator gears for damage"
    repair_hints:
      - "Same repair as P1632"
      - "Check door itself for damage"
    parts_needed:
      - "Blend door actuator"
    estimated_repair_time: "1-2 hours"
    estimated_cost: "$150-300"

repair_procedures:
  blend_door_actuator_replacement:
    title: "HVAC Blend Door Actuator Replacement"
    difficulty: "Moderate"
    tools_needed:
      - "Phillips screwdriver"
      - "7mm socket"
      - "Flashlight"
      - "Multimeter (for testing)"
    steps:
      - "Disconnect negative battery terminal"
      - "Remove glove box (4 screws)"
      - "Locate actuator on HVAC housing"
      - "Disconnect electrical connector"
      - "Remove 3 mounting screws"
      - "Remove old actuator"
      - "Test new actuator before installation"
      - "Install new actuator (3 screws)"
      - "Reconnect electrical connector"
      - "Reinstall glove box"
      - "Reconnect battery"
      - "Test temperature control"
      - "Clear DTCs"
    warnings:
      - "Disconnect battery to avoid airbag deployment"
      - "Be gentle with plastic clips on glove box"
    time_estimate: "1-2 hours"

related_vehicles:
  - make: Ford
    model: Fusion
    years: [2006, 2007, 2008, 2009]
    notes: "Similar HVAC system, procedures may apply"
  - make: Ford
    model: Focus
    years: [2008, 2009, 2010]
    notes: "Different actuator location but similar diagnosis"
  - make: Mercury
    model: Mariner
    years: [2008, 2009]
    notes: "Badge-engineered Escape, identical systems"
```

## Usage Examples

### Agent Lookup Flow

```python
# 1. Fast lookup from technical data
technical = load_technical_data("Ford_Escape_2008_technical.dat")
command = technical.commands["HVAC.READ_DTC"]  # < 5ms

# 2. Execute command
response = adapter.send_command(command)

# 3. Parse response using technical rules
dtc_codes = technical.parse_dtc_response(response)  # < 10ms

# 4. Get human descriptions from profile
profile = load_vehicle_profile("Ford_Escape_2008_profile.yaml")
for dtc in dtc_codes:
    desc = profile.dtc_descriptions[dtc.code]
    print(f"{dtc.code}: {desc.description}")
    print(f"Severity: {desc.severity}")
    print(f"Common causes: {desc.common_causes}")
    print(f"Repair hints: {desc.repair_hints}")
```

### Agent Learning Flow

```python
# User provides new procedure
new_procedure = {
    "module": "HVAC",
    "action": "READ_DTC",
    "command": {"mode": "03"},
    "response_pattern": "43[0-9A-F]{4,}"
}

# 1. Append to technical data (fast, compact)
append_to_technical_data(
    "Ford_Escape_2008_technical.dat",
    f"C:HVAC.READ_DTC M:03 R:43[0-9A-F]{{4,}}\n"
)

# 2. User provides DTC description
new_dtc = {
    "code": "P1632",
    "description": "HVAC Mix Door Actuator Circuit - Stuck",
    "user_notes": "Heard clicking noise, replaced actuator, fixed"
}

# 3. Update vehicle profile (human-readable)
update_vehicle_profile(
    "Ford_Escape_2008_profile.yaml",
    dtc_code="P1632",
    description=new_dtc
)
```

## Performance Benchmarks

### Technical Data Parsing
- File size: ~10KB for 50 procedures
- Parse time: 15-30ms
- Single lookup: < 5ms
- Memory usage: ~100KB

### Vehicle Profile Loading
- File size: ~50KB for rich descriptions
- Parse time: 50-100ms (YAML)
- Cached in memory after first load
- Memory usage: ~500KB

## Migration and Versioning

### Version Header
```
# Ford Escape 2008 - Technical Data
# Version: 1.0
# Generated: 2024-01-15
# Format: compact-v1
```

### Backward Compatibility
- Old format readers can skip unknown fields
- New fields added with default values
- Version number in header for validation
