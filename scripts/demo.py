"""
OLIP v1.0 — Full System Demo
=============================
Demonstrates identity generation, continuous authentication,
guardian onboarding, and recovery (with simulated veto period bypass).

Run:
    python scripts/demo.py
"""

import time
from olip.crypto_engine import generate_olip_identity
from olip.trust_engine import AdaptiveTrustEngine, BehavioralSignals
from olip.recovery_manager import RecoveryManager
from olip.guardian_interface import GuardianOnboarding, GuardianDashboard

SEPARATOR = "\n" + "=" * 60 + "\n"


def run_demo():
    print(SEPARATOR)
    print("  OmniLock Identity Protocol (OLIP) v1.0 — Demo")
    print(SEPARATOR)

    # ------------------------------------------------------------------
    # 1. Identity Generation
    # ------------------------------------------------------------------
    print("STEP 1: Generating Root Identity Key (3-of-5 threshold)\n")
    secret, shards, commitment = generate_olip_identity(k=3, n=5)
    print(f"  Identity commitment (SHA-256): {commitment}")
    print(f"  {len(shards)} shards generated.")
    print("  [NOTE] In production, secret lives only in Secure Enclave.\n")

    # ------------------------------------------------------------------
    # 2. Guardian Onboarding
    # ------------------------------------------------------------------
    print(SEPARATOR)
    print("STEP 2: Onboarding Guardians\n")
    guardian_names = ["Alice", "Bob", "Carol", "Dave", "Eve"]
    guardians = []
    for i, (name, shard) in enumerate(zip(guardian_names, shards)):
        profile = GuardianOnboarding.onboard(i + 1, name, shard)
        guardians.append(profile)

    # ------------------------------------------------------------------
    # 3. Continuous Authentication
    # ------------------------------------------------------------------
    print(SEPARATOR)
    print("STEP 3: Continuous Authentication — Behavioral Signals\n")
    engine = AdaptiveTrustEngine()

    # Simulate a suspicious signal set
    signals = BehavioralSignals(
        typing_rhythm_match=False,
        location_match=True,
        motion_sensor_present=True,
    )
    score = engine.evaluate_signals(signals)
    print(f"  Trust score after anomaly: {score}/100")

    # Restore via biometric step-up
    engine.restore_trust(biometric_verified=True)
    print(f"  Trust score after biometric step-up: {engine.trust_score}/100\n")

    # ------------------------------------------------------------------
    # 4. Recovery Flow
    # ------------------------------------------------------------------
    print(SEPARATOR)
    print("STEP 4: Identity Recovery — Quorum Collection\n")

    rm = RecoveryManager(commitment)
    dashboards = [GuardianDashboard(g, rm) for g in guardians]

    # Alice, Bob, Carol approve (3-of-5 quorum)
    for i in range(3):
        print(f"  Guardian '{guardians[i].name}' releasing shard...")
        shard = dashboards[i].release_shard()
        if shard:
            result = rm.initiate_recovery(shard)
            print(f"  → {result}\n")

    print(f"  Recovery status: {rm.status()}\n")

    # ------------------------------------------------------------------
    # 5. Simulate Veto Period Elapsed
    # ------------------------------------------------------------------
    print(SEPARATOR)
    print("STEP 5: Simulating Veto Period Elapsed (demo bypass)\n")
    rm.recovery_start_time = time.time() - (rm.VETO_PERIOD_SECONDS + 1)
    result = rm.finalize_recovery()
    print(f"  {result}\n")

    # ------------------------------------------------------------------
    # 6. Veto Demonstration
    # ------------------------------------------------------------------
    print(SEPARATOR)
    print("STEP 6: Demonstrating Veto (owner cancels fraudulent recovery)\n")
    rm2 = RecoveryManager(commitment)
    rm2.initiate_recovery(shards[0])
    rm2.initiate_recovery(shards[1])
    rm2.initiate_recovery(shards[2])
    veto_result = rm2.veto_recovery()
    print(f"  {veto_result}")
    print(f"  Attempt after veto: {rm2.initiate_recovery(shards[3])}\n")

    print(SEPARATOR)
    print("  Demo complete. See README.md for roadmap to production.\n")
    print(SEPARATOR)


if __name__ == "__main__":
    run_demo()
