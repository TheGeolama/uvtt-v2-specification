# ⏱️ UVTT v2 Developer Quickstart: Implement a Compliant Parser in 5 Minutes

Welcome, VTT developers and map-tool authors! If you are tired of parsing legacy formats with massive, browser-choking Base64 payloads and fragile coordinate systems, this guide is for you. 

Here is how to implement a fully compliant **Universal VTT v2 (UVTT v2)** parser in your engine in under five minutes.

---

## 📦 Step 1: Decompress the `.uvtt2z` Container
Unlike legacy V1 formats that stuffed 8K Base64-encoded images straight into single JSON blocks, **UVTT v2 uses a zipped directory structure (`.uvtt2z`)** to completely isolate metadata from heavy binary assets [128, 150, 1841].

Unzip the archive to reveal the following standard directory mapping:
```directory
map_package.uvtt2z/ (ZIP Root)
├── manifest.json            # Global metadata, grid resolution, and global audio
├── geometry.json            # Vector lines-of-sight, walls, and overhead roof boundaries
├── entities.json            # Dynamic lights, teleport triggers, audio zones, and emitters
└── assets/                  # Binary folder (basemap webp, spatial audio oggs, textures)
```

---

## 🔍 Step 2: Instant UI Rendering with `manifest.json` (Lazy Loading)
To build a fast map catalog or display a thumbnail, **do not parse the entire package**. Your UI thread only needs to load the lightweight `manifest.json` [151, 1727, 1730]:

```json
{
  "format_version": "2.0.0",
  "uvtt_version": "2.0.0",
  "name": "The Whispering Cellar",
  "resolution": {
    "width_pixels": 2800,
    "height_pixels": 2100,
    "pixels_per_grid": 70,
    "units_per_grid": 5,
    "grid_units": "feet",
    "topology": {
      "type": "square"
    }
  }
}
```
*   **The Big Win:** You can lazy-load the heavy vector geometry in the background only when the GM actively double-clicks to open the scene [136, 139, 140].

---

## 📐 Step 3: Draw the Walls with SVG Paths (`geometry.json`)
Open your vector-rendering pipeline (WebGL/WebGPU) and ingest `geometry.json` [1706]. UVTT v2 utilizes **W3C SVG-style path arrays** instead of bloated point lists, supporting native curves beautifully [1552, 1553, 1851]:

```json
{
  "walls": [
    {
      "id": "wall_01",
      "path": [
        { "type": "move", "x": 10.0, "y": 5.0 },
        { "type": "line", "x": 15.0, "y": 5.0 },
        { "type": "bezier", "cp1": {"x": 17.0, "y": 6.0}, "cp2": {"x": 19.0, "y": 4.0}, "to": {"x": 20.0, "y": 5.0} }
      ],
      "properties": {
        "blocks_sight": true,
        "blocks_movement": true,
        "blocks_light": true
      }
    }
  ]
}
```

### 🫵 Quick Rule: Directionality & One-Way Walls
Every wall possesses an inherent direction based on the array order [1556, 1557, 1561]. 
*   **The Right-Hand Rule:** Rotate the wall vector 90 degrees clockwise from the direction of drawing to find the **"Right" or "Front" face** [1556, 1557, 1561]. This determines sight-blocking half-spaces for one-way windows, illusions, or ledges [18, 54, 113, 227].

---

## ⚡ Step 4: Instantiate the Interactive Entities (`entities.json`)
The interactive layer houses dynamic world mechanics. It completely decouples coordinate mapping to prevent breaking if assets are resized [133, 136, 139, 149]:

### 1. 🚩 Spawn Points & Camera Snap Targets (Landing Zones)
Your engine reads the `landing_zones` array to figure out exactly where player tokens should spawn and what zoom level the camera should instantiate [2668, 2693]:
```json
{
  "landing_zones": [
    {
      "id": "lz_main_entrance",
      "name": "Main Entrance",
      "is_default": true,
      "coordinates": [15.5, 4.0],
      "heading_degrees": 180.0,
      "properties": {
        "description": "Party arrival point.",
        "camera_zoom_level": 1.0
      }
    }
  ]
}
```

### 2. 🚪 Seamless Teleportation Events
Instead of hardcoding brittle coordinates inside foreign files, teleport triggers simply target named `landing_zones` using the standardized **URI Protocol** [179, 1157, 1158, 1162, 1165]:
*   **Compound Archive:** `"uri": "internal://cellar_floor#lz_stairs_arrival"` [2838, 2839]
*   **Federated Archive:** `"uri": "relative://tavern_cellar.uvtt2z#lz_stairs_arrival"` [2841, 2842]

```json
{
  "events": [
    {
      "id": "trap_pit",
      "type": "teleport",
      "trigger_bounds": {
        "shape": "circle",
        "center": { "x": 15.5, "y": 10.0 },
        "radius": 1.0
      },
      "destination": {
        "type": "inter_map",
        "uri": "relative://dungeon_level_2.uvtt2z#lz_shaft_drop_landing"
      }
    }
  ]
}
```
*   **Performance Pro-Tip:** Implement **Pre-Slicing Prediction**! When a player moves within the `prediction_trigger_radius` (e.g., 3 units), pre-fetch the target map and cache the localized image tiles so the level transition is instant and seamless [180].

---

## 🛡️ Step 5: Verify Asset Integrity (Web Crypto API)
To support split-resolution DRM and protect creators' premium art and music assets from unauthorized modification or swapping, the exporter compiles a cryptographic signature root [248, 249, 275].

Before serving assets:
1.  Read the `manifest.hash` text file.
2.  Compute the **SHA-256** hash of the premium file (e.g., `assets/basemap.webp`) using your engine's crypto worker [248, 249, 275].
3.  If the hashes do not match, reject the asset.

---

*Now go build! Your platform's users are waiting for the performance and immersive world-building of UVTT v2.*
