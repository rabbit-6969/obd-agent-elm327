#!/usr/bin/env python3
"""
Jeep Wrangler JK - Emissions Readiness Check
Complete emissions system diagnostic for inspection/testing
"""

import obd
import time

def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def print_section(title):
    print(f"\n{title}")
    print("-" * 60)

def main():
    print_header("2007 Jeep Wrangler JK - Emissions Diagnostic")
    
    print("\nConnecting to COM4...")
    try:
        connection = obd.OBD("COM4", fast=False, timeout=10)
        
        if not connection.is_connected():
            print("✗ Failed to connect")
            print("Make sure:")
            print("  • Adapter is plugged into OBD-II port")
            print("  • Ignition is ON")
            print("  • Adapter LED is blinking")
            return
        
        print(f"✓ Connected!")
        print(f"  Protocol: {connection.protocol_name()}")
        print(f"  Port: {connection.port_name()}")
        
        # ============================================================
        # EMISSIONS-RELATED DIAGNOSTIC TROUBLE CODES
        # ============================================================
        print_header("EMISSIONS DIAGNOSTIC TROUBLE CODES")
        
        # Read stored DTCs
        response = connection.query(obd.commands.GET_DTC)
        
        if response.is_null():
            print("✗ Could not read DTCs")
        else:
            dtcs = response.value
            
            if not dtcs or len(dtcs) == 0:
                print("✓ NO EMISSIONS CODES - PASS")
                print("  No stored diagnostic trouble codes")
            else:
                print(f"⚠ FOUND {len(dtcs)} CODE(S) - MAY FAIL INSPECTION\n")
                
                p_codes = []
                other_codes = []
                
                for code, description in dtcs:
                    if code.startswith('P'):
                        p_codes.append((code, description))
                    else:
                        other_codes.append((code, description))
                
                if p_codes:
                    print("POWERTRAIN CODES (Emissions-related):")
                    for code, desc in p_codes:
                        print(f"  {code}: {desc}")
                
                if other_codes:
                    print("\nOTHER CODES (Not emissions-related):")
                    for code, desc in other_codes:
                        print(f"  {code}: {desc}")
                
                print("\n⚠ Vehicle will likely FAIL emissions test with P-codes")
        
        # ============================================================
        # MONITOR READINESS STATUS
        # ============================================================
        print_header("EMISSIONS MONITOR READINESS")
        print("\nChecking OBD-II monitor status...")
        print("(Monitors must be 'Ready' to pass emissions test)")
        
        response = connection.query(obd.commands.STATUS)
        
        if response.is_null():
            print("✗ Could not read monitor status")
        else:
            status = response.value
            
            # MIL (Check Engine Light) status
            print_section("Malfunction Indicator Lamp (MIL)")
            if hasattr(status, 'MIL'):
                if status.MIL:
                    print("⚠ CHECK ENGINE LIGHT: ON - WILL FAIL")
                else:
                    print("✓ CHECK ENGINE LIGHT: OFF - PASS")
            
            # DTC count
            if hasattr(status, 'DTC_count'):
                print(f"  Stored DTC Count: {status.DTC_count}")
            
            # Monitor status
            print_section("Emissions Monitor Status")
            
            # Monitors that must be ready for 2007 Jeep Wrangler
            monitors = [
                ('Misfire', 'MISFIRE_MONITORING'),
                ('Fuel System', 'FUEL_SYSTEM_MONITORING'),
                ('Components', 'COMPONENT_MONITORING'),
                ('Catalyst', 'CATALYST_MONITORING'),
                ('Heated Catalyst', 'HEATED_CATALYST_MONITORING'),
                ('Evaporative System', 'EVAPORATIVE_SYSTEM_MONITORING'),
                ('Secondary Air', 'SECONDARY_AIR_SYSTEM_MONITORING'),
                ('Oxygen Sensor', 'OXYGEN_SENSOR_MONITORING'),
                ('Oxygen Sensor Heater', 'OXYGEN_SENSOR_HEATER_MONITORING'),
                ('EGR System', 'EGR_SYSTEM_MONITORING'),
            ]
            
            ready_count = 0
            not_ready_count = 0
            not_supported_count = 0
            
            for name, attr in monitors:
                if hasattr(status, attr):
                    monitor_status = getattr(status, attr)
                    
                    if monitor_status is None:
                        print(f"  {name:25} NOT SUPPORTED")
                        not_supported_count += 1
                    elif monitor_status:
                        print(f"  {name:25} ✓ READY")
                        ready_count += 1
                    else:
                        print(f"  {name:25} ✗ NOT READY")
                        not_ready_count += 1
            
            # Summary
            print_section("Monitor Summary")
            print(f"  Ready: {ready_count}")
            print(f"  Not Ready: {not_ready_count}")
            print(f"  Not Supported: {not_supported_count}")
            
            if not_ready_count > 0:
                print("\n⚠ MONITORS NOT READY - MAY FAIL INSPECTION")
                print("\nTo set monitors to 'Ready':")
                print("  1. Fix any DTCs first")
                print("  2. Clear codes (if repairs done)")
                print("  3. Drive vehicle through complete drive cycle")
                print("  4. See drive cycle instructions below")
            else:
                print("\n✓ ALL MONITORS READY - PASS")
        
        # ============================================================
        # FREEZE FRAME DATA
        # ============================================================
        print_header("FREEZE FRAME DATA")
        print("(Snapshot of conditions when DTC was set)")
        
        response = connection.query(obd.commands.FREEZE_DTC)
        
        if response.is_null() or not response.value:
            print("✓ No freeze frame data (no recent faults)")
        else:
            print(f"Freeze Frame DTC: {response.value}")
            
            # Try to get freeze frame parameters
            freeze_commands = [
                (obd.commands.FUEL_STATUS, "Fuel System Status"),
                (obd.commands.ENGINE_LOAD, "Engine Load"),
                (obd.commands.COOLANT_TEMP, "Coolant Temperature"),
                (obd.commands.SHORT_FUEL_TRIM_1, "Short Term Fuel Trim"),
                (obd.commands.LONG_FUEL_TRIM_1, "Long Term Fuel Trim"),
                (obd.commands.RPM, "Engine RPM"),
                (obd.commands.SPEED, "Vehicle Speed"),
            ]
            
            print("\nConditions when fault occurred:")
            for cmd, name in freeze_commands:
                try:
                    resp = connection.query(cmd)
                    if not resp.is_null():
                        print(f"  {name}: {resp.value}")
                except:
                    pass
        
        # ============================================================
        # OXYGEN SENSOR DATA
        # ============================================================
        print_header("OXYGEN SENSOR DATA")
        print("(Critical for emissions control)")
        
        o2_sensors = [
            (obd.commands.O2_B1S1, "Bank 1 Sensor 1 (Upstream)"),
            (obd.commands.O2_B1S2, "Bank 1 Sensor 2 (Downstream)"),
        ]
        
        for cmd, name in o2_sensors:
            try:
                response = connection.query(cmd)
                if not response.is_null():
                    print(f"\n{name}:")
                    print(f"  Voltage: {response.value}")
                else:
                    print(f"\n{name}: No data")
            except:
                print(f"\n{name}: Not available")
        
        # ============================================================
        # FUEL SYSTEM STATUS
        # ============================================================
        print_header("FUEL SYSTEM STATUS")
        
        response = connection.query(obd.commands.FUEL_STATUS)
        if not response.is_null():
            print(f"Status: {response.value}")
            
            # Fuel trims (should be near 0%)
            print("\nFuel Trim Values:")
            print("(Should be between -10% and +10% for healthy system)")
            
            trims = [
                (obd.commands.SHORT_FUEL_TRIM_1, "Short Term Fuel Trim Bank 1"),
                (obd.commands.LONG_FUEL_TRIM_1, "Long Term Fuel Trim Bank 1"),
            ]
            
            for cmd, name in trims:
                try:
                    resp = connection.query(cmd)
                    if not resp.is_null():
                        value = resp.value.magnitude
                        status = "✓ GOOD" if -10 <= value <= 10 else "⚠ CHECK"
                        print(f"  {name}: {value:.1f}% {status}")
                except:
                    pass
        
        # ============================================================
        # CATALYST TEMPERATURE
        # ============================================================
        print_header("CATALYST TEMPERATURE")
        
        cat_temps = [
            (obd.commands.CATALYST_TEMP_B1S1, "Bank 1 Sensor 1"),
            (obd.commands.CATALYST_TEMP_B1S2, "Bank 1 Sensor 2"),
        ]
        
        for cmd, name in cat_temps:
            try:
                response = connection.query(cmd)
                if not response.is_null():
                    print(f"{name}: {response.value}")
            except:
                pass
        
        # ============================================================
        # EVAPORATIVE SYSTEM
        # ============================================================
        print_header("EVAPORATIVE EMISSION SYSTEM")
        
        try:
            response = connection.query(obd.commands.EVAP_VAPOR_PRESSURE)
            if not response.is_null():
                print(f"Vapor Pressure: {response.value}")
        except:
            print("Vapor pressure data not available")
        
        # ============================================================
        # CURRENT ENGINE DATA
        # ============================================================
        print_header("CURRENT ENGINE DATA")
        
        current_data = [
            (obd.commands.RPM, "Engine RPM"),
            (obd.commands.SPEED, "Vehicle Speed"),
            (obd.commands.COOLANT_TEMP, "Coolant Temperature"),
            (obd.commands.INTAKE_TEMP, "Intake Air Temperature"),
            (obd.commands.THROTTLE_POS, "Throttle Position"),
            (obd.commands.ENGINE_LOAD, "Engine Load"),
            (obd.commands.MAF, "Mass Air Flow"),
            (obd.commands.INTAKE_PRESSURE, "Intake Manifold Pressure"),
            (obd.commands.TIMING_ADVANCE, "Timing Advance"),
        ]
        
        for cmd, name in current_data:
            try:
                response = connection.query(cmd)
                if not response.is_null():
                    print(f"  {name}: {response.value}")
            except:
                pass
        
        # ============================================================
        # EMISSIONS TEST READINESS SUMMARY
        # ============================================================
        print_header("EMISSIONS TEST READINESS SUMMARY")
        
        # Re-check key items
        dtc_response = connection.query(obd.commands.GET_DTC)
        status_response = connection.query(obd.commands.STATUS)
        
        pass_items = []
        fail_items = []
        warning_items = []
        
        # Check DTCs
        if not dtc_response.is_null():
            dtcs = dtc_response.value
            if not dtcs or len(dtcs) == 0:
                pass_items.append("No stored DTCs")
            else:
                p_count = sum(1 for code, _ in dtcs if code.startswith('P'))
                if p_count > 0:
                    fail_items.append(f"{p_count} Powertrain DTC(s) stored")
        
        # Check MIL
        if not status_response.is_null():
            status = status_response.value
            if hasattr(status, 'MIL'):
                if status.MIL:
                    fail_items.append("Check Engine Light is ON")
                else:
                    pass_items.append("Check Engine Light is OFF")
        
        # Print summary
        if pass_items:
            print("\n✓ PASS:")
            for item in pass_items:
                print(f"  • {item}")
        
        if fail_items:
            print("\n✗ FAIL:")
            for item in fail_items:
                print(f"  • {item}")
        
        if warning_items:
            print("\n⚠ WARNING:")
            for item in warning_items:
                print(f"  • {item}")
        
        # Final verdict
        print_section("FINAL VERDICT")
        if fail_items:
            print("⚠ VEHICLE WILL LIKELY FAIL EMISSIONS TEST")
            print("\nAction Required:")
            print("  1. Diagnose and repair all DTCs")
            print("  2. Clear codes after repairs")
            print("  3. Complete drive cycle to set monitors")
            print("  4. Re-test before inspection")
        elif warning_items:
            print("⚠ VEHICLE MAY FAIL EMISSIONS TEST")
            print("\nRecommendation: Complete drive cycle before test")
        else:
            print("✓ VEHICLE SHOULD PASS EMISSIONS TEST")
            print("\nAll systems ready for inspection!")
        
        # ============================================================
        # DRIVE CYCLE INSTRUCTIONS
        # ============================================================
        print_header("JEEP WRANGLER DRIVE CYCLE")
        print("\nTo set all monitors to 'Ready' after clearing codes:")
        print("\n1. COLD START")
        print("   • Engine must be cold (coolant < 122°F)")
        print("   • Start engine and let idle for 2-3 minutes")
        
        print("\n2. IDLE PHASE")
        print("   • Idle for 2.5 minutes with A/C and rear defrost ON")
        
        print("\n3. ACCELERATION")
        print("   • Accelerate to 40-55 mph at 1/2 throttle")
        print("   • Maintain steady speed for 5 minutes")
        
        print("\n4. DECELERATION")
        print("   • Release throttle (coast down, don't brake)")
        print("   • Coast for 20 seconds")
        
        print("\n5. REPEAT")
        print("   • Repeat steps 3-4 at least 4 times")
        
        print("\n6. CITY DRIVING")
        print("   • Drive in stop-and-go traffic for 10 minutes")
        print("   • Include several stops and accelerations")
        
        print("\n7. HIGHWAY DRIVING")
        print("   • Drive at 55-65 mph for 10 minutes")
        print("   • Maintain steady speed")
        
        print("\n8. VERIFICATION")
        print("   • Run this script again to check monitor status")
        print("   • All monitors should show 'Ready'")
        
        print("\nNOTE: Drive cycle may take 50-100 miles to complete")
        print("      Some monitors may require multiple drive cycles")
        
        # Close connection
        connection.close()
        print_header("DIAGNOSTIC COMPLETE")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
