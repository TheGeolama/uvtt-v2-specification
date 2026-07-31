# 🗺️ Universal Virtual Tabletop v2 (UVTT v2) Master Changelog

All notable changes to the **Universal Virtual Tabletop v2 Specification** and its official **Reference Upgrader Web App** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and adheres to Semantic Versioning for specifications.

---

## [2.0.0-rc1] - 2026-07-12

This release marks the official finalization of the **UVTT v2.0.0-rc1 Specification** and the complete rollout of its **Reference Upgrader Web App**. This milestone transforms tabletop campaign maps from isolated, flat 2D graphics into a dynamic, performance-optimized, and interconnected **Topological Spatial Network**.

### 🚀 Core Architectural Enhancements

#### 1. Decoupled, Zipped Binary Container (`.uvtt2z` & `.uvtt2a`)

- **Map Asset Separation (`.uvtt2z`):** Replaced legacy V1 Base64-in-JSON payload structures with a zipped archive layout. By detaching massive, premium binary artwork and audio loops into a dedicated `assets/` subdirectory and keeping structural coordinates in text-based JSON, we eliminate the ~33% Base64 encoding overhead that causes browser Out-Of-Memory (OOM) crashes on 8K assets.
- **Standalone Asset Packs (`.uvtt2a`):** Introduced a new `assets.schema.json` specification to support smart, drag-and-drop standalone asset archives. Tokens, props, and audio loops can now be bundled with metadata that dictates auto-emitting lights, sound fields, and particle physics upon import.
- **Modular Sub-manifests:** The package structure is split into highly optimized files:
  - `manifest.json`: Stores lightweight index metadata, resolution data, and global environment variables to enable millisecond-level map-library catalog scanning without parsing massive coordinate files.
  - `geometry.json`: Houses system-neutral structural vectors, including walls, portals, and overhead boundaries.
  - `entities.json`: Collects logic-driven interactive layers, containing lights, teleport triggers, localized audio zones, spawns, and weather emitters.

#### 2. In-Memory Normalized Model (IMNM) Migration Router

- **Bi-Directional Pipeline:** Built a centralized migration router (`UvttMigrationEngine`) to decouple version parsing. Incoming map payloads (Legacy V1 or early V2 variants) are translated upward into a reactive, master in-memory state tree managed via a Svelte store. Outbound exports are then compiled or gracefully down-sampled based on the user's selected engine profile.
- **Graceful Degradation Protocol:** To prevent backward-compatibility anxiety, when a creator compiles a modern map back down to a legacy V1 `.dd2vtt` structure, the engine:
  - Mathematically flattens smooth SVG Bezier curves into multi-segment straight-line approximations so older parsers do not fail on unknown syntax.
  - Safely prunes advanced metadata properties, triggers, height levels, and audio zones.
  - Embeds an `__uvtt_migration_fallback` tracker in the header to preserve a historical record of the original v2 features should the file be re-imported.

#### 3. Dual-File Cryptographic DRM Architecture

- **Cryptographic Asset Signing:** Integrated Svelte's exporter with the browser's native Web Crypto API. Right before archive compilation, the exporter scans every image and audio file, hashes them asynchronously, and compiles a root `manifest.hash` validation index. This protects creators' rights by enabling VTT engines to automatically reject a map if a user has attempted to swap or modify premium visual assets.
- **Offline AES-256-GCM Decryption (`.uvtt2k`):** Replaced the legacy serverless ZKS (Zero-Knowledge Storage) clearinghouse with a robust, localized Dual-File DRM standard. Premium campaigns are now packaged as an AES-256-GCM encrypted payload (`.uvtt2z`) paired with a separate, physical 64-character hexadecimal key file (`.uvtt2k`), eliminating mandatory cloud dependencies and allowing secure, offline decryption natively in the browser via SubtleCrypto.

---

### 🎨 CAD Workspace & Geometry Tooling

#### 1. Hardware-Accelerated PixiJS v8 Viewport

- **WebGPU Native Render Engine:** Successfully migrated the client workspace from PixiJS v7 WebGL2 to the modern PixiJS v8 engine. The rendering pipeline now uses native WebGPU asynchronously while fallback WebGL2 capabilities remain intact, drastically reducing CPU/GPU overhead when handling massive coordinates, dynamic lighting arcs, and dense atmospheric particle shaders.
- **Stroke-Agnostic Hit-Testing:** WebGL engines natively evaluate stroke lines as mathematically transparent empty space, ignoring mouse-click interactions. We bypassed this limitation by generating invisible **20-pixel filled selection circles** ("Selection Nodes") at endpoints and segment midpoints, establishing a robust selection canvas.
- **Micro-Drag Tolerance:** Upgraded pointer listeners to PixiJS's native `pointertap`, which implements spatial tolerance for tiny hand-shivers (1-2 pixels) during click gestures to prevent the WebGL engine from cancelling actions.
- **Svelte Accessibility Compliance:** Wrapped interactive drawing controls, full-screen drop zones, and hud layers in clean, compiler-directed `svelte-ignore` flags, eliminating strict Svelte a11y linter warnings on WebGL containers while maintaining stable DOM performance.

#### 2. Precision Geometry Utilities

- **Vertex Snapping (Light Leak Prevention):** Legacy hand-drawn walls often have microscopic floating-point gaps (e.g., $x: 10.00$ vs $x: 10.02$) that cause raycasting engines to leak dynamic vision through solid corners. The Upgrader's ingest pipeline now passes all vertices through a shared registry, forcing any coordinates within a `SNAP_TOLERANCE` of 0.05 map units to snap together seamlessly.
- **Alt+Click Surgical Split Tool:** Implemented a geometric line projection algorithm in Svelte's map store. Holding Alt while clicking a wall segment finds the closest point, snaps it to a customizable micro-grid CAD increment, splits the array, and spawns two colinear segments, preventing light leaks when carving doors out of solid structures.
- **Shift+Click Multi-Select & Collinear Simplification:** Users can multi-select fragmented segments and merge them into unified paths. The merge action runs **Collinear Simplification**, mathematically deleting redundant `move` commands and intermediate points along a straight vector. This guarantees clean paths with a single Right-Hand direction handle.
- **Vector Reversal & Normal Flipping:** Added a manual **"Reverse Direction"** button. Because one-way sight and movement blockages are calculated dynamically using the **Right-Hand Rule** (rotating normal vectors 90 degrees clockwise from the coordinate sequence), this tool reverses the index sequence and swaps Bezier control handles to flip normal vectors 180 degrees without breaking geometry.
- **Automated Curve Smoothing:** Jagged legacy curves composed of dozens of performance-heavy straight segments can now be smoothed. Applying Catmull-Rom math to the merged paths automatically calculates tangent vectors and projects control points, fitting native, lightweight SVG cubic Bezier paths.

---

### 🚪 Relational Campaign Topology

#### 1. Dual-Topology Paradigm

- **Federated Mode (Distributed Networks):** Designed for sprawling sandbox environments where massive maps would exhaust browser memory. Independent map packages reside on disk as peer files, linking to one another natively across relative file paths (via the `relative://` URI protocol).
- **Compound Mode (Multi-Floor Archives):** Perfect for multi-story buildings, towers, and local dungeons. A single `.uvtt2z` zip archive acts as a multi-layered folder system, resolving local stairways and vertical transitions using the internal relative protocol (`internal://`).
- **URI Exporter Rewriter:** The Upgrader now allows creators to work in modular Svelte workspaces, yet compile them as a single Compound Dungeon. The exporter slugifies map names to guarantee OS-safe and URI-safe directories and dynamically translates `relative://` references to local `internal://` URIs during packaging.

#### 2. Decoupled Named Landing Zones

- **Spawn Point Anchors:** Standardized a `landing_zones` schema within the entities block. Teleport events target named zone IDs (e.g., `#lz_cellar_staircase`) rather than raw coordinates. This prevents "Brittle Coupling"—if a mapmaker updates a dungeon and moves a door, the incoming portals from external files continue to work flawlessly.
- **Camera Initialization:** Equipped zones with default flagging (`is_default`), description blocks, and target camera zoom scales, allowing VTT viewports to dynamically focus and scale upon map initialization.
- **Pre-Slicing Prediction:** The relative and internal URI parameters allow Go-based VTT backends to anticipate player movement. When player tokens step near a multi-level transition portal, Web Workers pre-load the target map's resources and begin pre-slicing Web Map Tile Service (WMTS) layers in the background, creating a zero-loading-screen cut.

---

### 🔊 Deep Environmental Simulation

#### 1. Advanced 3D-Aware Lighting

- **Dynamic Decay Physics:** Introduced points and directional light cones that support realistic inverse-square decay models alongside basic linear attenuation.
- **Rendering Boundary Rings:** The WebGL viewport renders dynamic semi-transparent colored boundaries reflecting the exact scaled physical bright and dim lighting radii, aiding precision setup.
- **Animation Profiling:** Standardized rendering parameters for flickering flame and pulsing lighting cycles directly into the data layer.

#### 2. Three-Tier Audio Hierarchy

- **Global Systems:** Outlined root-level configuration blocks for Global Music (ambient tracks) and Global Ambience (environmental loops like weather).
- **Localized Acoustic Zones:** Enabled the placement of localized audio triggers mapped to specific vector boundaries (circles and polygons).
- **Proximity Falloff:** Equipped localized zones with max volume settings and a `fade_distance` buffer. The VTT engine reads these bounds to calculate linear volume attenuation as a player token approaches, creating a fully immersive ambient atmosphere.

#### 3. Weather / Particle Emitters

- **Atmospheric Geometry:** Standardized bounded weather regions on the canvas to generate rain, snow, fog, embers, or magical effects.
- **GPU Particle Shader Mapping:** The schema stores visual configuration variables (intensity, speed, angle, and hexadecimal color tints), allowing client-side graphics cards to run optimized particle simulations natively.
- **Global Wind-Vector Inheritance:** Introduced a fluid dynamics wind model. Emitters can toggle an `inherit_global` wind vector defined in the root environment manifest, applying a linear scale multiplier. Local steam or chimney smoke can ignore global wind completely ($\text{scale} = 0.0$), while outdoor courtyard rain bends dynamically to match a global blizzard ($\text{scale} = 1.0$).
- **3D Collision Modes:** Configured advanced physical collision properties for particles:
  - `none`: Particles render continuously through all objects.
  - `mask_under_overhead`: Weather is dynamically masked on the GPU if particles fall under active roof layers.
  - `ground_terminate`: Particles terminate instantly and trigger splashing or pooling shaders when hitting defined floor levels.
  - `wall_bounce`: Particles physically bounce off standard wall geometry overlapping their height ranges.

#### 4. Overhead Layer Masks (Ceilings and Canopies)

- **Z-Axis Height Boundaries:** Added support for structural polygons representing roofs and tree canopies.
- **Dynamic Transparency Fading:** Enables VTT engines to track player height levels and token positions, smoothly fading roof layers to transparent when a character steps underneath.

---

### 📦 DevOps, Automation, and CI/CD

- **GitHub Pages CD Pipeline:** Engineered a fully automated GitHub Actions pipeline (`deploy-upgrader.yml`). On pushing to the main branch, a secure runner compiles production assets and deploys static code directly to GitHub's content delivery network.
- **Dynamic Vite Base Routing:** Standardized a dynamic subfolder routing configuration in `vite.config.js`. It evaluates environment variables, allowing the local dev server to run cleanly at root (`/`) while automatically resolving nested repository URLs on GitHub Pages to prevent strict MIME type errors.
