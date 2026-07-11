# Changelog: Universal VTT v2

All notable changes to the Universal VTT (UVTT) specification will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

---

## [2.0.0-rc2] - 2026-07-11

### 🚀 Added (Evolutionary Leap to PixiJS v8 & WebGPU Baseline)
*   **PixiJS v8 Upgrade Integration:** Officially migrated the standard client-side reference and upgrader engines from WebGL2-bound PixiJS v7 to **PixiJS v8**, establishing the native **WebGPU** pipeline as our first-class hardware execution target [uvtt-v2-drm-export-bundle.md].
*   **Asynchronous Scene Initialization:** Rewrote client-side bootstrap standards to use PixiJS v8’s async initialization (`await app.init()`) and unified drawing canvas buffers (`app.canvas` replacing `app.view`).
*   **First-Class WebGPU Hardware Profiles:** Enforced the `hardware_profile.recommended_pipeline: "webgpu"` schema definition to natively feed unencrypted vector arrays directly into GPU compute and geometry registers [uvtt-v2-drm-export-bundle.md].
*   **Decoupled Scene and Stroke Styles:** Refactored vector drawing code templates to match the new PixiJS v8 Graphics system, where shapes are drawn as pure structural nodes (`graphics.circle()`, `graphics.poly()`) and subsequently filled or stroked asynchronously (`fill()`, `stroke()`), dramatically optimizing batch draw-calls.

### 🧹 Fixed (Technical Alignments)
*   **Z-Fighting and Render Overlap Patches:** Standardized explicit layering inside WebGL/WebGPU Containers to isolate background textures, vector lines, lighting rings, and interactive selection joints, completely resolving collision rendering overlaps during real-time zoom calculations.

---

## [2.0.0-rc1] - 2026-07-11

### 🚀 Added (Evolutionary Leap from v1 Legacy Formats)
*   **The Binary Archive Container (.uvtt2z):** Replaced legacy, bloated Base64-in-JSON single-file structures with high-throughput compiled ZIP archives. Heavy raster textures and audio loops are now cleanly detached into the `/assets/` and `/protected/` folders, allowing serverless APIs to perform lightweight JSON header index queries without reading massive image files into host memory.
*   **Dual-Topology Archive Standard:** Formally implemented support for both **Compound Archives** (multi-story maps pre-linked inside a single ZIP file) and **Federated Archives** (modular campaign files living as peers on disk) resolving transitions using system-neutral `internal://` and `relative://` URI protocols.
*   **Hardware Profiles:** Added the `hardware_profile` schema block to the manifest, giving developers a structured framework to declare minimum and recommended hardware graphics pipelines (WebGL2 vs WebGPU) to safely handle advanced compute shaders.
*   **Material-Aware Geometry & Height Bounds:** Upgraded vector lines from 2D planes into 3D-aware structures by introducing explicit `bottom` and `top` Z-axis float height parameters. Expanded the `blocks` array to support selective obstruction (separating sight, light, and token movement parameters).
*   **Directional Line-of-Sight (Right-Hand Rule Normals):** Implemented vector coordinate heading analysis using the "Right-Hand Rule" to divide the canvas into mathematically locked left/right half-spaces, enabling one-way windows, ledges, and illusory walls.
*   **Interactive Spatial Events & Smart Teleports:** Established trigger-polygon bounding boxes supporting `on_enter`, `on_exit`, and `on_interact` event listeners. Built out intra-map (level staircase transitions) and inter-map (world portals) teleporters utilizing pinpoint, relative offset, and dynamic scatter-region landing behaviors to prevent token stacking.
*   **3D Point & Cone Lighting:** Added positional elevation (Z-axis) light nodes, bright/dim radii bounds, customizable color pickers, animation behaviors (flickering/pulsing), and math-clamped linear and inverse-square decay physical models ($I = \\frac{I_0}{d^2}$).
*   **Three-Tier Audio Architecture:** Formally separated audio into Global Music (Tier 1), Global Ambience (Tier 2), and Localized Acoustic Zones (Tier 3). Localized audio spheres use boundary geometry and linear falloff formulas to determine real-time volume decay as a token approaches.
*   **Atmospheric Weather Emitters:** Standardized boundary zones for particle simulations (rain, snow, fog, embers) configured with intensity, speed, angle, and rendering vectors.

### 🛡️ Added (DRM & Security Controls)
*   **Split-Resolution Encryption Model:** Segmented visual maps into unencrypted, heavily compressed, watermarked public proxies (`basemap.webp` capped at 50px per grid) and full-fidelity encrypted assets stored securely within `/protected/` using **AES-256-GCM**.
*   **In-Memory Volatile Decryption:** Mandated that unencrypted premium assets must never touch local physical hard drives or browser DOM contexts, streaming decoded textures straight to the GPU in RAM.
*   **Volatile Memory Disposal Protocol:** Standardized strict client-side garbage collection safeguards. Enforces JS-based WebGL engines to trigger `URL.revokeObjectURL()` immediately following texture binding, and WebGPU pipelines to synchronously close bitmaps and run zero-fills on plaintext ArrayBuffers (`.fill(0)`).
*   **Integrity Receipt Verifications:** Introduced the `manifest.hash` verification file. Clients must traverse the ZIP container, calculate SHA-256 hashes of all assets, and assert they match the receipt values before executing vector paths, preventing code injection attacks.
*   **Zero-Knowledge-Storage Edge Clearinghouse:** Implemented deterministic, stateless key derivation on the serverless edge via Cloudflare Workers, generating symmetrical keys dynamically in memory using standard HMAC-SHA256 calculations.
*   **Decentralized Revocation Sync:** Built out stateless edge database check paths using high-throughput Key-Value stores to automatically flag, sync, and flush local credential keys for refunded or fraudulent transaction ID hashes.

### 🧹 Fixed (Critical Technical Corrections)
*   **Acoustic Volume Boundary Clamping:** Mathematically corrected the linear volume decay equation:
    $$V = \\max\\left(0, \\min\\left(V_{\\text{max}}, V_{\\text{max}} \\times \\left(1 - \\frac{d}{r}\\right)\\right)\\right)$$
    This clamps values between $0$ and $V_{\\text{max}}$, completely eliminating negative values and preventing audio engine crashes or popping bugs on HTML5/Web Audio APIs when a token moves beyond the fade radius ($d \\ge r$).
*   **Predictive Pre-Slicing Window:** Replaced the legacy hardcoded 3-grid pre-slicing threshold with an optional, level-customizable `prediction_trigger_radius` float inside `entities.json`, preventing hardware bottlenecks during high-speed campaign movements.
*   **Interactive Hit-Testing (PixiJS Fills):** Patched client-side raycast interactions. Replaced line-strokes with filled 20-pixel selection nodes (circles) at segment joints to satisfy PixiJS's strict coordinate hit-testing constraints.
*   **Vector Midpoint Normals (Collinear Simplification):** Upgraded Svelte merging actions to use collinear simplification. Merging walls now strips redundant move commands and collinear points, preventing segmented right-hand normal vector tick calculations from failing.
*   **Browser-Based Base64 OOM Crashes:** Resolved browser memory crashes during legacy V1 ingestion by manually decoding bloated Base64 strings into binary Uint8Arrays and constructing Blobs in chunks.
