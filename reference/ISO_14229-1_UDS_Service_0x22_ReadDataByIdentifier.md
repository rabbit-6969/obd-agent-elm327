# ISO 14229-1 UDS Service 0x22: ReadDataByIdentifier

**Source:** ISO 14229-1:2013(E) Section 10.2 (pages 106-112)  
**Service ID:** 0x22  
**Response ID:** 0x62 (0x22 + 0x40)

---

## Service Description

The ReadDataByIdentifier service allows the client to request data record values from the server identified by one or more dataIdentifiers (DIDs). This is the primary service for reading live sensor data, calculated values, and system status information.

### Key Concepts

- Each DID is a **2-byte identifier** (e.g., 0x0100, 0xF190)
- Multiple DIDs can be requested in a single message
- The format and content of each dataRecord is **manufacturer-specific**
- The server may limit how many DIDs can be requested simultaneously
- DIDs can contain analog/digital signals, internal data, or status information

---

## Request Message Format

```
22 [DID1_high] [DID1_low] [DID2_high] [DID2_low] ...
```

### Single DID Request Example

```
Request:  22 01 00
Response: 62 01 00 [data bytes...]
```

**Request breakdown:**
- `22` = Service ID (ReadDataByIdentifier)
- `01 00` = DID 0x0100 (2 bytes, MSB first)

### Multiple DID Request Example

```
Request:  22 01 00 01 01
Response: 62 01 00 [data1...] 01 01 [data2...]
```

**Request breakdown:**
- `22` = Service ID
- `01 00` = First DID (0x0100)
- `01 01` = Second DID (0x0101)

---

## Positive Response Message Format

```
62 [DID1_high] [DID1_low] [dataRecord1...] [DID2_high] [DID2_low] [dataRecord2...] ...
```

### Response Structure

For each requested DID, the response contains:
1. **DID echo** (2 bytes) - confirms which DID this data is for
2. **dataRecord** (variable length) - the actual data values

### Example: VIN Number (DID 0xF190)

```
Request:  22 F1 90
Response: 62 F1 90 57 30 4C 30 30 30 30 34 33 4D 42 35 34 31 33 32 36
```

**Response breakdown:**
- `62` = Positive response (0x22 + 0x40)
- `F1 90` = DID echo (0xF190)
- `57 30 4C...` = VIN data (17 bytes ASCII: "W0L000043MB541326")

### Example: Multiple Parameters (DIDs 0x010A and 0x0110)

```
Request:  22 01 0A 01 10
Response: 62 01 0A A6 66 07 50 20 1A 00 63 4A 82 7E 01 10 8C
```

**Response breakdown:**
- `62` = Positive response
- `01 0A` = First DID echo
- `A6 66 07 50 20 1A 00 63 4A 82 7E` = First dataRecord (11 bytes of engine data)
- `01 10` = Second DID echo
- `8C` = Second dataRecord (1 byte: battery voltage)

---

## Data Record Format

The dataRecord content is **NOT defined by ISO 14229-1** - it is completely manufacturer-specific. Each manufacturer decides:

- How many bytes each DID returns
- What each byte represents
- The data type (unsigned int, signed int, ASCII, bitfield, etc.)
- The scaling formula (e.g., `(value - 40)` for temperature)
- The units (°C, PSI, RPM, etc.)

### Common Data Types

| Type | Bytes | Example | Description |
|------|-------|---------|-------------|
| Single byte | 1 | `0x7F` | Temperature: (0x7F - 40) = 87°C |
| Two bytes | 2 | `0x07 0x50` | RPM: (0x0750 / 4) = 468 RPM |
| ASCII string | Variable | `0x57 0x30 0x4C...` | VIN: "W0L..." |
| Bitfield | 1+ | `0x82` | Bit 7=1, Bit 1=1, others=0 |

---

## Negative Response Codes

| NRC | Mnemonic | Description |
|-----|----------|-------------|
| 0x13 | IMLOIF | incorrectMessageLengthOrInvalidFormat - Invalid message length or too many DIDs requested |
| 0x14 | RTL | responseTooLong - Response exceeds transport protocol limit |
| 0x22 | CNC | conditionsNotCorrect - Operating conditions not met |
| 0x31 | ROOR | requestOutOfRange - DID not supported or not supported in current session |
| 0x33 | SAD | securityAccessDenied - DID is secured, need SecurityAccess first |

---

## DID Ranges (from Annex C)

While ISO 14229-1 doesn't mandate specific DIDs, it defines standard ranges:

| Range | Purpose |
|-------|---------|
| 0x0000-0x00FF | Reserved by ISO 14229-1 |
| 0x0100-0xEFFF | Vehicle manufacturer specific |
| 0xF000-0xF0FF | Network configuration DIDs |
| 0xF100-0xF18F | Vehicle manufacturer specific |
| 0xF190-0xF19F | Vehicle information (VIN, etc.) |
| 0xF1A0-0xF1EF | Vehicle manufacturer specific |
| 0xF1F0-0xF1FF | System supplier specific |
| 0xF200-0xF2FF | ECU manufacturing data |
| 0xF300-0xF3FF | Vehicle manufacturer specific |
| 0xF400-0xF4FF | System supplier specific |

**Note:** Ford uses the 0x0100-0xEFFF range for their custom DIDs, including transmission parameters.

---

## NRC Evaluation Sequence

When the server receives a ReadDataByIdentifier request, it checks:

1. **Message length** - Must be 3+ bytes (SID + at least one DID)
2. **Modulo 2 check** - DIDs are 2 bytes, so total length must be odd (SID + 2n bytes)
3. **Security check** - For each DID, check if security access is required
4. **Session check** - For each DID, check if supported in current session
5. **At least one supported** - If NO DIDs are supported, return NRC 0x31
6. **Conditions check** - For each DID, check operating conditions
7. **Response length** - Check if total response fits in transport protocol

**Important:** If at least one DID is supported, the server returns a positive response with ONLY the supported DIDs (unsupported DIDs are silently omitted).

---

## Usage for Transmission Diagnostics

### Reading Single Parameter

```python
# Read transmission fluid temperature (DID 0x0100)
send: "22 0100"
receive: "62 01 00 0C"
# Parse: 0x0C = 12 decimal → (12 - 40) = -28°C
```

### Reading Multiple Parameters

```python
# Read temperature and pressure together
send: "22 0100 0101"
receive: "62 01 00 0C 01 01 01 CD"
# Parse: 
#   DID 0x0100: 0x0C = -28°C
#   DID 0x0101: 0x01CD = 461 (units TBD)
```

### Handling Unknown DIDs

```python
# Try to read gear position (DID 0x0102)
send: "22 0102"
receive: "7F 22 31"
# NRC 0x31 = requestOutOfRange (DID not supported)
```

---

## Ford-Specific Observations

Based on testing with 2008 Ford Escape:

1. **Working DIDs:**
   - 0x0100: Transmission Fluid Temperature (1 byte)
   - 0x0101: Transmission Line Pressure (2 bytes)

2. **DID Organization:**
   - Ford appears to use 0x0100-0x01FF range for transmission
   - Each parameter gets its own DID (not packed into one DID)

3. **Session Requirements:**
   - DIDs 0x0100 and 0x0101 work in default session
   - Extended session (0x10 03) is NOT supported by 2008 Escape PCM
   - Additional DIDs may require different approach

4. **Data Format:**
   - Temperature: 1 byte, formula `(value - 40) = °C`
   - Pressure: 2 bytes, formula unknown (needs calibration)

---

## Implementation Notes

- Always send DIDs in **MSB first** (big-endian) format
- The response echoes each DID before its data
- If requesting multiple DIDs, the server may omit unsupported ones
- Data length varies by DID - you must know expected length
- Manufacturer documentation is essential for parsing dataRecords
- Some DIDs may only be available when engine is running
- Some DIDs may require specific vehicle states (gear, speed, etc.)

---

## References

- ISO 14229-1:2013(E) Section 10.2 (pages 106-112)
- Annex C: Data Identifier Definitions (pages 337-352)
- ISO 15031-2: OBD-II PIDs (for emission-related parameters)
- Figure 15: NRC handling for ReadDataByIdentifier service
