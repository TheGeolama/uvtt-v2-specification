# 🧪 UVTT v2 Conformance Test Suite

This directory contains the automated testing infrastructure for the Universal Virtual Tabletop v2 specification[cite: 10]. These suites are executed automatically via GitHub Actions on every Pull Request to ensure structural validity and schema compliance[cite: 10].

### 📖 Documentation

- **Testing and Conformance Guide:** A structured framework providing platform engineers with the rules for validating custom parsers against the v2.0.0-rc1 conformance pipeline (including structural schemas, topological rules, and cryptographic DRM verification)[cite: 12].

### ⚙️ Core Testing Engines

- **Master Test Suite (`master-test-suite.py`):** The consolidated Python verification engine that validates ZIP conformance, strictly enforces geometric constraints (such as Z-bounds and SVG paths), and features a built-in mock ZKS Edge Clearinghouse daemon for token authorization integration testing[cite: 11].
- **Go Reference Parser (`validate_conformance.go`):** A high-concurrency Go validation backend that performs in-memory AES-GCM container extraction, verifies cryptographic manifest hashes, and executes concurrent sub-map schema validations[cite: 15].
- **Client Archive Verifier (`verify-signed-archive.js`):** A Node.js testing script that simulates a VTT client engine importing a cryptographically-signed archive, executing zero-knowledge key handshakes, and enforcing the volatile memory disposal protocol[cite: 16].
- **DRM Asset Validators (Python):** Reference implementation scripts designed to programmatically validate the SHA-256 integrity of split-resolution assets and test AES-256-GCM payload decryption directly against the `manifest.hash` ledger[cite: 13, 14].
- **Verification Wrapper (`verify-all.sh`):** The unified bash script for coordinating and executing the Python, Go, and WebGPU automated testing layers[cite: 10, 12].

_Developers MUST run `./tools/verify-all.sh --self-test` before submitting code to the Consortium[cite: 10]._

---

_Return to the [Main Specification Homepage](https://www.universalvtt.org)._
