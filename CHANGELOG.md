# 🗺️ Universal Virtual Tabletop v2 (UVTT v2) Master Changelog

All notable changes to the **Universal Virtual Tabletop v2 Specification** and its official **Reference Upgrader Web App** will be documented in this file. 

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and adheres to Semantic Versioning for specifications.

---

## [2.0.0-rc1] - 2026-07-12

This release marks the official finalization of the **UVTT v2.0.0-rc1 Specification** and the complete rollout of its **Reference Upgrader Web App**. This milestone transforms tabletop campaign maps from isolated, flat 2D graphics into a dynamic, performance-optimized, and interconnected **Topological Spatial Network** [176, 177, 224, 233].

### 🚀 Core Architectural Enhancements

#### 1. Decoupled, Zipped Binary Container (`.uvtt2z`)
*   **Asset Separation:** Replaced legacy V1 Base64-in-JSON payload structures with a zipped archive layout (.uvtt2z) [11, 13, 225, 234]. By detaching massive, premium binary artwork and audio loops into a dedicated `assets/` subdirectory [13, 225, 247] and keeping structural coordinates in text-based JSON, we eliminate the ~33% Base64 encoding overhead that causes browser Out-Of-Memory (OOM) crashes on 8K assets [212, 233, 275].
*   **Modular Sub-manifests:** The package structure is split into three highly optimized files [134, 136, 137, 139]:
    *   `manifest.json`: Stores lightweight index metadata, resolution data, and global environment variables to enable millisecond-level map-library catalog scanning without parsing massive coordinate files [136, 138, 139, 230].
    *   `geometry.json`: Houses system-neutral structural vectors, including walls, portals, and overhead boundaries [136, 225, 230].
    *   `entities.json`: Collects logic-driven interactive layers, containing lights, teleport triggers, localized audio zones, spawns, and weather emitters [136, 225, 230].

#### 2. In-Memory Normalized Model (IMNM) Migration Router
*   **Bi-Directional Pipeline:** Built a centralized migration router (`UvttMigrationEngine`) to decouple version parsing [152, 162, 163]. Incoming map payloads (Legacy V1 or early V2 variants) are translated upward into a reactive, master in-memory state tree managed via a Svelte store [152, 153, 158]. Outbound exports are then compiled or gracefully down-sampled based on the user's selected engine profile [152, 154, 162, 163].
*   **Graceful Degradation Protocol:** To prevent backward-compatibility anxiety, when a creator compiles a modern map back down to a legacy V1 `.dd2vtt` structure [162, 164, 229, 275], the engine:
    *   Mathematically flattens smooth SVG Bezier curves into multi-segment straight-line approximations so older parsers do not fail on unknown syntax [156, 162, 163].
    *   Safely prunes advanced metadata properties, triggers, height levels, and audio zones [155, 156, 162, 229].
    *   Embeds an `__uvtt_migration_fallback` tracker in the header to preserve a historical record of the original v2 features should the file be re-imported [156, 162, 229].

#### 3. Split-Resolution Cryptographic DRM Layer
*   **Cryptographic Asset Signing:** Integrated Svelte's exporter with the browser's native Web Crypto API [248, 249]. Right before archive compilation, the exporter scans every image and audio file, hashes them asynchronously, and compiles a root `manifest.hash` validation index [248, 249, 250]. This protects creators' rights by enabling VTT engines to automatically reject a map if a user has attempted to swap or modify premium visual assets [248, 250].
*   **ZKS Clearinghouse Authorization:** Established standard APIs and integration pathways for edge authentication and license verification routines, allowing platforms to protect commercial map catalogs [252, 255].

---

### 🎨 CAD Workspace & Geometry Tooling

#### 1. Hardware-Accelerated PixiJS v8 Viewport
*   **WebGPU Native Render Engine:** Successfully migrated the client workspace from PixiJS v7 WebGL2 to the modern PixiJS v8 engine [278, 279, 282, 283]. The rendering pipeline now uses native WebGPU asynchronously while fallback WebGL2 capabilities remain intact [279, 282, 283], drastically reducing CPU/GPU overhead when handling massive coordinates, dynamic lighting arcs, and dense atmospheric particle shaders [279].
*   **Stroke-Agnostic Hit-Testing:** WebGL engines natively evaluate stroke lines as mathematically transparent empty space, ignoring mouse-click interactions [1, 3, 4]. We bypassed this limitation by generating invisible **20-pixel filled selection circles** ("Selection Nodes") at endpoints and segment midpoints [4, 6, 275], establishing a robust selection canvas [5, 6].
*   **Micro-Drag Tolerance:** Upgraded pointer listeners to PixiJS's native `pointertap` [2], which implements spatial tolerance for tiny hand-shivers (1-2 pixels) during click gestures to prevent the WebGL engine from cancelling actions [1, 2].
*   **Svelte Accessibility Compliance:** Wrapped interactive drawing controls, full-screen drop zones, and hud layers in clean, compiler-directed `svelte-ignore` flags [26, 34], eliminating strict Svelte a11y linter warnings on WebGL containers while maintaining stable DOM performance [24, 25, 27, 34].

#### 2. Precision Geometry Utilities
*   **Vertex Snapping (Light Leak Prevention):** Legacy hand-drawn walls often have microscopic floating-point gaps (e.g., $x: 10.00$ vs $x: 10.02$) that cause raycasting engines to leak dynamic vision through solid corners [20, 21]. The Upgrader's ingest pipeline now passes all vertices through a shared registry, forcing any coordinates within a `SNAP_TOLERANCE` of 0.05 map units to snap together seamlessly [21, 23, 68, 275].
*   **Alt+Click Surgical Split Tool:** Implemented a geometric line projection algorithm in Svelte's map store [37, 38]. Holding Alt while clicking a wall segment finds the closest point, snaps it to a customizable micro-grid CAD increment, splits the array, and spawns two colinear segments [37, 39, 42, 43], preventing light leaks when carving doors out of solid structures [37].
*   **Shift+Click Multi-Select & Collinear Simplification:** Users can multi-select fragmented segments and merge them into unified paths [29, 30, 70]. The merge action runs **Collinear Simplification** [30, 116], mathematically deleting redundant `move` commands and intermediate points along a straight vector [115, 116, 117]. This guarantees clean paths with a single Right-Hand direction handle [116, 117].
*   **Vector Reversal & Normal Flipping:** Added a manual **"Reverse Direction"** button [210, 211]. Because one-way sight and movement blockages are calculated dynamically using the **Right-Hand Rule** (rotating normal vectors 90 degrees clockwise from the coordinate sequence) [18, 54, 227], this tool reverses the index sequence and swaps Bezier control handles to flip normal vectors 180 degrees without breaking geometry [210, 211].
*   **Automated Curve Smoothing:** Jagged legacy curves composed of dozens of performance-heavy straight segments can now be smoothed [62, 64]. Applying Catmull-Rom math to the merged paths automatically calculates tangent vectors and projects control points, fitting native, lightweight SVG cubic Bezier paths [65, 66, 70].

---

### 🚪 Relational Campaign Topology

#### 1. Dual-Topology Paradigm
*   **Federated Mode (Distributed Networks):** Designed for sprawling sandbox environments where massive maps would exhaust browser memory [173, 178]. Independent map packages reside on disk as peer files, linking to one another natively across relative file paths (via the `relative://` URI protocol) [172, 178].
*   **Compound Mode (Multi-Floor Archives):** Perfect for multi-story buildings, towers, and local dungeons [171, 172, 193]. A single `.uvtt2z` zip archive acts as a multi-layered folder system [171, 172, 193, 225], resolving local stairways and vertical transitions using the internal relative protocol (`internal://`) [171, 178, 194, 225].
*   **URI Exporter Rewriter:** The Upgrader now allows creators to work in modular Svelte workspaces, yet compile them as a single Compound Dungeon [193, 194, 198]. The exporter slugifies map names to guarantee OS-safe and URI-safe directories [195, 196, 198] and dynamically translates `relative://` references to local `internal://` URIs during packaging [194, 197, 198].

#### 2. Decoupled Named Landing Zones
*   **Spawn Point Anchors:** Standardized a `landing_zones` schema within the entities block [128, 149]. Teleport events target named zone IDs (e.g., `#lz_cellar_staircase`) rather than raw coordinates [128, 129, 131, 179]. This prevents "Brittle Coupling"—if a mapmaker updates a dungeon and moves a door, the incoming portals from external files continue to work flawlessly [127, 129].
*   **Camera Initialization:** Equipped zones with default flagging (`is_default`), description blocks, and target camera zoom scales [128, 146, 147], allowing VTT viewports to dynamically focus and scale upon map initialization [141, 146, 228].
*   **Pre-Slicing Prediction:** The relative and internal URI parameters allow Go-based VTT backends to anticipate player movement [141, 143, 180]. When player tokens step near a multi-level transition portal, Web Workers pre-load the target map's resources and begin pre-slicing Web Map Tile Service (WMTS) layers in the background, creating a zero-loading-screen cut [141, 143, 174, 180].

---

### 🔊 Deep Environmental Simulation

#### 1. Advanced 3D-Aware Lighting
*   **Dynamic Decay Physics:** Introduced points and directional light cones that support realistic inverse-square decay models alongside basic linear attenuation [73, 74, 228, 295].
*   **Rendering Boundary Rings:** The WebGL viewport renders dynamic semi-transparent colored boundaries reflecting the exact scaled physical bright and dim lighting radii, aiding precision setup [74, 75, 79].
*   **Animation Profiling:** Standardized rendering parameters for flickering flame and pulsing lighting cycles directly into the data layer [75, 295].

#### 2. Three-Tier Audio Hierarchy
*   **Global Systems:** Outlined root-level configuration blocks for Global Music (ambient tracks) and Global Ambience (environmental loops like weather) [91, 113, 201, 206, 208].
*   **Localized Acoustic Zones:** Enabled the placement of localized audio triggers mapped to specific vector boundaries (circles and polygons) [91, 92, 95, 297].
*   **Proximity Falloff:** Equipped localized zones with max volume settings and a `fade_distance` buffer [91, 92, 95, 297]. The VTT engine reads these bounds to calculate linear volume attenuation as a player token approaches, creating a fully immersive ambient atmosphere [95, 228].

#### 3. Weather / Particle Emitters
*   **Atmospheric Geometry:** Standardized bounded weather regions on the canvas to generate rain, snow, fog, embers, or magical effects [215, 216, 218, 228, 298].
*   **GPU Particle Shader Mapping:** The schema stores visual configuration variables (intensity, speed, angle, and hexadecimal color tints) [215, 216, 218, 228, 298], allowing client-side graphics cards to run optimized particle simulations natively [215, 218].
*   **Global Wind-Vector Inheritance:** Introduced a fluid dynamics wind model [284, 286]. Emitters can toggle an `inherit_global` wind vector defined in the root environment manifest, applying a linear scale multiplier [285, 286, 299]. Local steam or chimney smoke can ignore global wind completely ($\text{scale} = 0.0$), while outdoor courtyard rain bends dynamically to match a global blizzard ($\text{scale} = 1.0$) [285, 286].
*   **3D Collision Modes:** Configured advanced physical collision properties for particles [301]:
    *   `none`: Particles render continuously through all objects [301].
    *   `mask_under_overhead`: Weather is dynamically masked on the GPU if particles fall under active roof layers [301].
    *   `ground_terminate`: Particles terminate instantly and trigger splashing or pooling shaders when hitting defined floor levels [301].
    *   `wall_bounce`: Particles physically bounce off standard wall geometry overlapping their height ranges [301].

#### 4. Overhead Layer Masks (Ceilings and Canopies)
*   **Z-Axis Height Boundaries:** Added support for structural polygons representing roofs and tree canopies [92, 109, 110, 113].
*   **Dynamic Transparency Fading:** Enables VTT engines to track player height levels and token positions, smoothly fading roof layers to transparent when a character steps underneath [92, 109, 113, 228].

---

### 📦 DevOps, Automation, and CI/CD

*   **GitHub Pages CD Pipeline:** Engineered a fully automated GitHub Actions pipeline (`deploy-upgrader.yml`) [304]. On pushing to the main branch, a secure runner compiles production assets and deploys static code directly to GitHub's content delivery network [304].
*   **Dynamic Vite Base Routing:** Standardized a dynamic subfolder routing configuration in `vite.config.js` [306, 307]. It evaluates environment variables, allowing the local dev server to run cleanly at root (`/`) while automatically resolving nested repository URLs on GitHub Pages to prevent strict MIME type errors [306, 307].
