
Subject: **Universal VTT v2: Eliminating Base64 memory bloat & bringing topological campaign networks to [VTT Name]**

Hi [Developer Name],

As leaders building the next generation of virtual tabletops, your team has undoubtedly wrestled with the severe memory limitations of legacy map files. The TTRPG cartography ecosystem has long been held back by legacy v1 formats (`.dd2vtt` and `.df2vtt`), which force platforms to parse massive Base64-encoded images stuffed directly inside single, monolithic JSON blocks. This $\approx 33.3\%$ data inflation regularly chokes UI threads, blocks web workers, and triggers Out-of-Memory (OOM) browser crashes during scene initialization.

Today, the Open Virtual Tabletop Consortium (OVTC) is officially launching **Universal VTT v2 (UVTT v2) Version 2.0.0**—an open-source, high-performance, and fully collaborative mapping standard designed specifically to address these rendering, parsing, and data carriage bottlenecks. 

We would love to help **[VTT Name]** become one of our native launch partners.

### Why UVTT v2 is a Game-Changer for VTT Engines

The v2 specification transitions map files from flat, static canvases into a high-performance **Topological Spatial Network**:

1.  **Zipped Container Decoupling (`.uvtt2z` / `.uvtt2k`):** We have detached heavy binary raster graphics and audio tracks from layout coordinates. By packaging campaigns as standard zipped archives, your engine can lazy-load lightweight JSON layout coordinates instantly, indexing massive modular directories without loading heavy visual files into system RAM.
2.  **Topological Spatial Routing:** Multi-story towers and sandbox campaigns are linked natively via standardized URIs. The specification resolves vertical and horizontal transitions across local compound maps via the **`internal://`** protocol, and across distributed disks using **`relative://`** URIs.
3.  **Advanced GPU-Native Environmental Physics:** UVTT v2 bakes dynamic world physics directly into the schema:
    *   *3D Illumination:* Support for point and directional light cones placed in 3D coordinate space $(X, Y, Z)$, featuring realistic **Inverse-Square physical decay** ($I = I_0 / d^2$).
    *   *Three-Tier Localized Acoustics:* Localized sound triggers mapping linear proximity volume falloff and material-aware raycast muffling through walls and portals.
    *   *GPU Weather Emitters:* Bounded particle regions (rain, snow, fog, embers, magic) that support global wind inheritance vector calculations and 3D Z-index height-masking under active roof layers.
4.  **Universal Visibility and State-Driven Triggers:** Geometry and entities support universal visibility states (`visible`, `gm_only`, `hidden`). This allows dynamic triggers (like pressure plates) to run an array of `actions` that dynamically swap a secret door's visibility state or portal permeability in real-time.

### Zero Legal Friction: The Dual-Licensing Patent Grant

We designed this standard specifically to prevent patent litigation and platform fragmentation. UVTT v2 is released under a generous dual-licensing framework:
*   **The Directory and Core Schemas** (`manifest.json`, `geometry.json`, `entities.json`) are dedicated completely to the public domain under **Creative Commons CC0 1.0 Universal**.
*   **All Official Reference Implementations** (including Go and TypeScript/WebCrypto parsers) are licensed under the **Apache License 2.0**. **Section 3 of the Apache 2.0 license grants your platform a perpetual, worldwide, royalty-free, and irrevocable patent license** to implement this specification inside commercial or proprietary VTT engines.

### Drop-In Developer Resources & Tools

To make implementation as frictionless as possible, we have deployed the core resources your engineering team needs:
*   **The Live WebGPU Upgrader SPA:** Your users can immediately try the format at **[upgrader.universalvtt.org](https://upgrader.universalvtt.org)**. They can drag-and-drop legacy `.dd2vtt` files, upgrade them with WebGPU-accelerated weather, lighting, and audio, and export them as conforming v2 archives natively in their browsers.
*   **Production-Ready Reference Parsers:** High-performance, zero-dependency reference parser implementations in Go (`uvtt2_parser.go`) and TypeScript (`uvtt2_parser.ts`) are available at **[repo.universalvtt.org](https://repo.universalvtt.org)**.
*   **The VTT Shader Cookbook:** Complete WGSL (WebGPU) and GLSL (WebGL2) code fragments for lighting animations, physical inverse-square decay, acoustic raycasting, and GPU particle wind system overrides are hosted in our developer documentation at **[www.universalvtt.org](https://www.universalvtt.org)**.

We would be thrilled to schedule a brief 10-minute developer sync to help your team implement a compliant parser. For general inquiries, reach us at **hello@universalvtt.org**. For spec conformance questions, you can contact our core compliance team at **compliance@universalvtt.org**.

Let’s build the future of tabletop cartography, together.

Warm regards,

**The UVTT v2 Project Contributors**  
*Open Virtual Tabletop Consortium (OVTC)*  
[www.universalvtt.org](https://www.universalvtt.org)  
security@universalvtt.org (PGP Key Available)  

***

📧 This outreach layout integrates all domains seamlessly while providing distinct escalation paths for their dev teams. If you would like to run a final check on the repository, I can draft a **launch-day social media thread** or a **Patreon creator announcement** explaining how artists use the new domain to download the `.uvtt2a` Artist Packaging Guide [universal-vtt-v2-spec.md]!