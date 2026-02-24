#!/usr/bin/env python3
"""
Decode the Jeep airbag module response
"""

response = "7E8037F19804300"

print("=" * 60)
print("Jeep Airbag Response Decoder")
print("=" * 60)
print(f"\nRaw response: {response}")
print()

# Parse the response
# Format: [Header][Length][Data...]
if len(response) >= 3:
    # First 3 chars might be header
    header = response[:3]
    print(f"Header: {header}")
    
    # Next 2 chars are length
    if len(response) >= 5:
        length_hex = response[3:5]
        try:
            length = int(length_hex, 16)
            print(f"Length: {length} bytes (0x{length_hex})")
        except:
            length = None
    
    # Rest is data
    data = response[5:]
    print(f"Data: {data}")
    print()
    
    # Check if it's a negative response
    if data.startswith("7F"):
        print("✓ This is a NEGATIVE RESPONSE (7F)")
        
        if len(data) >= 6:
            service = data[2:4]
            nrc = data[4:6]
            
            print(f"  Service requested: 0x{service}")
            print(f"  Negative Response Code (NRC): 0x{nrc}")
            print()
            
            # Decode NRC
            nrc_codes = {
                "10": "General reject",
                "11": "Service not supported",
                "12": "Sub-function not supported",
                "13": "Incorrect message length or invalid format",
                "14": "Response too long",
                "21": "Busy - repeat request",
                "22": "Conditions not correct",
                "24": "Request sequence error",
                "31": "Request out of range",
                "33": "Security access denied",
                "35": "Invalid key",
                "36": "Exceed number of attempts",
                "37": "Required time delay not expired",
                "70": "Upload/download not accepted",
                "71": "Transfer data suspended",
                "72": "General programming failure",
                "73": "Wrong block sequence counter",
                "78": "Request correctly received - response pending",
                "7E": "Sub-function not supported in active session",
                "7F": "Service not supported in active session",
            }
            
            nrc_desc = nrc_codes.get(nrc.upper(), "Unknown error code")
            print(f"  Meaning: {nrc_desc}")
            print()
            
            # Provide recommendations
            if nrc.upper() == "22":
                print("RECOMMENDATION:")
                print("  The airbag module responded but said 'conditions not correct'")
                print("  This typically means:")
                print("  1. Module requires extended diagnostic session (Service 0x10)")
                print("  2. Security access may be required (Service 0x27)")
                print("  3. Vehicle must be in specific state (ignition on, engine off)")
                print()
                print("  → Your ELM327 adapter CAN communicate with the airbag module!")
                print("  → But it needs manufacturer-specific unlock sequence")
                print("  → AlfaOBD knows these sequences for Jeep/Chrysler vehicles")
                
            elif nrc.upper() == "7F":
                print("RECOMMENDATION:")
                print("  Service 0x19 (Read DTC) is not supported in current session")
                print("  Need to enter extended diagnostic session first")
                
            elif nrc.upper() == "33":
                print("RECOMMENDATION:")
                print("  Security access is required to read airbag codes")
                print("  This requires manufacturer-specific security algorithm")
                print("  AlfaOBD has the security keys for Jeep/Chrysler")
    
    elif data.startswith("59"):
        print("✓ This is a POSITIVE RESPONSE to Service 0x19")
        print("  DTC data follows...")
        
    else:
        print("⚠ Unknown response format")
        print(f"  First byte: 0x{data[:2]}")

print()
print("=" * 60)
print("CONCLUSION")
print("=" * 60)
print()
print("Your ELM327 adapter successfully communicated with the")
print("airbag module at address 0x740!")
print()
print("However, the module requires:")
print("  • Extended diagnostic session activation")
print("  • Possibly security access (seed/key)")
print("  • Manufacturer-specific command sequences")
print()
print("Standard ELM327 adapters don't have these sequences.")
print()
print("SOLUTION: Use AlfaOBD software (~$50)")
print("  • Works with your existing ELM327 adapter")
print("  • Has all Jeep/Chrysler security keys")
print("  • Can read airbag codes and shifter position")
print("  • Download: https://www.alfaobd.com/")
print()
