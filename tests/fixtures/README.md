# Test Fixtures

This directory contains real vehicle response data collected from a 2008 Ford Escape for use in unit and integration testing.

## Files

### `ford_escape_2008_responses.json`

Complete set of real OBD-II responses collected on February 14, 2026.

**Vehicle Details:**
- Make: Ford
- Model: Escape
- Year: 2008
- VIN: 1FMCU03Z68KB12969
- Calibration: QIEF1A6.HEX
- Condition: Engine off, ignition on
- Voltage: 11.4V

**Data Categories:**

1. **adapter_commands** - ELM327 AT commands and responses
2. **connection_test** - Initial connection verification
3. **supported_pids** - PID support bitmaps for ranges 01-20, 21-40, 41-60
4. **live_data** - 20 live data parameters with decoded values
5. **dtc_commands** - DTC reading (Mode 03, 07, 0A)
6. **monitor_status** - Emission monitor status
7. **freeze_frame** - Freeze frame data (none present)
8. **vehicle_info** - VIN, calibration ID, etc.
9. **module_tests** - Module accessibility tests (PCM, ABS, HVAC, etc.)
10. **test_scenarios** - Pre-defined test scenarios

## Usage in Tests

### Loading Fixtures

```python
import json
import os

def load_fixtures():
    """Load Ford Escape 2008 test fixtures"""
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        'fixtures',
        'ford_escape_2008_responses.json'
    )
    with open(fixture_path, 'r') as f:
        return json.load(f)

fixtures = load_fixtures()
```

### Example: Testing DTC Parser

```python
def test_dtc_parser_no_codes():
    """Test DTC parsing when no codes present"""
    fixtures = load_fixtures()
    
    # Get real vehicle response
    response = fixtures['dtc_commands']['03']['response']
    
    # Parse it
    dtcs = parse_dtc_response(response)
    
    # Verify
    assert response == '43 00'
    assert len(dtcs) == 0
    assert fixtures['dtc_commands']['03']['dtc_count'] == 0
```

### Example: Testing Live Data Parser

```python
def test_coolant_temperature_parsing():
    """Test coolant temperature parsing"""
    fixtures = load_fixtures()
    
    # Get real response
    response = fixtures['live_data']['0105']['response']
    
    # Parse it
    temp_c = parse_temperature(response)
    
    # Verify
    assert response == '41 05 36'
    assert temp_c == 14  # 0x36 - 40 = 54 - 40 = 14°C
    assert fixtures['live_data']['0105']['value'] == '14°C'
```

### Example: Testing VIN Decoder

```python
def test_vin_decoding():
    """Test VIN decoding from multi-line response"""
    fixtures = load_fixtures()
    
    # Get real multi-line response
    response = fixtures['vehicle_info']['0902']['response']
    expected_vin = fixtures['vehicle_info']['0902']['decoded']
    
    # Decode it
    vin = decode_vin(response)
    
    # Verify
    assert vin == expected_vin
    assert vin == '1FMCU03Z68KB12969'
```

### Example: Testing Module Detection

```python
def test_module_accessibility():
    """Test module accessibility detection"""
    fixtures = load_fixtures()
    
    # PCM should be accessible
    pcm = fixtures['module_tests']['7E0_PCM']
    assert pcm['accessible'] == True
    assert pcm['test_response'] == '43 00'
    
    # HVAC should not be accessible
    hvac = fixtures['module_tests']['7A0_HVAC']
    assert hvac['accessible'] == False
    assert hvac['test_response'] == 'NO DATA'
    
    # ABS should respond but with error
    abs_module = fixtures['module_tests']['760_ABS']
    assert abs_module['accessible'] == False
    assert abs_module['test_response'] == '7F 03 11'
```

### Example: Testing Error Handling

```python
def test_service_not_supported():
    """Test handling of 'service not supported' response"""
    fixtures = load_fixtures()
    
    # Mode 0A returns service not supported
    response = fixtures['dtc_commands']['0A']['response']
    
    # Should handle gracefully
    result = parse_dtc_response(response)
    
    assert response == '7F 0A 11'
    assert result['error'] == 'Service not supported'
    assert fixtures['dtc_commands']['0A']['error'] == 'Service not supported'
```

## Test Scenarios

The fixtures include pre-defined test scenarios:

### 1. No DTCs Present
```python
scenario = fixtures['test_scenarios']['no_dtcs_present']
assert scenario['commands']['03'] == '43 00'
assert scenario['commands']['07'] == '47 00'
```

### 2. Engine Off, Ignition On
```python
scenario = fixtures['test_scenarios']['engine_off_ignition_on']
assert scenario['commands']['010C'] == '41 0C 00 00'  # 0 RPM
assert scenario['commands']['010D'] == '41 0D 00'      # 0 km/h
```

### 3. Full Fuel Tank
```python
scenario = fixtures['test_scenarios']['full_fuel_tank']
assert scenario['commands']['012F'] == '41 2F FC'  # 99.2% full
```

## Mock ELM327 Adapter

You can use these fixtures to create a mock ELM327 adapter for testing:

```python
class MockELM327:
    """Mock ELM327 adapter using real vehicle responses"""
    
    def __init__(self):
        self.fixtures = load_fixtures()
    
    def send_obd_command(self, command):
        """Return real vehicle response for command"""
        
        # Check live data
        if command in self.fixtures['live_data']:
            return self.fixtures['live_data'][command]['response']
        
        # Check DTC commands
        if command in ['03', '07', '0A']:
            return self.fixtures['dtc_commands'][command]['response']
        
        # Check supported PIDs
        if command in self.fixtures['supported_pids']:
            return self.fixtures['supported_pids'][command]
        
        # Check vehicle info
        for pid, data in self.fixtures['vehicle_info'].items():
            if command == pid:
                return data['response']
        
        return 'NO DATA'
    
    def get_voltage(self):
        """Return real voltage"""
        return self.fixtures['adapter']['voltage']

# Usage in tests
def test_with_mock_adapter():
    adapter = MockELM327()
    
    # Test as if connected to real vehicle
    response = adapter.send_obd_command('0105')
    assert response == '41 05 36'
    
    voltage = adapter.get_voltage()
    assert voltage == 11.4
```

## Property-Based Testing

These fixtures are also useful for property-based testing:

```python
from hypothesis import given, strategies as st

@given(st.sampled_from(list(fixtures['live_data'].keys())))
def test_all_live_data_parseable(pid):
    """Property: All live data responses should parse without error"""
    response = fixtures['live_data'][pid]['response']
    
    # Should not raise exception
    result = parse_obd_response(response)
    
    # Should return valid data
    assert result is not None
    assert 'error' not in result
```

## Data Integrity

All responses in these fixtures are:
- ✅ Real responses from actual vehicle
- ✅ Collected under controlled conditions
- ✅ Verified for correctness
- ✅ Documented with metadata
- ✅ Ready for immediate use in tests

## Limitations

- Data collected with engine OFF, ignition ON
- No DTCs present (vehicle in good condition)
- No freeze frame data (only present when DTCs exist)
- Some PIDs return zero values (RPM, speed, MAF) due to engine being off
- Battery voltage low (11.4V) due to engine not running

## Adding New Fixtures

When adding new fixtures:

1. Collect data using `collect_vehicle_data.py`
2. Verify data quality
3. Add to appropriate category in JSON
4. Include metadata (date, conditions, vehicle state)
5. Document any special conditions
6. Update this README

## Related Files

- `knowledge_base/vehicle_data_20260214_185442.json` - Raw collection data
- `knowledge_base/Ford_Escape_2008_technical.dat` - Technical specifications
- `knowledge_base/Ford_Escape_2008_profile.yaml` - Vehicle profile
- `VEHICLE_DATA_COLLECTION_REPORT.md` - Detailed analysis
- `DATA_COLLECTION_SUMMARY.md` - Quick summary
