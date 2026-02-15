# Testing Quick Start Guide

This guide shows you how to use the collected vehicle data for testing.

## What We Have

✅ **Real vehicle responses** from 2008 Ford Escape  
✅ **Test fixtures** ready to use  
✅ **Knowledge base** updated with real data  
✅ **Documentation** comprehensive and detailed

## Files You Need

```
tests/fixtures/ford_escape_2008_responses.json  ← Main test fixtures
knowledge_base/Ford_Escape_2008_technical.dat   ← Technical specs
knowledge_base/Ford_Escape_2008_profile.yaml    ← Vehicle profile
```

## Quick Examples

### 1. Load Test Fixtures

```python
import json

with open('tests/fixtures/ford_escape_2008_responses.json') as f:
    fixtures = json.load(f)

# Now you have real vehicle responses!
print(fixtures['vehicle']['vin'])  # 1FMCU03Z68KB12969
```

### 2. Test DTC Parsing

```python
# Get real "no DTCs" response
response = fixtures['dtc_commands']['03']['response']
# Response: '43 00'

# Your parser should handle this
dtcs = your_dtc_parser(response)
assert len(dtcs) == 0
```

### 3. Test Temperature Conversion

```python
# Get real coolant temperature response
response = fixtures['live_data']['0105']['response']
# Response: '41 05 36'

# Your parser should convert correctly
temp = your_temp_parser(response)
assert temp == 14  # 0x36 - 40 = 14°C
```

### 4. Test VIN Decoding

```python
# Get real multi-line VIN response
response = fixtures['vehicle_info']['0902']['response']
expected = fixtures['vehicle_info']['0902']['decoded']

# Your decoder should extract VIN
vin = your_vin_decoder(response)
assert vin == '1FMCU03Z68KB12969'
```

### 5. Test Module Detection

```python
# PCM should be accessible
pcm = fixtures['module_tests']['7E0_PCM']
assert pcm['accessible'] == True

# HVAC should not be accessible
hvac = fixtures['module_tests']['7A0_HVAC']
assert hvac['accessible'] == False
```

## Create Mock Adapter

```python
class MockELM327:
    """Mock adapter using real responses"""
    
    def __init__(self):
        with open('tests/fixtures/ford_escape_2008_responses.json') as f:
            self.fixtures = json.load(f)
    
    def send_obd_command(self, cmd):
        # Return real response for command
        if cmd in self.fixtures['live_data']:
            return self.fixtures['live_data'][cmd]['response']
        if cmd in ['03', '07', '0A']:
            return self.fixtures['dtc_commands'][cmd]['response']
        return 'NO DATA'

# Use in tests
adapter = MockELM327()
response = adapter.send_obd_command('0105')
# Returns: '41 05 36' (real vehicle response!)
```

## Test Scenarios Included

### ✅ No DTCs Present
```python
scenario = fixtures['test_scenarios']['no_dtcs_present']
# Mode 03: '43 00'
# Mode 07: '47 00'
```

### ✅ Engine Off, Ignition On
```python
scenario = fixtures['test_scenarios']['engine_off_ignition_on']
# RPM: '41 0C 00 00' (0 RPM)
# Speed: '41 0D 00' (0 km/h)
```

### ✅ Service Not Supported
```python
response = fixtures['dtc_commands']['0A']['response']
# Returns: '7F 0A 11'
# Your code should handle this gracefully
```

## What You Can Test

### ✅ Unit Tests
- DTC parsing (no codes, pending codes, permanent codes)
- Live data parsing (20 different PIDs)
- Temperature conversion (3 temperature PIDs)
- Voltage calculation
- VIN decoding (multi-line response)
- Module detection
- Error handling

### ✅ Integration Tests
- Full diagnostic workflow
- Agent query processing
- Module accessibility detection
- Graceful error handling

### ✅ Property-Based Tests
- All responses parse without error
- Temperature values in valid range
- Voltage values in valid range
- Response format validation

## Example Test File

```python
# tests/test_dtc_parser.py
import json
import pytest

@pytest.fixture
def fixtures():
    with open('tests/fixtures/ford_escape_2008_responses.json') as f:
        return json.load(f)

def test_no_dtcs(fixtures):
    """Test parsing when no DTCs present"""
    response = fixtures['dtc_commands']['03']['response']
    dtcs = parse_dtc_response(response)
    
    assert response == '43 00'
    assert len(dtcs) == 0

def test_service_not_supported(fixtures):
    """Test handling service not supported"""
    response = fixtures['dtc_commands']['0A']['response']
    result = parse_dtc_response(response)
    
    assert response == '7F 0A 11'
    assert 'error' in result
    assert result['error'] == 'Service not supported'

def test_coolant_temperature(fixtures):
    """Test temperature parsing"""
    response = fixtures['live_data']['0105']['response']
    temp = parse_temperature(response)
    
    assert response == '41 05 36'
    assert temp == 14  # 0x36 - 40 = 14°C

def test_vin_decoding(fixtures):
    """Test VIN decoding"""
    response = fixtures['vehicle_info']['0902']['response']
    vin = decode_vin(response)
    
    assert vin == '1FMCU03Z68KB12969'
```

## Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_dtc_parser.py

# Run with coverage
pytest --cov=toolkit tests/

# Run verbose
pytest -v tests/
```

## Next Steps

1. ✅ Data collected
2. ✅ Fixtures created
3. ⏭️ Write unit tests (use examples above)
4. ⏭️ Write integration tests
5. ⏭️ Write property-based tests
6. ⏭️ Run tests and verify

## Need Help?

- See `tests/fixtures/README.md` for detailed fixture documentation
- See `VEHICLE_DATA_COLLECTION_REPORT.md` for data analysis
- See `DATA_COLLECTION_SUMMARY.md` for quick reference
- See `.kiro/specs/ai-vehicle-diagnostic-agent/tasks.md` for task list

## Key Points

✅ All responses are REAL data from actual vehicle  
✅ Data collected under controlled conditions  
✅ Fixtures organized and documented  
✅ Ready to use immediately  
✅ No vehicle connection needed for testing  

**You can now write tests without connecting to the vehicle!**
