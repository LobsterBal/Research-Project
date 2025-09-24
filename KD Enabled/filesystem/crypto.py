import os
import hmac
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from typing import Tuple

# ---------------- Constants ----------------
KEY_LEN = 32      # AES-256
HMAC_LEN = 32     # HMAC-SHA256 (digest size)
NONCE_LEN = 8     # AES-CTR nonce length (must be <= 15, 8 is standard)
PBKDF2_ITER = 100_000


# ---------------- Random Bytes ----------------
def random_bytes(n: int) -> bytes:
    """Generate secure random bytes."""
    return get_random_bytes(n)


# ---------------- Key Derivation ----------------
def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a key using PBKDF2 with SHA-256."""
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITER, KEY_LEN
    )


# ---------------- AES-CTR ----------------
def aes_ctr_encrypt(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
    """Encrypt with AES-CTR. Returns (ciphertext, nonce)."""
    if len(key) != KEY_LEN:
        raise ValueError("Invalid AES key length")

    nonce = random_bytes(NONCE_LEN)
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    ciphertext = cipher.encrypt(plaintext)
    return ciphertext, nonce


def aes_ctr_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """Decrypt AES-CTR ciphertext."""
    if len(key) != KEY_LEN:
        raise ValueError("Invalid AES key length")
    if len(nonce) != NONCE_LEN:
        raise ValueError(f"Invalid nonce length: got {len(nonce)}, expected {NONCE_LEN}")

    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    return cipher.decrypt(ciphertext)


# ---------------- HMAC ----------------
def compute_hmac(key: bytes, data: bytes) -> bytes:
    """Compute HMAC-SHA256."""
    return hmac.new(key, data, hashlib.sha256).digest()


def verify_hmac(key: bytes, data: bytes, mac: bytes) -> bool:
    """Verify HMAC-SHA256."""
    expected = compute_hmac(key, data)
    return hmac.compare_digest(mac, expected)
