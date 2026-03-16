"""
ELM327 Adapter Authenticity Checker

Detects whether the connected ELM327 adapter is a genuine chip or a clone
with limited functionality. Run once per session alongside VIN reading.

Detection methods (in order of reliability):
  1. AT AL  — the single most reliable test (clones return ? or nothing)
  2. AT I   — firmware version string (clones report v1.5 / v2.1 / garbage)
  3. AT @1  — device description (clones return empty / ?)
  4. AT PP 2F ON — protocol parameter (clones hang or return ?)
  5. AT CRA 7E8  — CAN receive address (clones return ? or fail)
  6. AT SH 7E0   — set CAN header (clones often fail)

Result levels:
  GENUINE   — all key tests pass, full functionality expected
  LIMITED   — some tests fail, reduced functionality (clone confirmed)
  UNKNOWN   — could not determine (adapter not responding properly)

Usage:
    from toolkit.vehicle_communication.adapter_checker import check_adapter, AdapterResult

    result = check_adapter(elm_serial_connection)
    if result.is_clone:
        print(result.user_message())
"""

import time
import re
from dataclasses import dataclass, field
from typing import Optional


# Firmware versions that are ONLY reported by clones (no official ELM release)
CLONE_FIRMWARE_VERSIONS = {"1.5", "2.1", "2.2", "3.0", "v1.5", "v2.1", "v2.2"}

# Firmware versions from genuine ELM Electronics chips
GENUINE_FIRMWARE_VERSIONS = {"1.0", "1.1", "1.2", "1.3", "1.3a", "1.4", "1.4b", "2.0"}


@dataclass
class AdapterCheckResult:
    """Result of adapter authenticity check"""

    # Raw test results
    firmware_version: Optional[str] = None      # from AT I
    device_description: Optional[str] = None    # from AT @1
    at_al_ok: Optional[bool] = None             # AT AL → OK?
    at_pp_ok: Optional[bool] = None             # AT PP 2F ON → OK?
    at_cra_ok: Optional[bool] = None            # AT CRA 7E8 → OK?
    at_sh_ok: Optional[bool] = None             # AT SH 7E0 → OK?

    # Derived verdict
    verdict: str = "UNKNOWN"                    # GENUINE / LIMITED / UNKNOWN
    clone_indicators: list = field(default_factory=list)
    genuine_indicators: list = field(default_factory=list)

    @property
    def is_clone(self) -> bool:
        return self.verdict == "LIMITED"

    @property
    def is_genuine(self) -> bool:
        return self.verdict == "GENUINE"

    def user_message(self) -> str:
        """Human-readable summary for display to the user"""
        lines = []
        lines.append("=" * 60)
        lines.append("ADAPTER QUALITY CHECK")
        lines.append("=" * 60)

        if self.firmware_version:
            lines.append(f"Firmware : {self.firmware_version}")
        if self.device_description:
            lines.append(f"Device   : {self.device_description}")

        lines.append(f"AT AL    : {'✓ OK' if self.at_al_ok else '✗ FAILED (clone indicator)'}")
        lines.append(f"AT PP    : {'✓ OK' if self.at_pp_ok else '✗ FAILED'}")
        lines.append(f"AT CRA   : {'✓ OK' if self.at_cra_ok else '✗ FAILED'}")
        lines.append(f"AT SH    : {'✓ OK' if self.at_sh_ok else '✗ FAILED'}")

        lines.append("")

        if self.verdict == "GENUINE":
            lines.append("✓ VERDICT: Genuine / high-quality adapter")
            lines.append("  Full functionality expected.")
        elif self.verdict == "LIMITED":
            lines.append("⚠ VERDICT: Clone / limited adapter detected")
            lines.append("")
            lines.append("  Known limitations of this adapter:")
            for ind in self.clone_indicators:
                lines.append(f"    • {ind}")
            lines.append("")
            lines.append("  Impact on diagnostics:")
            lines.append("    • CAN bus monitoring (ATMA) may not include headers")
            lines.append("    • Multi-ECU access (ABS/SRS/TCM) may fail or time out")
            lines.append("    • Freeze-frame and Mode 6 data may be unavailable")
            lines.append("    • Older ISO/KWP2000 vehicles may not connect at all")
            lines.append("    • Streaming many PIDs may cause disconnects")
            lines.append("")
            lines.append("  Recommended upgrades:")
            lines.append("    • Vgate iCar Pro (Bluetooth/WiFi, ~$25)")
            lines.append("    • OBDLink MX+ (Bluetooth, ~$100)")
            lines.append("    • OBDLink LX (Bluetooth, ~$80)")
        else:
            lines.append("? VERDICT: Could not determine adapter quality")
            lines.append("  Proceed with caution — some features may not work.")

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialisable dict for logging / JSON output"""
        return {
            "verdict": self.verdict,
            "firmware_version": self.firmware_version,
            "device_description": self.device_description,
            "at_al_ok": self.at_al_ok,
            "at_pp_ok": self.at_pp_ok,
            "at_cra_ok": self.at_cra_ok,
            "at_sh_ok": self.at_sh_ok,
            "clone_indicators": self.clone_indicators,
            "genuine_indicators": self.genuine_indicators,
            "is_clone": self.is_clone,
        }


def _send(ser, command: str, timeout: float = 2.0) -> str:
    """
    Send a raw AT command over an open serial.Serial connection and return
    the cleaned response (no prompt, no echo, stripped).
    """
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write((command + "\r").encode())

    buf = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ser.in_waiting:
            buf += ser.read(ser.in_waiting)
            if b">" in buf:
                break
        time.sleep(0.02)

    text = buf.decode("ascii", errors="ignore")
    # Strip echo (first line often mirrors the command)
    lines = [ln.strip() for ln in text.replace("\r", "\n").split("\n")]
    lines = [ln for ln in lines if ln and ln != ">" and ln.upper() != command.upper()]
    return " ".join(lines).strip()


def _ok(response: str) -> bool:
    """Return True if the response is a clean OK (not ? or empty)"""
    r = response.strip().upper()
    return r == "OK" or r.startswith("OK")


def check_adapter(ser) -> AdapterCheckResult:
    """
    Run the full adapter authenticity check.

    Args:
        ser: An open serial.Serial instance (already connected to the adapter,
             echo off, linefeeds off — i.e. after ATZ / ATE0 / ATL0).

    Returns:
        AdapterCheckResult with verdict and details.
    """
    result = AdapterCheckResult()

    # ── 1. Firmware version (AT I) ──────────────────────────────────────────
    fw_raw = _send(ser, "AT I")
    result.firmware_version = fw_raw if fw_raw else None

    if fw_raw:
        # Extract version number from strings like "ELM327 v1.5" or "ELM327 v2.0"
        m = re.search(r"v?(\d+\.\d+\w*)", fw_raw, re.IGNORECASE)
        version_str = m.group(1) if m else ""

        if version_str in CLONE_FIRMWARE_VERSIONS or version_str.lstrip("v") in CLONE_FIRMWARE_VERSIONS:
            result.clone_indicators.append(
                f"Firmware '{fw_raw}' — version {version_str} is clone-only (no official ELM release)"
            )
        elif version_str in GENUINE_FIRMWARE_VERSIONS or version_str.lstrip("v") in GENUINE_FIRMWARE_VERSIONS:
            result.genuine_indicators.append(f"Firmware '{fw_raw}' matches genuine ELM chip")
        elif not fw_raw or fw_raw in ("?", ""):
            result.clone_indicators.append("AT I returned empty/? — clone indicator")

    # ── 2. Device description (AT @1) ───────────────────────────────────────
    desc_raw = _send(ser, "AT @1")
    result.device_description = desc_raw if desc_raw else None

    if not desc_raw or desc_raw.strip() in ("?", ""):
        result.clone_indicators.append("AT @1 returned empty/? — clone indicator")
    else:
        result.genuine_indicators.append(f"Device description present: '{desc_raw}'")

    # ── 3. AT AL — THE single most reliable test ────────────────────────────
    al_raw = _send(ser, "AT AL")
    result.at_al_ok = _ok(al_raw)

    if not result.at_al_ok:
        result.clone_indicators.append(
            f"AT AL returned '{al_raw}' instead of OK — definitive clone indicator"
        )
    else:
        result.genuine_indicators.append("AT AL → OK")

    # ── 4. Protocol parameter (AT PP 2F ON) ─────────────────────────────────
    pp_raw = _send(ser, "AT PP 2F ON", timeout=3.0)
    result.at_pp_ok = _ok(pp_raw)

    if not result.at_pp_ok:
        result.clone_indicators.append(f"AT PP 2F ON returned '{pp_raw}' — clone indicator")
    else:
        result.genuine_indicators.append("AT PP 2F ON → OK")

    # ── 5. CAN receive address (AT CRA 7E8) ─────────────────────────────────
    cra_raw = _send(ser, "AT CRA 7E8")
    result.at_cra_ok = _ok(cra_raw)

    if not result.at_cra_ok:
        result.clone_indicators.append(f"AT CRA 7E8 returned '{cra_raw}' — CAN extended support missing")
    else:
        result.genuine_indicators.append("AT CRA 7E8 → OK")

    # Clear the CRA filter so we don't affect subsequent commands
    _send(ser, "AT CRA")

    # ── 6. Set CAN header (AT SH 7E0) ───────────────────────────────────────
    sh_raw = _send(ser, "AT SH 7E0")
    result.at_sh_ok = _ok(sh_raw)

    if not result.at_sh_ok:
        result.clone_indicators.append(f"AT SH 7E0 returned '{sh_raw}' — header setting failed")
    else:
        result.genuine_indicators.append("AT SH 7E0 → OK")

    # ── Verdict ──────────────────────────────────────────────────────────────
    # AT AL failure alone is enough to call it a clone (most reliable single test)
    # Two or more clone indicators → LIMITED
    if not result.at_al_ok or len(result.clone_indicators) >= 2:
        result.verdict = "LIMITED"
    elif len(result.genuine_indicators) >= 3:
        result.verdict = "GENUINE"
    else:
        result.verdict = "UNKNOWN"

    return result


def check_adapter_from_elm327base(elm_base_instance) -> AdapterCheckResult:
    """
    Convenience wrapper for scripts that already have an ELM327Base instance.

    Args:
        elm_base_instance: Connected ELM327Base (or compatible) object with
                           a .serial_conn attribute.

    Returns:
        AdapterCheckResult
    """
    return check_adapter(elm_base_instance.serial_conn)
