# 📚 UVTT v2 Documentation Hub

Welcome to the official documentation hub for the **Universal Virtual Tabletop Version 2 (UVTT v2)** standard.

These guides are designed to help developers, cartographers, and platform owners integrate the high-performance spatial network standard into their engines and tooling.

---

### 🧭 Core Specifications

The mathematical and structural foundations of the UVTT v2 ecosystem.

- **[The Master UVTT v2 Specification](UNIVERSAL_VTT_V2_SPEC.md)**
  The core schema definition for topological coordinate mapping, directional line-of-sight (Right-Hand Rule), spatial event targeting, and multi-floor campaign networking.
- **[Universal Visibility Flags and Cross-Entity Event Targeting](Universal_Visibility.md)**
  Defines the standard for permissions (`gm_only`, `hidden`) and spatial event triggers (teleports, state mutations) across VTT runtimes.
- **[VTT Graphics & Shader Cookbook](vtt-shader-cookbook.md)**
  Production-ready math and shader recipes for WebGPU/WebGL2 engines to render inverse-square 3D lighting, acoustic raycasting, and hardware-accelerated weather particles.

---

### 🛠️ Developer & Tooling Integration

Integration blueprints for virtual tabletop developers and mapmaking software authors.

- **[VTT Developer Quickstart](developer-quickstart.md)**
  A five-minute guide for VTT engine developers to correctly decompress `.uvtt2z` files, lazy-load geometry, and route Semantic Movement Zones to `.wasm` rule engines.
- **[Mapmaking Exporter Integration Blueprint](exporter-integration-blueprint.md)**
  The required algorithms for CAD/mapmaking software to export UVTT v2 packages, including vertex snapping, collinear simplification, and localized `internal://` URIs.

---

### 🛍️ Creator Assets & Storefront Distribution

Guidelines for artists packaging standalone assets and storefronts distributing premium, encrypted campaign data.

- **[Artist Packaging Guide](artist-packaging-guide.md)**
  How digital artists and Patreon creators can package smart `.uvtt2a` standalone assets (tokens, props, audio) with auto-emitting metadata.
- **[Storefront & Distribution Blueprint](storefront-api-blueprint.md)**
  Architectural guidelines for distributing the dual-file DRM system (`.uvtt2z` payloads and `.uvtt2k` keys) across subscription tiers and automated storefronts.
- **[Re-Signing & Watermarking API](RE-SIGNING-API.md)**
  For enterprise storefronts: How to dynamically inject cryptographic signatures into `manifest.json` for traitor tracing and IP protection.

---

_Return to the [Main Specification Homepage](https://www.universalvtt.org)._
