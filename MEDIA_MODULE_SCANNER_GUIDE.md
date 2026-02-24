# Ford Escape 2008 - Media Module Scanner Guide

## Overview

The ACM (Audio Control Module) is located on the MS-CAN bus, not HS-CAN. This requires:
1. Flipping your adapter switch to MS-CAN position
2. Using different protocol settings
3. Using different CAN addresses

## Quick Start

```bash
python scan_media_module.py
```

**CRITICAL:** Set adapter switch to MS-CAN position before running!

## Scan Modes

### 1. Quick Scan (2-3 minutes)
Tests 10 common module identification DIDs:
- VIN
- Part numbers
- Software versions
- Manufacturing date
- Serial numbers

**Use this first** to verify ACM communication.

### 2. Full Scan (30-40 minutes)
Scans all typical media module DID ranges:
- 0xF100-0xF1FF: Module identification
- 0x3000-0x30FF: Audio settings
- 0x3100-0x31FF: Radio tuner data
- 0x3200-0x32FF: Media player status
- 0x4000-0x40FF: Infotainment data
- 0xD000-0xD0FF: Diagnostic data

### 3. Custom Range
Specify your own start/end DIDs.

## Important Notes

### MS-CAN vs HS-CAN

| Feature | HS-CAN | MS-CAN |
|---------|--------|--------|
| Speed | 500 kbps | 125 kbps |
| Modules | PCM, ABS, IC | HVAC, ACM, BCM |
| Switch Position | Position 1 | Position 2 |
| OBD-II Pins | 6 & 14 | 3 & 11 |

### ACM Addressing

The scanner uses typical Ford ACM addresses:
- Request: 0x726
- Response: 0x72E

If these don't work, the ACM may use alternate addresses:
- 0x7A6 / 0x7AE
- 0x736 / 0x73E

### Protocol Differences

MS-CAN modules may:
- Respond slower (need longer timeouts)
- Require different initialization
- Use different security levels
- Have different DID ranges than PCM

## Expected Results

### If ACM Responds
You should see:
- Module identification DIDs (0xF1xx)
- Part number: 8L8T-19C107-AM (from FORScan)
- Software version and date
- Possibly audio settings and status

### If No Response
Possible causes:
1. Switch not in MS-CAN position
2. ACM uses different address
3. ACM requires security unlock
4. Protocol settings incorrect
5. MS-CAN not accessible with this adapter

## Troubleshooting

### "NO_RESPONSE" for all DIDs
- Verify switch is in MS-CAN position
- Check adapter supports MS-CAN (yours does - works with FORScan)
- Try alternate ACM addresses

### "SECURITY_LOCKED" responses
- ACM is responding but DIDs are protected
- May need security unlock sequence
- Some DIDs may be read-only in FORScan

### "CAN ERROR"
- Wrong protocol selected
- Baud rate mismatch
- Switch in wrong position

## Comparison with FORScan

FORScan can access ACM because it:
1. Knows exact ACM address for your vehicle
2. Has proprietary Ford protocol knowledge
3. Can perform security unlock if needed
4. Has database of ACM DIDs

Our scanner attempts to:
1. Use standard UDS protocol
2. Try typical Ford addresses
3. Scan common DID ranges

## Next Steps

### If Quick Scan Works
1. Run full scan to discover all available DIDs
2. Document findings in knowledge base
3. Decode discovered data

### If Quick Scan Fails
1. Capture FORScan ACM communication
2. Analyze protocol differences
3. Adjust scanner settings

### Future Enhancements
- Try alternate ACM addresses
- Implement security unlock
- Add DID decoding
- Create real-time ACM monitor

## Related Files

- `scan_ford_modules.py` - PCM scanner (HS-CAN)
- `FORD_CAN_BUS_ARCHITECTURE.md` - CAN bus details
- `FORSCAN_MODULE_DISCOVERY.md` - ACM info from FORScan
- `knowledge_base/Ford_Escape_UDS_Commands.yaml` - DID database

## Technical Details

### Common Media Module DIDs

**Module Identification (0xF1xx):**
- 0xF187: Spare Part Number
- 0xF188: ECU Software Number
- 0xF18C: ECU Serial Number
- 0xF190: VIN
- 0xF191: ECU Hardware Number
- 0xF192: Supplier ID
- 0xF193: Manufacturing Date
- 0xF194: System Supplier ID
- 0xF195: Software Version
- 0xF19E: ASAM/ODX File ID

**Audio Settings (0x30xx):**
- Volume levels
- Balance/fade
- Equalizer settings
- Audio source selection

**Radio Tuner (0x31xx):**
- Current frequency
- Signal strength
- RDS data
- Preset stations

**Media Player (0x32xx):**
- Track info
- Playback status
- Source (CD/USB/AUX)

## Safety Notes

- Read-only operations (UDS 0x22 service)
- No write commands
- No actuator tests
- Safe to run on running vehicle
- Will not affect audio operation

## Output

Results saved to JSON file:
```
ford_escape_acm_scan_YYYYMMDD_HHMMSS.json
```

Contains:
- Vehicle info
- Module details
- Discovered DIDs with data
- Scan timestamp

## Example Output

```
Ford Escape 2008 - Media Module (ACM) Scanner
======================================================================

⚠ CRITICAL: Set adapter switch to MS-CAN position!

Connecting to COM3...
Initializing ELM327 for MS-CAN...
✓ Connected and configured for MS-CAN
  Request address: 0x726
  Response address: 0x72E

Testing ACM communication...
✓ ACM responding!

======================================================================
QUICK SCAN - Common Media Module DIDs
======================================================================

  ✓ 0xF190 (VIN): 31464D4355303358363842313239363
  ✓ 0xF187 (Spare Part Number): 384C38542D3139433130372D414D
  ✓ 0xF188 (ECU Software Number): 384C38542D3134443039392D4148
  ...

SCAN SUMMARY
======================================================================

Total Available DIDs: 8
Total Security Locked: 2
Total Discovered: 10

✓ Results saved to: ford_escape_acm_scan_20260221_143022.json
✓ Disconnected
```

## Limitations

- May not access all DIDs (some require security)
- Protocol may differ from FORScan
- Address may need adjustment
- MS-CAN access depends on adapter capability

## Success Criteria

Scan is successful if:
- ACM responds to communication test
- At least module ID DIDs are readable
- Part number matches FORScan (8L8T-19C107-AM)

Even partial success provides valuable information about ACM accessibility.
