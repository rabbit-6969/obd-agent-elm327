# Vehicle Discovery Documentation - Quick Reference

**Purpose:** Index of all vehicle capability discovery documentation

---

## 🚀 Quick Start

**Want to discover everything your vehicle can do?**

1. **Start here:** [VEHICLE_CAPABILITY_DISCOVERY.md](VEHICLE_CAPABILITY_DISCOVERY.md)
2. **Run the scanner:** `python discover_vehicle_capabilities.py --quick`
3. **Use the results:** [USING_DISCOVERED_CAPABILITIES.md](USING_DISCOVERED_CAPABILITIES.md)

---

## 📚 Documentation Files

### Discovery & Scanning

| File | Purpose | Read Time |
|------|---------|-----------|
| [VEHICLE_CAPABILITY_DISCOVERY.md](VEHICLE_CAPABILITY_DISCOVERY.md) | Complete guide to the discovery scanner | 10 min |
| [USING_DISCOVERED_CAPABILITIES.md](USING_DISCOVERED_CAPABILITIES.md) | How to use discovered DIDs, routines, actuations | 8 min |
| [TRANSMISSION_DATA_DISCOVERY.md](TRANSMISSION_DATA_DISCOVERY.md) | Transmission parameter discovery results | 5 min |

### Reference Documentation

| File | Purpose | Read Time |
|------|---------|-----------|
| [reference/ISO_14229-1_UDS_INDEX.md](reference/ISO_14229-1_UDS_INDEX.md) | Index of UDS protocol documentation | 3 min |
| [reference/ISO_14229-1_UDS_Service_0x22_ReadDataByIdentifier.md](reference/ISO_14229-1_UDS_Service_0x22_ReadDataByIdentifier.md) | Reading live data (DIDs) | 5 min |
| [reference/ISO_14229-1_UDS_Service_0x31_RoutineControl.md](reference/ISO_14229-1_UDS_Service_0x31_RoutineControl.md) | Running test routines | 5 min |
| [reference/ISO_14229-1_UDS_Service_0x2F_InputOutputControlByIdentifier.md](reference/ISO_14229-1_UDS_Service_0x2F_InputOutputControlByIdentifier.md) | Controlling actuators | 5 min |

### Knowledge Base

| File | Purpose | Read Time |
|------|---------|-----------|
| [knowledge_base/Ford_Escape_2008_profile.yaml](knowledge_base/Ford_Escape_2008_profile.yaml) | Vehicle profile and known parameters | 5 min |
| [knowledge_base/Ford_Escape_2008_technical.dat](knowledge_base/Ford_Escape_2008_technical.dat) | Technical data and command formats | 3 min |
| [KNOWLEDGE_ORGANIZATION.md](KNOWLEDGE_ORGANIZATION.md) | How knowledge base is organized | 3 min |

---

## 🎯 Common Tasks

### I want to...

**Discover all vehicle capabilities**
→ Run: `python discover_vehicle_capabilities.py --quick`
→ Read: [VEHICLE_CAPABILITY_DISCOVERY.md](VEHICLE_CAPABILITY_DISCOVERY.md)

**Read a specific parameter (DID)**
→ Read: [USING_DISCOVERED_CAPABILITIES.md](USING_DISCOVERED_CAPABILITIES.md#reading-dids-service-0x22)
→ Reference: [ISO_14229-1_UDS_Service_0x22](reference/ISO_14229-1_UDS_Service_0x22_ReadDataByIdentifier.md)

**Run a diagnostic test (routine)**
→ Read: [USING_DISCOVERED_CAPABILITIES.md](USING_DISCOVERED_CAPABILITIES.md#running-routines-service-0x31)
→ Reference: [ISO_14229-1_UDS_Service_0x31](reference/ISO_14229-1_UDS_Service_0x31_RoutineControl.md)

**Control an actuator**
→ Read: [USING_DISCOVERED_CAPABILITIES.md](USING_DISCOVERED_CAPABILITIES.md#controlling-actuations-service-0x2f)
→ Reference: [ISO_14229-1_UDS_Service_0x2F](reference/ISO_14229-1_UDS_Service_0x2F_InputOutputControlByIdentifier.md)

**Understand what was already discovered**
→ Read: [TRANSMISSION_DATA_DISCOVERY.md](TRANSMISSION_DATA_DISCOVERY.md)

---

## 🔧 Tools & Scripts

### Discovery Tools

| Script | Purpose | Time Required |
|--------|---------|---------------|
| `discover_vehicle_capabilities.py` | ⭐ Comprehensive scanner (all modules, DIDs, routines) | 30 min - 4 hours |
| `scan_transmission_dids.py` | Scan transmission DIDs only | 5-10 min |
| `read_transmission_live.py` | Monitor transmission parameters in real-time | Continuous |
| `read_transmission_data.py` | Read transmission parameters once | < 1 min |

### Usage Examples

```bash
# Quick scan (recommended first run)
python discover_vehicle_capabilities.py --quick

# Full comprehensive scan (several hours)
python discover_vehicle_capabilities.py --full

# Resume interrupted scan
python discover_vehicle_capabilities.py --resume

# Scan specific components
python discover_vehicle_capabilities.py --modules
python discover_vehicle_capabilities.py --dids
python discover_vehicle_capabilities.py --routines
```

---

## 📊 What Gets Discovered

### 1. Modules (ECUs)

The scanner discovers which modules are accessible:

- **PCM** (Powertrain Control Module) - Engine & transmission
- **ABS** (Anti-lock Braking System)
- **HVAC** (Climate Control)
- **BCM** (Body Control Module)
- **IPC** (Instrument Panel Cluster)
- And more...

### 2. DIDs (Data Identifiers)

Readable parameters for each module:

- Transmission fluid temperature
- Line pressure
- Gear position
- Solenoid states
- Sensor voltages
- And thousands more...

### 3. Routines (Test Procedures)

Executable diagnostic tests:

- Transmission self-test
- ABS pump test
- EVAP leak test
- Actuator calibration
- And more...

### 4. Actuations (Controllable Outputs)

Components you can control:

- Shift solenoids
- HVAC blend doors
- Relays
- Valves
- And more...

---

## 🎓 Learning Path

### Beginner

1. Read [TRANSMISSION_DATA_DISCOVERY.md](TRANSMISSION_DATA_DISCOVERY.md) to see what's already known
2. Run `python read_transmission_live.py` to see live data
3. Read [VEHICLE_CAPABILITY_DISCOVERY.md](VEHICLE_CAPABILITY_DISCOVERY.md) overview

### Intermediate

1. Run `python discover_vehicle_capabilities.py --quick`
2. Review the results in `vehicle_discovery/summary_*.txt`
3. Read [USING_DISCOVERED_CAPABILITIES.md](USING_DISCOVERED_CAPABILITIES.md)
4. Try reading some discovered DIDs

### Advanced

1. Run full scan: `python discover_vehicle_capabilities.py --full`
2. Study ISO documentation in `reference/`
3. Write custom diagnostic tools using discovered capabilities
4. Experiment with routines and actuations (safely!)

---

## ⚠️ Safety Notes

### Safe Operations

- ✅ Reading DIDs (Service 0x22) - Always safe
- ✅ Requesting routine results (Service 0x31 sub 0x03) - Safe
- ✅ Returning control to ECU (Service 0x2F sub 0x00) - Safe

### Caution Required

- ⚠️ Starting routines (Service 0x31 sub 0x01) - May affect vehicle
- ⚠️ Controlling actuators (Service 0x2F sub 0x03) - Directly controls outputs
- ⚠️ Always ensure vehicle is in PARK with parking brake engaged
- ⚠️ Never test while vehicle is in motion

---

## 📈 Results & Output

### After Running Scanner

You'll have:

1. **JSON Database** - `vehicle_discovery/vehicle_capabilities_*.json`
   - Complete machine-readable results
   - All discovered DIDs, routines, actuations
   - Organized by module

2. **Human Summary** - `vehicle_discovery/summary_*.txt`
   - Easy-to-read summary
   - Counts and statistics
   - Quick reference

3. **Progress File** - `vehicle_discovery/scan_progress.json`
   - Resume capability
   - Current scan state
   - Statistics

---

## 🔍 Example Discoveries

### Known Working DIDs (2008 Ford Escape)

| DID | Description | Formula | Module |
|-----|-------------|---------|--------|
| 0x0100 | Transmission Fluid Temperature | `(hex - 40) = °C` | PCM |
| 0x0101 | Transmission Line Pressure | TBD | PCM |

### Potential Discoveries

Based on FORScan, these parameters exist but DIDs are unknown:

- TR (Transmission Range)
- TCC_RAT (Torque Converter Clutch Ratio)
- TCIL (Trans Control Indicator Light)
- TFT_V (TFT sensor voltage)
- TR_V (TR voltage)
- TRAN_OT (Over Temperature)

**The scanner will find these!**

---

## 🚀 Next Steps

After discovery:

1. **Analyze Results**
   - Review JSON and summary files
   - Identify interesting parameters
   - Note which modules are accessible

2. **Update Knowledge Base**
   - Add discovered DIDs to `knowledge_base/Ford_Escape_2008_technical.dat`
   - Update `knowledge_base/Ford_Escape_2008_profile.yaml`
   - Document formulas and units

3. **Build Tools**
   - Create monitoring scripts for important parameters
   - Build diagnostic test procedures
   - Develop actuation test tools

4. **Share Findings**
   - Document discoveries
   - Help other Ford Escape owners
   - Contribute to open-source diagnostic tools

---

## 📞 Support & References

### Documentation

- [VEHICLE_CAPABILITY_DISCOVERY.md](VEHICLE_CAPABILITY_DISCOVERY.md) - Complete scanner guide
- [USING_DISCOVERED_CAPABILITIES.md](USING_DISCOVERED_CAPABILITIES.md) - Usage examples
- [reference/ISO_14229-1_UDS_INDEX.md](reference/ISO_14229-1_UDS_INDEX.md) - Protocol reference

### Tools

- `discover_vehicle_capabilities.py` - Main scanner
- `read_transmission_live.py` - Live monitoring
- `scan_transmission_dids.py` - Quick DID scan

### Knowledge Base

- `knowledge_base/` - Vehicle-specific data
- `reference/` - Universal protocols

---

**Ready to discover what your vehicle can do?**

Start with: `python discover_vehicle_capabilities.py --quick`

Then read: [USING_DISCOVERED_CAPABILITIES.md](USING_DISCOVERED_CAPABILITIES.md)

---

**Last Updated:** 2026-02-15
