
# FORScan Command Capture Guide

## Method 1: Use FORScan's Built-in Logging

1. **Enable FORScan Logging:**
   - Open FORScan
   - Go to Settings/Options
   - Enable "Detailed Logging" or "Debug Mode"
   - Set log level to maximum

2. **Perform HVAC Diagnostics:**
   - Connect to vehicle
   - Navigate to HVAC module (usually 7A0)
   - Read DTCs
   - Read live data
   - Perform any tests

3. **Find Log Files:**
   - Check FORScan installation directory
   - Look in: `C:\Program Files (x86)\FORScan\Logs\`
   - Or: `C:\Users\[username]\AppData\Local\FORScan\Logs\`
   - Files named like: `FORScan_log_YYYYMMDD.txt`

4. **Extract Commands:**
   - Open log file
   - Look for lines with "7A0" (HVAC address)
   - Copy all commands and responses
   - Save to: `logs/forscan_hvac_commands.txt`

## Method 2: Use COM Port Monitor Tool

1. **Install COM Port Monitor:**
   - Free option: Portmon (Microsoft)
   - Paid option: Device Monitoring Studio
   - Alternative: Serial Port Monitor

2. **Setup Monitoring:**
   - Start monitor tool
   - Select COM3
   - Start capture
   - Open FORScan
   - Perform HVAC diagnostics
   - Stop capture

3. **Save Capture:**
   - Export to text file
   - Save as: `logs/com3_forscan_capture.txt`

## Method 3: Manual Command Recording

1. **In FORScan:**
   - Note each command sent
   - Note each response received
   - Take screenshots if needed

2. **Record Format:**
   ```
   Command: [hex bytes]
   Response: [hex bytes]
   Description: [what it does]
   ```

3. **Focus on:**
   - Module initialization
   - DTC read commands
   - Live data requests
   - Any HVAC-specific commands

## What to Look For

### Key Commands:
- **Module Init:** Usually starts with AT commands
- **Set Header:** AT SH 7A0 (or similar)
- **Set Protocol:** AT SP [number]
- **DTC Read:** Mode 19 or proprietary
- **Live Data:** Mode 22 or proprietary
- **Clear DTCs:** Mode 14 or proprietary

### Example FORScan HVAC Session:
```
> AT Z          (reset)
< ELM327 v1.5

> AT SP 6       (set protocol ISO 15765-4 CAN)
< OK

> AT SH 7A0     (set header to HVAC)
< OK

> 19 02 AF      (read DTCs - UDS Mode 19)
< 59 02 AF ...  (response with DTCs)

> 22 F1 90      (read VIN - UDS Mode 22)
< 62 F1 90 ...  (response with VIN)
```

## After Capture

1. **Organize Data:**
   - Separate commands by function
   - Group related sequences
   - Note timing between commands

2. **Analyze Patterns:**
   - Identify command structure
   - Find response patterns
   - Determine checksums/validation

3. **Implement:**
   - Add to `elm327_base.py`
   - Create HVAC-specific functions
   - Test with vehicle

## Files to Create

- `logs/forscan_hvac_commands.txt` - Raw commands
- `logs/forscan_hvac_analysis.md` - Analysis notes
- `knowledge_base/Ford_HVAC_protocol.md` - Protocol documentation
