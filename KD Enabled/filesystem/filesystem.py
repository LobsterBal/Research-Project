import os
import pickle
import struct
from dataclasses import dataclass
from typing import Optional, List
from . import header, types
from .crypto import aes_ctr_encrypt, aes_ctr_decrypt, compute_hmac, verify_hmac, NONCE_LEN, HMAC_LEN

# ---------------- Globals ----------------
vault_file = "vault.dat"
volume_headers: List[header.HeaderPayload] = []
current_volume_idx: Optional[int] = None

# ---------------- FileEntry ----------------
@dataclass
class FileEntry:
    name: str = ""
    type: types.FileType = types.FileType.FILE
    path: str = ""
    used: bool = False
    content: str = ""  # simple in-memory content

# current filesystem state
current_dir: Optional[FileEntry] = None
current_path: List[str] = [""]
file_entries: List[FileEntry] = []

# ---------------- Vault Handling ----------------
def vault_exists() -> bool:
    return os.path.exists(vault_file)

def create_new_volume(password: str, fsid: int) -> None:
    """Create a new volume header slot in vault file using fixed offsets."""
    global current_dir, current_path, file_entries, current_volume_idx, volume_headers

    hp = header.HeaderPayload.new(fsid)
    blob = header.encrypt_header_payload(hp, password)
    size = header.encrypted_header_size()

    # Write header to vault
    mode = "r+b" if os.path.exists(vault_file) else "w+b"
    with open(vault_file, mode) as f:
        f.seek(fsid * size)
        f.write(blob)

    while len(volume_headers) <= fsid:
        volume_headers.append(None)
    volume_headers[fsid] = hp

    # Initialize root
    current_volume_idx = fsid
    root = FileEntry(name="root", type=types.FileType.DIRECTORY, path="/", used=True)
    file_entries = [root]
    current_dir = root
    current_path = [""]

    write_encrypted_fs_region()
    print(f"[DEBUG] Initialized volume {fsid} with fixed offset={hp.volume_offset}")

def create_header_pointing_to_slot(target_slot: int, new_password: str, write_slot: int) -> int:
    """Create a new header pointing to target_slot, encrypted with new_password."""
    global volume_headers
    size = header.encrypted_header_size()

    if target_slot < 0 or target_slot >= header.NUM_HEADER_SLOTS or volume_headers[target_slot] is None:
        raise ValueError(f"target_slot {target_slot} header not available")

    target_hp = volume_headers[target_slot]
    new_hp = header.HeaderPayload(
        volume_key=target_hp.volume_key,
        volume_offset=target_hp.volume_offset,
        volume_size=target_hp.volume_size,
        fsid=target_hp.fsid
    )
    blob = header.encrypt_header_payload(new_hp, new_password)

    mode = "r+b" if os.path.exists(vault_file) else "w+b"
    with open(vault_file, mode) as f:
        f.seek(write_slot * size)
        f.write(blob)

    while len(volume_headers) <= write_slot:
        volume_headers.append(None)
    volume_headers[write_slot] = new_hp

    return write_slot

def mount(password: str, kd_ok: bool = False) -> int:
    """Mount a volume using password, limited to NUM_HEADER_SLOTS."""
    global current_volume_idx, current_dir, current_path, file_entries, volume_headers

    if not os.path.exists(vault_file):
        raise ValueError("Vault does not exist")

    size = header.encrypted_header_size()
    start_idx = 0 if kd_ok else 1
    print(f"[DEBUG] Trying to mount with kd_ok={kd_ok}, start_idx={start_idx}, password='{password}'")

    with open(vault_file, "rb") as f:
        for idx in range(start_idx, header.NUM_HEADER_SLOTS):
            f.seek(idx * size)
            blob = f.read(size)
            try:
                hp = header.decrypt_header_blob(blob, password)
                print(f"[DEBUG] Successfully decrypted header at slot {idx}")

                while len(volume_headers) <= idx:
                    volume_headers.append(None)
                volume_headers[idx] = hp
                current_volume_idx = idx

                try:
                    read_encrypted_fs_region()
                except Exception:
                    root = FileEntry(name="root", type=types.FileType.DIRECTORY, path="/", used=True)
                    file_entries = [root]

                current_dir = file_entries[0]
                current_path = [""]

                return idx, hp.fsid

            except ValueError as e:
                print(f"[DEBUG] Failed to decrypt header at slot {idx}: {e}")
                continue

    raise ValueError("Incorrect password for all volumes")

# ---------------- Filesystem Persistence ----------------
def write_encrypted_fs_region():
    global volume_headers, current_volume_idx, file_entries, vault_file
    if current_volume_idx is None:
        raise ValueError("No mounted volume")
    hp = volume_headers[current_volume_idx]
    plain = pickle.dumps(file_entries)
    ciphertext, nonce = aes_ctr_encrypt(hp.volume_key, plain)
    mac = compute_hmac(hp.volume_key, nonce + ciphertext)

    with open(vault_file, "r+b") as f:
        f.seek(hp.volume_offset)
        f.write(struct.pack("<I", len(ciphertext)))
        f.write(nonce)
        f.write(ciphertext)
        f.write(mac)
        f.truncate(hp.volume_offset + hp.volume_size)

    print(f"[DEBUG] Saved {len(file_entries)} entries to volume {current_volume_idx}")

def read_encrypted_fs_region():
    global volume_headers, current_volume_idx, file_entries, vault_file
    if current_volume_idx is None:
        raise ValueError("No mounted volume")
    hp = volume_headers[current_volume_idx]
    with open(vault_file, "rb") as f:
        f.seek(hp.volume_offset)
        length_data = f.read(4)
        if len(length_data) < 4:
            raise ValueError("FS region has no length prefix")
        ct_len = struct.unpack("<I", length_data)[0]
        nonce = f.read(NONCE_LEN)
        ciphertext = f.read(ct_len)
        mac = f.read(HMAC_LEN)

    if not verify_hmac(hp.volume_key, nonce + ciphertext, mac):
        raise ValueError("HMAC verification failed")

    file_entries[:] = pickle.loads(aes_ctr_decrypt(hp.volume_key, nonce, ciphertext))

def save_filesystem():
    if current_volume_idx is None:
        raise ValueError("No mounted volume")
    write_encrypted_fs_region()

# ---------------- Path Helpers ----------------
def join_path(base: str, name: str) -> str:
    if base == "/":
        return "/" + name
    return base.rstrip("/") + "/" + name


def get_current_path() -> str:
    if len(current_path) == 1 and current_path[0] == "":
        return "/"
    return "/" + "/".join(current_path[1:])


def parent_path(path: str) -> str:
    if path == "/":
        return ""
    last_slash = path.rfind("/")
    if last_slash == 0:
        return "/"
    return path[:last_slash]
