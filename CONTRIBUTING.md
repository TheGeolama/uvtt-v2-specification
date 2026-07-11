# Contributing to Universal VTT v2

Thank you for helping define the future of open-source TTRPG cartography and spatial database design! To ensure completely bulletproof execution across a multi-platform ecosystem, we enforce rigorous coding standards, structured governance systems, and strict backward-compatibility contracts.

---

## 📜 The Code Contribution Covenant

### 1. Zero-Dependency Reference Implementations
Reference parsers (such as our standard Go ingest engine `uvtt2_parser.go` and Go CI validator `validate_conformance.go`) MUST be written utilizing standard library modules only. This ensures serverless edge worker runtimes, terminal utilities, and host engines can easily digest code with zero compile-step regressions or security supply chain vulnerabilities.

### 2. Strict Memory Isolation Protocols
When drafting client-side Javascript, WebGL, or WebGPU code, contributors MUST strictly adhere to the **Volatile Memory Disposal Protocol**:
* All decrypted premium raster bytes MUST reside in volatile, isolated CPU RAM or GPU VRAM blocks only.
* Never leave un-revoked object references in browser DOM contexts. If utilizing transient `Blob` objects or `ImageBitmap` decoders, developers must trigger immediate cleanups (`URL.revokeObjectURL(blobUrl)` or `imageBitmap.close()`) immediately following GPU texture binding.
* ArrayBuffers carrying decrypted content MUST be actively overwritten (i.e. `uint8View.fill(0)`) to sanitize the system memory footprint before releasing variables.

### 3. Mathematical Safety Boundaries
All rendering offsets, audio algorithms, and physics curves must be calculated defensively:
* **Audio Decay:** Localized acoustic zone linear dampening calculations MUST mathematically clamp volume limits to prevent negative bounds or engine crashes:
  $$V = \max\left(0, \min\left(V_{\text{max}}, V_{\text{max}} \times \left(1 - \frac{d}{r}\right)\right)\right)$$
* **Grid Projection:** Isometric, Hexagonal (pointy/flat orientations), and standard Square grids must utilize explicit scale definitions to ensure coordinate precision across CAD edits.

---

## 🛠️ The RFC Contribution Pipeline

The UVTT v2 specification is a **Living Document**. To propose additive features (e.g. sound occlusion arrays, particle velocity matrices, WebGPU PBR custom normal layers), follow this structured pipeline:

```
[Draft RFC Markdown] ──► [Submit Pull Request] ──► [Run CI Verification] ──► [VTT Consensus Review] ──► [Merge & Version Update]
```

1. **Draft your Proposal:** Copy `/RFCs/rfc-template.md`, populate all fields completely, and place your file in the `/RFCs/` folder named `rfc-[id]-[feature-name].md`.
2. **Open a PR:** Stage your markdown proposal and any matching schema alterations.
3. **Trigger verification checks:** Ensure your branch passes all programmatic check gates and builds successfully.
4. **Community Consensus:** VTT developers and storefront cartographers will evaluate the performance, memory footprints, and architectural interoperability of the change.
5. **Approval:** Once approved, your RFC is merged, and the standard version increments gracefully.

---

## 🔒 The Backward-Compatibility Contract

Core features (such as standard walls, doors, windows, default landing zones, and coordinate mappings) are **immutable**. 
* Any new capabilities or platform-specific extensions MUST be added strictly inside the optional `extensions` block in the global `manifest.json`.
* Parsing engines must gracefully ignore unrecognized keys inside the extensions container, preventing legacy software from throwing syntax or runtime crash warnings.

---

## 🧪 Automated Testing Prior to Commits

Before submitting a Pull Request, contributors MUST run our unified automated test wrapper:

```bash
# Execute local environment audits, ZKS handshake tests, and schema compliance checks
./verify-all.sh --self-test
```

Any commits that return an exit code other than `0` will be blocked from merging by the automated GitHub Actions CI pipeline (`validate-uvtt2-ci.yml`).
