# Ford Escape 2008 - ABS Module DID Scanner Guide

## Overview

The ABS DID scanner (`scripts/debug/scan_ford_abs_dids.py`) is a comprehensive tool for discovering and reading all available Data Identifiers (DIDs) from the Ford Escape 2008 ABS module.

## What It Scans

### 1. Standard Identification DIDs (ISO 14229-1)

These are standardized UDS DIDs that should be supported by most modules:

- **0xF190**: Vehicle Identification Number (VIN)
- **0xF19D**: ECU Serial Number
- **0xF187**: Vehicle Manufacturer Spare Part Number
- **0xF191**: Vehicle Manufacturer ECU Hardware Number
- **0xF189**: Vehicle Manufacturer ECU Software Version Number
- **0xF18C**: System Supplier ECU Hardware Number
- **0xF18E**: System Supplier ECU Software Number
- **0xF18B**: ECU Manufacturing Date and Time
- **0xF197**: Programming Date
- **0xF198**: Calibration Identification

And many more (see script for complete list).

### 2. Ford-Specific ABS DIDs

These are manufacturer-specific DIDs that may contain:

#### Wheel Speed Sensors (0x0200-0x020F range)
- **0x0200**: Unknown ABS Parameter (confirmed working, returns 4 bytes)
  - Captured value: `00 00 00 00` (vehicle stationary)
  - Likely: Wheel speed data or ABS system status
  - Format: 4 bytes (possibly 4 individual wheel speeds or status flags)
- **0x0201**: Possible Wheel Speed Front Left
- **0x0202**: Unknown ABS Parameter (confirmed working, returns 4 bytes)
  - Captured value: `00 00 00 00` (vehicle stationary)
  - Likely: Related ABS parameter (pressure, valve status, or additional wheel data)
  - Format: 4 bytes
- **0x0203**: Possible Wheel Speed Front Right
- **0x0204**: Possible Wheel Speed Rear Left
- **0x0205**: Possible Wheel Speed Rear Right
- **0x0206**: Possible Wheel Speed Average
- **0x0207**: Possible Vehicle Speed

**Note**: DIDs 0x0200 and 0x0202 confirmed working on 2008 Ford Escape. Values are all zeros when vehicle is stationary. Dynamic testing (rolling vehicle, applying brakes) needed to determine exact meaning.

#### Brake System Parameters (0x0210-0x021F range)
- **0x0210**: Possible Brake Pressure Front Left
- **0x0211**: Possible Brake Pressure Front Right
- **0x0212**: Possible Brake Pressure Rear Left
- **0x0213**: Possible Brake Pressure Rear Right
- **0x0214**: Possible Master Cylinder Pressure
- **0x0215**: Possible Brake Pedal Position

#### ABS System Status (0x0220-0x022F range)
- **0x0220**: Possible ABS System Status
- **0x0221**: Possible Traction Control Status
- **0x0222**: Possible Stability Control Status
- **0x0223**: Possible Pump Motor Status
- **0x0224**: Possible Valve Status

#### Sensor Data (0x0230-0x023F range)
- **0x0230**: Possible Lateral Acceleration
- **0x0231**: Possible Yaw Rate
- **0x0232**: Possible Steering Angle
- **0x0233**: Possible Brake Light Switch

#### Module Information (0x0100-0x010F range)
- **0x0100**: Possible Module ID
- **0x0101**: Possible Hardware Version
- **0x0102**: Possible Software Version
- **0x0103**: Possible Calibration ID
- **0x0104**: Possible Serial Number
- **0x0105**: Possible Manufacturing Date

## Usage

### Basic Scan

```bash
python scripts/debug/scan_ford_abs_dids.py
```

This will scan all standard and Ford-specific DIDs.

### Quick Scan (Known Working DIDs Only)

```bash
python scripts/debug/scan_ford_abs_dids.py --quick
```

### Custom COM Port

```bash
python scripts/debug/scan_ford_abs_dids.py --port COM4
```

## Requirements

- Vehicle: Ford Escape 2008 (or similar Ford vehicles with ABS module at 0x760)
- Adapter: ELM327 compatible OBD-II adapter
- Connection: Vehicle ignition ON, engine OFF
- Python: 3.6+ with `pyserial` library

## Output

### Console Output

The scanner displays:
1. Connection status
2. Communication test results
3. Each DID scanned with:
   - Raw hex data
   - ASCII interpretation (for text data like VIN, part numbers)
   - Decimal interpretation (for numeric data)
4. Summary of findings

### JSON Output

Results are saved to:
```
knowledge_base/captured_data/ford_escape_abs_did_scan_YYYYMMDD_HHMMSS.json
```

The JSON file contains:
```json
{
  "scan_date": "2026-03-05T...",
  "vehicle": "Ford Escape 2008",
  "module": "ABS (0x760)",
  "identification_dids": {
    "F190": {
      "description": "Vehicle Identification Number (VIN)",
      "raw": "31 46 4D 43 55 30 33 5A 36 38 4B 42 31 32 39 36 39",
      "ascii": "1FMCU03Z68KB12969",
      "decimal": null
    }
  },
  "operational_dids": {
    "0200": {
      "description": "Unknown Parameter 1",
      "raw": "00",
      "ascii": null,
      "decimal": 0
    }
  },
  "failed_dids": {
    "F181": {
      "description": "Application Software Identification",
      "status": "NEGATIVE_RESPONSE_31_Request Out Of Range"
    }
  }
}
```

## Expected Results

### What Should Work

Based on previous testing, we know:
- **Tester Present (0x3E 01)**: Works, returns 0x7E
- **DID 0x0200**: Works, returns data
- **DID 0x0202**: Works, returns data

### What May NOT Work

Ford ABS modules typically do NOT support:
- **Service 0x10** (Diagnostic Session Control)
- **Service 0x19** (Read DTC Information)
- **Standard identification DIDs** (0xF180-0xF19F range)

This is NORMAL behavior for Ford ABS modules - they use manufacturer-specific protocols.

## Interpreting Results

### Negative Response Codes (NRC)

When a DID is not supported, you'll see:
- **0x11**: Service Not Supported
- **0x12**: Sub-Function Not Supported
- **0x13**: Incorrect Message Length
- **0x22**: Conditions Not Correct
- **0x31**: Request Out Of Range (most common for unsupported DIDs)
- **0x33**: Security Access Denied
- **0x78**: Response Pending

### Data Types

The scanner attempts to interpret data as:
1. **ASCII**: For text data (VIN, part numbers, serial numbers)
2. **Decimal**: For numeric data (speeds, pressures, counters)
3. **Raw Hex**: Always displayed for manual interpretation

## Next Steps After Scanning

### 1. Identify Wheel Speed DIDs

If DIDs in the 0x0200-0x020F range return data:
- Use `test_wheel_speed_dids.py` to test if they change when vehicle moves
- Roll vehicle slowly and watch for value changes
- Document which DID corresponds to which wheel

### 2. Identify Module Information

If DIDs in the 0x0100-0x010F range return data:
- Document serial number, part number, software version
- Update `knowledge_base/Ford_Escape_2008_profile.yaml` with findings

### 3. Create Live Monitoring Script

Once you identify useful DIDs:
- Create a live monitoring script for wheel speeds
- Create a brake system monitoring script
- Add to toolkit for future diagnostics

### 4. Update Knowledge Base

Document all findings in:
- `knowledge_base/Ford_Escape_2008_profile.yaml` (ABS module section)
- `knowledge_base/Ford_Escape_UDS_Commands.yaml` (DID definitions)
- `.kiro/steering/ford-specific-guidance.md` (diagnostic procedures)

## Troubleshooting

### No Response from Module

1. Verify ignition is ON
2. Check ELM327 connection
3. Try Tester Present first: `AT SH 760` then `3E 01`
4. Verify correct COM port

### All DIDs Return "Request Out Of Range"

This is normal for Ford ABS modules. They don't support standard UDS identification DIDs. Focus on the Ford-specific DIDs (0x0100-0x02FF range).

### Scan Takes Too Long

Use quick scan mode:
```bash
python scripts/debug/scan_ford_abs_dids.py --quick
```

## Safety Notes

- This is a READ-ONLY operation (Service 0x22 - ReadDataByIdentifier)
- No commands are sent that modify module behavior
- No actuator tests are performed
- Safe to run with vehicle stationary, ignition ON

## Related Scripts

- `test_ford_abs_connection.py` - Basic communication test
- `test_wheel_speed_dids.py` - Test if specific DIDs are wheel speeds
- `scan_abs_module.py` - Generic ABS scanner (Toyota/Ford)

## References

- ISO 14229-1: Unified Diagnostic Services (UDS)
- Ford Service Manual: ABS System Diagnostics
- `knowledge_base/Ford_Escape_2008_profile.yaml`: ABS module documentation
- `.kiro/steering/ford-specific-guidance.md`: Ford diagnostic procedures
