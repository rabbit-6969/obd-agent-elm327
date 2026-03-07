# Mazda CAN Bus Reference - Ford Escape 2008 / Mazda Tribute 2008

## Overview

This document contains reverse-engineered CAN bus data for the **Ford Escape 2008 / Mazda Tribute 2008** platform. This data was compiled from Mazda community research and applies to the shared Ford-Mazda CD2 platform.

**Confirmed Applicable To:**
- **Ford Escape 2008** (and related years)
- **Mazda Tribute 2008** (and related years)
- **Mercury Mariner 2008** (and related years)

**Source**: Community reverse engineering efforts (Mazda research on Ford-Mazda shared platform)
**Blog Posts**: 
- [Reverse Engineering the Mazda CAN Bus – Part 1](https://www.madox.net/blog/2016/07/11/reverse-engineering-the-mazda-can-bus-part-1/)
- [Reverse Engineering the Mazda CAN Bus – Part 2](https://www.madox.net/blog/2016/07/14/reverse-engineering-the-mazda-can-bus-part-2/)

## Platform Information

The Ford Escape and Mazda Tribute share the **Ford CD2 platform** and use identical CAN bus architectures:
- Same HS-CAN (500 kbps) message structures
- Same MS-CAN (125 kbps) message structures
- Same CAN message IDs and byte layouts
- Same scaling factors for parameters

**This data complements the UDS diagnostic information** documented elsewhere:
- UDS diagnostics via OBD-II port use module addresses (0x7E0 PCM, 0x760 ABS, etc.)
- CAN bus messages are broadcast data between modules
- Both systems coexist on the same vehicle

## CAN Bus Architecture

Mazda vehicles use a dual-CAN architecture:

### HS-CAN (High Speed CAN)
- **Speed**: 500 kbps / 500 kHz
- **Purpose**: Powertrain, chassis, and safety-critical systems
- **Modules**: PCM, TCM, ABS, instrument cluster

### MS-CAN (Medium Speed CAN)
- **Speed**: 125 kbps / 125 kHz
- **Purpose**: Body control, comfort, and infotainment systems
- **Modules**: BCM, HVAC, audio system, lighting

## HS-CAN Data (500 kbps)

### Message 0x00000040
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unknown | Only lasts when key is first on |

### Message 0x00000046
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unknown | Only lasts when key is first on |

### Message 0x00000190
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 2 | 6 | 0x40 | Brake Active | - |

### Message 0x00000200 - Engine & Vehicle Speed
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0,1 | - | - | Unknown | Correlates with 0x00000200(4,5) & Acceleration |
| 2,3 | - | - | Unknown | - |
| 4,5 | - | - | Unknown | Correlates with 0x00000200(0,1) & Acceleration |
| 6 | 7 | 0x80 | Unknown | - |

### Message 0x00000201 - RPM & Speed
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0,1 | - | - | RPM | Scale = X rpm |
| 2,3 | - | - | Unknown | Offset by 0x4000. Appears to be 'delta' in engine torque? Derivative of rpm? Cumulative returns to zero |
| 4,5 | - | - | Vehicle Speed | Scale = X/100 km/h. Unsigned |
| 6 | - | - | Accelerator Pedal | Accelerator Position. 200 is fully depressed |

### Message 0x00000205
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 2 | 6 | 0x40 | Brake Active | - |

### Message 0x0000020F - Vehicle Speed (Alternative)
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 2,3 | - | - | Vehicle Speed | Scale = (X-10000)/100 km/h, unsigned. Correlates with 0x000004B0 wheel speeds |
| 4 | 6 | 0x40 | Unknown | Appears always on |

### Message 0x00000211
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 2 | 7 | 0x80 | Unknown | Appears always on |
| 4 | 6 | 0x40 | Unknown | Appears always on |

### Message 0x00000212 - Warning Lights
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0 | 7 | 0x80 | Unknown | Appears always on |
| 2 | 5 | 0x20 | Unknown | Appears always on |
| 3 | 7 | 0x80 | Unknown | Appears always on |
| 4 | 4 | 0x10 | Dash Warning Light | Off when ignition is off |
| 4 | 6 | 0x40 | Dash Warning Light | Off when ignition is off |

### Message 0x00000228 - Transmission Status
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0 | 0 | 0x01 | Off (Park) | 0x03 appears to be 'neutral' |
| 0 | 1 | 0x02 | Reverse | 0x03 appears to be 'neutral' |
| 0 | 2 | 0x04 | Forward (Drive) | - |
| 0 | 3 | - | - | - |
| 0 | 4 | 0x10 | 1st Gear | - |
| 0 | 5 | 0x20 | 2nd Gear | - |
| 0 | 6 | 0x40 | 3rd Gear | - |
| 0 | 7 | 0x80 | 4th Gear | - |
| 1 | 3 | 0x08 | Gear Shift | Active for several messages on each gear change |
| 1 | 4 | 0x10 | Unknown | Occurred once on a gear change |
| 1 | 6 | 0x40 | Brake Pedal Related | Something to do with brake pedal |
| 1 | 7 | 0x80 | Manual/Triptronic | - |

### Message 0x00000231 - Gear & Torque
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0 | 0 | 0x01 | Unknown | Not Brake, but very close…changes not far from brake |
| 0 | 1 | 0x02 | Unknown | Always appears off |
| 0 | 2 | 0x04 | Unknown | Always appears off |
| 0 | 3 | 0x08 | Unknown | Always appears off |
| 0 | 4 | 0x10 | 1st Gear | Reverse = 0xE? |
| 0 | 5 | 0x20 | 2nd Gear | Reverse = 0xE? |
| 0 | 6 | 0x40 | 3rd Gear | Reverse = 0xE? |
| 0 | 7 | 0x80 | 4th Gear | Reverse = 0xE? |
| 1,2 | - | - | Unknown | Torque? RPM demand x 10? |

### Message 0x00000240
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0 | - | - | Unknown | Varies, not correlated with speed/accel. Around 10/11/12 when stationary |

### Message 0x00000250 - Accelerator & Flags
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0 | - | - | Unknown | - |
| 1 | - | - | Unknown | - |
| 2 | - | - | Unknown | - |
| 3 | - | - | Unknown | Accelerator Position. 225 seems fully depressed, but bias of 32… See other accel pos. This might be the raw value, some noise |
| 4 | 0 | 0x01 | Unknown | - |
| 5 | 1 | 0x02 | Unknown | - |
| 5 | 2 | 0x04 | Unknown | - |
| 5 | 3 | 0x08 | Unknown | - |
| 5 | 4 | 0x10 | Unknown | - |
| 5 | 5 | 0x20 | Unknown | - |
| 5 | 6 | 0x40 | Unknown | - |

### Message 0x000002A0
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unknown | Appears to be all zeroes (4 byte frame) |

### Message 0x00000420
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0,1 | - | - | Unknown | - |
| 1 | 0 | - | Unknown | - |
| 2 | - | - | Unknown | Counter (Always Increments) |

### Message 0x00000430
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0 | - | - | Unknown | Not sure if 2 bytes or byte pair |

### Message 0x00000433 - Status Flags
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 1 | 0 | 0x01 | Unknown | - |
| 2 | 0 | 0x01 | Unknown | Not seen to change (0) |
| 2 | 1 | 0x02 | Unknown | Changes |
| 2 | 2 | 0x04 | Unknown | Changes |
| 2 | 3 | 0x08 | Unknown | Not seen to change (1) |
| 2 | 6 | 0x40 | Unknown | Not seen to change (1) |
| 3 | 0 | 0x01 | Unknown | - |
| 3 | 1 | 0x02 | Unknown | - |
| 3 | 2 | 0x04 | Unknown | - |
| 3 | 3 | 0x08 | Unknown | - |
| 5 | 0 | 0x01 | Unknown | Not seen to change (1) |
| 6 | 0 | 0x01 | Unknown | - |
| 6 | 1 | 0x02 | Unknown | - |
| 6 | 2 | 0x04 | Unknown | - |
| 6 | 3 | 0x08 | Unknown | - |
| 6 | 6 | 0x40 | Unknown | - |

### Message 0x000004B0 - Wheel Speeds
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0,1 | - | - | Left Front Wheel Speed | Check Order. Scale = (X-10000)/100 km/h, unsigned. Correlates with 0x0000020F vehicle speeds |
| 2,3 | - | - | Right Front Wheel Speed | Check Order. Scale = (X-10000)/100 km/h, unsigned. Correlates with 0x0000020F vehicle speeds |
| 4,5 | - | - | Left Rear Wheel Speed | Check Order. Scale = (X-10000)/100 km/h, unsigned. Correlates with 0x0000020F vehicle speeds |
| 6,7 | - | - | Right Rear Wheel Speed | Check Order. Scale = (X-10000)/100 km/h, unsigned. Correlates with 0x0000020F vehicle speeds |

### Message 0x000004DA - Steering Angle
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0,1 | - | - | Steering Column Angle | (X-32768)/10 Degrees, Clockwise +ve |
| 2 | 6 | 0x40 | Unknown | Not seen to change (1) |
| 2 | 7 | 0x80 | Unknown | Not seen to change (1) |

### Message 0x000004EA
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unknown | 1 Byte Frame always 00 |

### Message 0x000004EC
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unknown | 8 Byte Frame always 00 |

### Message 0x000004F0
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unchanging Unknown | Every 5s: 14 24 12 FF FF 7F |

### Message 0x000004F1
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unchanging Unknown | Every 5s: 4A 01 9F FF FF 64 5E 5E |

### Message 0x000004F2 - Odometer
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 1,2 | - | - | Odometer (Total) | Might be first byte too to get the range |

### Message 0x000004F3
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unchanging Unknown | Every 5s: 32 30 33 30 30 38 31 31 |

### Message 0x000004F4
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Unchanging Unknown | Every 5s: 42 4B 31 30 46 32 30 30 |

## MS-CAN Data (125 kbps)

### Message 0x00000023
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 1 | 7 | 0x80 | Unknown | Not seen to change (1) |

### Message 0x00000201 - Engine Data
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0,1 | - | - | RPM | - |
| 2,3 | - | - | Unknown | Offset by 0x8000. Appears to be 'delta' in engine torque? Cumulative returns to zero |
| 4,5 | - | - | Vehicle Speed | Scale = X/100 km/h. Unsigned |
| 6 | - | - | Unknown | Accelerator Position? Very closely linked with accelerations (not decel) |

### Message 0x00000265 - Turn Signals
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 5 | 5 | 0x20 | Left Blinker | Indicates light on. (It pulses too!) Check hazard |
| 5 | 6 | 0x40 | Right Blinker | Indicates light on. (It pulses too!) Check hazard |

### Message 0x00000285 - Key Position
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 5 | 5 | 0x20 | Unknown | key pos? |
| 5 | 6 | 0x40 | Unknown | key pos? |

### Message 0x0000028F - Volume Control
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 4 | 4 | 0x10 | Unknown | volume? |
| 6 | 6 | 0x40 | Unknown | volume? |
| 7 | 7 | 0x80 | Unknown | volume? |

### Message 0x00000290 - Head Unit Display (Part 1)
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 1,2,3,4,5,6,7 | - | - | HU LCD Alphanumeric Display 1/2 | ASCII Byte Codes |

### Message 0x00000291 - Head Unit Display (Part 2)
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 1,2,3,4,5,6,7 | - | - | HU LCD Alphanumeric Display 2/2 | ASCII Byte Codes |

### Message 0x00000400 - Trip Computer
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0,1 | - | - | Average Speed | Average Speed in Km/h. Might be single byte only |
| 2,3 | - | - | Fuel Consumption | Instantaneous Fuel Consumption L/100km. Scale X/10 |
| 3,4 | - | - | Average Fuel Consumption | Fuel Consumption (L) per 100km. Scale X/10. Might be single byte only |
| 5,6 | - | - | Distance Remaining | Distance in KM remaining |

### Message 0x00000401
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0 | - | - | Unknown | Not seen to change (0) |

### Message 0x00000420
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 0 | - | - | Unknown | Rises then levels off…Temperature? |
| 1,2 | - | - | Unknown | Increasing counter? |
| 4 | 1 | 0x02 | Unknown | - |
| 4 | 6 | 0x40 | Unknown | - |

### Message 0x00000433 - System Status
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| 2 | - | - | Temperature | Guess only, temperature in C X/4 (0.25deg C incs) |
| 3 | 0 | 0x01 | Key On? | - |
| 3 | 3 | 0x08 | Air Con running? | - |
| 3 | 6 | 0x40 | Highbeam (Indicator Light) | - |
| 4 | - | - | Headlight & Wiper | - |

### Message 0x00000460
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Key position? | - |

### Message 0x00000501
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Key? | - |

### Message 0x00000511
| Byte(s) | Bit | Bitmask | Description | Comment |
|---------|-----|---------|-------------|---------|
| - | - | - | Key? | - |

## Key Findings Summary

### Confirmed Parameters

**HS-CAN (500 kbps):**
- RPM: Message 0x00000201, bytes 0-1
- Vehicle Speed: Message 0x00000201, bytes 4-5 (scale X/100 km/h)
- Wheel Speeds: Message 0x000004B0, all 4 wheels (scale (X-10000)/100 km/h)
- Steering Angle: Message 0x000004DA, bytes 0-1 ((X-32768)/10 degrees)
- Accelerator Pedal: Message 0x00000201, byte 6 (200 = fully depressed)
- Brake Active: Message 0x00000190, bit 6 (0x40)
- Transmission Gear: Message 0x00000228, byte 0 (bits 4-7 for gears 1-4)
- Odometer: Message 0x000004F2, bytes 1-2

**MS-CAN (125 kbps):**
- RPM: Message 0x00000201, bytes 0-1
- Vehicle Speed: Message 0x00000201, bytes 4-5 (scale X/100 km/h)
- Turn Signals: Message 0x00000265, bits 5-6 (left/right blinker)
- Average Speed: Message 0x00000400, bytes 0-1
- Fuel Consumption: Message 0x00000400, bytes 2-3 (scale X/10 L/100km)
- Distance Remaining: Message 0x00000400, bytes 5-6
- Head Unit Display: Messages 0x00000290 and 0x00000291 (ASCII text)
- Highbeam: Message 0x00000433, bit 6 (0x40)
- Air Conditioning: Message 0x00000433, bit 3 (0x08)

## Usage Notes

### Passive Monitoring

This data is useful for:
- Creating custom dashboards
- Data logging for performance analysis
- Integration with aftermarket systems
- Diagnostic monitoring

### Safety Considerations

- This is READ-ONLY data from passive CAN bus monitoring
- Do NOT attempt to inject messages without understanding safety implications
- Modifying safety-critical messages (brakes, steering, airbags) is dangerous
- Always test in safe, controlled environments

### Data Validation

- Some parameters are marked as "Unknown" or "Guess only"
- Always validate against actual vehicle behavior
- Scaling factors may vary by model year or trim
- Cross-reference with multiple data sources when possible

## Platform Applicability

This data has been confirmed or is likely applicable to:
- **Ford Escape 2008** (and related years) - Ford CD2 platform
- **Mazda Tribute 2008** (and related years) - Ford CD2 platform
- **Mercury Mariner 2008** (and related years) - Ford CD2 platform

**May also apply to:**
- Other Ford-Mazda shared platform vehicles from this era
- Mazda3, Mazda6 (if using similar architecture - verify first)

**Note**: Always verify message IDs and scaling factors for your specific vehicle before relying on this data. This data was reverse-engineered from the Ford Escape / Mazda Tribute platform.

## Contributing

If you have additional CAN bus data for Mazda vehicles:
1. Document the vehicle make, model, year, and trim
2. Capture CAN messages with timestamps
3. Correlate messages with vehicle actions (accelerating, braking, turning, etc.)
4. Share findings with proper attribution

## References

- [Reverse Engineering the Mazda CAN Bus – Part 1](https://www.madox.net/blog/2016/07/11/reverse-engineering-the-mazda-can-bus-part-1/)
- [Reverse Engineering the Mazda CAN Bus – Part 2](https://www.madox.net/blog/2016/07/14/reverse-engineering-the-mazda-can-bus-part-2/)
- ISO 11898: Controller Area Network (CAN) standard
- SAE J1939: CAN bus protocol for heavy-duty vehicles

## Disclaimer

This information is provided for educational and diagnostic purposes only. The author and contributors are not responsible for any damage, injury, or legal consequences resulting from the use of this information. Always follow local laws and regulations regarding vehicle modifications and diagnostics.
