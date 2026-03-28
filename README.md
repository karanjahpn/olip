# OmniLock Identity Protocol (OLIP) v1.0

A self-sovereign identity protocol built on threshold secret sharing, continuous behavioral authentication, and a human-powered guardian recovery network with a mandatory 24-hour veto window.

---

## Overview

OLIP answers a core question: *How do you recover a self-sovereign identity without a central authority — and without being tricked by a deepfake?*

The answer is three interlocking layers:

| Layer | Mechanism | Status |
|---|---|---|
| **Cryptographic Core** | Shamir's Secret Sharing (3-of-5) over Mersenne prime field | ✅ Implemented |
| **Continuous Auth** | Adaptive behavioral trust scoring | ✅ Implemented (sensor stubs) |
| **Human Recovery** | Guardian quorum + 24-hour veto window | ✅ Implemented (transport stubs) |

---

## Architecture

```
┌────────────────────────────────────────────┐
│              OLIP Identity Stack           │
├────────────────┬───────────────────────────┤
│  crypto_engine │  Shamir SSS, Lagrange     │
│                │  interpolation, SHA-256   │
│                │  commitment               │
├────────────────┼───────────────────────────┤
│  trust_engine  │  Behavioral signal eval,  │
│                │  adaptive trust scoring,  │
│                │  step-up auth trigger     │
├────────────────┼───────────────────────────┤
│recovery_manager│  Quorum collection,       │
│                │  24-hour veto window,     │
│                │  shard revocation         │
├────────────────┼───────────────────────────┤
│guardian_       │  Trust ceremony, human    │
│interface       │  firewall checklist,      │
│                │  guardian dashboard       │
└────────────────┴───────────────────────────┘
```

---

## Key Concepts

### Root Identity Key (RIK)
A secret integer generated with OS-level entropy. It is never stored in a central database. In production it lives exclusively in the device's Secure Enclave (iOS) or StrongBox (Android).

### Shamir's Secret Sharing (3-of-5)
The RIK is split into 5 cryptographic shards. Any 3 of those shards are sufficient to reconstruct it via Lagrange interpolation. Fewer than 3 reveal nothing about the secret.

### SHA-256 Commitment
At generation time, a `SHA-256(secret)` hash is stored. During recovery, the reconstructed secret must match this commitment — detecting any tampered or forged shards.

### Adaptive Trust Engine
Rather than a one-time login, trust is a continuously evaluated score (0–100) based on behavioral signals: typing rhythm, location, motion sensors. Falling below the threshold triggers a biometric step-up challenge.

### Guardian Network & Veto Window
Recovery requires 3-of-5 guardians to approve. Once quorum is reached, a **mandatory 24-hour countdown** begins. During this window:
- The real owner can **VETO** from any still-active device.
- Any guardian can **revoke** their shard if they believe they were deceived.

This prevents instant hijacking via social engineering or deepfake attacks.

---

## Installation

```bash
git clone https://github.com/karanjahpn/olip.git
cd olip
pip install -e ".[dev]"
```

**Requirements:** Python 3.11+. No third-party dependencies for the core protocol.

---

## Quick Start

```python
from olip import generate_olip_identity, RecoveryManager, AdaptiveTrustEngine, BehavioralSignals

# 1. Generate identity
secret, shards, commitment = generate_olip_identity(k=3, n=5)

# 2. Continuous auth
engine = AdaptiveTrustEngine()
signals = BehavioralSignals(typing_rhythm_match=True, location_match=True, motion_sensor_present=True)
engine.evaluate_signals(signals)

# 3. Recovery
rm = RecoveryManager(commitment)
rm.initiate_recovery(shards[0])
rm.initiate_recovery(shards[1])
rm.initiate_recovery(shards[2])
# rm.finalize_recovery()  # Only succeeds after 24-hour veto period
```

Run the full demo:
```bash
python scripts/demo.py
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 30+ tests cover: crypto correctness, tamper detection, trust scoring, recovery state machine, veto/revocation flows, and guardian interface.

---

## Guardian Human Firewall

When a guardian receives a recovery request, they **must** complete this checklist before approving:

1. **Vocal/Visual Check** — Call or FaceTime the user. Never act on text or email alone.
2. **Memory Test** — Ask a question only the real user would know. AI clones cannot answer real-time personal memories.
3. **Latency/Robotics Test** — Unnatural pauses or a robotic voice are red flags for AI voice cloning. Hang up.
4. **Safe Word** — Confirm the pre-agreed secret phrase (never stored in the cloud).

---

## Roadmap to Production

The following components are currently **stubs** and require platform-specific implementation:

### P0 — Required for any real deployment

| Component | What's needed |
|---|---|
| **Secure Enclave binding** | Replace `get_secure_random()` with a direct call to iOS `SecureEnclave` or Android `StrongBox` / Keystore API. The secret should never leave hardware. |
| **Shard transport** | Implement encrypted delivery of shards to guardians. Options: (A) Matrix/Signal protocol for async delivery, (B) Bluetooth/NFC for proximity-based physical handshake. |
| **Biometric step-up** | Replace `print()` stub in `AdaptiveTrustEngine._trigger_step_up_auth()` with `LocalAuthentication` (iOS) or `BiometricPrompt` (Android). |
| **Guardian shard storage** | Shards must be encrypted at rest in the guardian's Secure Enclave, not in app memory or a database. |

### P1 — Strongly recommended

| Component | What's needed |
|---|---|
| **Tamper-proof audit log** | Append-only local log of all trust deviations, signed with device key. |
| **Real behavioral sensors** | Wire `BehavioralSignals` to actual typing dynamics, GPS geofencing, and IMU data. |
| **Push notification layer** | Notify owner and guardians of recovery events via APNs / FCM with critical alert bypass. |
| **Guardian onboarding UX** | Mobile UI for the Trust Ceremony and the Guardian Dashboard. |

### P2 — Extended features

- Emergency Recovery Sheet (printable PDF for offline guardian instructions)
- Multi-device support (multiple active devices that can issue VETOs)
- Cross-platform (Swift / Kotlin native implementations)
- Formal security audit

---

## Security Notes

- This codebase has **not been professionally audited**. Do not use it to protect real identities until a full security review is completed.
- The Mersenne prime `2^127 - 1` provides 127-bit security for the finite field operations.
- The SHA-256 commitment scheme provides integrity verification but is not a zero-knowledge proof. An adversary who can observe the commitment and has sufficient shards will learn the secret. This is by design for the recovery flow.
- The 24-hour veto window is a social/UX control, not a cryptographic one. Its security depends on the owner having at least one active device that can receive the veto notification.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Contributing

Pull requests welcome. Please run `pytest` and ensure all tests pass before submitting. For significant changes, open an issue first to discuss the approach.
