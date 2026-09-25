# Universal VTT v2 Systems Specification

## High-Performance Rendering & Spatial Network Manual

**Version:** 2.0.0-rc2

**Date:** September 24, 2026

**Standards Body:** Open Virtual Tabletop Consortium (OVTC) & Open TableTop Initiative (OTI)

**License:** Dual CC0 1.0 (Schemas) & Apache 2.0 (Reference Code)

---

## Section 1: Executive Summary & Core Pillars

### 1.1. Introduction

The Universal Virtual Tabletop Version 2 (UVTT v2) standard establishes a modern, performant, and extensible system-neutral open specification for TTRPG campaign map data. It replaces legacy, flat-plane, single-file geometries with a multi-layered, topologically aware relational spatial database framework. This specification addresses severe rendering, parsing, and data carriage bottlenecks that have historically constrained developers using the legacy v1 formats (`.dd2vtt` and `.df2vtt`).

### 1.2. The Core Technical Bottlenecks of Legacy v1

- **Payload Inflation (Base64 Memory Crisis):** Legacy v1 packages visual assets by encoding multi-megabyte binary images as raw Base64 strings embedded directly inside a single monolithic JSON file. This encoding inflates transmission payloads by approximately 33.3% and forces client browsers or desktop VTT execution engines to perform expensive CPU string-parsing passes, causing frequent Out-of-Memory (OOM) exceptions and browser thread lock-ups during campaign initialization.
- **The "Flat Earth" Assumption:** Legacy standards assume all maps represent an infinite, perfectly flat 2D plane. They contain no native mechanism to express verticality, ceiling intersections, multi-level stairs, or 3D coordinate spaces, making vertical tactical gameplay a manual, improvised chore for GMs.
- **Computational Inefficiency:** To represent curved architecture, legacy formats force authors to plot dozens of rigid, multi-point straight-line approximations. This results in massive vertex arrays that degrade GPU vector processing performance and introduce microscopic "light leaks" and visual artifacts during real-time raycasting.
- **Disconnected Campaign Islands:** Legacy maps are isolated geographic entities. Interlinking separate rooms, levels, or distinct map coordinates requires manual GM placement or fragile, version-locked application macros and plugins.

### 1.3. The Architectural Solutions of UVTT v2

- **Zipped Binary Container Archive (`.uvtt2z` / `.gvtt`):** Replaces monolithic JSON payloads with a standard zipped directory structure that cleanly detaches heavy high-resolution visual artwork from lightweight, streamable structural layouts.
- **Hardware-Accelerated Client Pipeline:** Establishes native support for hardware-accelerated rendering pipelines, transitioning the default rendering engine baseline from legacy WebGL 2.0 contexts to WebGPU.
- **Material-Aware 3D Geometry:** Supports vertical boundaries for walls, portal states, and overhead roof foliage layers, integrated with W3C SVG parametric Bézier curve structures.
- **Topological Spatial Networks:** Connects maps as node objects within a directed campaign graph. Portals and landing zones form the interactive edges connecting these nodes, allowing for instant, lag-free transitions across levels.

---

## Section 2: Archive Container & Package Topology

### 2.1. The Zipped Container Directory Tree

A compliant `.uvtt2z` or `.gvtt` package is a standard compression-compliant ZIP archive. To prioritize streamability and sub-second catalog indexing on client VTT servers, file offsets inside the container must adhere to a strict structure. This allows backend services to query and load layout coordinates without loading heavy visual textures into system RAM.

To maximize CPU efficiency during extraction, the following compression standards are **strictly mandated**:

- **Structural Metadata (`.json`):** Must be packed using `DEFLATE` compression.
- **Media Binaries (`.webp`, `.ogg`, `.webm`):** Must be packed using `STORE` (no compression) to prevent wasting CPU cycles on already highly-compressed media algorithms.

The standard internal layout of a `.uvtt2z` archive conforms to the following directory structure:

```text
package-root.uvtt2z/            # Master ZIP Archive
├── manifest.json              # Global catalog index, grid topology, hardware specs
├── preview.webp               # 512x512 low-resolution map thumbnail
├── maps/                      # Map Catalog containing layout vectors and fallbacks
│   └── ground_floor/          # Slugified folder name for map level
│       ├── geometry.json      # Structural geometry vectors (walls, portals, roofs, zones)
│       └── entities.json      # Dynamic entities (lights, teleports, weather, audio)
└── assets/                    # Shared Binary Assets (Volatile Protected Layer)
    ├── map_hires.webp.enc     # AES-256-GCM encrypted high-resolution visual raster
    ├── audio_loop_01.ogg.enc  # AES-256-GCM encrypted premium ambient soundtrack
    └── basemap.webp           # Unencrypted 50px-grid watermarked fallback image


```

### 2.2. The Dual-Topology Paradigm: Compound vs. Federated

To support diverse campaign environments, UVTT v2 natively handles two packaging topologies using identical metadata schemas:

#### 2.2.1. Compound Archives (Single-File Multi-Floor Modules)

Perfect for a self-contained building or an official adventure module. The mapmaker packages all levels, levels, and structures into a single `.uvtt2z` file. The global `manifest.json` acts as the root registry, linking sub-map directories inside the ZIP. Multi-floor transitions use the **`internal://`** URI protocol:

`internal://second_floor#lz_staircase_arrival`

#### 2.2.2. Federated Archives (Distributed Map Networks)

Designed for sprawling sandbox campaign settings or massive mega-dungeons where compiling everything into a single archive would cause the package size to balloon past 500MB and crash browser memory limits. Each map exists on the host disk as a separate `.uvtt2z` file. Cross-file transitions utilize the **`relative://`** URI protocol, allowing maps to exist as peers:

`relative://undermountain_lvl2.uvtt2z#lz_shaft_arrival`

### 2.3. Path Safety & Slugification

To prevent cross-operating system file pathing exceptions and URI parsing bugs, folder and file references inside compound archives must be strictly **slugified**. Compliance engines must parse map and file names into URL-safe, lowercase alphanumeric formats.

---

## Section 3: Grid Topology & Resolution Scale

### 3.1. Grid Configurations

UVTT v2 replaces simple pixel-based grids with a flexible coordinate mapping topology system to natively support diverse tactical game engines. The grid type is declared under `resolution.topology` in `manifest.json`:

- **Square (`square`):** Standard orthogonal grid cells.
- **Hexagonal (`hex`):** Requires two parameters:
- `orientation`: Must be `flat_top` (sitting on its flat horizontal edge) or `pointy_top` (balancing on a vertex).
- `offset`: Row/column stagger alignment. Must be `odd_row`, `even_row` (for pointy_top), or `odd_col`, `even_col` (for flat_top).

- **Isometric (`isometric`):** Maps coordinates to a skewed 2.5D perspective. Requires a float `isometric_ratio` parameter (typically `0.5`, indicating a standard 2:1 pixel ratio) to calculate the mathematical projection skew without requiring GMs to manually stretch assets.

### 3.2. Hardware Profiles

To safeguard low-spec mobile or tablet hardware from WebGL context crashes, the manifest declares an explicit `hardware_profile`. This allows older WebGL2 engines to gracefully bypass advanced capabilities (like compute shaders or normal mapping layers) while letting modern engines flex their full power:

```json
"hardware_profile": {
  "minimum_pipeline": "webgl2",
  "recommended_pipeline": "webgpu",
  "requires_compute_shaders": false
}

```

---

## Section 4: 3D-Aware Material Geometry

The `geometry.json` file is the mathematical heart of the map. It strictly defines the spatial coordinate planes used by Virtual Tabletops to render Line-of-Sight (LoS), lighting, and evaluate movement capabilities (such as the Open TableTop Initiative's `.wasm` Zero-Knowledge engine).

### 4.1. The Cartesian Coordinate Mandate

All vector layouts (walls, portals, and semantic zones) **must** map to continuous 2D Cartesian spatial units (`X, Y`) relative to the `map_origin`. **These vector coordinates are completely independent of the visual grid topology.** Whether the `resolution.topology` is set to `square`, `hex`, or `isometric`, the underlying geometry math remains a pure Cartesian plane to ensure flawless cross-engine physics and raycasting.

### 4.2. W3C SVG Vector Paths & Height Boundaries

Every wall and portal segment abandons performance-killing multi-point segments in favor of native W3C SVG-style vector arrays, drastically reducing the client memory footprint and offloading curve rendering calculations:

- `move`: Establishes the starting coordinates (X, Y).
- `line`: Draws a linear segment to target coordinates (X, Y).
- `bezier`: Parametric Cubic Bézier curves defined by two control points `cp1`, `cp2`, and a destination point `to`.

Every vector contains a 3D verticality boundary object (`height`) containing `bottom` and `top` float limits, measured in standard map units (e.g. feet/meters).

### 4.3. Directional Line-of-Sight (The Right-Hand Rule)

To support one-way force fields, cliffside ledges, secret windows, and one-way mirrors, UVTT v2 implements directional ray-blocking vectors calculated mathematically using Left/Right normal projections relative to the vector heading.

In the schema, the `directional_blocks` array defines raycast blockage properties (`light`, `sight`, `movement`) passing from `left_to_right` and `right_to_left` independently.

### 4.4. Material-Aware Phasing States

- **Illusory Walls:** Walls that visually block light, sight, and movement, but can be bypassed. When a player disbelieves the illusion (e.g., via an active Investigation check), their client ID is added to the `disbelieved_by` array. The VTT selectively drops the sight block and lowers the opacity of the wall solely for those players.
- **Ethereal Walls:** A global boolean flag `ethereal: true`. This allows the VTT to temporarily bypass movement and sight restrictions globally (e.g., if a spell activates or a sliding gate shifts) without forcing the GM or software to physically delete the wall vectors from the map.
- **Portals (Doors/Windows):** Portals use the identical `path: []` array format as walls, but include interactive `state` properties (`open`, `closed`, `locked`) that dynamically toggle their blocking behavior based on player or GM interaction.

### 4.5. CAD-Style Geometry Cleanups

To guarantee zero light leaks during dynamic raycasting, compliance engines must execute a **Vertex Snapping (Tolerance) Algorithm** during ingestion. If the endpoint coordinates of two separate wall or portal segments fall within a microscopic radius of each other (<= 0.05 map units), the points are snapped to exact identical coordinates, mathematically sealing the corner.

This snapping pass must evaluate _all_ Walls, Portals, and Semantic Zones within a single, unified intersection graph to ensure corner seals between differing object types are completely watertight.

### 4.6. Semantic Zones

Zones define invisible mathematical boundaries that affect tokens traveling through or standing inside them. These polygons are explicitly **agnostic of rulesets**. They do not declare mechanical costs (like "costs 10 feet of movement"). Instead, they use standardized semantic `traits` that a ruleset's engine evaluates.

```json
"zones": [
  {
    "id": "zone_swamp_01",
    "path": [
      { "x": 5, "y": 5 },
      { "x": 8, "y": 5 },
      { "x": 8, "y": 9 },
      { "x": 5, "y": 9 }
    ],
    "properties": {
      "visibility": "gm_only"
    },
    "traits": ["difficult_terrain", "water"]
  }
]

```

#### Official Semantic Trait Dictionary

To guarantee interoperability across different game systems (D&D, Pathfinder, Year Zero Engine), mapmakers should tag zones using the following official string traits:

- `difficult_terrain`: Standard hindrance (e.g., mud, furniture).
- `greater_difficult_terrain`: Heavy hindrance (e.g., deep snow, thick bogs).
- `hazardous`: Environmental dangers (e.g., spikes, lava, acid).
- `obscured`: Visual hindrance without a solid wall (e.g., fog, magical darkness).
- `narrative_boundary`: Abstract spatial dividers (used in Zone-based games like _Fate_ or _Alien RPG_).
- _Custom / Flavor Tags:_ Creators may stack arbitrary string tags (e.g., `water`, `ice`, `magic`) for specific rulesets to intercept (e.g., ignoring difficult terrain if a creature has the "Swampwalk" or "Ice Climb" ability).

---

## Section 5: Environmental & Interactive Entities

### 5.1. Advanced Illumination

Lights support 3D coordinate space placement (X, Y, Z). The illumination math supports two physical decay models:

#### 5.1.1. Linear Decay

Light fades evenly from the bright center to the dim outer radius.

#### 5.1.2. Inverse-Square Decay (Physical Baseline)

Simulates realistic, natural light falloff based on the physical distance to the token along the 3D vector. Directional lights require the `cone` object to constrain the light beam to a designated sector beam, using compass heading `rotation` and arc width `arc`.

### 5.2. Topological Landing Zones

Landing zones establish player token spawn locations or camera viewpoints, resolving the "blind drop" coordinate problems of legacy formats:

- `is_default`: Exactly one default starting zone is permitted per map to securely initialize player viewports.
- `camera_zoom_level`: Sets the initial scale factor of the VTT viewport on load.

### 5.3. Spatial Event Triggers

Interactive triggers (traps, teleporters, elevators) are mapped inside `events` using geometric bounding polygons (`trigger_bounds`):

- **Intra-Map Teleports:** Swaps token coordinates on the active canvas (including Z-level stairs). Includes support for `relative_offset` coordinates to preserve party formation and prevent messy stacking.
- **Inter-Map Teleports:** Triggers transitions across separate map archives, utilizing relative URI path pointers and automated pre-load visual transition wipes.
- **Portal-Dependent Triggers (Gated Transitions):** For vertical or horizontal transitions blocked by a physical structure (e.g., trapdoors, hatches, sliding stone panels, or locked sewer grates), events support an optional `portal_dependency` property. This block references a specific portal by its `portal_id` and defines an array of `allowed_states` (e.g., `["open", "broken"]`) required for the event trigger to activate. If a token enters the event's `trigger_bounds` while the referenced portal is in a disallowed state (e.g., `"closed"` or `"locked"`), the transition fails, and the client engine displays a customizable `lock_feedback_message`.

### 5.4. Three-Tier Audio Physics

Audio structures are divided into three strict playback tiers:

1. **Tier 1 (Global Music):** Uniform background playback for all clients.
2. **Tier 2 (Global Ambience):** PERSISTENT environmental loops (wind, rain).
3. **Tier 3 (Localized Acoustic Zones):** Interactive 3D rooms using a geometric boundary and an outer `fade_radius` to calculate linear proximity attenuation as tokens approach.

Additionally, an optional `muffled_by_geometry` boolean flag determines if the VTT's acoustic engine should apply material-aware raycasting to block sound through closed portals and walls. If `muffled_by_geometry` is true, the acoustic zone **must** declare a `muffling_factor` float (e.g. `0.5`) to provide the host engine an explicit mathematical attenuation baseline when sound crosses a barrier.

### 5.5. Weather Emitters & Fluid Dynamics

Weather zones are mapped using geometric polygons. To minimize CPU overhead, the specification defines spatial coordinates and environmental scaling variables, letting the client VTT's GPU handle rendering:

- **The Presets (`type`):** Supports `rain`, `snow`, `fog`, `embers`, and `magic` shaders.
- **Global Overrides (`is_global`):** If true, the particle system blankets the entire map and the bounds polygon object becomes mathematically optional.
- **Z-Index Layering (`render_layer`):** Defines where the particles sit in the rendering stack (`above_overhead`, `below_overhead`, `ground_level`).
- **Height-Aware Clamping (`height`):** An optional bounding cylinder mapping standard bottom and top vertical planes, blocking particle rendering from bleeding onto upper floors or cellars.
- **Boundary Collision Mode (`collision_mode`):** Specifies shader collision interactions (`none`, `mask_under_overhead`, `ground_terminate`, `wall_bounce`).
- **Global Wind-Vector Inheritance:** Emitters scale baseline winds dynamically based on the master manifest using `influence_scale`.

---

## Section 6: DRM & Security Subsystem

### 6.1. The Split-Resolution Encryption Model

To protect premium intellectual property without restricting backwards compatibility, visual assets are divided into two categories:

#### 6.1.1. The Public Layer (`basemap.webp`)

A low-resolution, heavily compressed preview image capped at exactly **50 pixels per grid square**. A visible digital watermark (such as an order transaction ID or "PREVIEW ONLY" badge) must be burned directly into the raw pixels. This unencrypted proxy sits at the root, allowing basic or legacy tools to load the layout without encryption keys.

#### 6.1.2. The Protected Layer (`/protected/`)

Contains full-fidelity, high-resolution visual rasters (typically 140px per grid) and premium audio loops, encrypted using **AES-256-GCM** (Galois/Counter Mode).

- **The Volatile Memory Rule:** Unencrypted high-resolution bytes must **never** touch the user's local disk, browser cache, or persistent file directories. Decryption must occur in volatile, system-isolated RAM.
- **Web Crypto `TransformStream` Integration:** To prevent out-of-memory browser crashes and bypass synchronous garbage-collection race conditions, compliant VTTs should not decrypt massive images into unified array buffers. VTTs **must** utilize the Web Crypto API's native `TransformStream` to stream decrypted chunk fragments straight into the image decoder context, keeping the memory footprint microscopic and secure.

### 6.2. The Root Archive Receipt (`manifest.hash`)

To prevent bad actors from tampering with unencrypted vector lines (e.g. injecting malicious payload links or script coordinates into unencrypted layout files), every `.uvtt2z` archive must include a root integrity receipt file named `manifest.hash`.

This is a flat, newline-separated index mapping every file path in the ZIP archive to its cryptographically verified SHA-256 checksum. The importing VTT **must** compute the SHA-256 hash of every unpacked file and verify it against this ledger _before_ parsing any layout `.json` logic or executing scripts. To prevent infinite cryptographic recursion, the `manifest.hash` file must inherently exclude itself from the verification scan loop.

### 6.3. Zero-Knowledge Serverless Edge Clearinghouse (ZKS)

The licensing authority server **never** stores raw symmetric keys in a persistent database. Instead, when a purchase entitlement is verified via JWT/OAuth token verification, the serverless edge worker derives the AES-256 decryption key dynamically in volatile CPU memory using a secure HMAC-SHA256 calculation based on a locally-held master secret, the product SKU, and the file's random key salt:

```text
Derived_Key = HMAC-SHA256(Master_Secret, SKU + Salt)
```

---

## Section 7: Version Lifecycle, Migration, & Licensing

### 7.1. The In-Memory Normalized Model (IMNM) Router

To protect creators from version fragmentation, compliance upgrader tools implement an **In-Memory Normalized Model (IMNM)** routing engine. Every incoming map file—whether legacy v1.0, early v2.0, or future v2.X formats—is parsed upward into a unified, version-agnostic master state in application memory. When exporting, the translation engine down-samples this master memory model to fit the exact schema rules of the requested output target.

### 7.2. Graceful Degradation Rules

When compiling backward from a rich UVTT v2 master state down to a legacy v1.0 format, the exporter must enforce strict down-sampling rules to prevent runtime crashes on older engines:

1. **Bézier Path Subdivision:** SVG curves are mathematically subdivided using the parametric cubic equation at 10 discrete intervals, exporting them as rigid, multi-point straight-line approximations.
2. **Global Property Pruning:** Advanced parameters (like spatial audio zones, particle weather variables, overhead roofs, and landing zone zoom levels) are stripped.
3. **Metadata Comment Fallback:** The exporter embeds a tiny metadata header parameter (`__uvtt_migration_fallback`) inside the legacy output. If the file is later re-imported into a v2-compliant upgrader tool, the system instantly recognizes its heritage and flags the pruned layers by referencing the original object IDs.

### 7.3. Licensing

To encourage developer adoption and eliminate legal barriers for competitors, digital storefronts, and independent creators, the UVTT v2 standard utilizes a dual-licensing framework:

- **Layouts and Schemas (Creative Commons CC0 1.0 Universal):** Core JSON validation schemas, directories, file extensions, and the `manifest.hash` index format are dedicated to the public domain. No platform may claim proprietary patent, copyright, or trade secret rights over the file structure layouts.
- **Reference Implementation Code (Apache License 2.0):** Reference parsers, WebCrypto workers, and CI/CD validation scripts are licensed under Apache 2.0. Section 3 of this license grants all developers a perpetual, royalty-free, and irrevocable patent license to implement the specification inside commercial or proprietary engines.

---

## Section 8: Unified JSON Schema Architectures (v2.0.0)

The three production-ready JSON payloads below demonstrate the exact, validated schemas for `manifest.json`, `geometry.json`, and `entities.json` mapping a modern, high-performance campaign level:

### 8.1. Root Manifest Index: `manifest.json`

```json
{
  "format_version": "2.0.0",
  "uvtt_version": "2.0.0",
  "campaign_name": "Ghul's Labyrinth - Level 01",
  "author": "TheGeolama",
  "license": "CC-BY-NC-4.0",
  "hardware_profile": {
    "minimum_pipeline": "webgl2",
    "recommended_pipeline": "webgpu",
    "requires_compute_shaders": false
  },
  "encryption_handshake": {
    "clearinghouse_url": "https://licensing.retailer.com/v1/drm/handshake",
    "license_authority": "https://auth.retailer.com/.well-known/jwks.json",
    "key_salt_checksum": "a4d39f772b15e45a1f298cd310ba2dfc"
  },
  "environment": {
    "global_wind": {
      "speed": 5.0,
      "angle": 45.0,
      "gust_variance": 0.15
    }
  },
  "audio": {
    "music": {
      "uri": "assets/global_combat_theme.ogg",
      "volume": 0.75,
      "crossfade_duration": 3.0
    },
    "ambience": {
      "uri": "assets/global_storm_loop.ogg",
      "volume": 0.4
    }
  },
  "map_catalog": [
    {
      "id": "ghuls-labyrinth-lvl1",
      "name": "Upper Labyrinth",
      "slug": "upper-labyrinth",
      "path": "maps/upper_labyrinth/",
      "z_index": 0
    }
  ]
}
```

### 8.2. Material-Aware Vectors: `geometry.json`

```json
{
  "format_version": "2.0.0",
  "resolution": {
    "map_origin": { "x": 0.0, "y": 0.0 },
    "grid_size": { "x": 70.0, "y": 70.0 },
    "units_per_grid": 5.0,
    "unit_name": "ft",
    "topology": {
      "type": "hex",
      "orientation": "pointy_top",
      "offset": "odd_row"
    }
  },
  "geometry": {
    "walls": [
      {
        "id": "wall_curved_corridor",
        "type": "standard",
        "height": { "bottom": 0.0, "top": 10.0 },
        "path": [
          { "type": "move", "x": 10.0, "y": 5.0 },
          {
            "type": "bezier",
            "cp1": { "x": 15.0, "y": 5.0 },
            "cp2": { "x": 20.0, "y": 10.0 },
            "to": { "x": 25.0, "y": 15.0 }
          }
        ]
      },
      {
        "id": "wall_one_way_ledge",
        "type": "standard",
        "height": { "bottom": 0.0, "top": 4.5 },
        "path": [
          { "type": "move", "x": 5.0, "y": 10.0 },
          { "type": "line", "x": 15.0, "y": 10.0 }
        ],
        "directional_blocks": {
          "left_to_right": ["movement"],
          "right_to_left": []
        }
      },
      {
        "id": "wall_illusory_stone",
        "type": "illusory",
        "height": { "bottom": 0.0, "top": 10.0 },
        "path": [
          { "type": "move", "x": 20.0, "y": 30.0 },
          { "type": "line", "x": 30.0, "y": 30.0 }
        ],
        "directional_blocks": {
          "left_to_right": ["light", "sight", "movement"],
          "right_to_left": ["light", "sight", "movement"]
        },
        "states": {
          "ethereal": false,
          "disbelieved_by": ["player-token-02"]
        }
      }
    ],
    "portals": [
      {
        "id": "door_secret_treasury",
        "type": "door",
        "sub_type": "secret",
        "state": "closed",
        "height": { "bottom": 0.0, "top": 10.0 },
        "blocks": ["light", "sight", "movement"],
        "path": [
          { "type": "move", "x": 12.0, "y": 30.0 },
          { "type": "line", "x": 15.5, "y": 30.0 }
        ]
      }
    ],
    "overhead": [
      {
        "id": "roof_wizard_spire",
        "type": "roof",
        "height": { "bottom": 12.0, "top": 35.0 },
        "polygon": [
          { "x": 40.0, "y": 40.0 },
          { "x": 60.0, "y": 40.0 },
          { "x": 60.0, "y": 60.0 },
          { "x": 40.0, "y": 60.0 }
        ],
        "image": {
          "uri": "assets/spire_roof.webp"
        }
      }
    ],
    "zones": [
      {
        "id": "zone_swamp_01",
        "path": [
          { "x": 5, "y": 5 },
          { "x": 8, "y": 5 },
          { "x": 8, "y": 9 },
          { "x": 5, "y": 9 }
        ],
        "properties": {
          "visibility": "gm_only"
        },
        "traits": ["difficult_terrain", "water"]
      },
      {
        "id": "zone_lava_01",
        "path": [
          { "x": 12, "y": 15 },
          { "x": 14, "y": 15 },
          { "x": 14, "y": 18 }
        ],
        "properties": {
          "visibility": "gm_only"
        },
        "traits": ["hazardous", "difficult_terrain", "fire"]
      }
    ]
  }
}
```

### 8.3. Dynamic Entities & Interaction Layer: `entities.json`

```json
{
  "format_version": "2.0.0",
  "lights": [
    {
      "id": "light_flickering_torch",
      "type": "directional",
      "position": { "x": 15.0, "y": 12.0, "z": 6.5 },
      "color": "#f97316",
      "bright_radius": 15.0,
      "dim_radius": 30.0,
      "decay": "inverse_square",
      "cone": {
        "rotation": 180.0,
        "arc": 120.0
      },
      "animation": {
        "type": "flicker",
        "speed": 1.5,
        "intensity_variance": 0.25
      }
    }
  ],
  "landing_zones": [
    {
      "id": "lz_surface_stair_arrival",
      "name": "Stairwell Spawn",
      "is_default": true,
      "coordinates": [12.0, 14.5],
      "heading_degrees": 90.0,
      "properties": {
        "description": "Arrival point descending from the castle ruins.",
        "camera_zoom_level": 1.2
      }
    }
  ],
  "events": [
    {
      "id": "trigger_chasm_pitfall",
      "type": "teleport",
      "trigger_bounds": {
        "shape": "polygon",
        "points": [
          { "x": 45.0, "y": 30.0 },
          { "x": 47.0, "y": 30.0 },
          { "x": 47.0, "y": 32.0 },
          { "x": 45.0, "y": 32.0 }
        ]
      },
      "conditions": {
        "requires_interaction": false,
        "allowed_modes": ["walking", "running"]
      },
      "destination": {
        "type": "inter_map",
        "uri": "relative://ghuls_labyrinth_lvl2.uvtt2z#lz_shaft_drop_landing",
        "fade_transition": "crossfade_black",
        "prediction_trigger_radius": 3.0
      }
    },
    {
      "id": "event_tavern_trapdoor_down",
      "type": "teleport",
      "trigger_bounds": {
        "shape": "circle",
        "center": { "x": 12.0, "y": 14.5 },
        "radius": 1.5
      },
      "conditions": {
        "requires_interaction": true,
        "interaction_key": "use_ladder"
      },
      "destination": {
        "type": "intra_map",
        "uri": "internal://tavern_cellar#lz_cellar_staircase",
        "prediction_trigger_radius": 2.5
      },
      "portal_dependency": {
        "portal_id": "door_secret_treasury",
        "allowed_states": ["open", "broken"],
        "lock_feedback_message": "The heavy iron-bound trapdoor is firmly shut."
      }
    }
  ],
  "audio": {
    "zones": [
      {
        "id": "acoustic_water_dripping",
        "shape": "circle",
        "center": { "x": 22.4, "y": 18.1 },
        "radius": 4.0,
        "fade_radius": 6.0,
        "volume_max": 0.85,
        "audio_uri": "assets/sfx_dripping_water.ogg",
        "muffled_by_geometry": true,
        "muffling_factor": 0.5
      }
    ]
  },
  "emitters": [
    {
      "id": "weather_blizzard_courtyard",
      "type": "snow",
      "is_global": false,
      "bounds": {
        "shape": "polygon",
        "points": [
          { "x": 0.0, "y": 0.0 },
          { "x": 100.0, "y": 0.0 },
          { "x": 100.0, "y": 100.0 },
          { "x": 0.0, "y": 100.0 }
        ]
      },
      "height": {
        "bottom": 0.0,
        "top": 40.0
      },
      "properties": {
        "intensity": 0.8,
        "speed": 4.5,
        "angle": 135.0,
        "color": "#ffffff",
        "render_layer": "above_overhead",
        "collision_mode": "mask_under_overhead",
        "wind_influence": {
          "inherit_global": true,
          "influence_scale": 1.2
        }
      }
    }
  ]
}
```
