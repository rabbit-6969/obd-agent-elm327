# Knowledge Base

This directory contains **vehicle-specific operational knowledge** that grows over time through diagnostic sessions.

## Purpose

Store learned information about specific vehicles (make, model, year) including:
- Diagnostic procedures that work
- DTC descriptions and repair hints
- Module addresses and command sequences
- CAN signal definitions
- Captured diagnostic data

## Distinction from `reference/`

**`knowledge_base/`** (this directory):
- Vehicle-specific data (Ford_Escape_2008, etc.)
- Modified by agent during operation
- Grows through learning
- User's proprietary diagnostic knowledge

**`reference/`** (sibling directory):
- Universal protocol documentation (ISO 14229-1, OBD-II)
- Static reference material
- Industry standards
- Applies to all vehicles

## Contents

### Technical Data Files (`.dat`)
**Format**: Compact, machine-optimized
**Purpose**: Fast lookup of module addresses, commands, response patterns
**Example**: `Ford_Escape_2008_technical.dat`

```
M:HVAC A:7A0 P:CAN B:HS
C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,}
```

### Vehicle Profiles (`.yaml`)
**Format**: Human-readable YAML
**Purpose**: DTC descriptions, repair hints, common issues
**Example**: `Ford_Escape_2008_profile.yaml`

```yaml
dtc_descriptions:
  P1632:
    description: "HVAC Mix Door Actuator Circuit - Stuck"
    common_causes: ["Actuator motor failure"]
    repair_hints: ["Remove glove box for access"]
```

### CAN Bus Databases (`.kcd`)
**Format**: KCD (Kayak CAN Database)
**Purpose**: Signal definitions for CAN messages
**Example**: `Ford_Escape_2008_canbus.kcd`

### Captured Vehicle Data (`.json`)
**Format**: JSON
**Purpose**: Real diagnostic session data for analysis
**Example**: `vehicle_data_20260214_185442.json`

### Learned Procedures (`.md`)
**Format**: Markdown
**Purpose**: Documented successful diagnostic workflows
**Location**: `learned_procedures/`

## Structure

```
knowledge_base/
├── README.md                              # This file
├── {Make}_{Model}_{Year}_technical.dat    # Technical data (fast lookup)
├── {Make}_{Model}_{Year}_profile.yaml     # Vehicle profile (descriptions)
├── {Make}_{Model}_{Year}_canbus.kcd       # CAN database (optional)
├── vehicle_data_*.json                    # Captured diagnostic data
└── learned_procedures/                    # Successful workflows
    ├── hvac_blend_door_diagnosis.md
    └── transmission_shift_solenoid_test.md
```

## Growth Pattern

**Initial State** (minimal):
```
knowledge_base/
└── Ford_Escape_2008_profile.yaml  (basic DTC descriptions)
```

**After First Diagnostic**:
```
knowledge_base/
├── Ford_Escape_2008_profile.yaml
├── Ford_Escape_2008_technical.dat  (NEW: commands added)
└── vehicle_data_20260214_185442.json  (NEW: captured data)
```

**After Multiple Diagnostics** (rich knowledge):
```
knowledge_base/
├── Ford_Escape_2008_profile.yaml  (enriched with more DTCs)
├── Ford_Escape_2008_technical.dat  (multiple modules)
├── Ford_Escape_2008_canbus.kcd
├── vehicle_data_*.json  (multiple sessions)
└── learned_procedures/
    ├── hvac_blend_door_diagnosis.md
    ├── transmission_shift_solenoid_test.md
    └── abs_wheel_speed_sensor_test.md
```

## Agent Usage

### Lookup Flow
1. Agent receives diagnostic request
2. Checks `{Vehicle}_technical.dat` for known procedure (< 5ms)
3. If found: Execute immediately
4. If not found: Check `reference/` for protocol specs, then web research
5. After success: Document in technical.dat for next time

### Update Flow
1. Agent successfully executes new diagnostic
2. Appends command to `{Vehicle}_technical.dat`
3. If new DTC discovered, updates `{Vehicle}_profile.yaml`
4. Saves raw data to `vehicle_data_{timestamp}.json`
5. Next time: Instant lookup!

## File Naming Convention

**Pattern**: `{Make}_{Model}_{Year}_{Type}.{ext}`

**Examples**:
- `Ford_Escape_2008_technical.dat`
- `Ford_Escape_2008_profile.yaml`
- `Ford_Escape_2008_canbus.kcd`
- `Ford_Fusion_2010_technical.dat`
- `Toyota_Camry_2015_profile.yaml`

## Performance

- Technical data parse: < 50ms for entire file
- Single procedure lookup: < 5ms
- Profile load: < 100ms (cached after first load)
- Memory usage: ~100KB per vehicle

## See Also

- `reference/` - Universal protocol documentation
- `.kiro/specs/ai-vehicle-diagnostic-agent/design/knowledge-format.md` - Format specifications
- `.kiro/specs/ai-vehicle-diagnostic-agent/design/architecture.md` - Knowledge organization details
