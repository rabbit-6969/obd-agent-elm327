# Ford Escape Module Scanner Guide

## Overview

The `scan_ford_modules.py` script is optimized for slower ELM327 adapters. Instead of brute-forcing all 65,536 possible DIDs, it focuses on known useful ranges.

## Why This Approach?

**Problem with brute-force scanning:**
- 65,536 DIDs × 0.15 seconds = ~2.7 hours minimum
- Your ELM327 adapter is slower than native CAN interfaces
- Most DIDs don't exist anyway

**Solution - Module-focused scanning:**
- Scan only known Ford DID ranges
- Focus on practical diagnostic data
- Complete in 15-20 minutes instead of hours

## Scan Modes

### Mode 1: Quick Scan (2 minutes)
Tests only the 4 confirmed working transmission DIDs:
- `0x221E1C` - ATF Temperature
- `0x221E10` - ATF Temperature (alt)
- `0x221E14` - Turbine Speed
- `0x221E16` - Output Shaft Speed

**Use when:** You want to verify communication is working

### Mode 2: Module Scan (15-20 minutes)
Scans focused DID ranges for each module:

**PCM_Basic** (~32 DIDs):
- `0x0000-0x000F` - VIN and basic info
- `0x0080-0x008F` - Calibration IDs

**PCM_Engine** (~49 DIDs):
- `0x1000-0x1020` - Engine RPM, load, timing
- `0x1100-0x1110` - Fuel system
- `0x1200-0x1210` - Sensors (MAF, MAP, IAT)

**PCM_Transmission** (~50 DIDs):
- `0x2000-0x2020` - Transmission status
- `0x2100-0x2110` - Speed sensors
- `0x221E-0x221F` - Known transmission DIDs

**PCM_Engineering** (~49 DIDs):
- `0xF000-0xF020` - Diagnostic counters
- `0xF100-0xF110` - Engineering data

**Total:** ~180 DIDs in 15-20 minutes

**Use when:** You want comprehensive discovery of available parameters

### Mode 3: Custom Range
Scan any DID range you specify.

**Use when:** You want to explore a specific range based on findings

## Usage

### Step 1: Prepare Vehicle
```
1. Turn ignition to ON (engine can be off or running)
2. Set adapter switch to HS-CAN position
3. Connect adapter to OBD2 port
4. Verify adapter is on COM4 (or adjust in script)
```

### Step 2: Run Scanner
```bash
python scan_ford_modules.py
```

### Step 3: Select Mode
```
Select mode (1/2/3): 2
```

### Step 4: Wait for Completion
The scanner will:
- Show progress every 16 DIDs
- Display found DIDs in real-time
- Indicate security-locked DIDs
- Save results to JSON file

## Understanding Results

### Available DID
```
✓ 0x221E1C: 3F
```
- DID exists and returned data
- `3F` is the hex data (ATF temperature in this case)
- Can be read anytime without security

### Security Locked DID
```
🔒 0x2045: Security locked
```
- DID exists but requires SecurityAccess (0x27)
- Likely contains solenoid states or pressure data
- Need FORScan or security algorithm to access

### Not Supported
```
(no output)
```
- DID doesn't exist
- PCM returned "request out of range"
- Not shown to reduce clutter

## Output Files

### JSON Results File
`ford_escape_module_scan_YYYYMMDD_HHMMSS.json`

Structure:
```json
{
  "vehicle": {
    "make": "Ford",
    "model": "Escape",
    "year": 2008
  },
  "modules": {
    "PCM_Transmission": [
      {
        "did": "0x221E1C",
        "data": "3F",
        "length": 1,
        "status": "available"
      },
      {
        "did": "0x2045",
        "status": "security_locked"
      }
    ]
  }
}
```

## Next Steps After Scanning

### 1. Analyze Results
- Review JSON file
- Identify interesting DIDs
- Note security-locked DIDs

### 2. Test DIDs in Different States
Run scanner with vehicle in different conditions:
- Engine off vs running
- Different gears (P, R, N, D)
- Different speeds
- Different temperatures

Compare results to understand what each DID represents.

### 3. Document Findings
Add discovered DIDs to:
- `knowledge_base/Ford_Escape_2008_profile.yaml`
- `knowledge_base/Ford_Escape_UDS_Commands.yaml`

### 4. Create Monitoring Script
Use discovered DIDs to create real-time monitoring:
```python
# Read transmission temperature
did = 0x221E1C
response = read_did(did)
temp_c = int(response, 16) - 40  # Example conversion
print(f"ATF Temp: {temp_c}°C")
```

### 5. Consider FORScan for Locked DIDs
If you need solenoid states or line pressure:
- FORScan has security algorithms
- ~$25 for extended license
- Works with your adapter
- Provides full access to locked DIDs

## Troubleshooting

### No Response from PCM
```
✗ Connection failed: No response
```
**Solutions:**
- Verify adapter switch is on HS-CAN
- Check ignition is ON
- Try different COM port
- Restart adapter

### Slow Scanning
```
Rate: 2.5 DID/s
```
**Normal for ELM327:**
- ELM327 is slower than native CAN
- 2-5 DIDs/second is expected
- Module scan takes 15-20 minutes
- This is why we don't brute-force all 65k DIDs

### Many "Security Locked" DIDs
```
🔒 0x2045: Security locked
🔒 0x2046: Security locked
```
**This is normal:**
- Ford locks sensitive parameters
- Solenoid states require security
- Line pressure requires security
- Use FORScan for full access

## Comparison: Module Scan vs Brute Force

| Aspect | Module Scan | Brute Force |
|--------|-------------|-------------|
| DIDs scanned | ~180 | 65,536 |
| Time required | 15-20 min | 2.7+ hours |
| Coverage | Known useful ranges | Everything |
| Practical | ✓ Yes | ✗ Too slow |
| Recommended | ✓ Yes | ✗ No |

## Advanced: Expanding Scan Ranges

If you want to scan additional ranges, edit the script:

```python
modules = {
    'PCM_Transmission': [
        (0x2000, 0x2020, "Transmission status"),
        (0x2100, 0x2110, "Speed sensors"),
        (0x221E, 0x221F, "Known transmission DIDs"),
        # Add your custom range:
        (0x2200, 0x2210, "My custom range"),
    ],
}
```

## Tips for Efficient Discovery

1. **Start with Quick Scan** - Verify communication works
2. **Run Module Scan** - Get comprehensive baseline
3. **Test in Different States** - Understand parameter meanings
4. **Focus on Interesting Ranges** - Use Custom mode for deep dives
5. **Document Everything** - Add findings to knowledge base

## Safety Notes

- Read-only operations are safe
- Never write to unknown DIDs
- Keep vehicle stationary during scanning
- Maintain adequate battery voltage
- Don't scan while driving

## References

- `knowledge_base/Ford_Escape_2008_PCM_Architecture.md` - Technical details
- `FORD_ESCAPE_COMPLETE_DID_GUIDE.md` - Complete guide
- `brute_force_did_scanner.py` - Full brute-force version (for reference)
