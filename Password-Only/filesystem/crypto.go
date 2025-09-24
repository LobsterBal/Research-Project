package filesystem

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"errors"
	"io"

	"golang.org/x/crypto/pbkdf2"
)

const (
	KeyLen     = 32 // AES-256
	HMACLen    = 32 // HMAC-SHA256
	NonceLen   = 16 // AES-CTR nonce
	PBKDF2Iter = 100_000
)

// ---------------- Random Bytes ----------------
func RandomBytes(n int) ([]byte, error) {
	b := make([]byte, n)
	if _, err := io.ReadFull(rand.Reader, b); err != nil {
		return nil, err
	}
	return b, nil
}

// ---------------- Key Derivation ----------------
func DeriveKey(password string, salt []byte) []byte {
	return pbkdf2.Key([]byte(password), salt, PBKDF2Iter, KeyLen, sha256.New)
}

// ---------------- AES-CTR ----------------
func AESCTREncrypt(key, plaintext []byte) (ciphertext, nonce []byte, err error) {
	if len(key) != KeyLen {
		return nil, nil, errors.New("invalid AES key length")
	}
	nonce, err = RandomBytes(NonceLen)
	if err != nil {
		return nil, nil, err
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, nil, err
	}

	ct := make([]byte, len(plaintext))
	stream := cipher.NewCTR(block, nonce)
	stream.XORKeyStream(ct, plaintext)
	return ct, nonce, nil
}

func AESCTRDecrypt(key, nonce, ciphertext []byte) ([]byte, error) {
	if len(key) != KeyLen {
		return nil, errors.New("invalid AES key length")
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	plain := make([]byte, len(ciphertext))
	stream := cipher.NewCTR(block, nonce)
	stream.XORKeyStream(plain, ciphertext)
	return plain, nil
}

// ---------------- HMAC ----------------
func ComputeHMAC(key, data []byte) []byte {
	m := hmac.New(sha256.New, key)
	m.Write(data)
	return m.Sum(nil)
}

func VerifyHMAC(key, data, mac []byte) bool {
	expected := ComputeHMAC(key, data)
	return hmac.Equal(mac, expected)
}
