"""
OLIP Guardian Interface
========================
Models the guardian's perspective: onboarding, receiving recovery requests,
performing the human-firewall verification checklist, and releasing/revoking shards.

STATUS: Logic and checklist implemented.
        Secure shard storage and transport are STUBS — see roadmap.md.
"""

import hashlib
import time
from dataclasses import dataclass, field


@dataclass
class GuardianProfile:
    """Represents a designated guardian in the OLIP network."""
    guardian_id: int
    name: str
    shard: dict  # {'id': int, 'value': int}
    onboarded_at: float = field(default_factory=time.time)
    shard_released: bool = False
    shard_revoked: bool = False

    # STUB: In production, shard is encrypted and stored in the
    # guardian's device Secure Enclave, never in plain memory.


class GuardianOnboarding:
    """
    Manages the Trust Ceremony: assigning a shard to a guardian
    and presenting them with their responsibilities.
    """

    GOLDEN_RULES = [
        "Your device holds 1 of 5 shards of this person's digital identity.",
        "Never release your shard based on text messages or email alone.",
        "Always verify the requester's identity via voice call or in person.",
        "You have 24 hours to revoke your approval after releasing the shard.",
        "No company, police, or tech support should ever ask for your shard.",
    ]

    @staticmethod
    def onboard(guardian_id: int, name: str, shard: dict) -> GuardianProfile:
        """
        Register a guardian and assign their shard.

        Args:
            guardian_id: Unique integer ID for this guardian.
            name: Human-readable name of the guardian.
            shard: The shard dict {'id', 'value'} assigned to this guardian.

        Returns:
            A GuardianProfile instance.
        """
        print(f"\n[OLIP] === GUARDIAN ONBOARDING: {name} ===")
        for i, rule in enumerate(GuardianOnboarding.GOLDEN_RULES, 1):
            print(f"  Rule {i}: {rule}")
        print(f"[OLIP] Shard #{shard['id']} has been assigned to {name}.")
        print("[OLIP] STUB: In production, shard is encrypted into your device's Secure Enclave.\n")

        return GuardianProfile(guardian_id=guardian_id, name=name, shard=shard)


class GuardianVerificationChecklist:
    """
    The human-firewall verification checklist a guardian must complete
    before releasing their shard. Designed to defeat deepfakes and social engineering.
    """

    CHECKLIST = [
        {
            "step": 1,
            "action": "Vocal / Visual Check",
            "instruction": "Call the user or FaceTime them. Do NOT rely on text or email.",
        },
        {
            "step": 2,
            "action": "Memory Test",
            "instruction": (
                "Ask a question only the real user would know "
                "(e.g., 'What did we eat last Tuesday?'). "
                "AI clones cannot answer real-time personal memories."
            ),
        },
        {
            "step": 3,
            "action": "Latency / Robotics Test",
            "instruction": (
                "If the caller pauses unnaturally or sounds robotic, HANG UP. "
                "It may be an AI voice clone."
            ),
        },
        {
            "step": 4,
            "action": "Safe Word Confirmation",
            "instruction": (
                "Ask for the pre-agreed secret phrase established during setup. "
                "This phrase is never stored in the cloud."
            ),
        },
    ]

    @staticmethod
    def display():
        """Print the full verification checklist."""
        print("\n[OLIP] === GUARDIAN VERIFICATION CHECKLIST ===")
        for item in GuardianVerificationChecklist.CHECKLIST:
            print(f"  Step {item['step']}: {item['action']}")
            print(f"    → {item['instruction']}")
        print()

    @staticmethod
    def confirm_completed(guardian: GuardianProfile) -> bool:
        """
        Record that a guardian has confirmed all checklist steps.

        STUB: In production this triggers biometric authentication on
        the guardian's device to decrypt and transmit the shard.

        Args:
            guardian: The GuardianProfile of the approving guardian.

        Returns:
            True, representing checklist completion.
        """
        print(f"[OLIP] {guardian.name} confirmed verification checklist.")
        print("[OLIP] STUB: Biometric unlock of shard in Secure Enclave would occur here.")
        return True


class GuardianDashboard:
    """
    The guardian's view during an active recovery window.
    Allows shard release and revocation within the 24-hour veto period.
    """

    def __init__(self, guardian: GuardianProfile, recovery_manager):
        self.guardian = guardian
        self.recovery_manager = recovery_manager

    def release_shard(self) -> dict | None:
        """
        Guardian approves the recovery and releases their shard.

        Returns:
            The shard dict if released, None if already revoked.
        """
        if self.guardian.shard_revoked:
            print(f"[OLIP] {self.guardian.name}: Shard already revoked.")
            return None

        GuardianVerificationChecklist.display()
        verified = GuardianVerificationChecklist.confirm_completed(self.guardian)

        if verified:
            self.guardian.shard_released = True
            print(f"[OLIP] {self.guardian.name}: Shard #{self.guardian.shard['id']} released.")
            return self.guardian.shard

        return None

    def revoke_shard(self) -> str:
        """
        Guardian withdraws approval during the 24-hour veto window.

        Returns:
            Status message from the RecoveryManager.
        """
        self.guardian.shard_revoked = True
        self.guardian.shard_released = False
        return self.recovery_manager.revoke_guardian_shard(self.guardian.shard["id"])
