# Ford CAN Bus Architecture - 2008 Ford Escape

**Source:** [Ford-Trucks.com Forum Article](https://www.ford-trucks.com/forums/1256374-accessing-advanced-ford-pids-with-a-scan-tool.html)

---

## Overview

Ford vehicles (2004+) use two separate CAN buses:
- **HS-CAN (High Speed):** 500 kbps - Priority/safety systems
- **MS-CAN (Medium Speed):** 125 kbps - Comfort/convenience systems

The two buses are **bridged in the Instrument Panel Cluster (IPC)** to share data between networks.

---

## OBD-II Connector Pinout

| Pin | Function | Speed | Notes |
|-----|----------|-------|-------|
| 6 | CAN High (HS) | 500 kbps | Standard OBD-II |
| 14 | CAN Low (HS) | 500 kbps | Standard OBD-II |
| 3 | CAN High (MS) | 125 kbps | **Ford proprietary** |
| 11 | CAN Low (MS) | 125 kbps | **Ford proprietary** |

**Standard ELM327 adapters only connect to pins 6 & 14 (HS-CAN).**

---

## HS-CAN Modules (Pins 6 & 14)

✅ **Accessible via standard OBD-II:**

- **PCM** (Powertrain Control Module) - Address 7E0
- **ABS** (Anti-lock Brake System) - Address 760
- **RCM** (Restraint Control Module - Airbags)
- **AWD** (All Wheel Drive module, if equipped)
- **OCSM** (Occupant Classification System Module)
- **PAM** (Parking Aid Module)
- **IPC** (Instrument Panel Cluster) - Address 733
- **PSCM** (Power Steering Control Module)
- **SECM** (Steering Effort Control Module)
- **CCM** (Cruise Control Module)
- **APIM** (Accessory Protocol Interface Module - SYNC)

---

## MS-CAN Modules (Pins 3 & 11)

⚠️ **Accessible with modified adapter + correct protocol (not standard OBD-II):**

- **SJB/BCM** (Smart Junction Box/Body Control Module) - Address 726
- **HVAC** (Heating, Ventilation & Air Conditioning) - Address 7A0 ⭐
- **ACM** (Audio Control Module)
- **DSP** (Audio Digital Signal Processing Module)
- **DSM** (Driver Seat Module)
- **DDM** (Driver Door Module)
- **RFA** (Remote Function Actuator Module)
- **DCSM** (Dual Climate Controlled Seat Module)
- **SDARS** (Satellite Digital Audio Radio Service)
- **FCIM** (Front Controls Interface Module)
- **FDIM** (Front Display Interface Module)
- **ILCM** (Interior Lighting Control Module)
- **HCM-2** (High Beam Control Module)
- **SOD-R/L** (Side Obstacle Detection - BLIS)
- **IPC-MS** (Instrument Panel Cluster on MS-CAN)
- **GPSM** (Global Positioning System Module)

---

## Why HVAC Isn't Accessible

### The Problem

1. **HVAC is on MS-CAN** (pins 3 & 11)
2. **Standard ELM327 only connects to HS-CAN** (pins 6 & 14)
3. **The two buses are separate** (only bridged in IPC for specific data)

### Our Test Results Confirm This

| Test | Result | Explanation |
|------|--------|-------------|
| Switch Position 1 (HS-CAN) | PCM accessible, HVAC not | Correct - HVAC is on MS-CAN |
| Switch Position 2 (MS-CAN) | All CAN ERROR | Adapter connected to MS-CAN but using HS-CAN protocols |
| FORScan Works | HVAC accessible | FORScan knows how to switch between buses |

---

## Hardware Modification Required

### What Your ELM327 Switch Does

Your adapter has a **DPDT switch** that physically switches between:
- **Position 1:** Pins 6 & 14 (HS-CAN) → ELM327 chip
- **Position 2:** Pins 3 & 11 (MS-CAN) → ELM327 chip

**This is NOT proprietary hardware** - it's a standard modification that gives you physical access to both CAN buses.

### What You Need

1. ✅ Hardware connection to MS-CAN (you have this with the switch)
2. ✅ Ford-compatible adapter firmware (you have this - it works with FORScan)
3. ⚠️ Knowledge of Ford UDS protocol commands (this is what we need to capture)

---

## Why We Got CAN ERROR on MS-CAN

When you flipped the switch:
1. ✅ Adapter physically connected to MS-CAN (pins 3 & 11)
2. ❌ ELM327 tried to use standard OBD-II protocol
3. ❌ MS-CAN modules don't speak standard OBD-II
4. ❌ Result: CAN ERROR

---

## How FORScan Accesses HVAC

FORScan uses:
1. **Hardware switch** to connect to MS-CAN
2. **Ford-specific protocols** (not standard OBD-II)
3. **UDS (Unified Diagnostic Services)** commands
4. **Module-specific addressing** and timing

### Example FORScan HVAC Session

```
> AT Z              (reset adapter)
< ELM327 v1.5

> AT SP 6           (set protocol ISO 15765-4 CAN)
< OK

> AT SH 7A0         (set header to HVAC address)
< OK

> AT FC SH 7A8      (set flow control response address)
< OK

> 19 02 AF          (UDS Mode 19: Read DTCs by status)
< 59 02 AF ...      (positive response with DTCs)

> 22 F1 90          (UDS Mode 22: Read data by identifier)
< 62 F1 90 ...      (positive response with data)
```

**Key Differences from Standard OBD-II:**
- Uses **UDS Mode 19** instead of OBD-II Mode 03
- Uses **UDS Mode 22** instead of OBD-II Mode 01
- Requires **flow control** setup
- Uses **Ford-specific PIDs**

---

## What We Learned

### ✅ Confirmed
1. HVAC is on MS-CAN (pins 3 & 11)
2. Standard OBD-II only works on HS-CAN (pins 6 & 14)
3. PCM is fully accessible via standard OBD-II
4. Hardware switch alone is not enough
5. Need Ford-specific protocols for MS-CAN modules

### ❌ Cannot Do with Standard OBD-II Protocol
- Access HVAC using Mode 01/03 commands
- Use standard OBD-II on MS-CAN modules
- Auto-detect MS-CAN protocol

### ✅ Can Do with Your Modified Adapter + UDS Protocol
- Access all MS-CAN modules (HVAC, BCM, etc.)
- Read DTCs from HVAC using UDS Mode 19
- Read live data from HVAC using UDS Mode 22
- Perform actuator tests
- **No proprietary hardware needed** - just need the protocol commands!

---

## Recommendations

### For Standard OBD-II Diagnostics
- ✅ Focus on HS-CAN modules (PCM, ABS, etc.)
- ✅ Use standard Mode 01, 03, 07, 09 commands
- ✅ Works with any ELM327 adapter

### For HVAC Diagnostics
- ❌ Cannot use standard OBD-II
- ✅ Use FORScan with modified adapter
- ✅ Capture FORScan commands for reverse engineering
- ⏭️ Future: Implement UDS protocol in our agent

---

## Next Steps

### Immediate
1. ✅ Document CAN bus architecture (this file)
2. ✅ Update knowledge base with findings
3. ✅ Focus agent on HS-CAN modules (PCM, ABS)

### Future (HVAC Support)
1. Capture FORScan command logs
2. Reverse engineer UDS protocol
3. Implement UDS Mode 19 (read DTCs)
4. Implement UDS Mode 22 (read data)
5. Add MS-CAN protocol support
6. Test with HVAC module

---

## References

- [Ford-Trucks.com Forum Article](https://www.ford-trucks.com/forums/1256374-accessing-advanced-ford-pids-with-a-scan-tool.html)
- [FORScan Official Site](https://forscan.org)
- [ISO 14229 UDS Standard](https://en.wikipedia.org/wiki/Unified_Diagnostic_Services)
- Our investigation: `HVAC_FINAL_CONCLUSION.md`

---

## CRITICAL SAFETY WARNING ⚠️

**DO NOT send CAN messages on the HS-CAN bus via OBD-II port!**

### What Happened During FDIM Testing

When attempting to control FDIM (which is on MS-CAN) by sending messages via the OBD-II port (which connects to HS-CAN), the following occurred:

1. **ABS light started flickering**
2. **Warning sound and "check brake system" message appeared**
3. **ABS module stopped responding to diagnostic queries**
4. **CAN explorer failed to capture wheel speed data**
5. **Transmission gear data disappeared from CAN bus**

### Root Cause

- FDIM is on **MS-CAN** (125 kbps)
- OBD-II port connects to **HS-CAN** (500 kbps)
- Sending MS-CAN formatted messages on HS-CAN interfered with safety-critical ABS communication
- The two buses are separate - messages sent on HS-CAN cannot reach MS-CAN modules

### Why This Is Dangerous

**HS-CAN carries safety-critical data**:
- ABS wheel speed sensors (0x4B0)
- Brake status (0x190)
- Transmission gear (0x228)
- Engine control (PCM at 0x7E0)
- Steering angle (0x420)

**Injecting incorrect messages can**:
- Interfere with ABS operation
- Cause false warnings
- Disrupt safety system communication
- Potentially affect vehicle control systems

### Recovery Procedure

If you experience ABS issues after CAN bus testing:

1. **Immediate**: Turn off ignition, wait 30 seconds
2. **Clear fault**: Restart vehicle, check if ABS light clears
3. **Test ABS**: Run `scripts/debug/test_ford_abs_connection.py`
4. **Verify wheel speeds**: Run `scripts/debug/correlate_abs_wheel_speeds.py`
5. **If issues persist**: Disconnect battery for 5 minutes to reset all modules

## Summary

Your 2008 Ford Escape has:
- **HS-CAN (500 kbps):** PCM, ABS, IPC - ✅ Accessible via standard OBD-II (READ-ONLY recommended)
- **MS-CAN (125 kbps):** HVAC, BCM, Audio, FDIM - ⚠️ NOT accessible via standard OBD-II port

### Safe Practices

**✅ SAFE - Read-Only Operations**:
- Monitor CAN bus traffic (passive listening)
- Read diagnostic data from modules
- Query DIDs for parameters
- Read DTCs

**⚠️ CAUTION - Write Operations**:
- Clear DTCs (with user confirmation)
- Reset learned values (with user confirmation)

**❌ DANGEROUS - Never Do This**:
- Send CAN messages on HS-CAN bus
- Attempt to control FDIM via OBD-II port
- Inject messages without understanding bus architecture
- Test MS-CAN protocols on HS-CAN bus

### For FDIM Control

**Requirements**:
- Direct connection to MS-CAN bus (pins 3 & 11)
- Dual-CAN adapter (not standard ELM327)
- Professional tools (FORScan with MS-CAN license)
- **DO NOT attempt via standard OBD-II connection**

**For now:** Focus on HS-CAN modules (PCM, ABS) with READ-ONLY operations.  
**Future:** Use FORScan for MS-CAN access (HVAC, FDIM) - do not attempt DIY MS-CAN control.
