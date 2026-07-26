# 🗺️ Announcing Universal VTT v2 (UVTT v2) & The WebGPU Upgrader Web App
**To our incredible community of digital artists, fantasy cartographers, Patreon creators, and Gamemasters:**

For years, we have pushed the limits of virtual tabletop storytelling [101]. We’ve painted breathtaking multi-level dungeons, drafted sprawling cityscapes, and designed legendary encounters [101]. Yet, our file formats have kept us trapped in the "flat earth" era of 2D planes, plagued by sluggish performance, brittle coordinates, and file-bloat crashes [101]. 

Today, we are breaking down those walls [102]. We are proud to introduce **Universal VTT v2 (UVTT v2) Version 2.0.0**—an open-source, high-performance, and fully collaborative standard for interconnected campaign mapping [57, 102]—alongside the **UVTT v2 Upgrader**, a free, no-install, browser-based graphical level editor [102].

![UVTT v2 Launch Header](uvtt_v2_launch_header.jpg)

---

### 🚀 Why UVTT v2? The Death of "Flat Earth" Mapping
Legacy formats served us well during the early days of digital play, but they suffer from major structural bottlenecks that limit modern gameplay [102]. UVTT v2 transforms map files from static, isolated canvases into **Topological Spatial Networks** [34, 102]:

*   **Zero-Lag Asset Streaming (.uvtt2z):** Farewell to browser Out-Of-Memory (OOM) crashes [103]. Legacy formats embed massive high-resolution images as Base64 strings directly inside JSON payloads, inflating file sizes by ~33.3% [40, 103]. UVTT v2 introduces a zipped binary archive container (`.uvtt2z`) that completely detaches raw WebP/PNG maps from metadata, enabling instantaneous directory scanning and lightning-fast loading [13, 103].
*   **Modular Multi-Floor Compound Dungeons:** Whether you are building a 3-story wizard's tower or a 24-level mega-dungeon, UVTT v2 links your floors natively using standardized URIs [103]. In **Compound Mode**, our directory tree uses isolated level folders (`maps/[map-slug]/`) [86], each storing its own localized `manifest.json`, `geometry.json`, and `entities.json` coordinates along with the active `.webp` image binaries [86]. This allows clients to lazy-load assets and geometry on-demand [169], resolving transitions smoothly via the `internal://` protocol [7, 61]. Standing standalone maps are linked via **Federated Mode** using `relative://` URIs [7, 62].
*   **Cinematic Landing Zones:** No more dropping players blindly into the pitch-black top-left corner (0,0) of a scene [103]. You can now define explicit starting coordinates, compass facing angles, and camera zoom profiles for different party entrances, enabling seamless vertical and horizontal transitions [103].

---

### 🎨 The UVTT v2 Upgrader: Your Dynamic Level-Design Workspace
To carry your entire legacy map catalog cleanly into the future, we’ve built the **UVTT v2 Upgrader Web App** [104]. It is entirely free, requires **no installation**, and runs natively in your browser using hardware-accelerated WebGPU/WebGL2 engines [104].

#### 1. Watertight Vector Drafting (No More Light Leaks)
*   **Vertex Snapping:** The upgrader automatically snaps nearby endpoints within a microscopic tolerance of $0.05$ map units, mathematically sealing room corners so dynamic line-of-sight rays can never pierce through solid walls [6, 70, 105].
*   **Collinear Simplification:** Stitch fragmented, jagged wall paths into a single cohesive W3C SVG-style path with a single click, keeping file sizes lightweight [6, 105].
*   **Alt+Click Surgical Cuts:** Draft like an architect! Draw continuous structural outer walls, then hold Alt to slice perfect, colinear gaps for doors and windows—permanently preventing raycasting gaps [6, 105].
*   **Visual Midpoint Normal Ticks:** Displays perpendicular midpoint normal ticks calculated via the mathematical **Right-Hand Rule**, letting you visually verify directional line-of-sight blocking (like one-way windows or illusory walls) at a glance [6, 68, 105].

#### 2. Deep Environmental Simulation
*   **Hardware-Accelerated WebGPU Renderer:** The upgrader viewport has migrated natively to **PixiJS v8 and WebGPU** [5, 41]. This reduces CPU/GPU overhead drastically when executing massive coordinate maps, real-time lighting arcs, and dense particle effects [5].
*   **3D Point & Directional Lights:** Customize rich light setups featuring custom hex colors, pulse/flicker animation states, and realistic **Inverse-Square Decay physics** [9, 71, 106]:
    $$I = \\frac{I_0}{d^2}$$
*   **Three-Tier Audio & Localized Acoustic Zones:** Map proximity-based 3D audio triggers with customizable fade radii ($r$) [10, 74, 106]. Proximity damping calculations are mathematically clamped to prevent negative volume bounds or sudden audio pops [18, 74]:
    $$V = \\max\\left(0, \\min\\left(V_{\\text{max}}, V_{\\text{max}} \\times \\left(1 - \\frac{d}{r}\\right)\\right)\\right)$$
    Add `muffled_by_geometry: true` to dynamically muffle sound loops when standard walls or closed portals intersect the listener's line of sight [153].
*   **Atmospheric Weather Emitters:** Draw custom particle zones (rain, snow, fog, embers, magic) with adjustable speed, intensity, and direction [11, 75, 106]. Emitters can blanket the entire canvas automatically using `is_global: true` [154], rendering above ceilings or on the ground via explicit `render_layer` parameters (`above_overhead`, `below_overhead`, `ground_level`) [154].
*   **Global Wind-Vector Inheritance:** Emitters can inherit and blend dynamically with global map-wide wind settings [11, 75, 106]. The final particle velocity vector $\\vec{v}_{\\text{particle}}$ is calculated mathematically as [75]:
    $$\\vec{v}_{\\text{particle}} = \\vec{v}_{\\text{emitter\\_base}} + \\left(\\text{influence\\_scale} \\times \\vec{v}_{\\text{global\\_wind}}\\right)$$\
*   **3D Collision Height Controls (`collision_mode`):** Define vertical Z-axis boundaries for weather events and overhead roof layers [11, 75, 106]. Emitters support four advanced collision behaviors [75]:
    *   `none`: Particles render continuously through all objects [75].
    *   `mask_under_overhead`: Weather is dynamically masked on the GPU if particles fall under active roof layers [75].
    *   `ground_terminate`: Particles terminate instantly and trigger splash/pooling shaders upon hitting defined floor planes [75].
    *   `wall_bounce`: Particles physically bounce off standard wall geometry overlapping their height ranges [75].

---

### 📦 Zero Vendor Lock-In: The Indestructible Bridge
We believe your art and maps belong to you—not a single closed platform [107]. Built on an **In-Memory Normalized Model (IMNM)**, the Upgrader web app acts as a lossless, bi-directional bridge [26, 107]. 

Upgrade legacy maps to UVTT v2 to leverage cutting-edge WebGPU features, or trigger **Graceful Degradation** to compile a v2 map back down to a legacy V1 format—automatically flattening Bezier curves back into linear approximations and pruning advanced properties so older, legacy VTT engines won't crash [3, 81, 107].

---

### 🛡️ Split-Resolution Cryptographic DRM Layer
To protect creators' intellectual property without restricting backwards compatibility, visual assets are divided into two distinct structural layers [76]:
*   **The Public Layer (`basemap.webp`):** A heavily down-sampled, unencrypted preview image capped at exactly **50 pixels per grid square** with a visible digital watermark burned directly into the pixels [31, 76, 116]. This acts as a graceful fallback for basic or legacy tools [76, 116].
*   **The Protected Layer (.uvtt2k):** Secure archives utilize **AES-256-GCM envelope encryption** [84]. This protects the entire zipped campaign directory at rest [84]. To decompress or stream, compliant clients perform a serverless handshake [158], derive the key deterministically using **HMAC-SHA256** [158], and decrypt the container in volatile memory [156, 172].
*   **Volatile Memory Rule:** Unencrypted high-resolution bytes must **never** touch persistent storage or browser caches [77, 117]. Decryption happens strictly in isolated RAM, and render viewports must synchronously revoke Blob URLs (`URL.revokeObjectURL(blobUrl)`) immediately following texture binding [16, 117].
*   **Root Archive Receipt (`manifest.hash`):** To prevent malicious payload injections, every archive includes a flat, newline-separated index mapping the path of every single file within the archive to its cryptographically verified SHA-256 hash checksum [78, 121].
*   **Zero-Knowledge-Storage (ZKS) Clearinghouse:** Storefront servers never store raw symmetric keys in databases [79, 125]. Instead, edge nodes dynamically derive the symmetric key using deterministic HMAC-SHA256 math [79, 125]:
    $$\\text{Decryption Key} = \\text{HMAC-SHA256}(\\text{RETAILER\\_MASTER\\_SECRET}, \\text{Product SKU} + \\text{Key Salt})$$\

---

### 🤝 Join the Movement
Universal VTT v2 is an open, community-driven standard. By decoupling structural layout data from premium high-resolution art assets, we protect creators' work with cryptographic signatures while welcoming open collaboration [108].
*   **Upgrade Your Maps Now:** [Live Upgrader Web App Link] [108]
*   **Read the Specifications & Contribute:** [GitHub Repository Link] [108]

*Let’s build the future of tabletop cartography, together [108].*
