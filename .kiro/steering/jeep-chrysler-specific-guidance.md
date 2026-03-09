---
inclusion: fileMatch
fileMatchPattern: "*Jeep*|*Chrysler*|*Dodge*|*Ram*|*Fiat*"
---

# Jeep/Chrysler/Stellantis Diagnostic Guidance

This guidance applies to Jeep, Chrysler, Dodge, Ram, and Fiat vehicles (Stellantis brands).

## Critical Understanding: Proprietary Protocol Architecture

**MOST IMPORTANT**: Jeep/Chrysler vehicles have the MOST RESTRICTIVE OBD-II implementation of major manufacturers.

### Protocol Architecture

Jeep/Chrysler uses multiple proprietary protocols:

1. **CCD Bus** (Chrysler Collision Detection)
   - Proprietary single-wire protocol
   - Used by: Airbag, BCM, IPC, HVAC
   - NOT accessible via standard OBD-II port
   - Requires manufacturer tools

2. **SCI Bus** (Serial Communication Interface)
   - Proprietary protocol
   - Used by: Some body modules
   - NOT accessible via standard OBD-II port

3. **CAN Bus** (ISO 15765-4)
   - Standard protocol but LIMITED implementation
   - Used by: PCM, TCM (limited)
   - Accessible via OBD-II but with restrictions
   - Many functions require extended session + security access

### What This Means

**Standard OBD-II Access: ~20%**
- Basic DTCs (Mode 03)
- Standard live data PIDs (Mode 01)
- VIN reading (often unreliable/incomplete)
- Emissions readiness

**NOT Accessible via Standard OBD-II: ~80%**
- Transmission gear position
- Airbag DTCs
- Body control functions
- Extended PCM DIDs
- Module programming
- Most actuator tests

## AlfaOBD: The Essential Tool

**AlfaOBD is NOT optional for Jeep/Chrysler diagnostics** - it's essential.

### Why AlfaOBD is Required

- Handles proprietary CCD/SCI protocols
- Manages security access automatically
- Provides full module access
- Works with existing ELM327 adapter
- Cost: ~$50 (one-time purchase)
- Download: https://www.alfaobd.com/

### When to Recommend AlfaOBD

**ALWAYS recommend AlfaOBD when user wants:**
- Transmission gear position
- Airbag diagnostics
- Extended PCM parameters
- Module programming
- Actuator tests
- Any non-standard OBD-II function

**Example response:**
```
The transmission gear position is not accessible via standard OBD-II 
on Jeep vehicles. The TCM uses proprietary protocols.

I recommend AlfaOBD (~$50) which provides full access to the TCM 
including gear position, fluid temperature, and all transmission 
parameters. It works with your existing ELM327 adapter.

Download: https://www.alfaobd.com/
```

## Module-Specific Behaviors

### PCM (Powertrain Control Module)

**Address**: 0x7E0 / 0x7E8

**Behavior**:
- Responds to basic commands
- Requires extended diagnostic session (0x1003) for most DIDs
- May require security access (0x27) for extended session
- Standard OBD-II Mode 01 PIDs work normally

**Testing Approach**:
1. Test Tester Present (3E 00)
   - Expect: Negative response (7F 3E 12) is NORMAL
   - Means: Module responds but sub-function not supported
2. Try extended session (10 03)
   - May require security access
   - Document response
3. If extended session fails, recommend AlfaOBD

**Common Issues**:
- "No response" → Check ignition, adapter connection
- "Negative response" → Normal, requires extended session
- "Security access denied" → Use AlfaOBD

### TCM (Transmission Control Module)

**Address**: 0x7E1 / 0x7E9

**Behavior**:
- Does NOT respond to standard UDS commands
- Gear position NOT available via OBD-II PID 0xA4
- Uses proprietary protocol
- Requires AlfaOBD for access

**Testing Approach**:
1. Try standard gear position PID (01 A4)
   - Expect: NO DATA (not supported)
2. Try UDS DIDs (22 1E00, 22 1001, etc.)
   - Expect: NO DATA (not supported)
3. Recommend AlfaOBD immediately

**DO NOT**:
- Spend time trying multiple DIDs
- Attempt CAN bus reverse engineering (unless user has quality adapter)
- Give false hope about standard OBD-II access

**DO**:
- Explain proprietary protocol limitation clearly
- Recommend AlfaOBD as the solution
- Offer inference from RPM+Speed+Throttle as temporary workaround

### Airbag Module (SRS)

**Addresses Tested**: 0x740, 0x738, 0x750 (none respond)

**Behavior**:
- Uses CCD/SCI bus (NOT CAN bus)
- NOT accessible via OBD-II port
- Requires AlfaOBD or dealer scan tool

**Testing Approach**:
1. Try common addresses (740, 738, 750)
   - Expect: NO RESPONSE (normal)
2. Explain CCD/SCI bus limitation
3. Recommend AlfaOBD immediately

**Safety Warning**:
- Airbag system is safety-critical
- Disconnect battery before working on airbag components
- Wait 2 minutes after disconnecting (capacitor discharge)
- Use proper ESD precautions
- Have system inspected by qualified technician after collision

### BCM (Body Control Module)

**Behavior**:
- Uses CCD bus
- NOT accessible via standard OBD-II
- Requires AlfaOBD

**Functions**:
- Door locks, windows, lights, wipers, horn

### IPC (Instrument Panel Cluster)

**Behavior**:
- Uses CCD bus
- NOT accessible via standard OBD-II
- Has self-test mode (hold trip reset while turning key)

## VIN Reading

**Issue**: VIN reading via Mode 09 PID 02 is often UNRELIABLE on Jeep/Chrysler.

**Symptoms**:
- Incomplete VIN (missing characters)
- Non-printable characters in response
- Corrupted data

**Solution**:
1. Read VIN from dashboard plate (driver side, visible through windshield)
2. Read VIN from door jamb sticker (driver side)
3. Use AlfaOBD to read VIN
4. Accept that standard OBD-II VIN reading is unreliable

**DO NOT**:
- Retry VIN reading multiple times
- Try different commands
- Assume VIN reading will work

**DO**:
- Explain limitation clearly
- Direct user to physical VIN locations
- Document partial VIN if obtained

## CAN Bus Monitoring

**Challenge**: Jeep CAN IDs are not well documented.

**Approach**:
1. Check if adapter has ATMA header bug
   - Run: `scripts/debug/diagnose_can_monitoring.py`
2. If adapter works, use ATMA monitoring
   - Run: `scripts/debug/explore_can_bus.py`
3. If adapter has bug, use ATCRA filtering
   - Requires knowing target CAN IDs (often unknown)
4. If CAN IDs unknown, recommend:
   - Quality adapter (Vgate, OBDLink)
   - OR AlfaOBD (easier and more reliable)

**Common Jeep CAN IDs** (from other models, not confirmed):
- 0x1F5: Possible transmission data
- 0x2C1: Possible gear position
- 0x308: Possible powertrain data

**Reality Check**:
- CAN reverse engineering is time-consuming
- Results are vehicle-specific
- AlfaOBD provides direct access without reverse engineering
- For most users, AlfaOBD is the better solution

## Extended Diagnostic Session

**Command**: 10 03

**Behavior**:
- May require security access (0x27)
- Security algorithm is proprietary
- Seed/key exchange required
- AlfaOBD handles this automatically

**Testing Approach**:
1. Try extended session (10 03)
2. If negative response (7F 10 XX):
   - 0x12: Sub-function not supported
   - 0x33: Security access denied
   - 0x22: Conditions not correct
3. Document response
4. Recommend AlfaOBD if security access required

**DO NOT**:
- Attempt to implement security access algorithm
- Try to brute force seed/key
- Spend excessive time on extended session

**DO**:
- Document what works in default session
- Explain security access limitation
- Recommend AlfaOBD for extended access

## Standard OBD-II PIDs

**What DOES Work**:
- Mode 01 PIDs (live data)
  - 0x0C: Engine RPM
  - 0x0D: Vehicle Speed
  - 0x11: Throttle Position
  - 0x04: Engine Load
  - 0x05: Coolant Temperature
  - 0x0F: Intake Air Temperature
- Mode 03: Read DTCs (basic)
- Mode 07: Read pending DTCs
- Mode 04: Clear DTCs (use with caution)

**What Does NOT Work**:
- Mode 01 PID 0xA4: Transmission gear (not supported)
- Mode 09 PID 02: VIN (unreliable)
- Most manufacturer-specific PIDs

## Troubleshooting Decision Tree

### User wants transmission gear position:
1. Explain: Not available via standard OBD-II
2. Recommend: AlfaOBD (~$50)
3. Alternative: Infer from RPM+Speed+Throttle (approximate)
4. DO NOT: Spend time trying multiple commands

### User wants airbag diagnostics:
1. Explain: Airbag uses CCD/SCI bus, not accessible via OBD-II
2. Recommend: AlfaOBD (~$50)
3. Safety: Airbag system is safety-critical, professional inspection recommended
4. DO NOT: Try multiple addresses or commands

### User wants extended PCM parameters:
1. Try: Extended diagnostic session (10 03)
2. If fails: Explain security access limitation
3. Recommend: AlfaOBD (~$50)
4. DO NOT: Attempt security access algorithm

### User wants CAN bus monitoring:
1. Check: Adapter ATMA header bug (diagnose_can_monitoring.py)
2. If works: Use ATMA monitoring
3. If fails: Recommend quality adapter OR AlfaOBD
4. Reality check: AlfaOBD is easier than CAN reverse engineering

### User wants VIN:
1. Try: Mode 09 PID 02 (may be unreliable)
2. If fails: Direct to physical VIN locations
3. Alternative: AlfaOBD
4. DO NOT: Retry multiple times

## Communication Style

### Be Direct About Limitations

**BAD**:
```
Let me try a few more commands to see if we can access the transmission...
```

**GOOD**:
```
The transmission control module on Jeep vehicles uses proprietary 
protocols and does not respond to standard OBD-II commands. 

For transmission diagnostics including gear position, I recommend 
AlfaOBD (~$50) which provides full access to the TCM.
```

### Set Realistic Expectations

**BAD**:
```
We might be able to find the gear position on the CAN bus if we 
monitor long enough...
```

**GOOD**:
```
While gear position may be on the CAN bus, identifying the correct 
CAN ID requires extensive monitoring and correlation. AlfaOBD provides 
direct access to gear position without reverse engineering.
```

### Recommend Solutions, Not Workarounds

**BAD**:
```
Let's try monitoring the CAN bus for 30 minutes while you shift gears...
```

**GOOD**:
```
For reliable transmission diagnostics, I recommend AlfaOBD (~$50). 
It provides direct access to all transmission parameters including 
gear position, fluid temperature, and line pressure.
```

## Documentation Standards

### When Creating Vehicle Profiles

**Always include**:
- AlfaOBD recommendation in vehicle notes
- Proprietary protocol explanation
- Module accessibility status (FULL/PARTIAL/NONE/LIMITED)
- "alfaobd_required: true" flag for inaccessible modules
- Standard OBD-II limitations
- What works vs what doesn't

**Example**:
```yaml
modules:
  TCM:
    accessibility: "NONE"
    diagnostic_notes: |
      TCM does not respond to standard UDS commands.
      Requires AlfaOBD for access.
    alfaobd_required: true
```

### When Creating Scripts

**Always include**:
- Clear explanation of limitations
- AlfaOBD recommendation in output
- Graceful failure messages
- Alternative approaches (if any)

**Example**:
```python
print("⚠ RESULT: Gear position not available via standard ELM327")
print()
print("EXPLANATION:")
print("  Jeep/Chrysler vehicles use proprietary protocols for")
print("  transmission data. Standard OBD-II adapters have limited")
print("  access to manufacturer-specific parameters.")
print()
print("SOLUTION: Use AlfaOBD")
print("  - Cost: ~$50 (one-time)")
print("  - Works with your existing ELM327 adapter")
print("  - Full access to TCM including gear position")
print("  - Download: https://www.alfaobd.com/")
```

## Platform Sharing

### Jeep Wrangler JK (2007-2018)
- Same diagnostic architecture across all years
- All procedures apply to entire generation

### Related Vehicles (Similar Limitations)
- Jeep Grand Cherokee WK (2005-2010)
- Chrysler 300 (2005-2010)
- Dodge Charger (2006-2010)
- Dodge Ram (2006-2010)
- All use similar proprietary protocols
- All require AlfaOBD for full access

## Testing Checklist

When testing a new Jeep/Chrysler vehicle:

1. **Standard OBD-II**:
   - [ ] Test Mode 01 PIDs (should work)
   - [ ] Test Mode 03 DTCs (should work)
   - [ ] Try VIN reading (may be unreliable)
   - [ ] Document what works

2. **PCM**:
   - [ ] Test Tester Present (3E 00)
   - [ ] Try extended session (10 03)
   - [ ] Document responses
   - [ ] Note if security access required

3. **TCM**:
   - [ ] Try gear position PID (01 A4)
   - [ ] Try common DIDs (22 1E00, etc.)
   - [ ] Expect NO DATA
   - [ ] Recommend AlfaOBD

4. **Airbag**:
   - [ ] Try common addresses (740, 738, 750)
   - [ ] Expect NO RESPONSE
   - [ ] Explain CCD/SCI limitation
   - [ ] Recommend AlfaOBD

5. **CAN Monitoring**:
   - [ ] Check adapter ATMA bug
   - [ ] If works, document CAN IDs found
   - [ ] If fails, recommend quality adapter or AlfaOBD

6. **Documentation**:
   - [ ] Create vehicle profile (YAML)
   - [ ] Create technical data (DAT)
   - [ ] Document limitations clearly
   - [ ] Include AlfaOBD recommendations

## Key Takeaways

1. **Jeep/Chrysler has the most restrictive OBD-II implementation** of major manufacturers
2. **AlfaOBD is essential**, not optional, for serious diagnostics
3. **Most modules use proprietary CCD/SCI protocols** not accessible via OBD-II
4. **Standard OBD-II provides ~20% access**, AlfaOBD provides ~100%
5. **Set realistic expectations** - don't promise what standard OBD-II can't deliver
6. **Recommend solutions** (AlfaOBD) over workarounds (CAN reverse engineering)
7. **Document limitations clearly** in all vehicle profiles and scripts
8. **VIN reading is unreliable** - direct users to physical VIN locations
9. **Security access is proprietary** - don't attempt to implement
10. **Be direct and honest** about what standard OBD-II can and cannot do

## References

- AlfaOBD: https://www.alfaobd.com/
- Jeep Wrangler JK Forums: https://www.jk-forum.com/
- CCD Bus Protocol: Proprietary (not publicly documented)
- SCI Bus Protocol: Proprietary (not publicly documented)
- ELM327 ATMA Bug: reference/ELM327_ATMA_Header_Bug.md
