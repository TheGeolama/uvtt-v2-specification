# 🧪 UVTT v2 Testing and Conformance Guide

This guide provides platform engineers, VTT developers, and tool authors with a structured framework for validating custom parsers and exporters against the official **Universal VTT v2 (v2.0.0-rc1) Specification** conformance pipeline.

Passing this test suite guarantees that your platform's output matches the standard, ensuring seamless inter-VTT portability, watertight geometry, and cryptographic DRM enforcement.

---

## 🏗️ 1. Core Conformance Architecture

A fully compliant UVTT v2 map package is packaged as a `.uvtt2z` (ZIP-based binary container) which must contain three decoupled JSON layers alongside the raw assets directory:
1.  **`manifest.json`**: Global metadata, topology profiles, and hardware pipelines.
2.  **`geometry.json`**: Structural vectors (SVG-style paths and wall segment limits).
3.  **`entities.json`**: Interactive entities (lights, teleporters, localized audio, weather emitters).
4.  **`assets/`**: Premium raster art, custom textures, and audio loops.

The master validation runner (`verify-all.sh`) coordinates several automated testing layers:
*   **Structural Schema Linting**: JSON Schema validations for manifest, geometry, and entities layers.
*   **Topological Assertions**: Path validation, default landing zone verification, and relative URI integrity checks.
*   **Cryptographic Asset Signatures**: DRM verification of premium split-resolution binaries inside `assets/`.
*   **Resource & Purge Assertions**: Checking WebGPU context scrubbing routines to prevent client memory leaks.

---

## 📐 2. Structural & Topological Validation Rules

Your parser or export engine must pass three core structural validation gates before a `.uvtt2z` file is considered conformant.

### A. The Landing Zone Single-Default Check
To prevent client-side camera-frame loops or initial viewport collisions, a map manifest must define **exactly one default landing zone**. 
A conformant parser should run the following baseline logic (implemented in the Go verification backend `validate_conformance.go`):

```go
// ValidateLandingZones ensures the landing zone cluster has exactly one default entry
func ValidateLandingZones(zones []LandingZone) (bool, string) {
    defaultCount := 0
    for _, lz := range zones {
        if lz.IsDefault {
            defaultCount++
        }
    }
    if defaultCount > 1 {
        return false, "Topology Error: Map manifest defines multiple default landing zones."
    }
    // Note: 0 defaults is acceptable, the engine will default to map origin (0,0)
    return true, ""
}
```

### B. Inter-Map Relative Referencing & Dangling Link Detection
When a portal or staircase transitions a token across separate files (Federated Mode), it must utilize relative URI target formats:
*   **Conformant Format**: `relative://undermountain_lvl2.uvtt2z#lz_staircase_arrival`
*   **Non-Conformant Format**: Absolute OS file paths (e.g., `D:/Maps/...` or `file:///C:/...`) are strictly prohibited to ensure map portability across platforms.

During compilation or parsing, the conformance pipeline checks for **Dangling Links**:
*   If Map A contains a portal referencing an external target (e.g., `relative://undermountain_lvl2.uvtt2z`), the test suite warns or fails the validation check if the referenced target `.uvtt2z` file is not packaged or present in the same execution workspace.

---

## 🔒 3. Cryptographic DRM Verification

To protect split-resolution assets from unauthorized tampering or swapping, the conformance runner enforces cryptographic validation.

*   Every visual and auditory file inside the `assets/` sub-folder must have a matching SHA-256 cryptographic signature stored in the root `manifest.hash` file.
*   **The Signature Test Gate**:
    1.  Parse the `manifest.hash` key-value dictionary.
    2.  For every file path key, calculate the SHA-256 hash of the binary file currently resting in the `assets/` folder.
    3.  Assert that the generated hash matches the signature on record. If any hash mismatches, the runner throws an **Asset Integrity Violation** and terminates the map loading process.

---

## 💻 4. Running the Master Conformance Suite

### Setup Prerequisites
Your test environment must have Python 3.12+ and Go installed. All scripts are found in the `/reference-parsers` and `/qa` directories of the master specification repository.

### Execution Workflow

```bash
# 1. Generate a mock, structurally perfect test archive
python3 generate-mock-uvtt2z.py --out test_dungeon.uvtt2z

# 2. Run the master Python test suite to validate schema conformance
python3 master-test-suite.py --target test_dungeon.uvtt2z

# 3. Run the Go validator to compile and test Go parsing compliance
go run validate_conformance.go -file test_dungeon.uvtt2z
```

### WebGPU Volatile Memory Assertions
For frontend implementations using WebGPU engines (like PixiJS v8), we run automated headless assertions (`webgpu-purge-test.ts`) to ensure that volatile GPU assets are cleanly scrubbed from memory during level-swap events. The test verifies:
1.  All textures are detached and un-cached during `switchMap` sequences.
2.  WebGL2 and WebGPU graphics contexts are completely disposed of before initializing a new master map frame.

---

## 🏅 5. Schema Files Reference
Ensure your custom exporter validates directly against the draft-07 schemas contained within the repository:
*   `schemas/manifest.schema.json`
*   `schemas/geometry.schema.json`
*   `schemas/entities.schema.json`
