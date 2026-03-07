# Reference Documentation

This directory contains **universal protocol documentation and standards** that apply across all vehicles.

## Purpose

Store static reference material for:
- ISO 14229-1 UDS (Unified Diagnostic Services) specifications
- OBD-II protocol documentation
- CAN bus protocol standards
- Example implementations from other vehicles
- Industry standards and specifications

## Distinction from `knowledge_base/`

**`reference/`** (this directory):
- Universal protocol documentation
- Static reference material (rarely modified)
- Industry standards (ISO, SAE, etc.)
- Applies to all vehicles
- Protocol-level details

**`knowledge_base/`** (sibling directory):
- Vehicle-specific operational data
- Modified by agent during diagnostics
- Grows through learning
- User's proprietary knowledge
- Application-level data

## Contents

### ISO 14229-1 UDS Documentation

**Purpose**: Complete specification for Unified Diagnostic Services protocol

**Index**: `ISO_14229-1_UDS_INDEX.md` - Master index of available services

**Service Extracts**:
- `ISO_14229-1_UDS_Service_0x10_SessionControl.md` - Diagnostic session control
- `ISO_14229-1_UDS_Service_0x14_ClearDTC.md` - Clear diagnostic information
- `ISO_14229-1_UDS_Service_0x19_ReadDTC.md` - Read DTC information ✅
- `ISO_14229-1_UDS_Service_0x22_ReadData.md` - Read data by identifier
- `ISO_14229-1_UDS_Service_0x2E_WriteData.md` - Write data by identifier
- `ISO_14229-1_UDS_Service_0x2F_IOControl.md` - Input/output control
- `ISO_14229-1_UDS_Service_0x31_RoutineControl.md` - Routine control

**Annexes**:
- `ISO_14229-1_Annex_A_NegativeResponses.md` - Error codes
- `ISO_14229-1_Annex_D_DTCDefinitions.md` - DTC format and status
- `ISO_14229-1_Annex_E_IOControlParameters.md` - I/O control parameters
- `ISO_14229-1_Annex_F_RoutineIdentifiers.md` - Routine IDs

### CAN Bus Documentation

**Purpose**: Reference implementations and reverse-engineered CAN data

**Files**:
- `mazda_skyactiv.kcd` - Example CAN database structure (KCD format)
- `Mazda_CAN_Bus_Reference.md` - Reverse-engineered Mazda CAN message structures (Ford CD2 platform)
- `Valasek_Miller_Automotive_Networks_2014.md` - Seminal automotive security research
- `generic_obd2.kcd` - Standard OBD-II PIDs

**Mazda CAN Bus Reference**:
- HS-CAN (500 kbps) message structures for Ford Escape 2008 / Mazda Tribute
- MS-CAN (125 kbps) message structures for Ford Escape 2008 / Mazda Tribute
- Confirmed parameters: RPM, speed, wheel speeds, steering angle, transmission gear, etc.
- Scaling factors and byte layouts
- Source: Community reverse engineering efforts

**Valasek & Miller Research (2014)**:
- Comprehensive automotive security research by IOActive
- Detailed analysis of 2010 Ford Escape and Toyota Prius
- ISO 14229 (UDS) service documentation
- SecurityAccess implementation analysis
- ECU mapping and CAN ID documentation (Appendices A & B)
- Firmware extraction and analysis techniques
- **Use for**: Understanding protocols, ECU architecture, diagnostic procedures
- **Do NOT use for**: Unauthorized modifications, security bypass, malicious activities

**Usage**: 
- Study structure and signal definitions for implementing new vehicles
- Passive CAN monitoring for data logging
- Custom dashboard integration
- Performance analysis
- Understanding automotive security for defensive purposes

## Structure

```
reference/
├── README.md                                    # This file
├── ISO_14229-1_UDS_INDEX.md                    # Master index
├── ISO_14229-1_UDS_Service_0x[XX]_[Name].md    # Service specifications
├── ISO_14229-1_Annex_[X]_[Name].md             # Annexes
└── *.kcd                                        # Example CAN databases
```

## Agent Usage

### When Agent Needs Protocol Information

1. **Check index**: Read `ISO_14229-1_UDS_INDEX.md`
2. **Find service**: Locate required service (e.g., 0x22 for reading data)
3. **Check availability**: 
   - ✅ If documented: Read the extract
   - 🔲 If not documented: Request from user
4. **Implement**: Use protocol spec to construct commands
5. **Document**: Save successful procedure to `knowledge_base/`

### Request Template

When agent needs missing documentation:

```
To implement [feature], I need ISO 14229-1 documentation:

Service 0x[XX]: [ServiceName]
Section: [section number]
Pages: [page range]

Please paste the content from that section.
```

### Example Flow

```
User: "Read transmission fluid temperature"

Agent:
1. Check knowledge_base/Ford_Escape_2008_technical.dat
   → Not found: No TCM.READ_TEMP procedure

2. Check reference/ISO_14229-1_UDS_INDEX.md
   → Need: Service 0x22 (ReadDataByIdentifier)
   → Status: 🔲 Not documented

3. Request from user:
   "To read transmission temperature, I need ISO 14229-1:
    Service 0x22: ReadDataByIdentifier
    Section: 10.2 (pages 106-112)
    
    Please paste that section."

4. User provides documentation

5. Create: reference/ISO_14229-1_UDS_Service_0x22_ReadData.md

6. Implement command using spec

7. Document in knowledge_base/ for next time
```

## Growth Pattern

**Initial State**:
```
reference/
├── README.md
├── ISO_14229-1_UDS_INDEX.md
└── ISO_14229-1_UDS_Service_0x19_ReadDTC.md  (Service 0x19 only)
```

**After Transmission Diagnostics**:
```
reference/
├── README.md
├── ISO_14229-1_UDS_INDEX.md
├── ISO_14229-1_UDS_Service_0x19_ReadDTC.md
├── ISO_14229-1_UDS_Service_0x22_ReadData.md  (NEW: requested)
└── ISO_14229-1_UDS_Service_0x10_SessionControl.md  (NEW: needed for extended mode)
```

**After Multiple Features**:
```
reference/
├── README.md
├── ISO_14229-1_UDS_INDEX.md
├── ISO_14229-1_UDS_Service_0x10_SessionControl.md
├── ISO_14229-1_UDS_Service_0x14_ClearDTC.md
├── ISO_14229-1_UDS_Service_0x19_ReadDTC.md
├── ISO_14229-1_UDS_Service_0x22_ReadData.md
├── ISO_14229-1_UDS_Service_0x2F_IOControl.md
├── ISO_14229-1_UDS_Service_0x31_RoutineControl.md
├── ISO_14229-1_Annex_A_NegativeResponses.md
└── mazda_skyactiv.kcd
```

## File Naming Convention

### UDS Service Extracts
**Pattern**: `ISO_14229-1_UDS_Service_0x[HEX]_[ShortName].md`

**Examples**:
- `ISO_14229-1_UDS_Service_0x19_ReadDTC.md`
- `ISO_14229-1_UDS_Service_0x22_ReadData.md`
- `ISO_14229-1_UDS_Service_0x2F_IOControl.md`

### UDS Annexes
**Pattern**: `ISO_14229-1_Annex_[Letter]_[Name].md`

**Examples**:
- `ISO_14229-1_Annex_A_NegativeResponses.md`
- `ISO_14229-1_Annex_D_DTCDefinitions.md`
- `ISO_14229-1_Annex_E_IOControlParameters.md`

### CAN Databases
**Pattern**: `{manufacturer}_{model}.kcd` or `{purpose}.kcd`

**Examples**:
- `mazda_skyactiv.kcd`
- `generic_obd2.kcd`
- `ford_can_hs.kcd`

## Document Format

### Service Extract Template

```markdown
# ISO 14229-1 UDS Protocol - Service 0x[XX] [ServiceName]

**Source:** ISO 14229-1:2013(E) - Unified Diagnostic Services (UDS)  
**Extracted:** [Date]  
**Purpose:** [Brief description of use case]

---

## Overview

[Service description]

## Request Message Format

[Table with byte-by-byte breakdown]

## Positive Response Format

[Table with response structure]

## Negative Response Codes

[List of possible error codes]

## Implementation Example

[Python code example]

## Usage Notes

[Ford-specific notes, common issues, etc.]
```

## Maintenance

### Adding New Documentation

1. User provides ISO 14229-1 section
2. Create new file following naming convention
3. Format using template above
4. Update `ISO_14229-1_UDS_INDEX.md` to mark as ✅
5. Add usage notes specific to Ford vehicles

### Updating Existing Documentation

- Add Ford-specific notes to "Usage Notes" section
- Include examples from actual diagnostic sessions
- Document any quirks or deviations from standard

## See Also

- `knowledge_base/` - Vehicle-specific operational data
- `.kiro/specs/ai-vehicle-diagnostic-agent/design/knowledge-format.md` - Format specifications
- `.kiro/specs/ai-vehicle-diagnostic-agent/design/architecture.md` - Knowledge organization details
