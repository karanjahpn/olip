"""
OLIP Test Suite
===============
Unit and integration tests for the cryptographic engine,
trust engine, recovery manager, and guardian interface.
"""

import time
import pytest

from olip.crypto_engine import (
    generate_olip_identity,
    reconstruct_secret,
    verify_commitment,
    PRIME,
)
from olip.trust_engine import AdaptiveTrustEngine, BehavioralSignals
from olip.recovery_manager import RecoveryManager
from olip.guardian_interface import (
    GuardianOnboarding,
    GuardianDashboard,
    GuardianVerificationChecklist,
)


# ===========================================================================
# Cryptographic Engine Tests
# ===========================================================================

class TestCryptoEngine:

    def test_generate_identity_returns_correct_structure(self):
        secret, shards, commitment = generate_olip_identity(k=3, n=5)
        assert isinstance(secret, int)
        assert len(shards) == 5
        assert all("id" in s and "value" in s for s in shards)
        assert len(commitment) == 64  # SHA-256 hex digest

    def test_secret_within_prime_field(self):
        secret, _, _ = generate_olip_identity()
        assert 0 <= secret < PRIME

    def test_shards_within_prime_field(self):
        _, shards, _ = generate_olip_identity()
        for shard in shards:
            assert 0 <= shard["value"] < PRIME

    def test_commitment_matches_secret(self):
        secret, _, commitment = generate_olip_identity()
        assert verify_commitment(secret, commitment)

    def test_wrong_secret_fails_commitment(self):
        _, _, commitment = generate_olip_identity()
        assert not verify_commitment(12345, commitment)

    def test_reconstruct_with_exact_threshold(self):
        secret, shards, commitment = generate_olip_identity(k=3, n=5)
        reconstructed = reconstruct_secret(shards[:3])
        assert reconstructed == secret
        assert verify_commitment(reconstructed, commitment)

    def test_reconstruct_with_all_shards(self):
        secret, shards, _ = generate_olip_identity(k=3, n=5)
        reconstructed = reconstruct_secret(shards)
        assert reconstructed == secret

    def test_reconstruct_with_non_sequential_shards(self):
        secret, shards, _ = generate_olip_identity(k=3, n=5)
        reconstructed = reconstruct_secret([shards[0], shards[2], shards[4]])
        assert reconstructed == secret

    def test_invalid_k_greater_than_n_raises(self):
        with pytest.raises(ValueError):
            generate_olip_identity(k=6, n=5)

    def test_invalid_k_less_than_2_raises(self):
        with pytest.raises(ValueError):
            generate_olip_identity(k=1, n=5)

    def test_different_identities_produce_different_secrets(self):
        secret1, _, _ = generate_olip_identity()
        secret2, _, _ = generate_olip_identity()
        assert secret1 != secret2  # Astronomically unlikely to collide

    def test_tampered_shard_fails_commitment(self):
        secret, shards, commitment = generate_olip_identity(k=3, n=5)
        tampered = [{"id": shards[0]["id"], "value": shards[0]["value"] + 1}] + shards[1:3]
        reconstructed = reconstruct_secret(tampered)
        assert not verify_commitment(reconstructed, commitment)


# ===========================================================================
# Trust Engine Tests
# ===========================================================================

class TestTrustEngine:

    def test_starts_at_full_trust(self):
        engine = AdaptiveTrustEngine()
        assert engine.trust_score == 100
        assert not engine.is_locked

    def test_all_signals_pass_no_penalty(self):
        engine = AdaptiveTrustEngine()
        signals = BehavioralSignals(
            typing_rhythm_match=True,
            location_match=True,
            motion_sensor_present=True,
        )
        score = engine.evaluate_signals(signals)
        assert score == 100

    def test_failed_typing_rhythm_penalizes(self):
        engine = AdaptiveTrustEngine()
        signals = BehavioralSignals(typing_rhythm_match=False, location_match=True, motion_sensor_present=True)
        score = engine.evaluate_signals(signals)
        assert score == 60

    def test_multiple_failures_accumulate(self):
        engine = AdaptiveTrustEngine()
        signals = BehavioralSignals(typing_rhythm_match=False, location_match=False, motion_sensor_present=True)
        score = engine.evaluate_signals(signals)
        assert score == 20

    def test_low_trust_triggers_lock(self):
        engine = AdaptiveTrustEngine()
        signals = BehavioralSignals(typing_rhythm_match=False, location_match=False, motion_sensor_present=False)
        engine.evaluate_signals(signals)
        assert engine.is_locked

    def test_trust_restored_after_biometric(self):
        engine = AdaptiveTrustEngine()
        signals = BehavioralSignals(typing_rhythm_match=False, location_match=False, motion_sensor_present=False)
        engine.evaluate_signals(signals)
        engine.restore_trust(biometric_verified=True)
        assert engine.trust_score == 100
        assert not engine.is_locked

    def test_event_log_records_failures(self):
        engine = AdaptiveTrustEngine()
        signals = BehavioralSignals(typing_rhythm_match=False, location_match=True, motion_sensor_present=True)
        engine.evaluate_signals(signals)
        log = engine.get_event_log()
        assert any("typing_rhythm_match" in e["message"] for e in log)

    def test_trust_score_never_below_zero(self):
        engine = AdaptiveTrustEngine()
        for _ in range(10):
            signals = BehavioralSignals(False, False, False)
            engine.evaluate_signals(signals)
        assert engine.trust_score >= 0


# ===========================================================================
# Recovery Manager Tests
# ===========================================================================

class TestRecoveryManager:

    def _setup(self):
        secret, shards, commitment = generate_olip_identity(k=3, n=5)
        rm = RecoveryManager(commitment)
        return secret, shards, commitment, rm

    def test_shard_accepted_below_quorum(self):
        _, shards, _, rm = self._setup()
        result = rm.initiate_recovery(shards[0])
        assert "1/3" in result

    def test_quorum_message_on_third_shard(self):
        _, shards, _, rm = self._setup()
        rm.initiate_recovery(shards[0])
        rm.initiate_recovery(shards[1])
        result = rm.initiate_recovery(shards[2])
        assert "QUORUM REACHED" in result

    def test_duplicate_shard_rejected(self):
        _, shards, _, rm = self._setup()
        rm.initiate_recovery(shards[0])
        result = rm.initiate_recovery(shards[0])
        assert "WARNING" in result

    def test_finalize_blocked_during_veto_window(self):
        _, shards, _, rm = self._setup()
        rm.initiate_recovery(shards[0])
        rm.initiate_recovery(shards[1])
        rm.initiate_recovery(shards[2])
        result = rm.finalize_recovery()
        assert "Veto window" in result

    def test_finalize_blocked_insufficient_shards(self):
        _, shards, _, rm = self._setup()
        rm.initiate_recovery(shards[0])
        result = rm.finalize_recovery()
        assert "Insufficient" in result

    def test_veto_clears_everything(self):
        _, shards, _, rm = self._setup()
        rm.initiate_recovery(shards[0])
        rm.initiate_recovery(shards[1])
        rm.initiate_recovery(shards[2])
        result = rm.veto_recovery()
        assert "VETOED" in result
        assert rm.vetoed
        assert len(rm.collected_shards) == 0

    def test_shard_after_veto_rejected(self):
        _, shards, _, rm = self._setup()
        rm.veto_recovery()
        result = rm.initiate_recovery(shards[0])
        assert "vetoed" in result.lower()

    def test_guardian_revoke_breaks_quorum(self):
        _, shards, _, rm = self._setup()
        rm.initiate_recovery(shards[0])
        rm.initiate_recovery(shards[1])
        rm.initiate_recovery(shards[2])
        rm.revoke_guardian_shard(shards[0]["id"])
        assert rm.recovery_start_time is None  # countdown reset

    def test_status_reflects_state(self):
        _, shards, _, rm = self._setup()
        rm.initiate_recovery(shards[0])
        status = rm.status()
        assert status["shards_collected"] == 1
        assert not status["quorum_reached"]

    def test_finalize_success_after_veto_period(self):
        """Simulates a completed veto period by monkey-patching start time."""
        secret, shards, commitment, rm = self._setup()
        rm.initiate_recovery(shards[0])
        rm.initiate_recovery(shards[1])
        rm.initiate_recovery(shards[2])
        # Simulate veto period elapsed
        rm.recovery_start_time = time.time() - (rm.VETO_PERIOD_SECONDS + 1)
        result = rm.finalize_recovery()
        assert "SUCCESS" in result

    def test_tampered_shards_fail_verification(self):
        _, shards, commitment, rm = self._setup()
        tampered_shard = {"id": shards[0]["id"], "value": shards[0]["value"] + 999}
        rm.initiate_recovery(tampered_shard)
        rm.initiate_recovery(shards[1])
        rm.initiate_recovery(shards[2])
        rm.recovery_start_time = time.time() - (rm.VETO_PERIOD_SECONDS + 1)
        result = rm.finalize_recovery()
        assert "FAILURE" in result


# ===========================================================================
# Guardian Interface Tests
# ===========================================================================

class TestGuardianInterface:

    def test_onboarding_creates_profile(self):
        _, shards, _, _ = TestRecoveryManager()._setup()
        profile = GuardianOnboarding.onboard(1, "Alice", shards[0])
        assert profile.name == "Alice"
        assert profile.shard == shards[0]
        assert not profile.shard_released

    def test_release_shard_marks_released(self):
        secret, shards, commitment, rm = TestRecoveryManager()._setup()
        profile = GuardianOnboarding.onboard(1, "Alice", shards[0])
        dashboard = GuardianDashboard(profile, rm)
        shard = dashboard.release_shard()
        assert shard is not None
        assert profile.shard_released

    def test_revoke_shard_marks_revoked(self):
        secret, shards, commitment, rm = TestRecoveryManager()._setup()
        profile = GuardianOnboarding.onboard(1, "Alice", shards[0])
        dashboard = GuardianDashboard(profile, rm)
        dashboard.release_shard()
        result = dashboard.revoke_shard()
        assert profile.shard_revoked
        assert "revoked" in result.lower()

    def test_release_after_revoke_returns_none(self):
        secret, shards, commitment, rm = TestRecoveryManager()._setup()
        profile = GuardianOnboarding.onboard(1, "Alice", shards[0])
        dashboard = GuardianDashboard(profile, rm)
        profile.shard_revoked = True
        shard = dashboard.release_shard()
        assert shard is None
