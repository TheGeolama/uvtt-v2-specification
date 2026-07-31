# 🗺️ Announcing Universal VTT v2 (UVTT v2) & The WebGPU Upgrader Web App

**To our incredible community of digital artists, fantasy cartographers, Patreon creators, and Gamemasters:**

For years, we have pushed the limits of virtual tabletop storytelling. We’ve painted breathtaking multi-level dungeons, drafted sprawling cityscapes, and designed legendary encounters. Yet, our file formats have kept us trapped in the "flat earth" era of 2D planes, plagued by sluggish performance, brittle coordinates, and file-bloat crashes.

Today, we are breaking down those walls. We are proud to introduce **Universal VTT v2 (UVTT v2) Version 2.0.0**—an open-source, high-performance, and fully collaborative standard for interconnected campaign mapping—alongside the **UVTT v2 Upgrader**, a free, no-install, browser-based graphical level editor.

![UVTT v2 Launch Header](uvtt_v2_launch_header.jpg)

---

### 🚀 Why UVTT v2? The Death of "Flat Earth" Mapping

Legacy formats served us well during the early days of digital play, but they suffer from major structural bottlenecks that limit modern gameplay. UVTT v2 transforms map files from static, isolated canvases into **Topological Spatial Networks**:

- **Zero-Lag Asset Streaming (.uvtt2z):** Farewell to browser Out-Of-Memory (OOM) crashes. Legacy formats embed massive high-resolution images as Base64 strings directly inside JSON payloads, inflating file sizes by ~33%. UVTT v2 introduces a zipped binary archive container (`.uvtt2z`) that completely detaches raw WebP/PNG maps from metadata, enabling instantaneous directory scanning and lightning-fast loading.
- **Smart Standalone Assets (.uvtt2a):** Selling tokens, props, or soundscapes? The new `.uvtt2a` format bundles artwork and audio with a lightweight metadata sheet. When a GM drops your torch prop onto a map, it instantly scales to the grid, ignites a flickering fire light, plays a crackling sound loop, and triggers heat embers—all with a single mouse click.
- **Modular Multi-Floor Compound Dungeons:** Whether you are building a 3-story wizard's tower or a 24-level mega-dungeon, UVTT v2 links your floors natively using standardized URIs. In **Compound Mode**, our directory tree uses isolated level folders (`maps/[map-slug]/`), each storing its own localized `manifest.json`, `geometry.json`, and `entities.json` coordinates along with the active `.webp` image binaries. This allows clients to lazy-load assets and geometry on-demand, resolving transitions smoothly via the `internal://` protocol. Standalone maps are linked via **Federated Mode** using `relative://` URIs.
- **Cinematic Landing Zones:** No more dropping players blindly into the pitch-black top-left corner of a scene. You can now define explicit starting coordinates, compass facing angles, and camera zoom profiles for different party entrances, enabling seamless vertical and horizontal transitions.

---

### 🎨 The UVTT v2 Upgrader: Your Dynamic Level-Design Workspace

To carry your entire legacy map catalog cleanly into the future, we’ve built the **UVTT v2 Upgrader Web App**. It is entirely free, requires **no installation**, and runs natively in your browser using hardware-accelerated WebGPU/WebGL2 engines.

#### 1. Watertight Vector Drafting (No More Light Leaks)

- **Vertex Snapping:** The upgrader automatically snaps nearby endpoints within a microscopic tolerance of 0.05 map units, mathematically sealing room corners so dynamic line-of-sight rays can never pierce through solid walls.
- **Collinear Simplification:** Stitch fragmented, jagged wall paths into a single cohesive W3C SVG-style path with a single click, keeping file sizes lightweight.
- **Alt+Click Surgical Cuts:** Draft like an architect! Draw continuous structural outer walls, then hold Alt to slice perfect, colinear gaps for doors and windows—permanently preventing raycasting gaps.
- **Visual Midpoint Normal Ticks:** Displays perpendicular midpoint normal ticks calculated via the mathematical **Right-Hand Rule**, letting you visually verify directional line-of-sight blocking (like one-way windows or illusory walls) at a glance.

#### 2. Deep Environmental Simulation

- **Hardware-Accelerated WebGPU Renderer:** The upgrader viewport has migrated natively to **PixiJS v8 and WebGPU**. This reduces CPU/GPU overhead drastically when executing massive coordinate maps, real-time lighting arcs, and dense particle effects.
- **3D Point & Directional Lights:** Customize rich light setups featuring custom hex colors, pulse/flicker animation states, and realistic **Inverse-Square Decay physics**:
  $$I = \frac{I_0}{d^2}$$
- **Three-Tier Audio & Localized Acoustic Zones:** Map proximity-based 3D audio triggers with customizable fade radii ($r$). Proximity damping calculations are mathematically clamped to prevent negative volume bounds or sudden audio pops:
  $$V = \max\left(0, \min\left(V_{\text{max}}, V_{\text{max}} \times \left(1 - \frac{d}{r}\right)\right)\right)$$
  Add `muffled_by_geometry: true` to dynamically muffle sound loops when standard walls or closed portals intersect the listener's line of sight.
- **Atmospheric Weather Emitters:** Draw custom particle zones (rain, snow, fog, embers, magic) with adjustable speed, intensity, and direction. Emitters can blanket the entire canvas automatically using `is_global: true`, rendering above ceilings or on the ground via explicit `render_layer` parameters (`above_overhead`, `below_overhead`, `ground_level`).
- **Global Wind-Vector Inheritance:** Emitters can inherit and blend dynamically with global map-wide wind settings. The final particle velocity vector $\vec{v}_{\text{particle}}$ is calculated mathematically as:
  $$\vec{v}_{\text{particle}} = \vec{v}_{\text{emitter\_base}} + \left(\text{influence\_scale} \times \vec{v}_{\text{global\_wind}}\right)$$
- **3D Collision Height Controls (`collision_mode`):** Define vertical Z-axis boundaries for weather events and overhead roof layers. Emitters support four advanced collision behaviors:
  - `none`: Particles render continuously through all objects.
  - `mask_under_overhead`: Weather is dynamically masked on the GPU if particles fall under active roof layers.
  - `ground_terminate`: Particles terminate instantly and trigger splash/pooling shaders upon hitting defined floor planes.
  - `wall_bounce`: Particles physically bounce off standard wall geometry overlapping their height ranges.

---

### 📦 Zero Vendor Lock-In: The Indestructible Bridge

We believe your art and maps belong to you—not a single closed platform. Built on an **In-Memory Normalized Model (IMNM)**, the Upgrader web app acts as a lossless, bi-directional bridge.

Upgrade legacy maps to UVTT v2 to leverage cutting-edge WebGPU features, or trigger **Graceful Degradation** to compile a v2 map back down to a legacy V1 format—automatically flattening Bezier curves back into linear approximations and pruning advanced properties so older, legacy VTT engines won't crash.

---

### 🛡️ Dual-File Cryptographic DRM Architecture

To protect creators' intellectual property without restricting backwards compatibility or forcing vendor lock-in, UVTT v2 introduces a robust, localized security standard:

- **Offline AES-256-GCM Decryption (`.uvtt2k`):** We have entirely eliminated mandatory cloud dependencies and serverless handshakes. Premium campaigns are now packaged as an AES-256-GCM encrypted payload (`.uvtt2z`) paired with a separate, physical 64-character hexadecimal key file (`.uvtt2k`). This allows secure, offline decryption natively in the browser via the W3C SubtleCrypto API.
- **Root Archive Receipt (`manifest.hash`):** To prevent malicious payload injections or unauthorized asset swapping, every archive includes a flat, newline-separated index mapping the path of every single file within the archive to its cryptographically verified SHA-256 hash checksum.
- **Volatile Memory Rule:** Unencrypted high-resolution bytes must **never** touch persistent storage or browser caches. Decryption happens strictly in isolated RAM, and render viewports must synchronously scrub decrypted Blobs and ImageBitmaps from memory immediately following texture binding.

---

### 🤝 Join the Movement

Universal VTT v2 is an open, community-driven standard. By decoupling structural layout data from premium high-resolution art assets, we protect creators' work with cryptographic signatures while welcoming open collaboration.

- **Upgrade Your Maps Now:** [Live Upgrader Web App Link]
- **Read the Specifications & Contribute:** [GitHub Repository Link]

_Let’s build the future of tabletop cartography, together._
