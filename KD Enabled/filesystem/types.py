from dataclasses import dataclass

# ---------------- File Types ----------------
class FileType:
    FILE: str = "file"
    DIRECTORY: str = "dir"

    @classmethod
    def all(cls) -> list[str]:
        return [cls.FILE, cls.DIRECTORY]


# ---------------- Superblock ----------------
@dataclass
class Superblock:
    total_blocks: int
    free_blocks: int
    file_entries_count: int


# ---------------- FileEntry ----------------
@dataclass
class FileEntry:
    name: str
    type: str
    used: bool = False
    path: str = ""
    content: str = ""  # only meaningful for files


# ---------------- Header ----------------
@dataclass
class Header:
    magic: bytes
    version: int
    cipher: str
    kdf: str
    data_offset: int


# ---------------- Constants ----------------
VAULT_FILE_NAME: str = "vault.dat"
