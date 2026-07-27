### Reddit r/VTT Launch Thread

**Title: Announcing Universal VTT v2 (UVTT v2) & The Live WebGPU Upgrader Web App — Death to Base64 Bloat and "Flat Earth" Mapping!**

The **Open Virtual Tabletop Consortium (OVTC)** is thrilled to announce the official release of the **Universal Virtual Tabletop v2 (UVTT v2) Version 2.0.0 Systems Specification**, alongside the immediate launch of the **FOSS Web Upgrader**, a free, no-install, browser-based graphical level-design workspace hosted natively at **[upgrader.universalvtt.org](https://upgrader.universalvtt.org)** [README-v2.md]!

For years, virtual tabletop mapping has been held back by legacy v1 formats (`.dd2vtt` and `.df2vtt`). Embedding multi-megabyte visual assets as Base64 strings directly inside single monolithic JSON payloads inflates file sizes by $\approx 33.3\%$, choking browser threads and triggering severe Out-of-Memory (OOM) crashes on modern high-resolution assets.

**UVTT v2 completely breaks down these walls by transitioning maps into highly interactive nodes within a Topological Spatial Network!**

Here is a breakdown of what the v2 standard brings to the VTT ecosystem:

#### 📦 1. The Three New Packaging Standards
Rather than forcing all content into a single file style, UVTT v2 establishes three highly optimized container models:
*   **`.uvtt2z` (Standard Archive):** An unencrypted ZIP container that completely isolates lightweight JSON layout metadata from heavy binary WebP map rasters and OGG ambient tracks. This enables sub-second directory catalog scanning and streamable background loading.
*   **`.uvtt2k` (Encrypted Archive):** A secure container utilizing **AES-256-GCM** encryption. It is designed to secure premium cartography while enforcing our strict **Volatile Memory Disposal Protocol** (decrypted assets exist only in system-isolated RAM and are synchronously wiped via hard memory scrubs before leaving heap memory).
*   **`.uvtt2a` (Standalone Asset Pack):** Specifically designed for asset-only creators who distribute tokens, props, and audio [universal-vtt-v2-spec.md]. This format supports pre-configured grid footprints [universal-vtt-v2-spec.md] and **`auto_emits` arrays**, automatically spawning 3D point lights [entities.schema.json.txt], localized sound zones [entities.schema.json.txt], or floating GPU particle shaders [entities.schema.json.txt] when dragged onto a map [universal-vtt-v2-spec.md]!

#### 🏰 2. Advanced Multi-Floor campaign Topology
*   **Decoupled Compound Dungeons:** Multi-level maps are nested under modular, isolated subdirectories (`maps/[map-slug]/`). VTTs can query global campaign coordinates in milliseconds, loading heavy high-resolution visuals only when a token crosses floors.
*   **Topological Spatial URIs:** Connect levels natively! Intra-map stairs are resolved via the **`internal://`** protocol, while sprawling, multi-file sandbox campaigns link peers using **`relative://`** URIs.
*   **Pre-Slicing Prediction:** If a token approaches a transition trigger, the engine pre-fetches and caches target assets within a customizable `prediction_trigger_radius` for zero-loading-screen level cuts!

#### 🔊 3. High-Performance World Simulation
*   **3D Point & Directional Lights:** Positioned in 3D coordinate space $(X, Y, Z)$, supporting dynamic flickering and physical **Inverse-Square Decay** ($I = I_0 / d^2$).
*   **Occluded Proximity Audio:** Map localized sound zones using mathematically clamped volume curves to prevent negative boundaries or audio pops:
    $$V = \max\left(0, \min\left(V_{\text{max}}, V_{\text{max}} \times \left(1 - \frac{d}{r}\right)\right)\right)$$
    Toggling `muffled_by_geometry` applies dynamic raycasting, dampening volume through solid walls and doors.
*   **Wind-Vector Particle Emitters:** Bounded weather emitters (rain, snow, fog, embers, magic) scale their base speeds against global wind vectors defined in the root manifest:
    $$\vec{v}_{\text{particle}} = \vec{v}_{\text{emitter\_base}} + \left(\text{influence\_scale} \times \vec{v}_{\text{global\_wind}}\right)$$
*   **Cross-Entity Event Actions:** Triggers (like pressure plates) support dynamic state actions, instantly changing hidden trap coordinates or secret doors from `gm_only` visibility directly to the players' screens.

#### 🤝 4. Zero Vendor Lock-In & Open Governance
We believe your creative work belongs to you. UVTT v2 operates on a bi-directional **In-Memory Normalized Model (IMNM)**. You can upgrade legacy maps to v2 WebGPU standards, or run our **Graceful Degradation Protocol** to compile a v2 layout back down to a legacy V1 `.dd2vtt`—mathematically flattening SVG curves into multi-point approximations so legacy platforms won’t crash.

To guarantee developer safety, the specification is dual-licensed:
1.  **Schemas and Folder Trees** are dedicated to the public domain under **CC0 1.0 Universal**.
2.  **All Reference Implementations** (including Go and TypeScript WebCrypto parsers) are licensed under **Apache License 2.0**, granting a perpetual, royalty-free, and irrevocable patent license to all commercial or open-source platforms!

#### 🛠️ Getting Started
*   **Check out the Web App:** [upgrader.universalvtt.org](https://upgrader.universalvtt.org) [README-v2.md]
*   **Explore the Repository & Specifications:** [repo.universalvtt.org](https://repo.universalvtt.org)
*   **Deep-Dive the Spec & Docs:** [www.universalvtt.org](https://www.universalvtt.org)
*   **Get in Touch:** Reach our core team at `hello@universalvtt.org` or our compliance auditors at `compliance@universalvtt.org`!

***

### 💬 Discord Launch Announcement

**PING:** `@here` or `@everyone` (depending on server preferences)
**Channel:** `#announcements` or `#vtt-news`

***

## 🗺️ Universal Virtual Tabletop v2 (UVTT v2) Version 2.0.0 is officially LIVE!

Tabletop cartography is breaking out of the "flat earth" era! Today, we are proud to release the **Universal VTT v2 (UVTT v2) Systems Specification** alongside the **UVTT v2 Upgrader**, a free, zero-install, browser-based graphical level editor running on a hardware-accelerated **PixiJS v8 / WebGPU graphics engine**!

🔗 **Launch the Upgrader now:** https://upgrader.universalvtt.org [README-v2.md]  
📖 **Read the Specifications & Docs:** https://www.universalvtt.org  
💻 **Explore Reference Code & Schemas:** https://repo.universalvtt.org  

### 🚀 Why Upgrade to UVTT v2?
Legacy V1 formats (`.dd2vtt` and `.df2vtt`) embed massive visual assets as Base64 strings directly inside raw JSON. This causes a $\approx 33.3\%$ data inflation that routinely freezes UI threads and crashes web browsers on mobile or tablet devices.

**UVTT v2 solves these structural limitations natively:**
*   **Zero-Lag ZIP Container (`.uvtt2z`):** Detaches heavy raster graphics and audio tracks from coordinate data. Read vector layouts instantly while streaming image assets in the background.
*   **Modular Multi-Floor Topology:** Multi-story buildings are now packaged into isolated directories (`maps/[map-slug]/`), allowing you to lazy-load layout data only when a token actively transitions floors.
*   **3D Points, Audio, and Emitters:** Drop point and directional lights with physical **Inverse-Square Decay** ($I = I_0 / d^2$), configure 3D sound zones with dynamic material-aware raycast muffling, and draw custom particle emitters (rain, snow, fog, embers) that blend directly with global windy vector headings!
*   **Cross-Entity Event State Toggles:** Make maps run themselves! Drag-and-drop hidden pit traps tagged `gm_only`. Step your player tokens over a pressure plate trigger, and the map instantly updates the trap's visibility state, making it dynamically appear on the players' screens!

### 🔒 Cryptographic Protections for Artists
*   **Tamper-Proof Receipts (`manifest.hash`):** The exporter compiles a cryptographic SHA-256 hash layout of all assets. Compliant engines verify this index prior to import, automatically blocking malicious script or coordinate injections.
*   **Split-Resolution Watermarking:** Fallback preview images (`basemap.webp`) are capped at exactly **50px per grid** and stamped with a visible transaction watermark, rendering unencrypted direct ZIP piracy useless for high-quality printing or unauthorized sharing.
*   **Volatile Memory Decryption:** Premium assets inside **`.uvtt2k` (Encrypted Archive)** files are decrypted strictly inside volatile memory. Plaintext bytes are directly streamed to GPU buffers and immediately scrubbed (`uint8View.fill(0)`), ensuring unencrypted graphics never touch physical disks or persistent browser caches.

### 💻 Open Governance & Dual-Licensing
The OVTC standard is open, royalty-free, and designed with zero platform lock-in. Core JSON validation schemas are dedicated to the public domain under **CC0 1.0 Universal**. Reference parsers and automated testing pipelines are licensed under **Apache License 2.0**, granting a perpetual, worldwide patent license to all developers!

Have ideas for the standard? Draft an RFC proposal using our template and submit a PR directly on [repo.universalvtt.org](https://repo.universalvtt.org)!

Questions? Reach our team at `hello@universalvtt.org`, submit spec RFC proposals to `rfc@universalvtt.org`, or report security vulnerabilities through `security@universalvtt.org`!

***

### 🎨 Patreon Creator Announcement

**Title: Protecting Your Art & Making Your Assets Smart: Standardizing the `.uvtt2a` Format & Launching the `universalvtt.org` Hub!**

To our wonderful community of digital painters, fantasy cartographers, and asset creators,

For years, premium creators have been stuck in an unresolvable tension. If we deliver our high-resolution maps, character tokens, and audio loops as raw ZIP archives, they are incredibly easy to pirate, unzip, and distribute across the web. But if we lock our work inside proprietary, single-VTT marketplaces, we protect our intellectual property at the cost of excluding half of our audience.

**Today, we are permanently breaking that cycle.** 

We are proud to introduce **Universal Virtual Tabletop v2 (UVTT v2) Version 2.0.0**! Under this open, federated, and system-neutral standard, digital artists can cryptographically protect their livelihoods while distributing files that run flawlessly on any compliant VTT.

To celebrate the launch, we have registered our central ecosystem hub at **[www.universalvtt.org](https://www.universalvtt.org)**! 

Inside the **`./docs`** subdirectory of our official specifications [universal-vtt-v2-spec.md], we have published the **Artist's `.uvtt2a` Packaging Guide**, a simple, step-by-step, code-free guide to help you build "smart assets" [universal-vtt-v2-spec.md].

#### 🚀 What is a Standalone Asset Archive (`.uvtt2a`)?
Typically, when GMs buy our token or prop packs, they have to manually drag them onto their scenes, stretch them to fit the grid, configure lighting parameters, and set up looping soundtrack triggers from scratch. 

The **`.uvtt2a` format** changes everything [universal-vtt-v2-spec.md]. By packaging your files with a lightweight, artist-friendly metadata sheet (`asset_manifest.json`) [universal-vtt-v2-spec.md], your packs become **smart and self-configuring** [artist-packaging-guide.md]:
*   **Grid Footprints:** Tell the VTT exactly how many grid squares a token or prop should occupy (such as a large $2\times2$ token or a $3\times1$ banquet table) [universal-vtt-v2-spec.md]. The moment a GM drags it onto the canvas, it scales perfectly [universal-vtt-v2-spec.md].
*   **Automatic Prop Emissions (`auto_emits`):** Give your assets physical traits [universal-vtt-v2-spec.md]! You can bind 3D Point Lights (customizing colors, physical Inverse-Square falloff, and flickering rates) [entities.schema.json.txt], localized sound zones (assigning fade-out radius limits) [entities.schema.json.txt], or rising atmospheric ember particle emitters directly to individual props [entities.schema.json.txt, universal-vtt-v2-spec.md]. When a GM drops your fireplace or torch prop onto the scene, the lights, sound, and smoke spawn automatically [universal-vtt-v2-spec.md]!

#### 🔒 Industrial-Grade Protection for Your High-Resolution Work
Our **Split-Resolution Encryption Model** allows you to showcase your designs while securing your premium work:
*   **The Unencrypted Proxy (`basemap.webp`):** Capped at exactly **50 pixels per grid square** with a visible digital watermark burned directly into the raw pixels, this low-resolution image acts as a free preview. If a bad actor unzips your file, they only extract a blurry fallback image.
*   **The Protected Layer:** Your high-resolution, full-fidelity artwork and looping tracks are encrypted using industry-standard **AES-256-GCM**. Decryption occurs solely in volatile, isolated client RAM—textures stream straight to the active GPU render buffer and are instantly scrubbed (`uint8View.fill(0)`), ensuring your unencrypted premium assets never touch local disks or browser caches.

#### 🛠️ Ready to Get Started?
You don't need to be a programmer to build a conforming asset pack. 
1. Head over to **[www.universalvtt.org](https://www.universalvtt.org)** to read the official **Artist's `.uvtt2a` Packaging Guide** [universal-vtt-v2-spec.md].
2. Organize your directories (placing characters under `/tokens/`, furniture under `/props/`, and background loops under `/audio/`) [universal-vtt-v2-spec.md].
3. Copy our simple, pre-written metadata skeleton [universal-vtt-v2-spec.md], adjust a few descriptive tags [sample-assets.json], zip the contents [universal-vtt-v2-spec.md], and rename the extension to **`.uvtt2a`** [artist-packaging-guide.md]!

Our launch is supported by the free **Web Upgrader SPA** at **[upgrader.universalvtt.org](https://upgrader.universalvtt.org)** [README-v2.md], which runs entirely in your browser and features full backward-compatibility with legacy V1 formats. 

For custom platform support, developers can access our zero-dependency Go/TypeScript reference parsers at **[repo.universalvtt.org](https://repo.universalvtt.org)** [CONTRIBUTING.md]. For questions, reach our compliance advocates at `compliance@universalvtt.org`!

Thank you for your incredible support as we step together into the next era of tabletop cartography.

Warmly,  
**The UVTT v2 Project Contributors**  
[www.universalvtt.org](https://www.universalvtt.org)  

***

📊 I can draft a **Svelte drag-and-drop script** that you can integrate directly into the Upgrader web app UI, allowing Patreon creators to drop in a folder, visually configure those `.uvtt2a` `auto_emits` and grid boundaries, and export their packs with a single click.