# 🧬 UVTT v2 Reference Parsers

Welcome to the Open Virtual Tabletop Consortium reference parser directory. This folder contains official, zero-dependency implementation examples for ingesting, decrypting, and auditing UVTT v2 campaign archives.

These parsers are designed to be studied, adapted, or integrated directly into your Virtual Tabletop's backend or client rendering engines to guarantee 100% specification compliance.

### 🐹 Go Reference Engine (`/go/`)

The Go directory contains our primary server-side validation and ingestion engine (`uvtt2_parser.go`). It is optimized for high-concurrency, serverless edge workers, and desktop client backends.

- **Comprehensive Data Models:** Features strictly typed Go structs mapping the complete Draft-07 JSON schemas for `manifest.json`, `geometry.json`, `entities.json`, and `asset_manifest.json`[cite: 17].
- **Cryptographic Decryption:** Implements the `IngestEngine` to securely resolve AES-256-GCM envelope decryption for premium `.uvtt2k` archives using Zero-Knowledge derived keys[cite: 17].
- **Integrity Auditing:** Automatically parses the `manifest.hash` ledger to perform SHA-256 cryptographic checksum validations on all extracted files, blocking corrupted or maliciously altered archives[cite: 17].
- **Geometric & Topological Safety:** Programmatically audits vertical Z-height collisions, enforces the single-default landing zone rule, and validates acoustic/weather boundary constraints during ingestion[cite: 17].

### 📘 TypeScript Reference Engine (`/typescript/`)

The TypeScript directory contains the client-side parsing logic (`uvtt2-parser.ts`) built specifically for browser-based VTTs.

- **Web Crypto Integration:** Handles secure payload extraction and decryption natively within the browser, strictly adhering to the Consortium's Volatile Memory Disposal Protocol.
- **Client-Side Topological Mapping:** Translates raw JSON vectors into simplified paths ready for hardware-accelerated WebGL/WebGPU canvas rendering.

---

_Return to the [Main Specification Homepage](https://www.universalvtt.org)._
