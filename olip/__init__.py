"""
OmniLock Identity Protocol (OLIP) v1.0
=======================================
A threshold secret-sharing based self-sovereign identity protocol
with continuous behavioral authentication and a 24-hour veto recovery window.
"""

from olip.crypto_engine import generate_olip_identity, reconstruct_secret, verify_commitment
from olip.trust_engine import AdaptiveTrustEngine, BehavioralSignals
from olip.recovery_manager import RecoveryManager
from olip.guardian_interface import GuardianOnboarding, GuardianDashboard

__version__ = "1.0.0"
__all__ = [
    "generate_olip_identity",
    "reconstruct_secret",
    "verify_commitment",
    "AdaptiveTrustEngine",
    "BehavioralSignals",
    "RecoveryManager",
    "GuardianOnboarding",
    "GuardianDashboard",
]
