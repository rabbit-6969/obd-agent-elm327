# Vehicle Capability Discovery - Complete Guide

**Date:** 2026-02-15  
**Vehicle:** 2008 Ford Escape  
**Purpose:** Discover ALL accessible DIDs, routines, and actuations across ALL modules

---

## Overview

This document describes the comprehensive vehicle capability discovery process using the `discover_vehicle_capabilities.py` scanner. This tool systematically discovers:

1. **Modules**: All accessible ECUs on the CAN bus
2. **DIDs**: All readable Data Identifiers (Service 0x22) for each module
3. **Routines**: All executable test routines (Service 0x31) for each module
4. **Actuations**: All controllable outputs (Service 0x2F) for each module

---

## Quick Start

### Basic Usage

```bash
# Quick scan (common ranges, ~30 minutes)
python discover_vehicle_capabilities.py --quick

# Full scan (all 65,536 DIDs per module, several hours)
python discover_vehicle_capabilities.py --full

# Resume interrupted scan
python discover_vehicle_capabilities.py --resume
```

### Targeted Scans

```bash
# Scan for modules only
python discover_vehicle_capabilities.py --modules

# Scan DIDs only (requires module scan first)
python discover_vehicle_capabilities.py --dids

# Scan routines only
python discover_vehicle_capabilities.py --routines

# Scan actuations (CAUTION: may affect vehicle)
python discover_vehicle_capabilities.py --actuations
```

---

## Scan Modes

### Quick Scan (Recommended)

Scans common DID and routine ranges:

**DID Ranges:**
- `0x0100-0x01FF`: Transmission parameters
- `0x1000-0x10FF`: Common Ford diagnostic range
- `0xF000-0xF0FF`: Manufacturer-specific
- `0xF100-0xF1FF`: Vehicle identification
- `0xF400-0xF4FF`: Vehicle manufacturer specific

**Routine Ranges:**
- `0x0200-0x02FF`: Transmission routines
- `0x0300-0x03FF`: Engine routines
- `0xFF00-0xFFFF`: Manufacturer-specific routines

**Estimated Time:** 30-60 minutes

### Full Scan

Scans the complete DID and routine space:

**DID Range:** `0x0000-0xFFFF` (65,536 DIDs)  
**Routine Range:** `0x0000-0xFFFF` (65,536 routines)

**Estimated Time:** 2-4 hours per module

---

## What Gets Discovered

### 1. Module Discovery

The scanner tests known Ford module addresses:

| Module | Address | Description |
|--------|---------|-------------|
| PCM | 0x7E0 | Powertrain Control Module |
| TCM | 0x7E1 | Transmission Control (may be integrated with PCM) |
| ABS | 0x760 | Anti-lock Braking System |
| HVAC | 0x7A0 | Climate Control |
| BCM | 0x726 | Body Control Module |
| IPC | 0x720 | Instrument Panel Cluster |
| RCM | 0x737 | Restraint Control Module (Airbags) |
| PAM | 0x736 | Parking Aid Module |
| PSCM | 0x730 | Power Steering Control Module |

**Test Commands:**
- `19 02 AF`: Read DTCs (UDS Service 0x19)
- `22 F190`: Read VIN (UDS Service 0x22)
- `10 01`: Default session (UDS Service 0x10)

### 2. DID Discovery (Service 0x22)

For each accessible module, the scanner tests DIDs using:

```
Command: 22 [DID_high] [DID_low]
Positive Response: 62 [DID_high] [DID_low] [data...]
Negative Response: 7F 22 [NRC]
```

**What's Recorded:**
- DID number (e.g., 0x0100)
- Command sent (e.g., "220100")
- Response received (e.g., "62 01 00 0C")
- Range description (e.g., "Transmission parameters")
- Discovery timestamp

### 3. Routine Discovery (Service 0x31)

For each module, the scanner tests routine IDs using:

```
Command: 31 03 [RID_high] [RID_low]  (requestRoutineResults - safe, doesn't start routine)
Positive Response: 71 03 [RID_high] [RID_low] [results...]
Negative Response: 7F 31 [NRC]
```

**Important NRCs:**
- `0x31` (ROOR): Routine doesn't exist
- `0x24` (RSE): Routine exists but wrong sequence (needs to be started first)
- `0x22` (CNC): Routine exists but conditions not met

**What's Recorded:**
- Routine ID (e.g., 0x0201)
- Command sent
- Response received
- NRC code (if applicable)
- Notes about routine availability

### 4. Actuation Discovery (Service 0x2F)

For each discovered DID, the scanner tests if it supports actuation:

```
Command: 2F [DID_high] [DID_low] 00  (returnControlToECU - safe, doesn't activate)
Positive Response: 6F [DID_high] [DID_low] 00
Negative Response: 7F 2F [NRC]
```

**Important NRCs:**
- `0x31` (ROOR): Actuation not supported
- `0x22` (CNC): Actuation supported but conditions not met
- `0x33` (SAD): Actuation supported but needs security access

**What's Recorded:**
- DID number
- Whether actuation is supported
- Required conditions (if any)
- Security requirements (if any)

---

## Output Files

### Progress File

**Location:** `vehicle_discovery/scan_progress.json`

Contains:
- Current scan progress
- Modules found so far
- DIDs/routines/actuations discovered
- Statistics
- Last saved timestamp

**Use:** Resume interrupted scans with `--resume`

### Results File

**Location:** `vehicle_discovery/vehicle_capabilities_YYYYMMDD_HHMMSS.json`

Complete JSON database containing:
- Vehicle information
- Scan metadata
- All discovered modules
- All discovered DIDs (by module)
- All discovered routines (by module)
- All discovered actuations (by module)
- Statistics

### Summary File

**Location:** `vehicle_discovery/summary_YYYYMMDD_HHMMSS.txt`

Human-readable summary with:
- Scan statistics
- Module list
- DID counts by module
- Routine counts by module
- Actuation counts by module

---

## Safety Considerations

### Safe Operations

The scanner uses safe commands by default:

- **DID scanning**: Read-only (Service 0x22)
- **Routine scanning**: Uses `requestRoutineResults` (doesn't start routines)
- **Actuation scanning**: Uses `returnControlToECU` (doesn't activate outputs)

### Cautions

⚠️ **Vehicle Conditions:**
- Ensure vehicle is in PARK
- Parking brake engaged
- Engine can be running or off (running provides more data)
- Do not drive vehicle during scan

⚠️ **Actuation Scan:**
- Requires explicit confirmation
- Tests if DIDs support actuation (doesn't actually actuate)
- Still safe, but be aware it's testing control capabilities

⚠️ **Time Requirements:**
- Quick scan: 30-60 minutes
- Full scan: 2-4 hours per module
- Plan accordingly (vehicle must remain on)

---

## Interpreting Results

### Example DID Discovery

```json
{
  "0x0100": {
    "did": 256,
    "command": "220100",
    "response": "62 01 00 0C",
    "range": "Transmission parameters",
    "discovered_at": "2026-02-15T14:30:00"
  }
}
```

**Interpretation:**
- DID 0x0100 is accessible
- Response: `62 01 00 0C`
  - `62` = Positive response (0x22 + 0x40)
  - `01 00` = DID echo
  - `0C` = Data value (12 decimal)
- This is transmission fluid temperature
- Formula: `(0x0C - 40) = -28°C` (engine cold)

### Example Routine Discovery

```json
{
  "0x0201": {
    "rid": 513,
    "command": "31030201",
    "response": "7F 31 24",
    "nrc": "24",
    "note": "Routine exists but cannot be queried (may need to start first)",
    "discovered_at": "2026-02-15T15:00:00"
  }
}
```

**Interpretation:**
- Routine 0x0201 exists
- NRC 0x24 (RSE) = requestSequenceError
- This means the routine exists but needs to be started first
- To use: Send `31 01 0201` (startRoutine) then `31 03 0201` (requestResults)

### Example Actuation Discovery

```json
{
  "0x0103": {
    "did": 259,
    "command": "2F010300",
    "response": "7F 2F 22",
    "nrc": "22",
    "note": "Supports actuation but requires conditions/security",
    "discovered_at": "2026-02-15T15:30:00"
  }
}
```

**Interpretation:**
- DID 0x0103 supports actuation
- NRC 0x22 (CNC) = conditionsNotCorrect
- This means actuation is supported but vehicle conditions aren't met
- Possible requirements: engine running, transmission in park, etc.

---

## Next Steps After Discovery

### 1. Analyze Results

Review the JSON and summary files to understand:
- Which modules are accessible
- What parameters can be read
- What tests can be run
- What outputs can be controlled

### 2. Update Knowledge Base

Add discovered DIDs to:
- `knowledge_base/Ford_Escape_2008_technical.dat`
- `knowledge_base/Ford_Escape_2008_profile.yaml`

### 3. Create Monitoring Tools

For discovered DIDs:
- Create live data monitoring scripts
- Parse data values with correct formulas
- Display in user-friendly format

### 4. Document Routines

For discovered routines:
- Document what each routine does
- Document required conditions
- Create safe test procedures

### 5. Test Actuations

For discovered actuations:
- Document what each actuation controls
- Test in safe conditions
- Document required parameters

---

## Troubleshooting

### No Modules Found

**Symptoms:** Scanner reports 0 modules found

**Possible Causes:**
- Vehicle ignition not ON
- ELM327 adapter not connected
- Wrong COM port
- Adapter not initialized properly

**Solutions:**
- Turn ignition to ON position
- Check adapter connection
- Verify COM port in script (default: COM3)
- Try resetting adapter (unplug/replug)

### Scan Very Slow

**Symptoms:** Scan taking much longer than expected

**Possible Causes:**
- Using full scan mode
- Module not responding (timeouts)
- Adapter timeout too long

**Solutions:**
- Use quick scan mode instead
- Skip non-responsive modules
- Reduce timeout in script (ATST command)

### Scan Interrupted

**Symptoms:** Scan stopped before completion

**Solutions:**
- Use `--resume` flag to continue
- Progress is saved every 100 DIDs
- Check `vehicle_discovery/scan_progress.json`

---

## References

- `reference/ISO_14229-1_UDS_Service_0x22_ReadDataByIdentifier.md`
- `reference/ISO_14229-1_UDS_Service_0x31_RoutineControl.md`
- `reference/ISO_14229-1_UDS_Service_0x2F_InputOutputControlByIdentifier.md`
- `TRANSMISSION_DATA_DISCOVERY.md`
- `scan_transmission_dids.py` (original DID scanner)

---

## Success Metrics

After running the scanner, you should have:

- ✅ Complete list of accessible modules
- ✅ All readable DIDs for each module
- ✅ All available routines for each module
- ✅ All actuatable DIDs for each module
- ✅ JSON database for programmatic access
- ✅ Human-readable summary
- ✅ Foundation for building diagnostic tools

---

**Status:** Ready to use  
**Last Updated:** 2026-02-15
