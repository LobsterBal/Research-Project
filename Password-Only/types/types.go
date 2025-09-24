package types

type FileType string

const (
	FileTypeFile      FileType = "file"
	FileTypeDirectory FileType = "dir"
)

type Superblock struct {
	TotalBlocks      uint64
	FreeBlocks       uint64
	FileEntriesCount uint32
}

type FileEntry struct {
	Name    string
	Type    FileType
	Used    bool
	Path    string
	Content string
}

// Header constants
type Header struct {
	Magic      [8]byte
	Version    uint32
	Cipher     string
	KDF        string
	DataOffset uint64
}

const VaultFileName = "vault.dat"
