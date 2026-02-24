# Ford Escape - Diagnostic Quick Reference Guide

## Quick PID Lookup by Symptom

### Engine Performance Issues

#### Poor Acceleration / Loss of Power
**Check these PIDs:**
- `ESCAPE_RPM` - Verify engine responds to throttle
- `ESCAPE_ENG_LOAD_ACT` - Should increase under acceleration
- `ESCAPE_ACC_POS` vs `ESCAPE_ETC_ANG_ACT` - Throttle response
- `ESCAPE_MAP` - Intake manifold pressure (low = vacuum leak)
- `ESCAPE_STFT` / `ESCAPE_LTFT` - Fuel trim issues
- `ESCAPE_VCT_INT_ERR` / `ESCAPE_VCT_EXH_ERR` - VCT problems

**Turbocharged Models Add:**
- `ESCAPE_TIP_ABS` vs `ESCAPE_TIP_DES_ABS` - Boost pressure
- `ESCAPE_WGDC` - Wastegate control
- `ESCAPE_CAT` - Charge air temperature

#### Rough Idle / Stalling
**Check these PIDs:**
- `ESCAPE_RPM` - Should be 600-750 rpm
- `ESCAPE_ETC_ANG_ACT` - Idle throttle position
- `ESCAPE_MAP` - Manifold vacuum (should be 18-22 inHg)
- `ESCAPE_STFT` / `ESCAPE_LTFT` - Fuel compensation
- `ESCAPE_VCT_INT_ACT` - Cam timing at idle
- `ESCAPE_IAT_ALT2` - Intake air temp
- `ESCAPE_ECT` - Coolant temperature

#### Engine Hesitation / Stumble
**Check these PIDs:**
- `ESCAPE_ACC_POS` - Pedal input
- `ESCAPE_ETC_ANG_DES` vs `ESCAPE_ETC_ANG_ACT` - Throttle lag
- `ESCAPE_STFT` - Should respond quickly
- `ESCAPE_MAP` - Manifold pressure response
- `ESCAPE_IGN_TIM_CYL1` - Ignition timing
- `ESCAPE_TRQ_CTRL_REQ` - Torque reduction requests

### Fuel System Diagnostics

#### Running Rich (Black Smoke, Poor MPG)
**Check these PIDs:**
- `ESCAPE_STFT` - Negative values indicate rich
- `ESCAPE_LTFT` - Negative values indicate chronic rich
- `ESCAPE_RO2_V` - Should be high (0.7-0.9V) if rich
- `ESCAPE_LPFP_ACT` - Excessive fuel pressure
- `ESCAPE_MAP` - High reading = boost leak or sensor issue
- `ESCAPE_IAT_ALT2` - Cold air = rich mixture

**Typical Rich Condition Values:**
- STFT: -15% to -25%
- LTFT: -10% to -20%
- O2 Sensor: >0.8V constantly

#### Running Lean (Rough Running, Codes)
**Check these PIDs:**
- `ESCAPE_STFT` - Positive values indicate lean
- `ESCAPE_LTFT` - Positive values indicate chronic lean
- `ESCAPE_RO2_V` - Should be low (0.1-0.3V) if lean
- `ESCAPE_LPFP_ACT` vs `ESCAPE_LPFP_DES` - Low fuel pressure
- `ESCAPE_LPFP_DUTY` - High duty = struggling pump
- `ESCAPE_MAP` - Low reading = vacuum leak
- `ESCAPE_EVAP_PURGE_CMD` - Excessive purge

**Typical Lean Condition Values:**
- STFT: +15% to +25%
- LTFT: +10% to +20%
- O2 Sensor: <0.2V constantly

#### Fuel Pressure Issues
**Check these PIDs:**
- `ESCAPE_LPFP_ACT` vs `ESCAPE_LPFP_DES` - Pressure deviation
- `ESCAPE_LPFP_DUTY` - >80% indicates weak pump
- `ESCAPE_LPFP_SENS_V` - Verify sensor operation
- `ESCAPE_HPFP_DES` - Direct injection pressure (EcoBoost)
- `ESCAPE_HPFP_V` - High pressure sensor

**Normal Values:**
- Low pressure: 40-60 psi
- High pressure (DI): 500-2500 psi
- Pump duty: 30-70% typical

### Ignition System

#### Misfire Diagnosis
**Check these PIDs:**
- `ESCAPE_PCM_MISF_ACCEL_CYL1_NORM` (and CYL2, 3, 4, 6)
- `ESCAPE_PCM_MISF_EVENTS_LATEST_CYC` - Recent misfire count
- `ESCAPE_IGN_TIM_CYL1` - Spark timing
- `ESCAPE_IGN_CORR_CYL1` - Timing correction (knock retard)
- `ESCAPE_STFT` / `ESCAPE_LTFT` - Fuel compensation
- `ESCAPE_KS1_RAW` / `ESCAPE_KS2_RAW` - Knock sensor activity

**Misfire Pattern Analysis:**
- Single cylinder high: Bad coil, plug, or injector
- Multiple cylinders: Fuel pressure, vacuum leak, timing
- Random misfires: Fuel quality, lean condition, vacuum leak
- Under load only: Weak coil, fouled plug, compression

#### Knock / Ping
**Check these PIDs:**
- `ESCAPE_KS1_RAW` / `ESCAPE_KS2_RAW` - Knock sensor signal
- `ESCAPE_IGN_CORR_CYL1` - Negative = timing retard
- `ESCAPE_PCM_CYL_1_KNK_COMB_PERF_CNT` - Knock event counter
- `ESCAPE_OAR` - Octane adaptation
- `ESCAPE_IAT_ALT2` - High intake temp causes knock
- `ESCAPE_ECT` - Overheating causes knock

**Normal vs Problem:**
- Occasional knock: Normal under heavy load
- Constant knock: Fuel quality, carbon buildup, timing issue
- Knock counter increasing: Investigate immediately

### Variable Valve Timing (VCT)

#### VCT Performance Issues
**Check these PIDs:**
- `ESCAPE_VCT_INT_ACT` vs `ESCAPE_VCT_INT_DES` - Intake cam error
- `ESCAPE_VCT_EXH_ACT` vs `ESCAPE_VCT_EXH_DES` - Exhaust cam error
- `ESCAPE_VCT_INT_ERR` - Should be <5 degrees
- `ESCAPE_VCT_EXH_ERR` - Should be <5 degrees
- `ESCAPE_VCT_INT_DUTY` - Solenoid control signal
- `ESCAPE_VCT_EXH_DUTY` - Solenoid control signal

**Diagnosis:**
- Error >10 degrees: Solenoid or phaser problem
- Duty cycle stuck at 0% or 100%: Solenoid failure
- Slow response: Low oil pressure, dirty oil
- No response: Electrical issue, solenoid failure

**Common VCT Codes:**
- P0011: Intake cam over-advanced
- P0012: Intake cam over-retarded
- P0021: Exhaust cam over-advanced
- P0022: Exhaust cam over-retarded

### Turbocharger System (EcoBoost)

#### Boost Issues
**Check these PIDs:**
- `ESCAPE_TIP_ABS` - Actual boost pressure
- `ESCAPE_TIP_DES_ABS` - Desired boost pressure
- `ESCAPE_WGDC` - Wastegate duty cycle
- `ESCAPE_MAP` - Manifold pressure
- `ESCAPE_CAT` - Charge air temperature
- `ESCAPE_BPV_OPEN` - Bypass valve status

**Low Boost Diagnosis:**
- WGDC at 100% but low boost: Boost leak, wastegate stuck open
- WGDC at 0%: Solenoid failure, electrical issue
- High charge air temp: Intercooler problem

**Overboost Diagnosis:**
- Boost exceeds desired: Wastegate stuck closed, control issue
- WGDC at 0% but high boost: Wastegate actuator failure

### Temperature Monitoring

#### Overheating
**Check these PIDs:**
- `ESCAPE_ECT` - Coolant temperature (>105°C = problem)
- `ESCAPE_PCM_CYL_HEAD_T_CORR` - Head temperature
- `ESCAPE_CAT_TEMP` - Catalyst temperature
- `ESCAPE_IAT_ALT2` - Intake air temperature
- `ESCAPE_CAT` - Charge air temperature (turbo)
- `ESCAPE_GRILL_SHUT_DC` - Active grill shutter position

**Normal Operating Temps:**
- Coolant: 85-95°C (185-203°F)
- Catalyst: 400-800°C under load
- Intake air: Ambient +10-30°C
- Charge air: 30-60°C (turbo)

#### Cold Running Issues
**Check these PIDs:**
- `ESCAPE_ECT` - Should reach 85°C within 10 minutes
- `ESCAPE_ERT` - Engine run time
- `ESCAPE_STFT` / `ESCAPE_LTFT` - Cold enrichment
- `ESCAPE_IAT_ALT2` - Intake air temperature
- `ESCAPE_GRILL_SHUT_DC` - Should be closed when cold

**Thermostat Stuck Open:**
- ECT stays below 80°C
- Long warm-up time (>15 minutes)
- Poor fuel economy
- Heater not hot

### Emissions System

#### Catalyst Efficiency
**Check these PIDs:**
- `ESCAPE_RO2_V` - Post-catalyst O2 sensor
- `ESCAPE_CAT_TEMP` - Catalyst temperature
- `ESCAPE_STFT` / `ESCAPE_LTFT` - Fuel control
- `ESCAPE_CL_LC` - Lambda correction

**Catalyst Failure Indicators:**
- Rear O2 sensor switching like front (0.1-0.9V)
- Catalyst temp too low (<300°C under load)
- P0420 / P0430 codes

#### EVAP System
**Check these PIDs:**
- `ESCAPE_EVAP_PURGE_CMD` - Purge valve duty cycle
- `ESCAPE_EVAP_V` - EVAP pressure sensor voltage
- `ESCAPE_STFT` - Should respond to purge

**EVAP Leak Detection:**
- Purge active but no STFT change: Purge valve stuck
- EVAP pressure not holding: System leak
- P0442, P0455, P0456 codes

### Maintenance Indicators

#### Oil Life & Pressure
**Check these PIDs:**
- `ESCAPE_PCM_ENG_OIL_LIFE_REM` - Remaining oil life %
- `ESCAPE_PCM_ENG_EOP_RAW` - Oil pressure (kPa)

**Normal Oil Pressure:**
- Cold idle: 200-400 kPa (29-58 psi)
- Hot idle: 100-200 kPa (14-29 psi)
- Cruising: 250-400 kPa (36-58 psi)

**Low Pressure Causes:**
- Worn oil pump
- Worn bearings
- Low oil level
- Wrong oil viscosity

#### Drive Cycle Tracking
**Check these PIDs:**
- `ESCAPE_DIST_DTC_CLR` - Distance since codes cleared
- `ESCAPE_MIL_DIST` - Distance with check engine light
- `ESCAPE_WARMUP_CLR` - Warm-up cycles since clear

**Readiness Monitor Completion:**
- Requires specific drive cycle
- Monitor with Mode 01 PID 01
- Some monitors need multiple cycles

## Common Diagnostic Scenarios

### Scenario 1: Check Engine Light - P0171 (System Too Lean Bank 1)

**Step 1: Verify the condition**
- Check `ESCAPE_STFT` - Should be positive (+15% or more)
- Check `ESCAPE_LTFT` - Should be positive (+10% or more)
- Check `ESCAPE_RO2_V` - Should be low (<0.3V)

**Step 2: Check for vacuum leaks**
- Monitor `ESCAPE_MAP` at idle - Should be 18-22 inHg
- Check `ESCAPE_ENG_LOAD_ACT` - Should be 15-25% at idle
- Look for MAP reading higher than expected

**Step 3: Check fuel delivery**
- Monitor `ESCAPE_LPFP_ACT` vs `ESCAPE_LPFP_DES`
- Check `ESCAPE_LPFP_DUTY` - High duty = weak pump
- Verify fuel pressure is 40-60 psi

**Step 4: Check MAF/MAP sensor**
- Compare `ESCAPE_MAP` with known good values
- Check `ESCAPE_MAP_V` - Should be 0.5-4.5V
- Verify sensor voltage changes with throttle

### Scenario 2: Poor Acceleration - Turbocharged Model

**Step 1: Verify boost system**
- Monitor `ESCAPE_TIP_ABS` under acceleration
- Compare with `ESCAPE_TIP_DES_ABS`
- Should see 15-20 psi boost under load

**Step 2: Check wastegate control**
- Monitor `ESCAPE_WGDC` - Should increase under load
- 0% duty = wastegate open (no boost)
- 100% duty = wastegate closed (max boost)

**Step 3: Check for boost leaks**
- Monitor `ESCAPE_CAT` - Charge air temperature
- High temp = possible intercooler issue
- Compare `ESCAPE_MAP` with `ESCAPE_TIP_ABS`

**Step 4: Check throttle response**
- Monitor `ESCAPE_ACC_POS` vs `ESCAPE_ETC_ANG_ACT`
- Should respond immediately
- Check `ESCAPE_TRQ_CTRL_REQ` for torque limiting

### Scenario 3: Rough Idle - VCT Equipped

**Step 1: Check VCT operation**
- Monitor `ESCAPE_VCT_INT_ERR` at idle
- Should be <5 degrees
- Check `ESCAPE_VCT_INT_DUTY` - Should be 30-70%

**Step 2: Check fuel trim**
- Monitor `ESCAPE_STFT` and `ESCAPE_LTFT`
- Should be -10% to +10%
- Large corrections indicate air/fuel issue

**Step 3: Check idle control**
- Monitor `ESCAPE_ETC_ANG_ACT` at idle
- Should be stable 3-8 degrees
- Check `ESCAPE_RPM` - Should be 600-750 rpm

**Step 4: Check for misfires**
- Monitor `ESCAPE_PCM_MISF_ACCEL_CYL1_NORM` (all cylinders)
- Check `ESCAPE_PCM_MISF_EVENTS_LATEST_CYC`
- Identify which cylinder(s) misfiring

## PID Access Methods

### Standard OBD-II (Mode 01)
Basic parameters available with any OBD-II scanner:
- Engine RPM
- Coolant temperature
- Fuel trim (short and long term)
- Engine load
- Throttle position
- O2 sensor voltages

### Ford Enhanced (Manufacturer-Specific)
Requires Ford-compatible scan tool:
- All ESCAPE_* parameters listed in this guide
- VCT positions and control
- Turbo boost parameters
- Detailed misfire data
- Oil life and pressure

### UDS Extended Session (Mode 0x22)
Requires advanced tool (FORScan, professional scanner):
- Transmission parameters (DIDs 0x0100-0x01FF)
- ABS parameters (DIDs 0x0200-0x02FF)
- Module-specific data
- Actuator tests

## Tool Recommendations

### Basic Diagnostics
- Any OBD-II scanner with live data
- Can read standard PIDs and DTCs
- Good for basic troubleshooting

### Advanced Diagnostics
- Ford-compatible scan tool (IDS, FDRS)
- FORScan (free, Windows-based)
- Professional multi-brand scanner with Ford protocols

### Required for Full Access
- FORScan with ELM327 or J2534 adapter
- Ford IDS (dealer tool)
- FDRS (Ford Diagnostic and Repair System)

## Data Logging Tips

### What to Log for Performance Issues
1. `ESCAPE_RPM`
2. `ESCAPE_ACC_POS`
3. `ESCAPE_ETC_ANG_ACT`
4. `ESCAPE_MAP` or `ESCAPE_TIP_ABS` (turbo)
5. `ESCAPE_STFT` and `ESCAPE_LTFT`
6. `ESCAPE_IGN_TIM_CYL1`
7. `ESCAPE_VCT_INT_ACT` and `ESCAPE_VCT_EXH_ACT`

### What to Log for Fuel System Issues
1. `ESCAPE_STFT` and `ESCAPE_LTFT`
2. `ESCAPE_LPFP_ACT` and `ESCAPE_LPFP_DES`
3. `ESCAPE_LPFP_DUTY`
4. `ESCAPE_RO2_V`
5. `ESCAPE_MAP`
6. `ESCAPE_EVAP_PURGE_CMD`

### What to Log for Misfire Issues
1. `ESCAPE_PCM_MISF_ACCEL_CYL1_NORM` (all cylinders)
2. `ESCAPE_IGN_TIM_CYL1`
3. `ESCAPE_IGN_CORR_CYL1`
4. `ESCAPE_STFT` and `ESCAPE_LTFT`
5. `ESCAPE_KS1_RAW`
6. `ESCAPE_RPM`

## Reference Values Summary

### Idle (Warm Engine)
- RPM: 600-750
- Coolant Temp: 85-95°C
- Throttle Angle: 3-8°
- MAP: 18-22 inHg (8-10 psi)
- STFT/LTFT: -10% to +10%
- Engine Load: 15-25%

### Cruising (55 mph, flat road)
- RPM: 1800-2200
- Throttle Angle: 10-20°
- MAP: 10-14 inHg
- Engine Load: 25-40%
- Fuel Trim: -5% to +5%

### Wide Open Throttle
- Throttle Angle: 85-90°
- MAP: 14-15 inHg (N/A), 18-25 psi (turbo)
- Engine Load: 85-100%
- Fuel Trim: May go rich (negative)
- Boost: 15-20 psi (turbo models)

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-15  
**Data Source:** Sidecar / OBDB Community  
**Applicable Models:** Ford Escape 2001-2024 (parameter availability varies)
