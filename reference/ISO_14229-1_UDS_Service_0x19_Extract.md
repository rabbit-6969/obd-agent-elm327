# ISO 14229-1 UDS Protocol - Service 0x19 ReadDTCInformation

**Source:** ISO 14229-1:2013(E) - Unified Diagnostic Services (UDS)  
**Extracted:** February 14, 2026  
**Purpose:** HVAC diagnostic implementation for 2008 Ford Escape

---

## Overview

Service 0x19 (ReadDTCInformation) is used to read diagnostic trouble codes from vehicle modules. This is the UDS equivalent of OBD-II Mode 03, but with more capabilities and flexibility.

**Key Differences from OBD-II Mode 03:**
- Uses 3-byte DTC format (vs 2-byte in OBD-II)
- Includes detailed status information for each DTC
- Supports filtering by status mask
- Works on MS-CAN modules (HVAC, BCM, etc.)

---

## Service 0x19 Sub-function 0x02: reportDTCByStatusMask

This sub-function retrieves a list of DTCs that match a client-defined status mask.

### Request Message Format

| Byte | Parameter | Value | Description |
|------|-----------|-------|-------------|
| #1 | Service ID | 0x19 | ReadDTCInformation |
| #2 | Sub-function | 0x02 | reportDTCByStatusMask |
| #3 | DTCStatusMask | 0x00-0xFF | Status filter mask |

**Example Request:**
```
19 02 AF
```
- `19` = ReadDTCInformation service
- `02` = reportDTCByStatusMask sub-function
- `AF` = Status mask (binary: 10101111)

### Positive Response Format

| Byte | Parameter | Value | Description |
|------|-----------|-------|-------------|
| #1 | Response SID | 0x59 | Positive response (0x19 + 0x40) |
| #2 | Sub-function | 0x02 | Echo of request sub-function |
| #3 | DTCStatusAvailabilityMask | 0x00-0xFF | Which status bits are supported |
| #4-7 | DTC #1 | 3 bytes + 1 byte | First DTC and its status |
| #8-11 | DTC #2 | 3 bytes + 1 byte | Second DTC and its status |
| ... | ... | ... | Additional DTCs (4 bytes each) |

**DTC Record Format (4 bytes per DTC):**
- Byte 1: DTCHighByte
- Byte 2: DTCMiddleByte
- Byte 3: DTCLowByte
- Byte 4: statusOfDTC

**Example Response (2 DTCs):**
```
59 02 AF 12 34 56 08 AB CD EF 10
```
- `59` = Positive response
- `02` = Sub-function echo
- `AF` = Status availability mask
- `12 34 56` = First DTC code
- `08` = First DTC status
- `AB CD EF` = Second DTC code
- `10` = Second DTC status

**Example Response (No DTCs):**
```
59 02 AF
```
- Only 3 bytes returned when no DTCs match the mask

---

## DTC Status Bits (Byte 4 of each DTC)

Each DTC has an 8-bit status byte that indicates various states:

| Bit | Name | Description |
|-----|------|-------------|
| 0 | testFailed | Most recent test result (1=failed, 0=passed) |
| 1 | testFailedThisOperationCycle | Failed at least once this cycle |
| 2 | pendingDTC | Failed in current or last cycle |
| 3 | confirmedDTC | Confirmed malfunction (stored in memory) |
| 4 | testNotCompletedSinceLastClear | Test hasn't run since clear |
| 5 | testFailedSinceLastClear | Failed at least once since clear |
| 6 | testNotCompletedThisOperationCycle | Test hasn't run this cycle |
| 7 | warningIndicatorRequested | Warning light requested |

### Status Bit Details

#### Bit 0: testFailed
- **1** = Most recent test indicated failure (malfunction currently present)
- **0** = Most recent test passed (no current malfunction)
- Reset when test passes or ClearDiagnosticInformation called

#### Bit 1: testFailedThisOperationCycle
- **1** = Test failed at least once during current operation cycle
- **0** = Test has not failed this operation cycle
- Reset at start of new operation cycle or after clear

#### Bit 2: pendingDTC
- **1** = Test failed during current or last operation cycle
- **0** = Test completed and passed for full operation cycle
- Cleared after completing cycle with no failures

#### Bit 3: confirmedDTC (MANDATORY)
- **1** = DTC confirmed and stored in long-term memory
- **0** = DTC not confirmed or aged out
- Set after confirmation threshold met (e.g., 2 operation cycles)
- Cleared by ClearDiagnosticInformation or aging threshold

#### Bit 4: testNotCompletedSinceLastClear
- **1** = Test has not run to completion since last clear
- **0** = Test has completed at least once since clear
- Initialized to 1 after clear

#### Bit 5: testFailedSinceLastClear
- **1** = Test failed at least once since last clear
- **0** = Test has not failed since clear
- Latched at 1 once set

#### Bit 6: testNotCompletedThisOperationCycle
- **1** = Test has not run to completion this cycle
- **0** = Test completed at least once this cycle
- Reset at start of each operation cycle

#### Bit 7: warningIndicatorRequested
- **1** = Warning indicator (MIL/light) should be active
- **0** = Warning indicator not requested
- Typically set when confirmedDTC = 1

---

## Status Mask Usage

The DTCStatusMask in the request filters which DTCs are returned. The server performs:
```
(statusOfDTC & DTCStatusMask) != 0
```

If the result is non-zero, the DTC is included in the response.

### Common Status Masks

| Mask | Binary | Description |
|------|--------|-------------|
| 0xFF | 11111111 | All DTCs (any status bit set) |
| 0x0F | 00001111 | Active/recent DTCs (bits 0-3) |
| 0x08 | 00001000 | Only confirmed DTCs (bit 3) |
| 0x01 | 00000001 | Only currently failing DTCs (bit 0) |
| 0xAF | 10101111 | Common FORScan mask |

**FORScan typically uses 0xAF (10101111):**
- Bit 7: warningIndicatorRequested ✓
- Bit 6: (not checked)
- Bit 5: testFailedSinceLastClear ✓
- Bit 4: (not checked)
- Bit 3: confirmedDTC ✓
- Bit 2: pendingDTC ✓
- Bit 1: testFailedThisOperationCycle ✓
- Bit 0: testFailed ✓

---

## DTC Code Format

DTCs use 3-byte format (ISO 14229-1):

**Format:** `XX YY ZZ`

### Decoding Example

DTC: `12 34 56`

**Method 1: Hex representation**
- Display as: `123456`

**Method 2: Standard format (if using SAE J2012-DA)**
- Byte 1 bits 7-6: DTC type
  - 00 = Powertrain (P)
  - 01 = Chassis (C)
  - 10 = Body (B)
  - 11 = Network (U)
- Remaining bits: DTC number

**For Ford HVAC, typically use hex format: `123456`**

---

## Implementation Example

### Python Code Structure

```python
def read_hvac_dtcs(elm327, status_mask=0xAF):
    """
    Read DTCs from HVAC module using UDS Service 0x19 Sub-function 0x02
    
    Args:
        elm327: ELM327 adapter instance
        status_mask: Status filter (default 0xAF for all relevant DTCs)
    
    Returns:
        List of DTCs with status information
    """
    # Set protocol and addressing for MS-CAN HVAC
    elm327.send_command("AT SP 6")  # ISO 15765-4 CAN
    elm327.send_command("AT SH 7A0")  # HVAC request address
    elm327.send_command("AT FC SH 7A8")  # HVAC response address
    
    # Send UDS request
    request = f"19 02 {status_mask:02X}"
    response = elm327.send_command(request)
    
    # Parse response
    if response[0:2] == "59" and response[2:4] == "02":
        availability_mask = int(response[4:6], 16)
        dtcs = []
        
        # Parse DTC records (4 bytes each)
        i = 6
        while i + 8 <= len(response):
            dtc_high = response[i:i+2]
            dtc_mid = response[i+2:i+4]
            dtc_low = response[i+4:i+6]
            status = int(response[i+6:i+8], 16)
            
            dtc_code = f"{dtc_high}{dtc_mid}{dtc_low}"
            dtc_status = parse_dtc_status(status)
            
            dtcs.append({
                "code": dtc_code,
                "status": status,
                "status_bits": dtc_status
            })
            
            i += 8
        
        return {
            "availability_mask": availability_mask,
            "dtcs": dtcs
        }
    else:
        # Handle negative response or error
        return None

def parse_dtc_status(status_byte):
    """Parse DTC status byte into individual bits"""
    return {
        "testFailed": bool(status_byte & 0x01),
        "testFailedThisOperationCycle": bool(status_byte & 0x02),
        "pendingDTC": bool(status_byte & 0x04),
        "confirmedDTC": bool(status_byte & 0x08),
        "testNotCompletedSinceLastClear": bool(status_byte & 0x10),
        "testFailedSinceLastClear": bool(status_byte & 0x20),
        "testNotCompletedThisOperationCycle": bool(status_byte & 0x40),
        "warningIndicatorRequested": bool(status_byte & 0x80)
    }
```

---

## Comparison: OBD-II Mode 03 vs UDS Service 0x19

| Feature | OBD-II Mode 03 | UDS Service 0x19 |
|---------|----------------|------------------|
| Service ID | 0x03 | 0x19 |
| Response ID | 0x43 | 0x59 |
| DTC Format | 2 bytes | 3 bytes |
| Status Info | None | 8-bit status per DTC |
| Filtering | No | Yes (status mask) |
| Modules | PCM only (HS-CAN) | All modules (HS/MS-CAN) |
| Sub-functions | No | Yes (multiple) |

---

## Next Steps for Implementation

1. ✅ Understand protocol structure (this document)
2. ⏭️ Capture FORScan logs to verify Ford-specific implementation
3. ⏭️ Implement UDS Service 0x19 in `elm327_base.py`
4. ⏭️ Add HVAC-specific functions in `hvac_diagnostics.py`
5. ⏭️ Test with vehicle
6. ⏭️ Implement Service 0x14 (ClearDiagnosticInformation)
7. ⏭️ Implement Service 0x22 (ReadDataByIdentifier for live data)

---

## References

- ISO 14229-1:2013(E) - Road vehicles — Unified diagnostic services (UDS)
- Section 11.3: ReadDTCInformation service
- Annex D.2: DTC status bit definitions
- Our documentation: `FORD_CAN_BUS_ARCHITECTURE.md`

---

## Summary

The ISO 14229-1 UDS standard provides the complete protocol specification for communicating with Ford HVAC and other MS-CAN modules. Service 0x19 with sub-function 0x02 allows reading DTCs with detailed status information, which is exactly what FORScan uses.

**Key Takeaways:**
- Request: `19 02 [mask]` (3 bytes)
- Response: `59 02 [avail] [DTC1 3bytes + status] [DTC2 3bytes + status] ...`
- Each DTC has 8 status bits providing detailed diagnostic state
- Status mask filters which DTCs are returned
- Works on MS-CAN with proper addressing (7A0 for HVAC)

Tomorrow when you capture FORScan logs, we'll see this protocol in action and verify Ford's specific implementation details.
