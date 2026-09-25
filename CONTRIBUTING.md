# Contributing to Universal VTT v2

Thank you for helping define the future of open-source TTRPG cartography and spatial database design! To ensure completely bulletproof execution across a multi-platform ecosystem, we enforce rigorous coding standards, structured governance systems, and strict backward-compatibility contracts.

---

## 📜 The Code Contribution Covenant

### 1. Zero-Dependency Reference Implementations

Reference parsers (such as our standard Go ingest engine `uvtt2_parser.go` and Go CI validator `validate_conformance.go`) MUST be written utilizing standard library modules only. This ensures local validation workflows, terminal utilities, and host engines can easily digest code with zero compile-step regressions or security supply chain vulnerabilities.

### 2. Strict Memory Isolation Protocols

When drafting client-side Javascript, WebGL, or WebGPU code, contributors MUST strictly adhere to the **Volatile Memory Disposal Protocol** to support the Dual-File DRM (`.uvtt2k`) standard:

- All decrypted premium raster bytes MUST reside in volatile, isolated CPU RAM or GPU VRAM blocks only.
- Never leave un-revoked object references in browser DOM contexts. If utilizing transient `Blob` objects or `ImageBitmap` decoders, developers must trigger immediate cleanups (`URL.revokeObjectURL(blobUrl)` or `imageBitmap.close()`) immediately following GPU texture binding.
- ArrayBuffers carrying decrypted content or raw AES-256 keys MUST be actively overwritten (i.e. `uint8View.fill(0)`) to sanitize the system memory footprint before releasing variables.

### 3. PixiJS v8 Client Rendering Standards

To support hardware-accelerated WebGPU rendering, any updated client-side HUD components (like `CanvasWorkspace.svelte`) must strictly use **PixiJS v8** standards:

- **Asynchronous App Instantiation**: Always use `await app.init()` for Application startups, mounting `app.canvas` (replacing the legacy `app.view`).
- **Decoupled Geometry & Style**: Always separate line path generation from raster fills and strokes (e.g. `graphics.circle(x, y, r).fill({ color })` or `graphics.poly(coords).stroke({ width })`).
- **Interactive Fills Requirement**: Under WebGL/WebGPU renderers, line strokes cannot reliably register mouse hover or pointer-tap events. To build clickable vector nodes, you MUST use filled circular shapes (`graphics.circle().fill()`) at path midpoints and joints.

### 4. Mathematical Safety Boundaries

All rendering offsets, audio algorithms, and physics curves must be calculated defensively:

- **Audio Decay:** Localized acoustic zone linear dampening calculations MUST mathematically clamp volume limits to prevent negative bounds or engine crashes:
  ```text
  Volume = max(0, min(Volume_max, Volume_max * (1 - (distance / radius))))
