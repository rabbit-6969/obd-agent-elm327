"""
ELM327 OBD-II Diagnostic Tool Package
Ford Escape 2008 Diagnostics
"""

__version__ = "1.0.0"
__author__ = "Diagnostic Tool Developer"
__description__ = "ELM327 OBD-II adapter communication and vehicle diagnostics"

from elm327_diagnostic.elm327_adapter import ELM327Adapter
from elm327_diagnostic.vin_reader import VINReader
from elm327_diagnostic.hvac_diagnostics import HVACDiagnostics

__all__ = [
    'ELM327Adapter',
    'VINReader',
    'HVACDiagnostics',
]
