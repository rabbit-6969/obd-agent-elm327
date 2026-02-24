# Vgate iCar Pro BLE 4.0 - Bluetooth Pairing Guide

Complete step-by-step guide to pair your Vgate adapter with Windows.

## Before You Start

### What You Need:
- Vgate iCar Pro BLE 4.0 adapter
- Windows PC with Bluetooth
- 2007 Jeep Wrangler JK
- Vehicle ignition key

### Default Pairing Information:
- **Device Name**: Usually "Vgate iCar Pro" or "OBDII" or "V-LINK"
- **PIN Code**: `1234` or `0000` (try 1234 first)
- **Bluetooth Version**: BLE 4.0 (Bluetooth Low Energy)

---

## Step-by-Step Pairing (Windows 10/11)

### Step 1: Prepare the Adapter

1. **Plug adapter into vehicle OBD-II port**
   - Location: Under dashboard, left of steering column (above brake pedal)
   - Push firmly until it clicks into place
   - Adapter should be horizontal (not hanging down)

2. **Turn vehicle ignition to ON**
   - Insert key and turn to ON position
   - Engine does NOT need to be running
   - Dashboard lights should come on

3. **Wait for adapter to power up**
   - LED on adapter should start blinking
   - Blue LED = Bluetooth ready
   - Red LED = Power on
   - Wait 10-15 seconds for full startup

### Step 2: Enable Bluetooth on Windows

1. **Open Windows Settings**
   - Press `Windows Key + I`
   - Or click Start → Settings (gear icon)

2. **Go to Bluetooth settings**
   - Click "Devices"
   - Click "Bluetooth & other devices" in left menu
   - Turn Bluetooth ON (toggle switch)

### Step 3: Pair the Adapter

1. **Add Bluetooth device**
   - Click "+ Add Bluetooth or other device"
   - Select "Bluetooth" (first option)
   - Windows will start scanning

2. **Find your adapter**
   - Look for device named:
     - "Vgate iCar Pro"
     - "OBDII"
     - "V-LINK"
     - "ELM327"
     - Or similar OBD-II related name
   - Click on the device name

3. **Enter PIN code**
   - Windows will ask for PIN
   - Try: `1234` (most common)
   - If that fails, try: `0000`
   - Click "Connect" or "Pair"

4. **Wait for pairing**
   - Windows will show "Connecting..."
   - Should complete in 5-10 seconds
   - You'll see "Connected" when successful

### Step 4: Find COM Port Number

1. **Open Device Manager**
   - Press `Windows Key + X`
   - Select "Device Manager"

2. **Expand "Ports (COM & LPT)"**
   - Look for entry like:
     - "Standard Serial over Bluetooth link (COM5)"
     - "Bluetooth Serial Port (COM3)"
   - Note the COM port number (e.g., COM5)

3. **Write down the COM port**
   - You'll need this for the diagnostic script
   - Example: COM5, COM3, COM7, etc.

---

## Troubleshooting

### Adapter Not Showing Up

**Check adapter power:**
- Is LED blinking on adapter?
- Is vehicle ignition ON?
- Try unplugging and replugging adapter
- Wait 15 seconds after plugging in

**Check Bluetooth:**
- Is Bluetooth enabled on PC?
- Try turning Bluetooth OFF then ON again
- Restart Bluetooth service:
  ```
  Windows Key + R → services.msc
  Find "Bluetooth Support Service"
  Right-click → Restart
  ```

**Check adapter visibility:**
- Some adapters need button press to enter pairing mode
- Check if adapter has a button - press and hold 3 seconds
- LED should blink rapidly when in pairing mode

### PIN Code Not Working

Try these PINs in order:
1. `1234` (most common)
2. `0000`
3. `6789`
4. `1111`

If none work:
- Check adapter manual/packaging for correct PIN
- Some adapters have no PIN (just click "Pair" without entering code)

### Pairing Fails

**Remove old pairing:**
1. Go to Bluetooth settings
2. Find the adapter in device list
3. Click on it → "Remove device"
4. Wait 10 seconds
5. Try pairing again

**Reset adapter:**
1. Unplug adapter from vehicle
2. Wait 30 seconds
3. Plug back in
4. Wait for LED to blink
5. Try pairing again

**Restart Bluetooth:**
1. Turn Bluetooth OFF
2. Wait 10 seconds
3. Turn Bluetooth ON
4. Try pairing again

### Connected But Not Working

**Check COM port:**
1. Device Manager → Ports (COM & LPT)
2. Verify COM port exists
3. Note the number

**Test connection:**
1. Open Command Prompt
2. Type: `mode COM5` (replace COM5 with your port)
3. Should show port settings

**Update Bluetooth drivers:**
1. Device Manager → Bluetooth
2. Right-click on Bluetooth adapter
3. "Update driver"
4. "Search automatically for drivers"

---

## Alternative Pairing Methods

### Method 1: Using Command Line

```cmd
# Open Command Prompt as Administrator
# List Bluetooth devices
powershell Get-PnpDevice -Class Bluetooth

# Pair device (replace XX:XX:XX:XX:XX:XX with adapter MAC address)
powershell Add-BluetoothDevice -DeviceID "XX:XX:XX:XX:XX:XX"
```

### Method 2: Using Control Panel (Windows 10)

1. Open Control Panel
2. Hardware and Sound → Devices and Printers
3. Click "Add a device"
4. Select your adapter
5. Enter PIN when prompted

### Method 3: Using Bluetooth Tray Icon

1. Click Bluetooth icon in system tray (bottom-right)
2. "Add a Bluetooth Device"
3. Follow pairing wizard

---

## After Successful Pairing

### Verify Connection

1. **Check Bluetooth settings**
   - Adapter should show "Connected"
   - Status: "Paired"

2. **Check Device Manager**
   - COM port should be listed
   - No yellow warning icons

3. **Note your COM port**
   - Example: COM5
   - You'll need this for the script

### Update Diagnostic Script

Edit `jeep_wrangler_diagnostics.py` if auto-detect fails:

```python
# Around line 30, change:
self.connection = obd.OBD()

# To (replace COM5 with your port):
self.connection = obd.OBD("COM5")
```

### Test Connection

Run the diagnostic script:
```bash
python jeep_wrangler_diagnostics.py
```

Should see:
```
✓ Connected successfully!
  Protocol: ISO 15765-4 (CAN 11/500)
  Port: COM5
```

---

## Common Issues & Solutions

### Issue: "Device is paired but not connected"

**Solution:**
1. Right-click adapter in Bluetooth settings
2. Click "Connect"
3. Wait 5-10 seconds

### Issue: "COM port not found"

**Solution:**
1. Uninstall device from Device Manager
2. Unplug adapter from vehicle
3. Restart computer
4. Plug adapter back in
5. Pair again

### Issue: "Access denied to COM port"

**Solution:**
1. Close all programs using the port
2. Run Python script as Administrator
3. Check if another app is using the port:
   ```cmd
   netstat -ano | findstr :COM5
   ```

### Issue: "Adapter keeps disconnecting"

**Solution:**
1. Check vehicle battery voltage (should be >12V)
2. Disable power saving for Bluetooth:
   - Device Manager → Bluetooth adapter
   - Properties → Power Management
   - Uncheck "Allow computer to turn off this device"
3. Keep laptop closer to vehicle
4. Check for Bluetooth interference

---

## LED Status Indicators

### Vgate iCar Pro LED Meanings:

| LED Color | Pattern | Meaning |
|-----------|---------|---------|
| Blue | Slow blink | Bluetooth ready, not paired |
| Blue | Fast blink | Pairing mode active |
| Blue | Solid | Bluetooth connected |
| Red | Solid | Power on, no vehicle connection |
| Red | Blinking | Communicating with vehicle |
| Red + Blue | Alternating | Connected and active |

---

## Using Mobile App (Alternative)

If PC pairing is difficult, try mobile app first:

### Android:
1. Download "Torque Lite" (free)
2. Enable Bluetooth on phone
3. Pair adapter (same steps as PC)
4. Open Torque → Settings → OBD2 Adapter
5. Select your adapter
6. Test connection

### iOS:
1. Download "Car Scanner ELM OBD2" (free)
2. Enable Bluetooth
3. Pair adapter
4. Open app → Connect
5. Test connection

Once working on mobile, PC pairing should be easier.

---

## Quick Reference Card

```
┌─────────────────────────────────────────┐
│  VGATE PAIRING QUICK REFERENCE          │
├─────────────────────────────────────────┤
│  1. Plug adapter into OBD-II port       │
│  2. Turn ignition ON                    │
│  3. Wait for blue LED to blink          │
│  4. Windows Settings → Bluetooth        │
│  5. Add device → Bluetooth              │
│  6. Select "Vgate iCar Pro"             │
│  7. Enter PIN: 1234                     │
│  8. Note COM port in Device Manager     │
│  9. Run: python jeep_wrangler_diagnostics.py │
└─────────────────────────────────────────┘

Default PIN: 1234 (or 0000)
Device Name: Vgate iCar Pro / OBDII / V-LINK
```

---

## Next Steps After Pairing

1. ✓ Adapter paired successfully
2. ✓ COM port identified
3. → Run diagnostic script
4. → Read airbag codes
5. → Check shifter position
6. → Consider AlfaOBD for full access

---

## Support Resources

- **Vgate Support**: Check adapter packaging for support email
- **Windows Bluetooth Help**: Settings → Update & Security → Troubleshoot → Bluetooth
- **OBD-II Forums**: https://www.obdii.com/forums/
- **Jeep Forums**: https://www.jk-forum.com/

---

## Safety Notes

⚠️ **Important:**
- Never pair while driving
- Keep ignition ON during pairing
- Don't leave adapter plugged in when not in use (drains battery)
- Disconnect adapter after diagnostics complete

---

## Summary

**Successful pairing checklist:**
- [ ] Adapter plugged into OBD-II port
- [ ] Vehicle ignition ON
- [ ] Adapter LED blinking
- [ ] Bluetooth enabled on PC
- [ ] Device found in Bluetooth scan
- [ ] PIN entered correctly (1234)
- [ ] Device shows "Connected"
- [ ] COM port visible in Device Manager
- [ ] COM port number noted
- [ ] Ready to run diagnostic script

**Your COM port: ________** (write it here)

Now you're ready to run the diagnostic script!
