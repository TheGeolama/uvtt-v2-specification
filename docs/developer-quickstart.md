# 🚀 UVTT v2 Developer Quickstart Guide

Welcome to the UVTT v2 ecosystem! If you are a Virtual Tabletop (VTT) platform developer building an importer for the new v2 standard, you are in the right place.

The v2 standard moves away from massive, monolithic text files and adopts a clean, modular zipped directory structure (`.uvtt2z`). This guide will walk you through the exact pipeline your code needs to follow to successfully unpack and render a v2 campaign.

## The Import Pipeline: 5 Steps to Render

### Step 1: Unpack the `.uvtt2z` Archive

A `.uvtt2z` file is simply a standard ZIP archive.

1. Use your language's native zip library (e.g., `jszip` for JS/Node, `archive/zip` for Go) to open the file.
2. Inside, you will find three core JSON files (`manifest.json`, `geometry.json`, `entities.json`) and an `assets/` directory.

### Step 2: Read `manifest.json` (The Foundation)

Always parse the manifest first. It dictates your canvas size and grid calibration.

- **Extract the Background:** Locate `manifest.background.image`. This will point to a relative path in the `assets/` folder (e.g., `assets/tavern_floor.webp`).
- **Calibrate the Grid:** Use `manifest.grid.ppi` (Pixels Per Inch) to scale the background image against your VTT's internal grid system.

### Step 3: Parse `geometry.json` (The Topology)

Next, ingest the CAD vectors for lighting and line-of-sight.

- **Iterate Arrays:** Loop through the `walls`, `portals`, and `roofs` arrays.
- **Apply the Snapping Rule:** To prevent light leaks in your VTT, programmatically merge any vector endpoints (`p1`, `p2`) that fall within **0.05 map units** of each other.
- **Check Portal States:** Note the `state` property on portals (`open`, `closed`, `locked`, `broken`) and register them with your VTT's door system.

### Step 4: Populate `entities.json` (The Actors)

Finally, drop in the interactive elements.

- **Extract Points of Interest:** Loop through `lights`, `audio`, `spawns`, and `events`.
- **Honor Visibility Flags:** **CRITICAL:** Every object in the v2 schema has a `visibility` property. Ensure your importer respects `visible`, `gm_only`, and `hidden`. Do not accidentally expose a `gm_only` secret teleport pad to your players!
- **Resolve Media:** If an entity (like an audio emitter) references a file, resolve its path against the unpacked `assets/` directory.

### Step 5: Handling Encryption (`.uvtt2k`)

If your zip library throws an error or reads garbage data, you have likely encountered an AES-256-GCM encrypted premium campaign.

1. Prompt the user to provide their `.uvtt2k` cryptographic key file.
2. Ingest the key stream into volatile RAM.
3. Decrypt the buffered archive in memory.

- **Security Rule:** You must _never_ save the decrypted premium assets or the `.uvtt2k` key string to the user's local disk. Wipe the key from memory when the session ends.

---

## Need the exact math?

If you need the specific JSON schemas, the Right-Hand Rule math for one-way walls, or the exact acoustic proximity falloff equations, please refer to the official [UNIVERSAL_VTT_V2_SPEC.md](./UNIVERSAL_VTT_V2_SPEC.md).
