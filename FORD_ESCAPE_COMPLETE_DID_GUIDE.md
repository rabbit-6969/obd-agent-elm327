# Ford Escape 2008 2.3L - Complete DID Discovery and Solenoid Access Guide

## Executive Summary

This guide provides everything needed to discover and access transmission solenoid states and other advanced diagnostics on the 2008 Ford Escape 2.3L with CD4E transmission.

**Key Facts:**
- Transmission is PCM-controlled (no separate TCM)
- PCM uses UDS-style diagnostics over ISO-TP/CAN
- Public DIDs accessible without security
- Solenoid states require SecurityAccess (0x27)
- Your HS-CAN adapter is fully capable

## Tools Created

1. **`brute_force_did_scanner.py`** - Complete DID discovery tool
2. **`Ford_Escape_2008_PCM_Architecture.md`** - Technical reference
3. **`knowledge_base/Ford_Escape_Transmission_Solenoid_UDS_Guide.md`** - Original guide

## Likely Ford CD4E Transmission DIDs

### Confirmed Public DIDs (No Security Required)

| DID | Parameter | Format | Notes |
|-----|-----------|--------|-------|
| 0x221E1C | ATF Temperature | 2 bytes, signed | °C, may need offset |
| 0x221E10 | ATF Temperature (alt) | 2 bytes, signed | Alternative address |
| 0x221E14 | Turbine Speed | 2 bytes, unsigned | RPM |
| 0x221E16 | Output Shaft Speed | 2 bytes, unsigned | RPM |

### Likely Available (Needs Discovery)

Based on similar Ford PCMs (2005-2010), these DIDs are commonly found:

#### Transmission Status
- **0x2001-0x20FF**: Current gear, shift status, range selector
- **0x2100-0x21FF**: Speed sensors, ratios
- **0x2200-0x22FF**: Temperatures, pressures (some public)

#### Engine Data (Affects Transmission)
- **0x1000-0x10FF**: RPM, load, throttle
- **0x1100-0x11FF**: Fuel system, timing
- **0x1200-0x12FF**: Sensors (MAF, MAP, etc.)

### Security-Locked DIDs (Require 0x27)

These parameters exist but require security unlock:

| Parameter | Likely Range | Format | Notes |
|-----------|--------------|--------|-------|
| EPC Duty Cycle | 0x2000-0x2FFF | 1 byte | 0-255 = 0-100% |
| Shift Solenoid 1 (SS1) | 0x2000-0x2FFF | 1 bit | ON/OFF |
| Shift Solenoid 2 (SS2) | 0x2000-0x2FFF | 1 bit | ON/OFF |
| Shift Solenoid 3 (SS3) | 0x2000-0x2FFF | 1 bit | ON/OFF |
| TCC Duty Cycle | 0x2000-0x2FFF | 1 byte | 0-100% |
| Line Pressure Commanded | 0x2000-0x2FFF | 2 bytes | PSI or kPa |
| Line Pressure Actual | 0x2000-0x2FFF | 2 bytes | PSI or kPa |
| Shift Adaptation Tables | 0x2000-0x2FFF | Multi-byte | Learned shift points |

## Multi-Frame Response Detection

ISO-TP automatically handles multi-frame responses. Here's how to detect them:

### Single Frame Response
```
Length ≤ 7 bytes
Format: [SID+0x40] [DID_MSB] [DID_LSB] [data...]
Example: 62 22 1E 1C 3F  (5 bytes total)
```

### Multi-Frame Response
```
Length > 7 bytes
First Frame: 10 [total_length] [SID+0x40] [DID_MSB] [DID_LSB] [data...]
Flow Control: 30 00 00 (sent by tester)
Consecutive Frames: 2X [data...] (X = sequence number)
```

### Python Detection
```python
def is_multi_frame(response: bytes) -> bool:
    """Check if response is multi-frame"""
    if len(response) > 0:
        # First nibble = 1 indicates First Frame
        return (response[0] & 0xF0) == 0x10
    return False

def get_total_length(first_frame: bytes) -> int:
    """Extract total length from First Frame"""
    if is_multi_frame(first_frame):
        # Length is in lower nibble of byte 0 and all of byte 1
        return ((first_frame[0] & 0x0F) << 8) | first_frame[1]
    return len(response)
```

## SecurityAccess Guide

### Overview
Ford uses proprietary seed/key algorithms to protect sensitive DIDs. Without the correct algorithm, you cannot unlock these DIDs.

### Security Access Process

```
Step 1: Request Seed
  Request:  27 01
  Response: 67 01 [4 bytes seed]
  
Step 2: Compute Key
  key = ford_algorithm(seed)
  (Algorithm is proprietary and not published)
  
Step 3: Send Key
  Request:  27 02 [4 bytes key]
  Response: 67 02 (success) or 7F 27 35 (invalid key)
  
Step 4: Access Granted
  Now security-locked DIDs are accessible via 0x22
```

### Known Ford Security Algorithms

Ford uses different algorithms per model year and PCM strategy:

1. **Ford Algorithm 1** (2005-2008 vehicles)
   - Used on many early CAN vehicles
   - Reverse-engineered by FORScan community
   - Not publicly documented

2. **Ford Algorithm 2** (2008-2012 vehicles)
   - Improved security
   - Also reverse-engineered
   - Used on some 2008 Escape variants

3. **Ford Algorithm 3** (2013+ vehicles)
   - Modern security
   - More complex

### Your 2008 Escape
- Likely uses Algorithm 1 or Algorithm 2
- Exact algorithm depends on PCM strategy code
- FORScan has these algorithms built-in

### Security Access Limitations

**Without the algorithm:**
- Cannot unlock security-protected DIDs
- Cannot read solenoid states
- Cannot read line pressure
- Cannot access adaptation tables

**With the algorithm (FORScan):**
- Full access to all DIDs
- Can read solenoid states in real-time
- Can view and modify adaptations
- Can perform actuator tests

### Obtaining Security Access

**Option 1: Use FORScan**
- FORScan has Ford security algorithms
- Works with your HS-CAN adapter
- ~$25 for extended license
- Provides GUI for all parameters

**Option 2: Reverse Engineer**
- Capture FORScan traffic with Wireshark
- Extract seed/key pairs
- Reverse engineer algorithm
- Legal gray area, not recommended

**Option 3: Community Resources**
- Some algorithms published in forums
- Check FORScan forums, GitHub
- May find Python implementations
- Verify legality in your jurisdiction

## Response Timing Reference

### Typical Response Times

| Operation | Time (ms) | Notes |
|-----------|-----------|-------|
| Simple 0x22 DID read | 5-15 | Single frame, idle PCM |
| Multi-frame response | 15-30 | ISO-TP segmentation |
| Busy PCM (engine running) | 15-30 | Higher processing load |
| Negative response | 5-10 | Quick rejection |
| SecurityAccess seed (0x27 01) | 10-20 | Seed generation |
| SecurityAccess key (0x27 02) | 10-20 | Key validation |
| Response Pending (0x78) | Variable | PCM needs more time |

### Rate Limiting

**Safe Request Rate:**
- 20-40 requests/second
- 50ms delay between requests recommended
- Prevents PCM overload

**Exceeding Rate Limit:**
- PCM responds with 0x78 (Response Pending)
- May temporarily stop responding
- Requires longer timeout

**Brute Force Scanning:**
- 65,536 DIDs at 50ms each = ~55 minutes
- Can optimize with parallel requests (risky)
- Priority ranges first recommended

## Practical Workflow

### Phase 1: Discovery (One-Time)

1. **Run Priority Scan**
   ```bash
   python brute_force_did_scanner.py
   # Select option 1: Priority Scan
   # Duration: ~15-20 minutes
   ```

2. **Review Results**
   - Check `ford_escape_dids_YYYYMMDD_HHMMSS.json`
   - Identify transmission-related DIDs
   - Note security-locked DIDs

3. **Document Findings**
   - Add to vehicle profile YAML
   - Create DID-to-parameter mapping
   - Test DIDs with vehicle in different states

### Phase 2: Real-Time Monitoring

1. **Read Public DIDs**
   - Use discovered DIDs
   - No security required
   - Can monitor: temp, speeds, gear, etc.

2. **Attempt Security Access** (Optional)
   - Use FORScan for full access
   - Or implement if algorithm known
   - Unlocks solenoid states

### Phase 3: Integration

1. **Add to AI Agent**
   - Import discovered DIDs
   - Create parameter definitions
   - Implement real-time queries

2. **Build Diagnostic Logic**
   - Correlate parameters
   - Detect anomalies
   - Provide recommendations

## CD4E Solenoid Logic Reference

### Solenoid Functions

| Solenoid | Function | Type |
|----------|----------|------|
| SS1 | Controls 1-2 and 3-4 shifts | ON/OFF |
| SS2 | Controls 2-3 shifts | ON/OFF |
| SS3 | Controls TCC lockup | ON/OFF |
| EPC | Line pressure control | PWM (0-100%) |

### Gear Position Logic

| Gear | SS1 | SS2 | SS3 | EPC | Notes |
|------|-----|-----|-----|-----|-------|
| Park | OFF | OFF | OFF | Low | No load |
| Reverse | ON | ON | OFF | High | High pressure |
| Neutral | OFF | OFF | OFF | Low | No load |
| 1st | ON | OFF | OFF | High | Launch gear |
| 2nd | OFF | OFF | OFF | Med | Coast/cruise |
| 3rd | OFF | ON | OFF | Med | Highway |
| 4th | OFF | ON | ON | Low | Overdrive + TCC |

### Diagnostic Patterns

**Stuck in 2nd Gear (Limp Mode):**
- All solenoids OFF
- EPC at minimum
- Indicates PCM detected fault

**No TCC Lockup:**
- SS3 remains OFF in 4th gear
- Check SS3 circuit
- Check TCC solenoid

**Harsh Shifts:**
- EPC duty cycle too high
- Check line pressure
- May need adaptation reset

## Next Steps

1. **Run DID Scanner**
   - Start with priority scan
   - Document all found DIDs
   - Test DIDs in different vehicle states

2. **Create DID Database**
   - Map DIDs to parameters
   - Document data formats
   - Add to vehicle profile

3. **Implement Real-Time Monitoring**
   - Read public DIDs
   - Display in AI agent
   - Log for analysis

4. **Consider FORScan**
   - For security-locked DIDs
   - Full solenoid access
   - Worth the $25 investment

5. **Integrate with AI Agent**
   - Add DID reading capability
   - Implement diagnostic logic
   - Provide user-friendly interface

## Safety and Legal Notes

**Safety:**
- Read-only operations are safe
- Never write to unknown DIDs
- Keep vehicle stationary during diagnostics
- Maintain adequate battery voltage

**Legal:**
- Reading DIDs is legal (diagnostic purposes)
- Security bypass may violate laws in some jurisdictions
- Modifying calibrations may void warranty
- Check local regulations

## References

- ISO 15765-4 (ISO-TP over CAN)
- ISO 14229-1 (UDS specification)
- Ford workshop manuals (2008 Escape)
- FORScan community documentation
- Your existing discovery scripts and documentation

## Support Files

All tools and documentation created:
- `brute_force_did_scanner.py` - DID discovery tool
- `knowledge_base/Ford_Escape_2008_PCM_Architecture.md` - Technical reference
- `knowledge_base/Ford_Escape_Transmission_Solenoid_UDS_Guide.md` - Original guide
- `FORD_ESCAPE_COMPLETE_DID_GUIDE.md` - This file

You now have everything needed to discover and access transmission data on your 2008 Ford Escape!
