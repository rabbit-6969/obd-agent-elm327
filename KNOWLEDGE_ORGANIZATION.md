# Knowledge Organization Guide

## Quick Reference

### Two Directories, Two Purposes

| Directory | Purpose | Content Type | Modified By | Growth |
|-----------|---------|--------------|-------------|--------|
| `knowledge_base/` | Vehicle-specific operational data | Learned procedures, DTCs, commands | Agent during diagnostics | Grows over time |
| `reference/` | Universal protocol documentation | ISO standards, protocol specs | User provides extracts | Grows on demand |

## When to Use Each

### Use `knowledge_base/` for:
- ✅ Ford Escape 2008 HVAC module address
- ✅ DTC P1632 description and repair hints
- ✅ Successful diagnostic procedures
- ✅ Captured vehicle data
- ✅ CAN signal definitions for specific vehicle

### Use `reference/` for:
- ✅ ISO 14229-1 Service 0x22 specification
- ✅ UDS protocol message formats
- ✅ OBD-II standard definitions
- ✅ Example CAN database structures
- ✅ Industry standard reference material

## Agent Search Flow

```
User Request
    ↓
1. Check knowledge_base/{Vehicle}_technical.dat
   ├─ Found? → Execute immediately (< 5ms)
   └─ Not found? ↓
    
2. Check reference/ISO_14229-1_UDS_INDEX.md
   ├─ Service documented? → Read spec, implement
   └─ Not documented? ↓
    
3. Request documentation from user
   ├─ User provides → Save to reference/
   └─ Implement using spec ↓
    
4. Execute diagnostic
   └─ Success? → Document in knowledge_base/
    
5. Next time: Instant lookup from knowledge_base!
```

## Directory Structure

```
project/
├── knowledge_base/              # Vehicle-specific (grows through learning)
│   ├── README.md               # Explains vehicle-specific data
│   ├── Ford_Escape_2008_profile.yaml
│   ├── Ford_Escape_2008_technical.dat
│   ├── Ford_Escape_2008_canbus.kcd
│   ├── vehicle_data_*.json
│   └── learned_procedures/
│       ├── hvac_blend_door_diagnosis.md
│       └── transmission_shift_solenoid_test.md
│
├── reference/                   # Universal protocols (static reference)
│   ├── README.md               # Explains protocol documentation
│   ├── ISO_14229-1_UDS_INDEX.md
│   ├── ISO_14229-1_UDS_Service_0x19_ReadDTC.md
│   ├── ISO_14229-1_UDS_Service_0x22_ReadData.md
│   └── mazda_skyactiv.kcd
│
└── .kiro/specs/ai-vehicle-diagnostic-agent/
    └── design/
        ├── architecture.md      # Detailed knowledge organization
        └── knowledge-format.md  # File format specifications
```

## Example Scenarios

### Scenario 1: First HVAC Diagnostic

**Initial State**:
```
knowledge_base/
└── Ford_Escape_2008_profile.yaml  (basic DTCs)

reference/
└── ISO_14229-1_UDS_Service_0x19_ReadDTC.md
```

**User**: "Check HVAC codes on my 2008 Ford Escape"

**Agent**:
1. Checks `knowledge_base/Ford_Escape_2008_technical.dat` → Not found
2. Checks `reference/ISO_14229-1_UDS_Service_0x19_ReadDTC.md` → Found!
3. Uses ISO spec to construct command
4. Executes diagnostic successfully
5. Documents in `knowledge_base/Ford_Escape_2008_technical.dat`

**Final State**:
```
knowledge_base/
├── Ford_Escape_2008_profile.yaml
└── Ford_Escape_2008_technical.dat  (NEW: HVAC.READ_DTC added)

reference/
└── ISO_14229-1_UDS_Service_0x19_ReadDTC.md
```

### Scenario 2: Transmission Temperature Reading

**Initial State**:
```
knowledge_base/
├── Ford_Escape_2008_profile.yaml
└── Ford_Escape_2008_technical.dat  (has HVAC commands)

reference/
└── ISO_14229-1_UDS_Service_0x19_ReadDTC.md
```

**User**: "Read transmission fluid temperature"

**Agent**:
1. Checks `knowledge_base/` → No TCM.READ_TEMP procedure
2. Checks `reference/ISO_14229-1_UDS_INDEX.md` → Need Service 0x22
3. Service 0x22 not documented → Request from user
4. User provides ISO 14229-1 Section 10.2
5. Agent creates `reference/ISO_14229-1_UDS_Service_0x22_ReadData.md`
6. Implements command using spec
7. Executes successfully
8. Documents in `knowledge_base/Ford_Escape_2008_technical.dat`

**Final State**:
```
knowledge_base/
├── Ford_Escape_2008_profile.yaml
└── Ford_Escape_2008_technical.dat  (NEW: TCM.READ_TEMP added)

reference/
├── ISO_14229-1_UDS_Service_0x19_ReadDTC.md
└── ISO_14229-1_UDS_Service_0x22_ReadData.md  (NEW)
```

### Scenario 3: Shift Solenoid Actuation

**User**: "Actuate shift solenoid 1"

**Agent**:
1. Checks `knowledge_base/` → No TCM.ACTUATE_SOLENOID procedure
2. Checks `reference/ISO_14229-1_UDS_INDEX.md` → Need Service 0x2F or 0x31
3. Services not documented → Request from user
4. User provides ISO 14229-1 Sections 12.2 and 13.2
5. Agent creates both service documentation files
6. Implements using appropriate service
7. Documents successful procedure

## File Naming Conventions

### knowledge_base/
- **Pattern**: `{Make}_{Model}_{Year}_{Type}.{ext}`
- **Examples**:
  - `Ford_Escape_2008_technical.dat`
  - `Ford_Escape_2008_profile.yaml`
  - `Ford_Escape_2008_canbus.kcd`

### reference/
- **UDS Services**: `ISO_14229-1_UDS_Service_0x[HEX]_[Name].md`
- **UDS Annexes**: `ISO_14229-1_Annex_[Letter]_[Name].md`
- **CAN Databases**: `{manufacturer}_{model}.kcd`

## Key Principles

1. **Separation of Concerns**
   - `knowledge_base/` = What works on YOUR vehicle
   - `reference/` = How the protocol works in general

2. **Growth Pattern**
   - `knowledge_base/` grows automatically through diagnostics
   - `reference/` grows on-demand when new services needed

3. **Search Hierarchy**
   - Always check `knowledge_base/` first (fastest)
   - Fall back to `reference/` for protocol details
   - Request missing documentation from user

4. **Documentation Flow**
   - User provides ISO standard extracts → `reference/`
   - Agent learns successful procedures → `knowledge_base/`

## Benefits

### For the Agent
- Clear search strategy
- Knows where to find information
- Knows when to request documentation
- Efficient lookup (< 5ms for known procedures)

### For the User
- Organized knowledge base
- Clear distinction between vehicle data and protocols
- Easy to understand what's stored where
- System gets smarter over time

### For Future Development
- Easy to add new vehicles (just add to `knowledge_base/`)
- Easy to add new protocols (just add to `reference/`)
- Clear extension points
- Maintainable structure

## See Also

- `knowledge_base/README.md` - Detailed explanation of vehicle-specific data
- `reference/README.md` - Detailed explanation of protocol documentation
- `.kiro/specs/ai-vehicle-diagnostic-agent/design/architecture.md` - Complete architecture
- `.kiro/specs/ai-vehicle-diagnostic-agent/design/knowledge-format.md` - File formats
