"""
OLIP Recovery Manager
======================
Handles quorum-based shard collection, the 24-hour veto window,
and final identity reconstruction with commitment verification.

STATUS: Core logic fully implemented.
        Shard transport (Bluetooth/NFC/Matrix) is a STUB — see roadmap.md.
"""

import time
from datetime import datetime, timedelta

from olip.crypto_engine import reconstruct_secret, verify_commitment


class RecoveryManager:
    """
    Manages the full identity recovery lifecycle:
      1. Collects shards from guardians (requires k-of-n quorum).
      2. Enforces a mandatory 24-hour veto window after quorum is reached.
      3. Reconstructs and verifies the Root Identity Key.

    The veto window allows the real owner to cancel a fraudulent recovery
    from any still-logged-in device.
    """

    VETO_PERIOD_SECONDS = 24 * 3600  # 24 hours
    REQUIRED_SHARDS = 3

    def __init__(self, commitment: str):
        """
        Args:
            commitment: SHA-256 hex digest created at identity generation.
                        Used to verify reconstructed secret authenticity.
        """
        self.commitment = commitment
        self.collected_shards: list[dict] = []
        self.recovery_start_time: float | None = None
        self.vetoed: bool = False
        self._revoked_guardian_ids: set[int] = set()

    # ------------------------------------------------------------------
    # Shard Collection
    # ------------------------------------------------------------------

    def initiate_recovery(self, shard: dict) -> str:
        """
        Accept a shard from a guardian and start the veto countdown
        once the required quorum is first reached.

        Args:
            shard: Dict with 'id' (int) and 'value' (int) keys.

        Returns:
            Status message string.
        """
        if self.vetoed:
            return "ERROR: This recovery has been vetoed and cannot continue."

        guardian_id = shard["id"]
        if guardian_id in self._revoked_guardian_ids:
            return f"ERROR: Guardian {guardian_id} has revoked their shard."

        already_ids = {s["id"] for s in self.collected_shards}
        if guardian_id in already_ids:
            return f"WARNING: Shard from guardian {guardian_id} already received."

        self.collected_shards.append(shard)

        # Start the veto countdown the moment quorum is reached
        if (
            len(self.collected_shards) >= self.REQUIRED_SHARDS
            and self.recovery_start_time is None
        ):
            self.recovery_start_time = time.time()
            deadline = datetime.now() + timedelta(seconds=self.VETO_PERIOD_SECONDS)
            return (
                f"QUORUM REACHED. Veto window open until {deadline.strftime('%Y-%m-%d %H:%M:%S')}. "
                f"Recovery will finalize automatically if not vetoed."
            )

        return f"Shard {guardian_id} accepted. ({len(self.collected_shards)}/{self.REQUIRED_SHARDS} collected)"

    # ------------------------------------------------------------------
    # Veto & Revocation
    # ------------------------------------------------------------------

    def veto_recovery(self) -> str:
        """
        Owner cancels an in-progress recovery (e.g., from a still-active device).

        Returns:
            Confirmation message.
        """
        self.vetoed = True
        self.collected_shards = []
        self.recovery_start_time = None
        return "RECOVERY VETOED. All collected shards have been discarded."

    def revoke_guardian_shard(self, guardian_id: int) -> str:
        """
        A guardian withdraws their shard during the veto window.

        Args:
            guardian_id: The integer ID of the revoking guardian.

        Returns:
            Status message.
        """
        self._revoked_guardian_ids.add(guardian_id)
        self.collected_shards = [
            s for s in self.collected_shards if s["id"] != guardian_id
        ]
        # If quorum is broken, reset the countdown
        if len(self.collected_shards) < self.REQUIRED_SHARDS:
            self.recovery_start_time = None
        return f"Guardian {guardian_id} has revoked their shard. Countdown paused."

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    def finalize_recovery(self) -> str:
        """
        Attempt to reconstruct the Root Identity Key.

        Will fail if:
          - The recovery was vetoed.
          - The veto period has not yet elapsed.
          - Fewer than REQUIRED_SHARDS shards are present.
          - The reconstructed secret does not match the commitment.

        Returns:
            Status message string. In production, the restored key would
            be written directly to the device's Secure Enclave.
        """
        if self.vetoed:
            return "ERROR: Recovery has been vetoed."

        if len(self.collected_shards) < self.REQUIRED_SHARDS:
            return (
                f"ERROR: Insufficient shards. "
                f"Have {len(self.collected_shards)}, need {self.REQUIRED_SHARDS}."
            )

        if self.recovery_start_time is None:
            return "ERROR: Quorum not yet reached. Cannot finalize."

        elapsed = time.time() - self.recovery_start_time
        if elapsed < self.VETO_PERIOD_SECONDS:
            remaining_hours = (self.VETO_PERIOD_SECONDS - elapsed) / 3600
            return (
                f"ERROR: Veto window still active. "
                f"{remaining_hours:.2f} hours remaining."
            )

        secret = reconstruct_secret(self.collected_shards)

        if not verify_commitment(secret, self.commitment):
            return "FAILURE: Reconstructed secret does not match commitment. Shards may be corrupted or forged."

        # STUB: In production, write 'secret' to Secure Enclave here.
        return f"SUCCESS: Identity restored. Root Identity Key reconstructed and verified."

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """Return a summary of current recovery state."""
        elapsed = (
            time.time() - self.recovery_start_time
            if self.recovery_start_time
            else None
        )
        remaining = (
            max(0, self.VETO_PERIOD_SECONDS - elapsed) if elapsed is not None else None
        )
        return {
            "shards_collected": len(self.collected_shards),
            "required_shards": self.REQUIRED_SHARDS,
            "quorum_reached": self.recovery_start_time is not None,
            "vetoed": self.vetoed,
            "veto_window_remaining_seconds": remaining,
        }
