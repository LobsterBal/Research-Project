package filesystem

import (
	"encoding/binary"
	"fmt"
	"io"
	"os"
)

const (
	SaltLen = 16
)

// ---------------- HeaderPayload ----------------
type HeaderPayload struct {
	VolumeKey    [KeyLen]byte
	VolumeOffset uint64
	VolumeSize   uint64
	FSID         uint32
}

// Create a new HeaderPayload with random VolumeKey
func NewHeaderPayload(fsid uint32) (*HeaderPayload, error) {
	hp := &HeaderPayload{
		VolumeOffset: 512,
		VolumeSize:   0,
		FSID:         fsid,
	}
	key, err := RandomBytes(KeyLen)
	if err != nil {
		return nil, fmt.Errorf("failed to generate volume key: %w", err)
	}
	copy(hp.VolumeKey[:], key)
	return hp, nil
}

// Encrypt header with password
func EncryptHeaderPayload(hp *HeaderPayload, password string) ([]byte, error) {
	salt, err := RandomBytes(SaltLen)
	if err != nil {
		return nil, err
	}

	key := DeriveKey(password, salt)

	buf := make([]byte, KeyLen+8+8+4)
	copy(buf[0:KeyLen], hp.VolumeKey[:])
	binary.LittleEndian.PutUint64(buf[KeyLen:KeyLen+8], hp.VolumeOffset)
	binary.LittleEndian.PutUint64(buf[KeyLen+8:KeyLen+16], hp.VolumeSize)
	binary.LittleEndian.PutUint32(buf[KeyLen+16:KeyLen+20], hp.FSID)

	ct, nonce, err := AESCTREncrypt(key, buf)
	if err != nil {
		return nil, err
	}

	out := append(salt, nonce...)
	out = append(out, ct...)
	return out, nil
}

// Decrypt header blob with password
func DecryptHeaderBlob(blob []byte, password string) (*HeaderPayload, error) {
	if len(blob) < SaltLen+NonceLen {
		return nil, fmt.Errorf("invalid header blob")
	}

	salt := blob[:SaltLen]
	nonce := blob[SaltLen : SaltLen+NonceLen]
	ct := blob[SaltLen+NonceLen:]

	key := DeriveKey(password, salt)

	plain, err := AESCTRDecrypt(key, nonce, ct)
	if err != nil {
		return nil, fmt.Errorf("wrong password or corrupted header")
	}

	if len(plain) != KeyLen+8+8+4 {
		return nil, fmt.Errorf("invalid header payload size")
	}

	var hp HeaderPayload
	copy(hp.VolumeKey[:], plain[0:KeyLen])
	hp.VolumeOffset = binary.LittleEndian.Uint64(plain[KeyLen : KeyLen+8])
	hp.VolumeSize = binary.LittleEndian.Uint64(plain[KeyLen+8 : KeyLen+16])
	hp.FSID = binary.LittleEndian.Uint32(plain[KeyLen+16 : KeyLen+20])

	return &hp, nil
}

// ---------------- Header Slot I/O ----------------
func EncryptedHeaderSize() int {
	return SaltLen + NonceLen + KeyLen + 8 + 8 + 4
}

func WriteEncryptedHeaderSlot(f io.WriterAt, slotIdx int, blob []byte) error {
	offset := int64(slotIdx * EncryptedHeaderSize())
	_, err := f.WriteAt(blob, offset)
	return err
}

func ReadEncryptedHeaderSlotFromFile(path string, slotIdx int) ([]byte, error) {
	f, err := os.OpenFile(path, os.O_RDONLY, 0)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	size := EncryptedHeaderSize()
	offset := int64(slotIdx * size)
	blob := make([]byte, size)
	if _, err := f.ReadAt(blob, offset); err != nil {
		return nil, err
	}
	return blob, nil
}

func printDecryptedHeaderInfo(prefix string) {
	if headerPayload != nil {
		fmt.Printf("%s decrypted header:\n", prefix)
		fmt.Printf("  VolumeOffset: %d\n", headerPayload.VolumeOffset)
		fmt.Printf("  VolumeSize: %d\n", headerPayload.VolumeSize)
		fmt.Printf("  FSID: %d\n", headerPayload.FSID)
		return
	}
	fmt.Printf("%s (no header payload available)\n", prefix)
}
