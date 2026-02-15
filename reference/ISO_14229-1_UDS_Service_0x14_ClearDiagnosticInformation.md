# ISO 14229-1 UDS Service 0x14: ClearDiagnosticInformation

**Source:** ISO 14229-1:2013(E) Section 11.2 (pages 175-177)  
**Service ID:** 0x14  
**Response ID:** 0x54 (0x14 + 0x40)

---

## Service Description

The ClearDiagnosticInformation service is used to clear diagnostic information (DTCs and related data) from one or multiple servers' memory.

**What Gets Cleared:**
- DTC status bytes
- DTC snapshot data (freeze frames)
- DTC extended data
- First/most recent DTC records
- DTC-related flags, counters, timers

**What Does NOT Get Cleared:**
- DTC mirror memory (if present)
- Permanent DTCs (emissions-related)
- Long-term memory (updated during power-latch phase)

---

## Request Message Format

```
14 [groupOfDTC_high] [groupOfDTC_mid] [groupOfDTC_low]
```

### Group of DTC Parameter (3 bytes)

The 3-byte parameter specifies which DTCs to clear:

| Value | Description |
|-------|-------------|
| `FF FF 00` | All emissions-related DTCs |
| `FF FF 33` | All emissions-related DTCs (alternate) |
| `00 00 00` | All DTCs (powertrain, chassis, body, network) |
| `[specific DTC]` | Clear one specific DTC |

### DTC Format

DTCs are encoded as 3 bytes:
- Byte 1: High byte (includes DTC type)
- Byte 2: Middle byte
- Byte 3: Low byte

**DTC Types:**
- `0x00-0x3F`: Powertrain (P codes)
- `0x40-0x7F`: Chassis (C codes)
- `0x80-0xBF`: Body (B codes)
- `0xC0-0xFF`: Network (U codes)

---

## Examples

### Example 1: Clear All Emissions-Related DTCs

```
Request:  14 FF FF 33
Response: 54
```

**Breakdown:**
- `14` = Service ID
- `FF FF 33` = All emissions-related DTCs
- `54` = Positive response (no data)

### Example 2: Clear All DTCs

```
Request:  14 00 00 00
Response: 54
```

### Example 3: Clear Specific DTC (P0420)

```
Request:  14 04 20 00
Response: 54
```

**DTC P0420 encoding:**
- P = Powertrain (0x0)
- 0420 = 0x0420
- Encoded as: `04 20 00`

---

## Positive Response Format

```
54
```

The positive response contains only the response SID (0x54). No additional data is returned.

**Important:** The server sends a positive response even if no DTCs were stored.

---

## Negative Response Codes

| NRC | Mnemonic | Description |
|-----|----------|-------------|
| 0x13 | IMLOIF | incorrectMessageLengthOrInvalidFormat - Wrong message length |
| 0x22 | CNC | conditionsNotCorrect - Internal conditions prevent clearing |
| 0x31 | ROOR | requestOutOfRange - groupOfDTC parameter not supported |
| 0x72 | GPF | generalProgrammingFailure - Error writing to memory |

---

## Usage Examples

### Clear All DTCs from PCM

```python
# Clear all DTCs
send: "14 00 00 00"
receive: "54"  # Success
```

### Clear Specific DTC

```python
# Clear P0171 (System Too Lean Bank 1)
# P0171 = 0x0171 → encoded as 01 71 00
send: "14 01 71 00"
receive: "54"  # Success
```

### Clear After Repair

```python
# 1. Read DTCs to confirm issue
send: "19 02 AF"
receive: "59 02 AF [DTCs...]"

# 2. Perform repair

# 3. Clear DTCs
send: "14 00 00 00"
receive: "54"

# 4. Verify cleared
send: "19 02 AF"
receive: "59 02 AF 00"  # No DTCs
```

---

## Important Notes

- Always clear DTCs AFTER repairs are complete
- Clearing DTCs resets readiness monitors (emissions testing)
- Some DTCs may return immediately if fault is still present
- Permanent DTCs (emissions) cannot be cleared manually
- DTC mirror memory is not affected by this service

---

## Power-Latch Phase

The server may maintain backup copies of DTC data in long-term memory (EEPROM). These backups are updated during the power-latch phase (when ignition is turned off).

**Warning:** If power is interrupted during power-latch (e.g., battery disconnect), data inconsistency may occur.

---

## References

- ISO 14229-1:2013(E) Section 11.2 (pages 175-177)
- Annex D.1: DTC format definitions
- Annex D.2: DTC status bit definitions
- Service 0x19: ReadDTCInformation (to read DTCs before clearing)
