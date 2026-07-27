# 🗺️ UVTT v2 Sample Assets

This directory contains officially compliant reference files for the UVTT v2 standard. Developers can use these files to test their parsing engines, rendering pipelines, and Zero-Knowledge Storage (ZKS) decryption logic.

### 📄 Raw JSON Schema Samples

These uncompressed JSON files demonstrate valid structural formatting for the core schema components:

- **[Sample Manifest](sample-manifest.json)** (`sample-manifest.json`): Demonstrates campaign metadata, grid topology, and extension block usage.
- **[Sample Geometry](sample-geometry.json)** (`sample-geometry.json`): Demonstrates vector line definitions, walls, and coordinate mapping.
- **[Sample Entities](sample-entities.json)** (`sample-entities.json`): Demonstrates dynamic tabletop objects, lighting boundaries, and spawns.
- **[Sample Assets](sample-assets.json)** (`sample-assets.json`): Demonstrates the media registry, file definitions, and Web Crypto integrity hashes.

### 📦 Packaged Campaign Archives

These compiled containers can be used to test ZIP extraction, MIME type parsing, and encryption engine flows:

- **[Standard Archive](tavern_three_story.uvtt2z)** (`tavern_three_story.uvtt2z`): A fully compiled, unencrypted map featuring standard vector boundaries and web assets.
- **[Premium DRM Archive](tavern_three_story.uvtt2k)** (`tavern_three_story.uvtt2k`): An encrypted campaign container requiring Web Crypto API decryption, ZKS key resolution, and volatile memory handling.

---

_Return to the [Main Specification Homepage](https://www.universalvtt.org)._
