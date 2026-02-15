# HVAC System Data Report
## 2008 Ford Escape - Live Vehicle Data

**Date**: February 14, 2026  
**Vehicle**: 2008 Ford Escape  
**Adapter**: ELM327 v1.5 on COM3  
**Voltage**: 11.7V

---

## Temperature Readings

### Engine Coolant Temperature (PID 0105)
- **Raw Response**: `41 05 36`
- **Hex Value**: 0x36 = 54 decimal
- **Calculation**: 54 - 40 = **14°C (57°F)**
- **Status**: ✓ Normal (engine cold/warming up)

### Intake Air Temperature (PID 010F)
- **Raw Response**: `41 0F 41`
- **Hex Value**: 0x41 = 65 decimal
- **Calculation**: 65 - 40 = **25°C (77°F)**
- **Status**: ✓ Normal room temperature

### Ambient Air Temperature (PID 0146)
- **Raw Response**: `41 46 36`
- **Hex Value**: 0x36 = 54 decimal
- **Calculation**: 54 - 40 = **14°C (57°F)**
- **Status**: ✓ Matches coolant temp (vehicle has been sitting)

---

## Electrical System

### Control Module Voltage (PID 0142)
- **Raw Response**: `41 42 2E B5`
- **Hex Value**: 0x2EB5 = 11,957 decimal
- **Calculation**: 11,957 / 1000 = **11.96V**
- **Status**: ⚠ Slightly low (normal is 12.6V+ when off, 13.5-14.5V when running)
- **Note**: Battery may need charging or vehicle is not running

---

## Supported PIDs Analysis

### PIDs 01-20 (Response: 41 00 BE 3F B8 13)
Binary: `10111110 00111111 10111000 00010011`

**Supported PIDs:**
- 01: Monitor status
- 03: Fuel system status
- 04: Calculated engine load
- 05: Engine coolant temperature ✓
- 06: Short term fuel trim
- 07: Long term fuel trim
- 0C: Engine RPM
- 0D: Vehicle speed
- 0E: Timing advance
- 0F: Intake air temperature ✓
- 10: MAF air flow rate
- 11: Throttle position
- 13: Oxygen sensors present
- 14: Oxygen sensor 1
- 15: Oxygen sensor 2
- 1C: OBD standards
- 1D: Oxygen sensors present (alternate)

### PIDs 21-40 (Response: 41 20 C0 17 E0 11)
Binary: `11000000 00010111 11100000 00010001`

**Supported PIDs:**
- 21: Distance traveled with MIL on
- 22: Fuel rail pressure
- 24: Oxygen sensor 1 (wide range)
- 26: Oxygen sensor 2 (wide range)
- 27: Oxygen sensor 3 (wide range)
- 2C: Commanded EGR
- 2D: EGR error
- 2E: Commanded evaporative purge
- 2F: Fuel tank level input
- 33: Absolute barometric pressure

### PIDs 41-60 (Response: 41 40 FC 00 00 00)
Binary: `11111100 00000000 00000000 00000000`

**Supported PIDs:**
- 41: Monitor status this drive cycle
- 42: Control module voltage ✓
- 43: Absolute load value
- 44: Fuel/air commanded equivalence ratio
- 45: Relative throttle position
- 46: Ambient air temperature ✓

---

## Mode 22 Response (Read Data by ID)

### Command: 2201
- **Response**: `62 01 00 0C`
- **Analysis**: 
  - 0x62 = Positive response to Mode 22
  - Data ID: 0x01
  - Data: 0x00 0x0C (12 decimal)
- **Interpretation**: Successfully read data identifier 0x01
- **Note**: Mode 22 is working! This is a manufacturer-specific data read

---

## Failed/Unsupported Commands

### Mode 19 (UDS Diagnostic Services)
All Mode 19 commands returned: `7F 19 11`
- **7F**: Negative Response
- **19**: Service ID (Mode 19)
- **11**: Service Not Supported (NRC)

**Tested Mode 19 Sub-functions:**
- 1901: Report DTC count - ✗ Not supported
- 1902FF: Report DTC by status mask - ✗ Not supported
- 190A: Report supported DTCs - ✗ Not supported

### Mode 21 (Manufacturer-Specific)
All Mode 21 commands returned: `7F 21 11`
- Service not supported on this vehicle

### PID 015C (Engine Oil Temperature)
- No response (not supported on this vehicle)

---

## HVAC-Specific Findings

### What We Can Read:
1. **Ambient Temperature**: 14°C (57°F) - Used by HVAC for auto climate control
2. **Coolant Temperature**: 14°C (57°F) - Used by HVAC for heater operation
3. **Intake Air Temperature**: 25°C (77°F) - Indirect HVAC reference
4. **Control Module Voltage**: 11.96V - HVAC module power supply

### What We Cannot Read:
1. **HVAC-Specific DTCs**: Mode 19 not supported
2. **Blend Door Position**: No direct PID available
3. **HVAC Mode Settings**: No standard OBD-II access
4. **Fan Speed**: No standard OBD-II access
5. **AC Compressor Status**: Would need Mode 01 PID for AC request

### Mode 22 Success:
- **Mode 22 (Read Data by ID) works!**
- This is a manufacturer-specific command
- Could potentially access HVAC data with correct data identifiers
- Need Ford-specific data ID documentation

---

## Recommendations

### For HVAC Diagnostics:
1. **Use Mode 22**: Successfully responds - need Ford data IDs
2. **Research Ford Data IDs**: Find HVAC-specific identifiers for Mode 22
3. **Check AC Compressor**: Use PID 0100 bit analysis for AC request status
4. **Monitor Temperatures**: Current temperature PIDs work well

### For Agent Implementation:
1. **Implement Mode 22 Support**: Add to toolkit scripts
2. **Create Ford Data ID Library**: Document known HVAC data identifiers
3. **Temperature Monitoring**: Already working via standard PIDs
4. **Voltage Monitoring**: Working - can detect HVAC electrical issues

---

## Summary

**Working Standard OBD-II:**
- ✓ Temperature sensors (coolant, intake, ambient)
- ✓ Voltage monitoring
- ✓ Supported PID detection
- ✓ Mode 22 (manufacturer-specific data read)

**Not Working:**
- ✗ Mode 19 (UDS diagnostic services)
- ✗ Mode 21 (manufacturer-specific)
- ✗ Direct HVAC module communication

**Key Discovery:**
Mode 22 works! This is the path forward for HVAC diagnostics. Need to research Ford-specific data identifiers for HVAC parameters.

---

## Next Steps

1. Research Ford Mode 22 data identifiers for HVAC
2. Implement Mode 22 support in toolkit
3. Test various data IDs to find HVAC parameters
4. Document successful data IDs in knowledge base
5. Create HVAC-specific diagnostic procedures using Mode 22

**Status**: Data collection complete ✓  
**HVAC Access Method**: Mode 22 (manufacturer-specific) ✓  
**Standard OBD-II**: Fully functional ✓
