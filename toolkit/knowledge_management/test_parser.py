"""
Quick test script for technical data parser
"""

from technical_parser import (
    TechnicalDataParser,
    ModuleInfo,
    CommandDef,
    DTCRule,
    ResponseRule,
    BitMapping
)


def test_module_round_trip():
    """Test module serialization round trip"""
    parser = TechnicalDataParser()
    
    # Create module
    original = ModuleInfo(
        name="HVAC",
        address="7A0",
        protocol="CAN",
        bus="HS"
    )
    
    # Serialize
    serialized = parser.serialize_module(original)
    print(f"Module serialized: {serialized}")
    
    # Parse back
    parser._parse_module_line(serialized)
    parsed = parser.knowledge.modules["HVAC"]
    
    # Verify
    assert parsed.name == original.name
    assert parsed.address == original.address
    assert parsed.protocol == original.protocol
    assert parsed.bus == original.bus
    
    print("✓ Module round trip successful")


def test_command_round_trip():
    """Test command serialization round trip"""
    parser = TechnicalDataParser()
    
    # Create command
    original = CommandDef(
        id="HVAC.READ_DTC",
        mode="03",
        response_pattern="43[0-9A-F]{4,}"
    )
    
    # Serialize
    serialized = parser.serialize_command(original)
    print(f"Command serialized: {serialized}")
    
    # Parse back
    parser._parse_command_line(serialized)
    parsed = parser.knowledge.commands["HVAC.READ_DTC"]
    
    # Verify
    assert parsed.id == original.id
    assert parsed.mode == original.mode
    assert parsed.response_pattern == original.response_pattern
    
    print("✓ Command round trip successful")


def test_dtc_round_trip():
    """Test DTC rule serialization round trip"""
    parser = TechnicalDataParser()
    
    # Create DTC rule
    original = DTCRule(
        code="P1632",
        byte_range="0-1",
        bit_range="0-15",
        calculation="hex"
    )
    
    # Serialize
    serialized = parser.serialize_dtc_rule(original)
    print(f"DTC rule serialized: {serialized}")
    
    # Parse back
    parser._parse_dtc_line(serialized)
    parsed = parser.knowledge.dtc_rules["P1632"]
    
    # Verify
    assert parsed.code == original.code
    assert parsed.byte_range == original.byte_range
    assert parsed.bit_range == original.bit_range
    assert parsed.calculation == original.calculation
    
    print("✓ DTC rule round trip successful")


def test_response_round_trip():
    """Test response rule serialization round trip"""
    parser = TechnicalDataParser()
    
    # Create response rule
    original = ResponseRule(
        cmd_id="READ_DTC",
        pattern="43([0-9A-F]{4})+",
        extract=["dtc_hex"],
        calculations=[]
    )
    
    # Serialize
    serialized = parser.serialize_response_rule(original)
    print(f"Response rule serialized: {serialized}")
    
    # Parse back
    parser._parse_response_line(serialized)
    parsed = parser.knowledge.response_rules["READ_DTC"]
    
    # Verify
    assert parsed.cmd_id == original.cmd_id
    assert parsed.pattern == original.pattern
    assert parsed.extract == original.extract
    
    print("✓ Response rule round trip successful")


def test_bit_mapping_round_trip():
    """Test bit mapping serialization round trip"""
    parser = TechnicalDataParser()
    
    # Create bit mapping
    original = BitMapping(
        field="monitor_status",
        byte_pos=1,
        bit_range="0",
        meanings={"0": "incomplete", "1": "complete"}
    )
    
    # Serialize
    serialized = parser.serialize_bit_mapping(original)
    print(f"Bit mapping serialized: {serialized}")
    
    # Parse back
    parser._parse_bitmapping_line(serialized)
    parsed = parser.knowledge.bit_mappings["monitor_status"]
    
    # Verify
    assert parsed.field == original.field
    assert parsed.byte_pos == original.byte_pos
    assert parsed.bit_range == original.bit_range
    assert parsed.meanings == original.meanings
    
    print("✓ Bit mapping round trip successful")


if __name__ == '__main__':
    print("Testing technical data parser round trips...\n")
    
    test_module_round_trip()
    print()
    test_command_round_trip()
    print()
    test_dtc_round_trip()
    print()
    test_response_round_trip()
    print()
    test_bit_mapping_round_trip()
    
    print("\n✓ All round trip tests passed!")
