# Universal VTT v2 (UVTT v2) Specification

[![Version](https://img.shields.io/badge/version-2.0.0--rc1-blue.svg)]()
[![Standard](https://img.shields.io/badge/schema-uvtt2z-success.svg)]()

**The open-source, high-performance standard for interconnected TTRPG campaign mapping.**

The UVTT v2 specification provides a modern, robust, and extensible framework for TTRPG map data. Designed to replace the legacy 2D-only flat formats (`.dd2vtt` / `.df2vtt`), UVTT v2 enables verticality, complex spatial triggers, hardware-accelerated rendering, and multi-file campaign networking.

---

### 🚀 Why UVTT v2?

Legacy V1 standards were ground-breaking, but they suffer from significant architectural bottlenecks. UVTT v2 solves these by treating maps not as static images, but as nodes within a **Topological Spatial Network**.

#### The Problem with v1

- **Data Bloat:** Base64-encoded images embedded in JSON inflate payloads by ~33.3%, causing UI freezes and OOM errors in browser-based VTTs.
- **The "Flat Earth" Assumption:** Legacy formats assume all maps are 2D planes, rendering vertical gameplay (multi-level dungeons) a nightmare to manage.
- **Mathematical Inefficiency:** Jagged straight-line approximation for curved walls wastes GPU resources and creates visual light leaks.
- **Fragmented Campaigns:** Maps are isolated islands. Linking a portal in Map A to Map B required manual GM intervention.

#### The Solution: v2 Architecture

- **Binary Archive Container (`.uvtt2z`):** A zipped directory that detaches heavy image assets from lightweight JSON metadata. This enables streamability, lazy loading, and sub-second directory browsing.
- **Native Cryptography (`.uvtt2k`):** Built-in AES-256-GCM encryption splits premium campaigns into a public encrypted payload (`.uvtt2z`) and a private cryptographic key (`.uvtt2k`) to securely distribute and protect creator content.
- **Material-Aware Geometry:** Directional Line-of-Sight (using the Right-Hand Rule) and explicit height-blocking properties for walls, terrain, and foliage.
- **Spatial Routing:** A native URI-based system allows for seamless, zero-lag transitions between maps and floors in mega-dungeons.

---

### 💻 The Upgrader Application (Web & Desktop Pro)

Included in this ecosystem is the **UVTT v2 Upgrader**, a hardware-accelerated WebGPU/PixiJS authoring tool that imports legacy maps and upgrades them to the v2 standard. It operates on a unified Svelte 5 codebase across two tiers:

1. **The Web SPA (Free):** An offline-first, browser-based app featuring genuine CAD tools, Rubber-Sheet grid alignment, and a 50-step deep-cloned History Engine.
2. **Desktop Pro (Paid):** A native OS executable built with Wails/Go unlocking FFmpeg cinematic video rendering, a Topology Validation queue, and live-syncing local asset folders.

---

### 📂 Repository Structure

    uvtt-v2-workspace/               # Open the parent folder directly in VS Code
    ├── .github/                     # Automated repository workflows and CI validation
    ├── docs/                        # 📚 Official Documentation Suite
    │   ├── UNIVERSAL_VTT_V2_SPEC.md # The core mathematical and structural schema
    │   ├── developer-quickstart.md  # 5-step implementation guide for VTT devs
    │   ├── storefront-api-blueprint.md # Distribution architecture for premium content
    │   ├── RE-SIGNING-API.md        # Dynamic watermark injection for anti-piracy
    │   └── Universal_Visibility.md  # Specs for secret doors and event targeting
    ├── schemas/                     # Machine-readable standards validation files
    │   ├── manifest.schema.json     # Validation rules for global manifest properties
    │   ├── geometry.schema.json     # Validation rules for vector coordinates and walls
    │   └── assets.schema.json       # Validation rules for media assets and paths
    ├── reference-parsers/           # Zero-dependency reference parsing files
    │   ├── go/uvtt2_parser.go       # Backend reference parser suite
    │   └── typescript/uvtt2_parser.ts # Client-side parser with Web Crypto decryption
    ├── tests/                       # Programmatic validation & security checking engines
    ├── tools/                       # Repository automation and campaign asset creators
    ├── samples/                     # Compliant testing files to feed into validators
    │   ├── tavern_three_story.uvtt2z # Multi-story sample campaign archive
    │   ├── sample-manifest.json     # Unpacked sample of a valid manifest
    │   ├── sample-geometry.json     # Unpacked sample of valid CAD vectors
    │   ├── sample-entities.json     # Unpacked sample of valid interactive points
    │   └── sample-assets.json       # Unpacked sample of valid asset metadata
    ├── RFCs/                        # Request for Comments proposal directory
    ├── CHANGELOG.md                 # Ledger of version milestones & technical fixes
    ├── CONTRIBUTING.md              # Open-source developer rules of engagement
    ├── SECURITY.md                  # Threat models and vulnerability reporting
    └── README.md                    # Landing page, feature matrices, and start guide

---

### 🛠️ Feature Matrix

| Feature               | Legacy v1            | UVTT v2                               |
| --------------------- | -------------------- | ------------------------------------- |
| **Asset Delivery**    | Base64-in-JSON       | Zipped Directory (`.uvtt2z`)          |
| **Content Security**  | None                 | AES-256-GCM Dual-File Encryption      |
| **Grid Logic**        | Square Only          | Square, Hex, Isometric                |
| **Verticality**       | Flat Plane           | 3D Bounds (Bottom/Top Z)              |
| **Curves**            | Jagged Line Segments | Native SVG Bézier Paths               |
| **Visibility**        | Symmetrical          | Directional (Right-Hand Rule)         |
| **Interoperability**  | Disconnected Islands | Topological Spatial Network           |
| **Weather**           | None                 | Bounded Particle Emitters             |
| **Graphics Baseline** | WebGL 1.0 / Canvas   | WebGL 2.0 / WebGPU (PixiJS v8 Native) |

---

### 📝 Governance & Contribution

The UVTT v2 specification is a **Living Document**. We welcome contributions from VTT engine developers and map-making tool authors.

#### The RFC Pipeline

To propose a new feature (e.g., new atmospheric shaders, advanced lighting physics):

1. **Draft an RFC:** Create a markdown proposal in the `/RFCs` directory using the provided template.
2. **Pull Request:** Submit your RFC via a Pull Request.
3. **Community Review:** We evaluate based on backward compatibility, performance impact, and interoperability.

#### The Backward-Compatibility Contract

Core features—including basic walls, portals, and landing zones—are immutable. Any new functionality must be implemented as additive, optional properties within the `extensions` block to ensure existing engines remain compliant.

---

### 🔗 Getting Started

- **[Read the Full Specification](./docs/UNIVERSAL_VTT_V2_SPEC.md)**
- **[Launch the Upgrader Web App](https://upgrader.universalvtt.org)** - **[View the Source Code on GitHub](https://repo.universalvtt.org)**
- **[Join the Discussion](https://discuss.universalvtt.org)**
