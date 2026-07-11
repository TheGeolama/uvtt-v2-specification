# Universal VTT v2 (UVTT v2) Specification

**The open-source, high-performance standard for interconnected TTRPG campaign mapping.**

The UVTT v2 specification provides a modern, robust, and extensible framework for TTRPG map data [6]. Designed to replace the legacy 2D-only flat formats (`.dd2vtt` / `.df2vtt`), UVTT v2 enables verticality, complex spatial triggers, hardware-accelerated rendering, and multi-file campaign networking [6].

---

### 🚀 Why UVTT v2?

Legacy V1 standards were ground-breaking, but they suffer from significant architectural bottlenecks [7]. UVTT v2 solves these by treating maps not as static images, but as nodes within a **Topological Spatial Network** [7].

#### The Problem with v1

- **Data Bloat:** Base64-encoded images embedded in JSON inflate payloads by ~33%, causing UI freezes and OOM errors in browser-based VTTs [7].
- **The "Flat Earth" Assumption:** Legacy formats assume all maps are 2D planes, rendering vertical gameplay (multi-level dungeons) a nightmare to manage [7].
- **Mathematical Inefficiency:** Jagged straight-line approximation for curved walls wastes GPU resources and creates visual artifacts [7].
- **Fragmented Campaigns:** Maps are isolated islands [7]. Linking a portal in Map A to Map B required manual GM intervention or third-party plug-ins [7].

#### The Solution: v2 Architecture

- **Binary Archive Container (.uvtt2z):** A zipped directory that detaches heavy image assets from metadata [8]. This enables streamability, lazy loading, and sub-second directory browsing [8].
- **Material-Aware Geometry:** Directional Line-of-Sight (using the Right-Hand Rule) and explicit height-blocking properties for walls, terrain, and foliage [8].
- **Spatial Routing:** A native URI-based system (`internal://` and `relative://`) allows for seamless, zero-lag transitions between maps and floors in mega-dungeons [8].
- **Future-Proof Extensibility:** A `hardware_profile` block ensures the format can scale from WebGL2 to WebGPU without requiring a schema rewrite [8].

---

### 📂 Repository Structure

Below is the standard, system-neutral workspace structure for the official **UVTT v2 Specification Repository** when loaded into a development environment such as VS Code on Windows 11:

```yaml
uvtt-v2-workspace/               # Open the parent folder directly in VS Code
├── .github/                     # Automated repository workflows and templates
│   └── workflows/
│       └── validate-uvtt2-ci.yml # GitHub Actions automated CI validation pipeline
├── .git/                        # Hidden directory (created automatically by 'git init')
│   └── hooks/
│       └── pre-commit           # Git Hook: Blocks commits on test/schema failure
├── schemas/                     # Machine-readable standards validation files
│   ├── manifest.schema.json     # Standard validation rules for global manifest properties
│   ├── geometry.schema.json     # Standard validation rules for vector coordinates and walls
│   └── entities.schema.json     # Standard validation rules for lighting, weather, and triggers
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
│   └── tavern_three_story.uvtt2z # Multi-story sample campaign archive conforming to standard
├── RFCs/                        # Request for Comments proposal directory
│   └── rfc-template.md          # Standard proposal template for community extensions
├── CHANGELOG.md                 # Detailed ledger of version milestones & technical fixes
├── CONTRIBUTING.md              # Open-source developer rules of engagement & standards
└── README.md                    # Landing page, feature matrices, and getting-started guide
```

---

### 🛠️ Feature Comparison Matrix

| Feature              | Legacy v1                | UVTT v2                           |
| :------------------- | :----------------------- | :-------------------------------- |
| **Asset Delivery**   | Base64-in-JSON [9]       | Zipped Directory (`.uvtt2z`) [9]  |
| **Grid Logic**       | Square Only [9]          | Square, Hex, Isometric [9]        |
| **Verticality**      | Flat Plane [9]           | 3D Bounds (Bottom/Top Z) [9]      |
| **Curves**           | Jagged Line Segments [9] | Native SVG Bézier Paths [9]       |
| **Visibility**       | Symmetrical [9]          | Directional (Right-Hand Rule) [9] |
| **Interoperability** | Disconnected Islands [9] | Topological Spatial Network [9]   |
| **Weather**          | None [9]                 | Bounded Particle Emitters [9]     |

---

### 📝 Governance & Contribution

The UVTT v2 specification is a **Living Document** [10]. We welcome contributions from VTT engine developers and map-making tool authors [10].

#### The RFC Pipeline

To propose a new feature (e.g., new atmospheric shaders, advanced lighting physics), please follow these steps [10]:

1. **Draft an RFC:** Create a markdown proposal in the `/RFCs` directory using the provided template [10].
2. **Pull Request:** Submit your RFC via a Pull Request [10].
3. **Community Review:** We evaluate based on backward compatibility, performance impact, and interoperability [10].

#### The Backward-Compatibility Contract

Core features—including basic walls, portals, and landing zones—are immutable [11]. Any new functionality (e.g., advanced WebGPU compute shaders) must be implemented as additive, optional properties within the `extensions` block to ensure that existing engines remain compliant [11].

---

### 🔗 Getting Started

- **[View the Full Specification](schemas/)** [11]
- **[Download the Reference Upgrader Tool](https://github.com/TheGeolama/uvtt-v2-upgrader)** [11] (Migrate legacy maps to v2).
- **[Join the Discussion](https://github.com/TheGeolama/uvtt-v2-specification/issues)** [11]
