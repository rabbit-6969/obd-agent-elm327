# CAN Database Formats for Vehicle Diagnostics

## Overview

CAN database files describe how to decode raw CAN bus messages into human-readable data. These are essential for understanding manufacturer-specific protocols.

---

## Common Formats

### 1. DBC (CAN Database) Files
**Format:** Text-based  
**Extension:** `.dbc`  
**Used by:** Vector CANdb++, many open-source tools  
**Content:** CAN message definitions, signal mappings, scaling factors

**Example:**
```
BO_ 1234 HVAC_Status: 8 HVAC
 SG_ Temperature : 0|16@1+ (0.1,-40) [-40|215] "C" Vector__XXX
 SG_ FanSpeed : 16|8@1+ (1,0) [0|7] "" Vector__XXX
```

### 2. KCD (Kayak CAN Definition) Files
**Format:** XML-based  
**Extension:** `.kcd`  
**Used by:** Kayak (open-source CAN analyzer)  
**Content:** Similar to DBC but in XML format

**Example:**
```xml
<Message id="0x7A0" name="HVAC_Request">
  <Signal name="Temperature" offset="0" length="16"/>
  <Signal name="FanSpeed" offset="16" length="8"/>
</Message>
```

### 3. ODX (Open Diagnostic Data Exchange) Files
**Format:** XML-based  
**Extension:** `.odx`, `.pdx`  
**Used by:** Professional diagnostic tools, OEMs  
**Content:** Complete diagnostic protocol definitions including UDS services

---

## What We Need for Ford Escape HVAC

### Option 1: DBC/KCD File (Ideal)
A database file that defines:
- HVAC CAN message IDs (0x7A0, 0x7A8)
- Signal definitions (temperature, fan speed, blend door position)
- Scaling factors and units
- DTC definitions

### Option 2: FORScan Logs (Practical)
Capture actual commands and responses:
- UDS service requests (Mode 19, 22, etc.)
- Response formats
- Timing requirements
- Flow control parameters

### Option 3: Reverse Engineering (Manual)
Document through testing:
- Send commands, observe responses
- Build our own database
- Test and validate

---

## Resources to Look For

### Ford-Specific
1. **Ford DBC files** - Search GitHub for "Ford DBC" or "Ford CAN database"
2. **FORScan definitions** - FORScan may have definition files
3. **Ford service manuals** - May contain CAN message definitions
4. **Ford diagnostic specifications** - Technical service bulletins

### Similar Vehicles
Since Ford Escape shares platform with:
- **Mazda Tribute** (same platform)
- **Mercury Mariner** (badge-engineered Escape)
- **Ford Fusion** (similar era, similar systems)

Look for CAN databases for these vehicles too.

### Open Source Projects
- [opendbc](https://github.com/commaai/opendbc) - Community CAN databases
- [cantools](https://github.com/eerimoq/cantools) - Python CAN database tools
- [Kayak](https://github.com/dschanoeh/Kayak) - CAN analyzer with KCD support

---

## The Mazda Example

The file you found (`skyactiv.kcd`) is a KCD file for Mazda Skyactiv vehicles. While it's a different manufacturer, it shows:

1. **Format structure** - How CAN messages are defined
2. **Signal mapping** - How to decode multi-byte values
3. **Documentation approach** - How to organize vehicle CAN data

**Key takeaway:** If we can find a similar file for Ford Escape, we'd have a complete map of the HVAC CAN protocol!

---

## Next Steps

### Immediate (Tomorrow)
1. ✅ Capture FORScan logs when reading HVAC
2. ✅ Document exact commands and responses
3. ✅ Build initial protocol understanding

### Short Term
1. Search for Ford Escape DBC/KCD files
2. Check FORScan installation for definition files
3. Look for Ford diagnostic specifications

### Long Term
1. Create our own Ford Escape CAN database
2. Implement UDS protocol in our agent
3. Add HVAC support with proper signal decoding

---

## Tools for Working with CAN Databases

### Python Libraries
```python
# cantools - Parse DBC/KCD files
import cantools
db = cantools.database.load_file('ford_escape.dbc')
message = db.get_message_by_name('HVAC_Status')
data = message.decode(raw_bytes)

# python-can - CAN bus communication
import can
bus = can.interface.Bus(channel='COM3', bustype='elm327')
```

### Analysis Tools
- **Kayak** - Open-source CAN analyzer (supports KCD)
- **CANdb++** - Professional tool (supports DBC)
- **SavvyCAN** - Open-source CAN reverse engineering tool
- **Wireshark** - Can decode CAN with proper plugins

---

## What to Look for in FORScan Logs

When you capture tomorrow, look for:

### 1. Initialization Sequence
```
AT Z          (reset)
AT SP 6       (set protocol)
AT SH 7A0     (set header to HVAC)
AT FC SH 7A8  (set flow control)
```

### 2. UDS Service Requests
```
19 02 AF      (Read DTCs by status)
22 F1 90      (Read data by identifier)
31 01 XX YY   (Routine control)
```

### 3. Response Patterns
```
59 02 AF ...  (Positive response to 19 02 AF)
62 F1 90 ...  (Positive response to 22 F1 90)
7F 19 78      (Negative response - request correctly received, response pending)
```

### 4. Multi-Frame Messages
```
10 14 62 F1 90 ...  (First frame)
21 XX XX XX XX ...  (Consecutive frame 1)
22 XX XX XX XX ...  (Consecutive frame 2)
```

---

## References

- [CSS Electronics - CAN DBC File Intro](https://www.csselectronics.com/pages/can-dbc-file-database-intro)
- [CSS Electronics - UDS Protocol Tutorial](https://www.csselectronics.com/pages/uds-protocol-tutorial-unified-diagnostic-services)
- [Wikipedia - Unified Diagnostic Services](https://en.wikipedia.org/wiki/Unified_Diagnostic_Services)
- [Kayak CAN Analyzer](https://github.com/dschanoeh/Kayak)
- [cantools Python Library](https://github.com/eerimoq/cantools)

---

## Summary

The Mazda KCD file you found is a great example of how CAN protocols can be documented. For Ford Escape HVAC, we need similar information. Tomorrow's FORScan log capture will give us the raw protocol data, which we can then organize into a similar database format for our agent to use.

**Goal:** Build a Ford Escape CAN database (DBC or KCD format) that documents the HVAC protocol, making it easy for our agent to communicate with the HVAC module.
