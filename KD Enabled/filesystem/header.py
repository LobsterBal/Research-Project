import struct
from typing import Optional
from filesystem.crypto import (
    KEY_LEN,
    NONCE_LEN,
    HMAC_LEN,
    random_bytes,
    derive_key,
    aes_ctr_encrypt,
    aes_ctr_decrypt,
    compute_hmac,
    verify_hmac,
)

# ---------------- Constants ----------------
SALT_LEN = 16
VOLUME_SIZE = 1024 * 1024  # 1 MB per volume
NUM_HEADER_SLOTS = 3       # fixed number of header slots

# ---------------- HeaderPayload ----------------
class HeaderPayload:
    def __init__(self, volume_key: bytes, volume_offset: int, volume_size: int, fsid: int):
        if len(volume_key) != KEY_LEN:
            raise ValueError("VolumeKey must be 32 bytes")
        self.volume_key = volume_key
        self.volume_offset = volume_offset
        self.volume_size = volume_size
        self.fsid = fsid

    @classmethod
    def new(cls, fsid: int) -> "HeaderPayload":
        """Create a new HeaderPayload with a random VolumeKey and fixed offset."""
        volume_key = random_bytes(KEY_LEN)
        volume_size = VOLUME_SIZE
        # Fixed offset: headers first, then volume regions
        volume_offset = NUM_HEADER_SLOTS * (KEY_LEN + 8 + 8 + 4 + SALT_LEN + NONCE_LEN + HMAC_LEN)
        volume_offset += fsid * VOLUME_SIZE  # each volume gets its own 1 MB region
        return cls(volume_key, volume_offset, volume_size, fsid)

# ---------------- Encrypt / Decrypt ----------------
def encrypt_header_payload(hp: HeaderPayload, password: str) -> bytes:
    salt = random_bytes(SALT_LEN)
    key = derive_key(password, salt)
    buf = (
        hp.volume_key
        + struct.pack("<Q", hp.volume_offset)
        + struct.pack("<Q", hp.volume_size)
        + struct.pack("<I", hp.fsid)
    )
    ciphertext, nonce = aes_ctr_encrypt(key, buf)
    mac = compute_hmac(key, ciphertext)
    return salt + nonce + mac + ciphertext

def decrypt_header_blob(blob: bytes, password: str) -> Optional[HeaderPayload]:
    min_len = SALT_LEN + NONCE_LEN + HMAC_LEN + KEY_LEN + 8 + 8 + 4
    if len(blob) < min_len:
        raise ValueError("invalid header blob")
    salt = blob[:SALT_LEN]
    nonce = blob[SALT_LEN:SALT_LEN + NONCE_LEN]
    mac = blob[SALT_LEN + NONCE_LEN:SALT_LEN + NONCE_LEN + HMAC_LEN]
    ct = blob[SALT_LEN + NONCE_LEN + HMAC_LEN:]
    key = derive_key(password, salt)
    if not verify_hmac(key, ct, mac):
        raise ValueError("wrong password or corrupted header")
    plain = aes_ctr_decrypt(key, nonce, ct)
    if len(plain) != KEY_LEN + 8 + 8 + 4:
        raise ValueError("invalid header payload size")
    volume_key = plain[:KEY_LEN]
    volume_offset = struct.unpack("<Q", plain[KEY_LEN:KEY_LEN + 8])[0]
    volume_size = struct.unpack("<Q", plain[KEY_LEN + 8:KEY_LEN + 16])[0]
    fsid = struct.unpack("<I", plain[KEY_LEN + 16:KEY_LEN + 20])[0]
    return HeaderPayload(volume_key, volume_offset, volume_size, fsid)

# ---------------- Header Slot I/O ----------------
def encrypted_header_size() -> int:
    return SALT_LEN + NONCE_LEN + HMAC_LEN + KEY_LEN + 8 + 8 + 4
