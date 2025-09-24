module file_system

go 1.24.0

toolchain go1.24.5

// Use 'replace' to explicitly force a known working version of x/crypto
// that contains the 'subtle' package in its expected location.
require golang.org/x/crypto v0.33.0

require (
	golang.org/x/sys v0.36.0 // indirect
	golang.org/x/term v0.35.0 // indirect
)

replace golang.org/x/crypto => golang.org/x/crypto v0.17.0
