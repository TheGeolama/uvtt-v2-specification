# Universal VTT v2 (UVTT v2) Specification
**The open-source, high-performance standard for interconnected TTRPG campaign mapping.**

The UVTT v2 specification provides a modern, robust, and extensible framework for TTRPG map data. Designed to replace the legacy 2D-only flat formats (.dd2vtt / .df2vtt), UVTT v2 enables verticality, complex spatial triggers, hardware-accelerated rendering, and multi-file campaign networking.

---

### 🚀 Why UVTT v2?
Legacy V1 standards were ground-breaking, but they suffer from significant architectural bottlenecks. UVTT v2 solves these by treating maps not as static images, but as nodes within a **Topological Spatial Network**.

#### The Problem with v1
*   **Data Bloat:** Base64-encoded images embedded in JSON inflate payloads by ~33.3%, causing UI freezes and OOM errors in browser-based VTTs.
*   **The "Flat Earth" Assumption:** Legacy formats assume all maps are 2D planes, rendering vertical gameplay (multi-level dungeons) a nightmare to manage.
*   **Mathematical Inefficiency:** Jagged straight-line approximation for curved walls wastes GPU resources and creates visual air leaks.
*   **Fragmented Campaigns:** Maps are isolated islands. Linking a portal in Map A to Map B required manual GM intervention.

#### The Solution: v2 Architecture
*   **Binary Archive Container (.uvtt2z):** A zipped directory that detaches heavy image assets from metadata. This enables streamability, lazy loading, and sub-second directory browsing.
*   **Encrypted Archive Envelope (.uvtt2k):** A secure counterpart utilizing AES-256-GCM encryption over the entire zipped container. Decrypted completely in-memory, avoiding local disk writes.
*   **Modular Compound Topology:** Compound dungeons bundle levels in isolated subdirectories (`maps/[map-slug]/`), each containing localized coordinates, manifests, and WebP images to optimize browser memory and lazy-loading.
*   **Material-Aware Geometry:** Directional Line-of-Sight (using the Right-Hand Rule) and explicit height-blocking properties for walls, terrain, and foliage.
*   **Spatial Routing:** A native URI-based system (internal:// and relative://) allows for seamless, zero-lag transitions between maps and floors in mega-dungeons.
*   **State-Driven Interactions:** Standardizes universal visibility flags, sync identifiers, and cross-entity actions to let map triggers alter other elements dynamically.
*   **Future-Proof Extensibility:** A hardware_profile block ensures the format can scale from WebGL2 to WebGPU without requiring a schema rewrite.
*   **PixiJS v8 Ready**: Full architectural integration with PixiJS v8's async initialization, decoupled styling, and WebGPU hardware execution targets.

---

### 📂 Repository Structure
```yaml
uvtt-v2-workspace/               # Open the parent folder directly in VS Code
├── .github/                     # Automated repository workflows and templates
│   └── workflows/
│       ├── validate-uvtt2-ci.yml # GitHub Actions automated CI validation pipeline
│       ├── deploy-upgrader.yml   # CD pipeline to compile and deploy the Svelte SPA
│       └── create-v2-release.yml # Automated release and package pipeline
├── .git/                        # Hidden directory (created automatically by 'git init')
│   └── hooks/
│       └── pre-commit           # Git Hook: Blocks commits on test/schema failure
├── schemas/                     # Machine-readable standards validation files
│   ├── manifest.schema.json     # Standard validation rules for global manifest properties
│   ├── geometry.schema.json     # Standard validation rules for vector coordinates and walls
│   ├── entities.schema.json     # Standard validation rules for lighting, weather, and triggers
│   └── assets.schema.json       # Standard validation rules for standalone .uvtt2a asset packs
├── docs/                        # Comprehensive developer resources and tutorials
│   ├── artist-packaging-guide.md # Non-technical guide for packaging standalone .uvtt2a packs
│   ├── exporter-integration-blueprint.md # CAD and math-snapping guide for software authors
│   └── vtt-shader-cookbook.md   # Reference WGSL/GLSL shaders and audio decay math
├── reference-parsers/           # Zero-dependency reference parsing files
│   ├── go/
│   │   └── uvtt2_parser.go      # Backend reference parser suite (zero-dependency)
│   └── typescript/
│       └── uvtt2_parser.ts      # Client-side parser with Web Crypto decryption and curve math
├── clearinghouse/               # Zero-Knowledge-Storage serverless edge infrastructure
│   ├── zks-clearinghouse-worker.js # Cloudflare Worker edge key-derivation script
│   ├── wrangler.toml            # Deployment environment & database configurations
│   ├── seed_revocations.js      # Utility script to bulk hash and seed revoked transactions
│   └── manage_revocations.js    # Node.js command-line tool to manage revoked transaction IDs
├── tests/                       # Programmatic validation & security checking engines
│   ├── master-test-suite.py     # Consolidated master test runner (verifies schemas, geometry, & ZKS handshakes)
│   ├── validate_conformance.go   # Go-based high-concurrency binary validation suite
│   └── webgpu-purge-test.ts     # TypeScript unit tests validating WebGPU volatile RAM scrubbing
├── tools/                       # Repository automation and campaign asset creators
│   ├── verify-all.sh            # Unified Bash script coordinating all tests & environment audits
│   └── generate-mock-uvtt2z.py  # Dynamic script to generate conforming signed test maps
├── samples/                     # Compliant testing files to feed into validators
│   ├── tavern_three_story.uvtt2z # Multi-story unencrypted sample campaign archive
│   └── tavern_three_story.uvtt2k # Multi-story AES-GCM encrypted campaign archive
├── RFCs/                        # Request for Comments proposal directory
│   └── rfc-template.md          # Standard proposal template for community extensions
├── CHANGELOG.md                 # Detailed ledger of version milestones & technical fixes
├── CONTRIBUTING.md              # Open-source developer rules of engagement & standards
└── README.md                    # Landing page, feature matrices, and getting-started guide
```

---

### 🛠️ Feature Matrix
| Feature | Legacy v1 | UVTT v2 |
| ------ | ------ | ------ |
| **Asset Delivery** | Base64-in-JSON | Zipped Directory (.uvtt2z) or Envelope GCM (.uvtt2k) |
| **Asset Packs** | None | Standalone .uvtt2a with auto_emits and footprints |
| **Grid Logic** | Square Only | Square, Hex, Isometric |
| **Verticality** | Flat Plane | 3D Bounds (Bottom/Top Z) |
| **Curves** | Jagged Line Segments | Native SVG Bézier Paths |
| **Visibility** | Symmetrical | Directional (Right-Hand Rule) & Universal visibility |
| **State Tracking**| None | sync_id variant linking and cross-entity actions |
| **Interoperability** | Disconnected Islands | Topological Spatial Network |
| **Weather** | None | Bounded Particle Emitters with height limits & collision |
| **Graphics Baseline**| WebGL 1.0 / Canvas | WebGL 2.0 / WebGPU (PixiJS v8 Native) |

---

### 📝 Governance & Contribution
The UVTT v2 specification is a **Living Document**. We welcome contributions from VTT engine developers and map-making tool authors.

#### The RFC Pipeline
To propose a new feature (e.g., advanced WebGPU compute shaders, custom PBR normal layers), please follow these steps:
1. **Draft an RFC:** Create a markdown proposal in the `/RFCs` directory using the template.
2. **Pull Request:** Submit your RFC via a Pull Request.
3. **Community Review:** We evaluate based on backward compatibility, performance impact, and interoperability.

#### The Backward-Compatibility Contract
Core features—including basic walls, portals, and landing zones—are immutable. Any new functionality must be implemented as additive, optional properties within the extensions block to ensure that existing engines remain compliant.

---

### 🔗 Getting Started
*   **[View the Full Specification](universal-vtt-v2-spec.md)**
*   **[Read the JSON Schemas](schemas/)**
*   **[Read the Developer Docs](docs/)**
*   **[Download the Reference Upgrader Tool](https://github.com/TheGeolama/uvtt-v2-upgrader)** (Migrate legacy maps to v2).
*   **[Join the Discussion](https://github.com/TheGeolama/uvtt-v2-specification/issues)**
