# Ford Escape - ECU Parameter Index

Quick reference for all 113 OBDB parameters organized by ECU address.

## ECU Address Overview

| ECU Address | Module Name | Parameters | Protocol |
|-------------|-------------|------------|----------|
| 0x720 | Instrument Panel Cluster (IPC) | 2 | MS-CAN (125 kbaud) |
| 0x726 | Body Control Module (BCM) | 10 | MS-CAN (125 kbaud) |
| 0x760 | Anti-Lock Brake System (ABS) | 9 | HS-CAN (500 kbaud) |
| 0x764 | Cruise Control Module | 1 | HS/MS-CAN |
| 0x7DF | OBD-II Broadcast | 1 | ISO 15765-4 |
| 0x7E0 | Powertrain Control Module (PCM) | 90 | HS-CAN (500 kbaud) |

## Response Address Mapping

CAN UDS uses request/response pairs. Response address = Request address + 8:

| Request | Response | Module |
|---------|----------|--------|
| 0x720 | 0x728 | IPC |
| 0x726 | 0x72E | BCM |
| 0x760 | 0x768 | ABS |
| 0x764 | 0x76C | Cruise Control |
| 0x7DF | 0x7E8 | Broadcast → PCM responds |
| 0x7E0 | 0x7E8 | PCM |

## 0x720 - Instrument Panel Cluster (2 parameters)

Display and warning indicators

| PID | Name | Status | Suggested Metric |
|-----|------|--------|------------------|
| ESCAPE_TPMS_WARN | Tire pressure warning | Debugging | - |
| ESCAPE_FLI_ALT | Fuel tank level | Production | fuelTankLevel |

## 0x726 - Body Control Module (10 parameters)

TPMS, battery management, odometer

| PID | Name | Status | Suggested Metric |
|-----|------|--------|------------------|
| ESCAPE_TP_FL | Front left tire pressure | Production | frontLeftTirePressure |
| ESCAPE_TP_FR | Front right tire pressure | Production | frontRightTirePressure |
| ESCAPE_TP_RRO | Rear right outer tire pressure | Production | rearRightTirePressure |
| ESCAPE_TP_RLO | Rear left outer tire pressure | Production | rearLeftTirePressure |
| ESCAPE_TP_RRI | Rear right inner tire pressure | Production | rearRightTirePressure |
| ESCAPE_TP_RLI | Rear left inner tire pressure | Production | rearLeftTirePressure |
| ESCAPE_BATT_AGE | Battery age | Production | - |
| ESCAPE_ODO_726 | Odometer | Production | odometer |
| ESCAPE_BATT_SOC | Battery charge | Production | - |
| ESCAPE_BATT_TEMP | Battery temperature | Production | - |

## 0x760 - Anti-Lock Brake System (9 parameters)

Wheel speeds, brake pressure, vehicle dynamics

| PID | Name | Status | Suggested Metric |
|-----|------|--------|------------------|
| ESCAPE_PARK_BRK | Parking brake | Production | - |
| ESCAPE_LAT_G | Lateral acceleration | Production | - |
| ESCAPE_FR_VSS | Front right wheel speed | Production | - |
| ESCAPE_FL_VSS | Front left wheel speed | Production | - |
| ESCAPE_RR_VSS | Rear right wheel speed | Production | - |
| ESCAPE_RL_VSS | Rear left wheel speed | Production | - |
| ESCAPE_LAT_ANGLE | Lateral angle | Production | - |
| ESCAPE_BRK_FL_P | Brake hydraulic pressure | Production | - |
| ESCAPE_STEER_ANGLE | Steering wheel angle | Production | - |

## 0x764 - Cruise Control Module (1 parameter)

| PID | Name | Status | Suggested Metric |
|-----|------|--------|------------------|
| ESCAPE_CC_TGT_VSS | Target speed | Production | - |

## 0x7DF - OBD-II Broadcast (1 parameter)

Standard OBD-II functional address. All compliant ECUs listen, appropriate ECU responds.

| PID | Name | Status | Suggested Metric |
|-----|------|--------|------------------|
| ESCAPE_TOT | Transmission oil temperature | Production | transmissionFluidTemperature |

**Note:** Request sent to 0x7DF, response comes from PCM at 0x7E8.

## 0x7E0 - Powertrain Control Module (90 parameters)

Engine, fuel, ignition, transmission, emissions

### Engine Performance (7 parameters)
- ESCAPE_RPM - Engine speed
- ESCAPE_ENG_LOAD_ACT - Engine load (actual)
- ESCAPE_ENG_LOAD_PCT - Engine load (percent)
- ESCAPE_PCM_ACT_ENG_PCT_TRQ - Actual engine percent torque
- ESCAPE_PCM_ENG_REFERENCE_TRQ - Engine reference torque
- ESCAPE_TRQ_CTRL_REQ - Torque request
- ESCAPE_ACC_POS - Accelerator position

### Fuel System (14 parameters)
- ESCAPE_STFT - Short term fuel trim
- ESCAPE_LTFT - Long term fuel trim
- ESCAPE_LPFP_ACT - Low pressure fuel pump (actual)
- ESCAPE_LPFP_DES - Low pressure fuel pump (desired)
- ESCAPE_LPFP_DUTY - Low pressure fuel pump duty cycle
- ESCAPE_LPFP_SENS_V - Low pressure fuel sensor voltage
- ESCAPE_HPFP_DES - High pressure fuel pump (desired)
- ESCAPE_HPFP_V - High pressure fuel rail sensor voltage
- ESCAPE_FLI - Fuel level
- ESCAPE_DTE - Distance to empty (calculated)
- ESCAPE_DTE_DISP - Distance to empty (displayed)
- ESCAPE_CL - Lambda (commanded) [Debugging]
- ESCAPE_CL_LC - Lambda correction
- ESCAPE_INJ_MODE - Injection mode

### Air Intake (11 parameters)
- ESCAPE_MAP - Manifold absolute pressure
- ESCAPE_MAP_V - MAP sensor voltage
- ESCAPE_IAT_ALT2 - Intake air temperature
- ESCAPE_IAT_SENS_V - IAT sensor voltage
- ESCAPE_IAT_FAULT - Intake temperature fault
- ESCAPE_MCT - Manifold charge temperature
- ESCAPE_CAT - Charge air temperature
- ESCAPE_CAT_SENS_V - Charge air temperature sensor voltage
- ESCAPE_BARO - Barometric pressure
- ESCAPE_BARO_V - Barometric pressure sensor voltage
- ESCAPE_GRILL_SHUT_DC - Grill shutter duty cycle

### Throttle Control (6 parameters)
- ESCAPE_ETC_ANG_ACT - Throttle angle (actual)
- ESCAPE_ETC_ANG_DES - Throttle angle (desired)
- ESCAPE_ETC_TRIM_LRN - Throttle control trim angle (learned)
- ESCAPE_TIP_ABS - Throttle inlet pressure
- ESCAPE_TIP_V - Throttle inlet pressure sensor voltage
- ESCAPE_TIP_DES_ABS - Throttle inlet pressure (desired)

### Turbocharger (2 parameters)
- ESCAPE_WGDC - Wastegate duty cycle
- ESCAPE_BPV_OPEN - Bypass valve

### Variable Valve Timing (8 parameters)
- ESCAPE_VCT_INT_ACT - Intake camshaft position (actual)
- ESCAPE_VCT_INT_DES - Intake camshaft position (desired)
- ESCAPE_VCT_INT_ERR - Intake camshaft position error
- ESCAPE_VCT_INT_DUTY - Intake camshaft solenoid duty cycle
- ESCAPE_VCT_EXH_ACT - Exhaust camshaft position (actual)
- ESCAPE_VCT_EXH_DES - Exhaust camshaft position (desired)
- ESCAPE_VCT_EXH_ERR - Exhaust camshaft position error
- ESCAPE_VCT_EXH_DUTY - Exhaust camshaft solenoid duty cycle

### Ignition System (9 parameters)
- ESCAPE_IGN_TIM_CYL1 - Ignition timing (cylinder 1)
- ESCAPE_IGN_CORR_CYL1 - Ignition correction (cylinder 1)
- ESCAPE_OAR - Octane adjustment
- ESCAPE_KS1_RAW - Knock sensor 1
- ESCAPE_KS2_RAW - Knock sensor 2
- ESCAPE_PCM_CYL_1_KNK_COMB_PERF_CNT - Knock counter (cylinder 1)
- ESCAPE_PCM_CYL_2_KNK_COMB_PERF_CNT - Knock counter (cylinder 2)
- ESCAPE_PCM_CYL_3_KNK_COMB_PERF_CNT - Knock counter (cylinder 3)
- ESCAPE_PCM_CYL_4_KNK_COMB_PERF_CNT - Knock counter (cylinder 4)

### Temperature Sensors (6 parameters)
- ESCAPE_ECT - Engine coolant temperature
- ESCAPE_PCM_CYL_HEAD_T_CORR - Cylinder head temperature (corrected)
- ESCAPE_PCM_CYL_HEAD_T_SENS_2_RAW - Cylinder head temperature sensor 2
- ESCAPE_CAT_TEMP - Catalyst temperature
- ESCAPE_AAT_V - Ambient air temperature sensor voltage
- ESCAPE_AAT_ALT - Ambient air temperature (alternate)

### Emissions (3 parameters)
- ESCAPE_RO2_V - Rear O2 sensor voltage
- ESCAPE_EVAP_V - Evaporative pressure sensor voltage
- ESCAPE_EVAP_PURGE_CMD - Evaporative purge

### Misfire Detection (6 parameters)
- ESCAPE_PCM_MISF_ACCEL_CYL1_NORM - Misfire acceleration (cylinder 1)
- ESCAPE_PCM_MISF_ACCEL_CYL2_NORM - Misfire acceleration (cylinder 2)
- ESCAPE_PCM_MISF_ACCEL_CYL3_NORM - Misfire acceleration (cylinder 3)
- ESCAPE_PCM_MISF_ACCEL_CYL4_NORM - Misfire acceleration (cylinder 4)
- ESCAPE_PCM_MISF_ACCEL_CYL6_NORM - Misfire acceleration (cylinder 6) [Debugging]
- ESCAPE_PCM_MISF_EVENTS_LATEST_CYC - Misfire events (latest cycle)

### Transmission (7 parameters)
- ESCAPE_GEAR - Current gear
- ESCAPE_GEAR_ENG - Engaged gear
- ESCAPE_GEAR_SHFT - Shift gear
- ESCAPE_PCM_CMD_TRANS_GEAR_RATIO - Commanded gear ratio
- ESCAPE_PCM_CMD_TRANS_MAIN_LINE_P - Commanded transmission line pressure
- ESCAPE_AXLE_GEAR_RATIO_MEAS - Measured axle gear ratio
- ESCAPE_VSS - Vehicle speed

### Climate Control (4 parameters)
- ESCAPE_AC_P - A/C compressor pressure
- ESCAPE_AC_P_SENS_V - A/C compressor pressure sensor voltage
- ESCAPE_PCM_A_C_REFRIG_P - A/C refrigerant pressure
- ESCAPE_AC_STATE - A/C compressor state

### Maintenance (5 parameters)
- ESCAPE_DIST_DTC_CLR - Distance since DTC clear
- ESCAPE_MIL_DIST - Distance with MIL
- ESCAPE_WARMUP_CLR - Warm-ups since DTC clear
- ESCAPE_PCM_ENG_OIL_LIFE_REM - Oil life remaining
- ESCAPE_PCM_ENG_EOP_RAW - Engine oil pressure

### Odometer (2 parameters)
- ESCAPE_PCM_VEH_ODO - Vehicle odometer (PCM)
- ESCAPE_ERT - Engine run time

## Suggested Metric Mappings (15 total)

For cross-platform API compatibility:

| Suggested Metric | Ford PID(s) | ECU |
|------------------|-------------|-----|
| speed | ESCAPE_VSS | 0x7E0 |
| engineLoad | ESCAPE_ENG_LOAD_ACT, ESCAPE_ENG_LOAD_PCT | 0x7E0 |
| engineCoolantTemperature | ESCAPE_ECT | 0x7E0 |
| shortTermFuelTrim | ESCAPE_STFT | 0x7E0 |
| fuelTankLevel | ESCAPE_FLI, ESCAPE_FLI_ALT | 0x7E0, 0x720 |
| fuelRange | ESCAPE_DTE, ESCAPE_DTE_DISP | 0x7E0 |
| odometer | ESCAPE_PCM_VEH_ODO, ESCAPE_ODO_726 | 0x7E0, 0x726 |
| transmissionFluidTemperature | ESCAPE_TOT | 0x7DF |
| frontLeftTirePressure | ESCAPE_TP_FL | 0x726 |
| frontRightTirePressure | ESCAPE_TP_FR | 0x726 |
| rearLeftTirePressure | ESCAPE_TP_RLO, ESCAPE_TP_RLI | 0x726 |
| rearRightTirePressure | ESCAPE_TP_RRO, ESCAPE_TP_RRI | 0x726 |

## Usage Notes

### Querying Specific ECUs

```python
# Query BCM for tire pressure
ecu_address = 0x726
command = bytes([0x22, 0xB0, 0x01])  # Read front left tire pressure
response_address = 0x72E  # BCM response

# Query PCM for engine RPM
ecu_address = 0x7E0
command = bytes([0x22, 0x0C])  # Read engine speed
response_address = 0x7E8  # PCM response
```

### Using Broadcast Address

```python
# Broadcast request (any ECU can respond)
ecu_address = 0x7DF
command = bytes([0x01, 0x05])  # Mode 01, PID 05 (coolant temp)
# Response will come from 0x7E8 (PCM)
```

### Multi-Module Parameters

Some parameters available from multiple ECUs for cross-checking:

- **Odometer**: Compare ESCAPE_ODO_726 (IPC) with ESCAPE_PCM_VEH_ODO (PCM) to detect tampering
- **Fuel Level**: Compare ESCAPE_FLI (PCM) with ESCAPE_FLI_ALT (IPC) for accuracy
- **Vehicle Speed**: Compare ESCAPE_VSS (PCM) with individual wheel speeds from ABS

## Diagnostic Scenarios by ECU

### BCM Diagnostics (0x726)
- TPMS system check: Read all 6 tire pressures + warning indicator
- Battery health: Monitor SOC, temperature, and age
- Odometer verification: Cross-check with PCM reading

### ABS Diagnostics (0x760)
- Wheel speed sensor check: Compare all 4 wheel speeds
- Brake system: Monitor hydraulic pressure and parking brake
- Vehicle dynamics: Check lateral G, yaw angle, steering angle

### PCM Diagnostics (0x7E0)
- Engine performance: RPM, load, torque
- Fuel system: Trim, pressure, injection mode
- Emissions: O2 sensors, catalyst temp, EVAP
- Transmission: Gear position, line pressure, fluid temp

## Data Source

- **Source**: OBDB Community
- **URL**: https://obdb.community/#/vehicles/Ford/Escape
- **Date**: February 15, 2026
- **Total Parameters**: 113
- **Status**: 111 Production, 2 Debugging

## Related Files

- `knowledge_base/Ford_Escape_OBDII_PIDs.yaml` - Complete parameter database
- `knowledge_base/Ford_Escape_UDS_Commands.yaml` - Low-level UDS specifications
- `scripts/obdb_batch_update_feb15.yaml` - Batch import template
- `knowledge_base/OBDB_EXTRACTION_SUMMARY.md` - Extraction process documentation
