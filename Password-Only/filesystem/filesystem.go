package filesystem

import (
	"bytes"
	"encoding/gob"
	"fmt"
	"io"
	"os"
	"strings"

	"file_system/types"
)

// ---------------- Globals ----------------
var (
	headerPayload *HeaderPayload
	superblock    types.Superblock
	fileEntries   []types.FileEntry
	currentDir    *types.FileEntry
	currentPath   []string = []string{""} // root represented as ""
	vaultFile              = types.VaultFileName
)

const InitialFileEntries = 128

// ---------------- Path Helpers ----------------

func joinPath(base, name string) string {
	if base == "/" {
		return "/" + name
	}
	return base + "/" + name
}

func GetCurrentPath() string {
	if len(currentPath) == 1 && currentPath[0] == "" {
		return "/"
	}
	return "/" + strings.Join(currentPath[1:], "/")
}

func parentPath(path string) string {
	if path == "/" {
		return ""
	}
	lastSlash := strings.LastIndex(path, "/")
	if lastSlash == 0 {
		return "/"
	}
	return path[:lastSlash]
}

// ---------------- Encrypted FS Region ----------------

func writeEncryptedFSRegion() error {
	if headerPayload == nil {
		return fmt.Errorf("no header payload")
	}

	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	if err := enc.Encode(superblock); err != nil {
		return fmt.Errorf("encode superblock: %w", err)
	}
	if err := enc.Encode(fileEntries); err != nil {
		return fmt.Errorf("encode fileEntries: %w", err)
	}
	plain := buf.Bytes()

	ct, nonce, err := AESCTREncrypt(headerPayload.VolumeKey[:], plain)
	if err != nil {
		return fmt.Errorf("AES encrypt: %w", err)
	}

	dataForMac := append(nonce, ct...)
	mac := ComputeHMAC(headerPayload.VolumeKey[:], dataForMac)

	f, err := os.OpenFile(vaultFile, os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		return fmt.Errorf("open vault: %w", err)
	}
	defer f.Close()

	if _, err := f.Seek(int64(headerPayload.VolumeOffset), io.SeekStart); err != nil {
		return fmt.Errorf("seek vault: %w", err)
	}

	if _, err := f.Write(nonce); err != nil {
		return err
	}
	if _, err := f.Write(ct); err != nil {
		return err
	}
	if _, err := f.Write(mac); err != nil {
		return err
	}

	return f.Truncate(int64(headerPayload.VolumeOffset + uint64(len(nonce)+len(ct)+len(mac))))
}

func readEncryptedFSRegion() error {
	if headerPayload == nil {
		return fmt.Errorf("no header payload")
	}

	f, err := os.Open(vaultFile)
	if err != nil {
		return fmt.Errorf("open vault: %w", err)
	}
	defer f.Close()

	offset := int64(headerPayload.VolumeOffset)
	stat, err := f.Stat()
	if err != nil {
		return fmt.Errorf("stat vault: %w", err)
	}
	if stat.Size() <= offset {
		return fmt.Errorf("vault too small")
	}

	if _, err := f.Seek(offset, io.SeekStart); err != nil {
		return fmt.Errorf("seek failed: %w", err)
	}

	nonce := make([]byte, NonceLen)
	if _, err := f.Read(nonce); err != nil {
		return err
	}

	remaining := stat.Size() - offset - int64(len(nonce))
	if remaining <= HMACLen {
		return fmt.Errorf("FS region too small")
	}
	ctLen := int(remaining - HMACLen)
	ct := make([]byte, ctLen)
	if _, err := f.Read(ct); err != nil {
		return err
	}

	mac := make([]byte, HMACLen)
	if _, err := f.Read(mac); err != nil {
		return err
	}

	dataForMac := append(nonce, ct...)
	if !VerifyHMAC(headerPayload.VolumeKey[:], dataForMac, mac) {
		return fmt.Errorf("HMAC verification failed")
	}

	plain, err := AESCTRDecrypt(headerPayload.VolumeKey[:], nonce, ct)
	if err != nil {
		return fmt.Errorf("AES decrypt failed: %w", err)
	}

	dec := gob.NewDecoder(bytes.NewReader(plain))
	if err := dec.Decode(&superblock); err != nil {
		return err
	}
	if err := dec.Decode(&fileEntries); err != nil {
		return err
	}

	return nil
}

// ---------------- Init / Mount ----------------

func InitOrLoadVolume(password string) error {
	if _, err := os.Stat(vaultFile); os.IsNotExist(err) {
		fmt.Println("No vault found, creating new one...")
		return CreateNewVolume(password)
	}
	return Mount(password)
}

func CreateNewVolume(password string) error {
	hp, err := NewHeaderPayload(0)
	if err != nil {
		return err
	}

	blob, err := EncryptHeaderPayload(hp, password)
	if err != nil {
		return err
	}

	superblock = types.Superblock{TotalBlocks: 100, FreeBlocks: 97, FileEntriesCount: 1}
	fileEntries = make([]types.FileEntry, InitialFileEntries)
	fileEntries[0] = types.FileEntry{Name: "root", Type: types.FileTypeDirectory, Used: true, Path: "/"}
	currentDir = &fileEntries[0]
	currentPath = []string{""}

	f, err := os.OpenFile(vaultFile, os.O_CREATE|os.O_RDWR|os.O_TRUNC, 0600)
	if err != nil {
		return err
	}
	defer f.Close()

	if err := WriteEncryptedHeaderSlot(f, 0, blob); err != nil {
		return err
	}

	headerPayload = hp
	fmt.Println("Vault Created. Mounting..")
	fmt.Println("")
	return writeEncryptedFSRegion()
}

func Mount(password string) error {
	blob, err := ReadEncryptedHeaderSlotFromFile(vaultFile, 0)
	if err != nil {
		return err
	}

	hp, err := DecryptHeaderBlob(blob, password)
	if err != nil {
		return fmt.Errorf("wrong password or corrupted vault")
	}

	headerPayload = hp
	if err := readEncryptedFSRegion(); err != nil {
		return err
	}

	currentDir = &fileEntries[0]
	currentPath = []string{""}
	return nil
}

func SaveFilesystem() error {
	if headerPayload == nil {
		return fmt.Errorf("no header loaded")
	}
	return writeEncryptedFSRegion()
}

func VaultExists() bool {
	_, err := os.Stat(vaultFile)
	return !os.IsNotExist(err)
}
