# Universal Virtual Tabletop (UVTT) v2 Specification

## 1. Introduction & Architecture

### 1.1 Purpose

The UVTT v2 Specification defines a modern, multi-floor, interactive spatial database format for Virtual Tabletop (VTT) environments. It standardizes dynamic lighting, acoustic falloff, interactive entities, and CAD-level vector topology to ensure maps port flawlessly between authoring tools and VTT runtimes.

### 1.2 Scope of the Specification: Runtime vs. Authoring

This specification defines the **final spatial database delivery format** required for a VTT runtime to render maps, enforce topology, and calculate lighting.

It **does not** govern authoring tool states. Proprietary editor files (such as `.uvtt-proj` workspace files), rubber-sheet grid-alignment algorithms, and memory-safe Undo/Redo history engines are exclusive to the application layer of the cartography software. Compliant VTT import engines should ignore proprietary workspace files and focus solely on the finalized `.uvtt2z` structural schema defined herein.

### 1.3 Export Deliverables & Graceful Degradation

The official delivery mechanism for the UVTT v2 specification is the **`.uvtt2z` zipped container**, which cleanly separates `manifest.json`, `geometry.json`, `entities.json`, and raw media assets into a directory tree.

- **Standard Compliant Export:** All modern authoring tools—including client-side Web SPAs utilizing in-memory libraries like `jszip`—must package and output the `.uvtt2z` container as their primary deliverable.

- **Graceful Degradation (`map.uvtt`):** To maintain backward compatibility with legacy V1 virtual tabletops, authoring tools may offer a fallback export that compiles the multi-file architecture back into a monolithic, flat `map.uvtt` JSON string. This is strictly a legacy fallback and is deprecated for modern v2 workflows.

### 1.4 Cryptographic Standards and Campaign Protection

To protect premium creator content, the V2 standard natively supports AES-256-GCM encryption. When an authoring tool exports an encrypted campaign, it generates two distinct files:

- **`.uvtt2z` (The Locked Archive):** The standard ZIP container, but its internal byte streams (such as `geometry.json` and `.webp` assets) are encrypted via AES-256-GCM. This file is safe for public distribution.

- **`.uvtt2k` (The Cryptographic Key):** A standalone symmetric key file containing the raw hex string required to decrypt the specific `.uvtt2z` archive.

**Decryption Pipeline:** Compliant VTT clients must _never_ cache decrypted premium assets to disk. Keys ingested from a `.uvtt2k` file must be held strictly in volatile RAM (e.g., via an Offline Service Worker or Web Crypto API) and wiped upon session termination.

---

## 2. File Structure

A standard `.uvtt2z` archive must contain the following flat directory structure for JSON payloads, with a strictly segregated media architecture:

```text
campaign_name.uvtt2z/
├── manifest.json       # Metadata, grid sizing, and background definitions
├── geometry.json       # Walls, portals, and roofs (Vectors)
├── entities.json       # Lights, audio, spawns, and events (Points)
└── assets/             # Root media directory
    ├── maps/           # Background map images (.webp, .jpg)
    ├── audio/          # Ambient tracks and sound effects (.mp3, .ogg)
    └── props/          # Tokens, furniture, and animated assets (.webm, .png)

```

An example could look like this:

```text
feodors_campout.uvtt2z/
├── manifest.json       # Metadata, grid sizing, and background definitions
├── geometry.json       # Walls, portals, and roofs (Vectors)
├── entities.json       # Lights, audio, spawns, and events (Points)
└── assets/             # Directory containing all referenced media
    ├── maps/
    │   └── background.webp # (Example) Base map image referenced in manifest.json
    ├── audio/
    │   └── rain.mp3        # (Example) Audio track referenced in entities.json
    └── props/
        └── campfire.webm   # (Example) Animated prop referenced in entities.json

```

---

## 3. JSON Schemas

### 3.1 manifest.json

Defines the global environment and grid calibration.

```json
{
  "version": "2.0",
  "metadata": {
    "title": "Compound Dungeon Level 1",
    "author": "Creator Name"
  },
  "grid": {
    "type": "square",
    "ppi": 70,
    "offset": { "x": 0, "y": 0 }
  },
  "background": {
    "image": "assets/maps/background.webp",
    "scale": 1.0
  }
}
```

### 3.2 geometry.json

Defines the CAD vector layers. All coordinates are mapped in raw pixel space relative to the top-left origin (0,0). **In Draft-08, all geometric arrays MUST be nested within their respective Map ID to ensure multi-map compatibility.**

```json
{
  "map_uuid_1234": {
    "walls": [
      {
        "id": "uuid-1234",
        "p1": { "x": 100, "y": 100 },
        "p2": { "x": 500, "y": 100 },
        "type": "terrain",
        "visibility": "visible"
      }
    ],
    "portals": [
      {
        "id": "uuid-5678",
        "p1": { "x": 500, "y": 100 },
        "p2": { "x": 600, "y": 100 },
        "state": "closed",
        "visibility": "gm_only"
      }
    ],
    "roofs": []
  }
}
```

Note: Valid portal states are `open`, `closed`, `locked`, and `broken`.

### 3.3 entities.json

Defines interactive points of interest. **In Draft-08, all entity arrays MUST be nested within their respective Map ID to ensure multi-map compatibility.**

```json
{
  "map_uuid_1234": {
    "lights": [
      {
        "id": "uuid-9012",
        "x": 300,
        "y": 300,
        "radius_dim": 600,
        "radius_bright": 300,
        "color": "#ffaa00",
        "intensity": 0.8,
        "visibility": "visible"
      }
    ],
    "audio": [],
    "spawns": [
      {
        "id": "uuid-3456",
        "x": 150,
        "y": 150,
        "is_default_landing": true,
        "visibility": "hidden"
      }
    ],
    "events": []
  }
}
```

Note: Every object across all JSON files supports the universal `visibility` override flag (`visible`, `gm_only`, `hidden`).

---

## 4. Topology & Mathematical Standards

To ensure cross-platform compatibility, rendering engines must implement the following mathematical baseline behaviors.

### 4.1 Vertex Snapping & Light Leak Prevention

During import or vector generation, endpoints within a Euclidean distance of **0.05 map units** must be programmatically merged to prevent raycasting light leaks.

### 4.2 Acoustic Proximity Falloff

Audio zones must utilize a clamped linear proximity falloff to prevent volume pops or negative gains when tokens approach the emitter. The volume $V$ at distance $d$ from an emitter with radius $r$ and maximum volume $V_{\text{max}}$ is calculated as:

$$V = \max\left(0, \min\left(V_{\text{max}}, V_{\text{max}} \times \left(1 - \frac{d}{r}\right)\right)\right)$$

### 4.3 One-Way Vision (The Right-Hand Rule)

Walls configured as one-way line-of-sight blockers (e.g., cliffs, one-way mirrors) must calculate their blocking normal using the Right-Hand Rule. Given a vector heading from $p_1$ to $p_2$, the blocking normal $\vec{n}_{\text{right}}$ is calculated clockwise as:

$$\vec{n}_{\text{right}} = (\Delta y, -\Delta x)$$

Any raycast intersecting this vector from the direction of the normal is blocked; rays originating from behind the normal pass through.

---
