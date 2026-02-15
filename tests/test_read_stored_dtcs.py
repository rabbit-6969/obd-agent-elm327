import pytest

from elm327_diagnostic.elm327_adapter import ELM327Adapter


def test_read_stored_dtcs_parses_two_codes(monkeypatch):
    adapter = ELM327Adapter(port='COM_TEST')

    # Simulate a Mode 03 response with leading 0x43 and two DTC pairs:
    # 43 01 02 03 04 -> data bytes: 01 02 03 04 -> P0102, P0304
    monkeypatch.setattr(adapter, 'send_obd_command', lambda cmd: '43 01 02 03 04')

    dtcs = adapter.read_stored_dtcs()
    assert dtcs == ['P0102', 'P0304']


def test_get_emission_readiness_includes_stored_dtcs(monkeypatch):
    adapter = ELM327Adapter(port='COM_TEST')

    # Patch stored dtcs and the monitor/time helpers to make outcome deterministic
    monkeypatch.setattr(adapter, 'read_stored_dtcs', lambda: ['P0102'])
    monkeypatch.setattr(adapter, 'get_emissions_monitor_status', lambda: {'ready': True, 'pending_dtc': False, 'monitors': {'m1': True}})
    monkeypatch.setattr(adapter, 'get_time_since_dtc_clear', lambda: 3600)

    res = adapter.get_emission_readiness_status()
    assert res.get('stored_dtcs') == ['P0102']
    assert res.get('pass_emission_test') is True
