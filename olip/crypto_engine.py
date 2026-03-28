"""
OLIP Cryptographic Engine
=========================
Implements Shamir's Secret Sharing over a large Mersenne prime field.

STATUS: Core math is fully implemented and tested.
        Hardware Secure Enclave binding is a STUB — see roadmap.md.
"""

import secrets
import hashlib

PRIME = 2**127 - 1  # Mersenne prime for finite field security


def get_secure_random() -> int:
    """Cryptographically secure random integer using OS-level entropy."""
    return secrets.randbelow(PRIME)


def generate_olip_identity(k: int = 3, n: int = 5) -> tuple[int, list[dict], str]:
    """
    Generate a Root Identity Key (RIK) and split it into n shards,
    requiring k shards for reconstruction (k-of-n threshold scheme).

    Args:
        k: Minimum number of shards needed for recovery (threshold).
        n: Total number of shards to distribute to guardians.

    Returns:
        Tuple of (secret, shards, commitment_hash)

    Notes:
        In production, 'secret' should be generated inside the device's
        Secure Enclave (iOS) or StrongBox (Android). See roadmap.md.
    """
    if k > n:
        raise ValueError(f"Threshold k={k} cannot exceed total shards n={n}.")
    if k < 2:
        raise ValueError("Threshold k must be at least 2 for security.")

    secret = get_secure_random()

    # Polynomial coefficients: f(x) = secret + c1*x + c2*x^2 + ...
    coeffs = [secret] + [get_secure_random() for _ in range(k - 1)]

    # SHA-256 commitment allows verification without revealing the secret
    commitment = hashlib.sha256(str(secret).encode()).hexdigest()

    shards = []
    for i in range(1, n + 1):
        y = sum(c * pow(i, p, PRIME) for p, c in enumerate(coeffs)) % PRIME
        shards.append({"id": i, "value": y})

    return secret, shards, commitment


def reconstruct_secret(shards: list[dict]) -> int:
    """
    Reconstruct the secret from k or more shards using Lagrange interpolation.

    Args:
        shards: List of shard dicts with 'id' and 'value' keys.

    Returns:
        Reconstructed integer secret.
    """
    secret = 0
    for i, s_i in enumerate(shards):
        xi, yi = s_i["id"], s_i["value"]
        num, den = 1, 1
        for j, s_j in enumerate(shards):
            if i != j:
                xj = s_j["id"]
                num = (num * -xj) % PRIME
                den = (den * (xi - xj)) % PRIME
        secret = (secret + yi * (num * pow(den, -1, PRIME))) % PRIME
    return secret


def verify_commitment(secret: int, commitment: str) -> bool:
    """
    Verify a reconstructed secret matches the original SHA-256 commitment.

    Args:
        secret: The reconstructed integer secret.
        commitment: The hex SHA-256 digest created during identity generation.

    Returns:
        True if the secret is authentic, False if shards were tampered with.
    """
    return hashlib.sha256(str(secret).encode()).hexdigest() == commitment
