# Universal VTT v2: Mapmaking Exporter Integration Blueprint
## High-Performance Coordinate Compilation, Path Optimization, and ZIP Packaging
**Format Version:** 2.0.0  
**Target Audience:** Mapmaking Tool Authors, CAD/GIS Engineers, and Procedural Generation Developers  

---

### 🏛️ Executive Summary

The **Universal Virtual Tabletop v2 (UVTT v2)** standard replaces legacy flat formats with a performant, topologically aware, and highly optimized campaign packaging framework [universal-vtt-v2-spec.md]. 

For developers of map-making applications (such as Dungeondraft, Inkarnate, Dungeon Alchemist, or Campaign Cartographer), implementing a high-fidelity v2 export pipeline is critical. The quality of your exporter directly dictates runtime performance inside virtual tabletop (VTT) engines [universal-vtt-v2-spec.md]. 

This blueprint defines the exact mathematical, algorithmic, and packaging standards required to compile, simplify, sign, and build conforming `.uvtt2z` (Standard) [universal-vtt-v2-spec.md] and `.uvtt2k` (DRM-encrypted) [universal-vtt-v2-spec.md] campaign archives.

---

### 🎨 1. The Geometry Compiler Pipeline

To optimize memory usage and offload complex curve drawing to GPU vector processors inside VTT viewports, UVTT v2 deprecates raw vertex lists [universal-vtt-v2-spec.md]. All wall and portal structures MUST be serialized as native, lightweight **W3C SVG-style path arrays** [universal-vtt-v2-spec.md].

#### A. Path Node Schema Mapping (`geometry.json`)
Every element in the `geometry.json` array must map to one of three parametric SVG path nodes [universal-vtt-v2-spec.md]:

1.  **`"type": "move"`**: Resets the coordinate cursor to starting coordinates $(x, y)$ [universal-vtt-v2-spec.md].
2.  **`"type": "line"`**: Evaluates a linear segment from the active cursor position to target coordinates $(x, y)$ [universal-vtt-v2-spec.md].
3.  **`"type": "bezier"`**: Plots a Parametric Cubic Bézier curve [universal-vtt-v2-spec.md], defined by control points `cp1`, `cp2`, and a final anchor point `to` [universal-vtt-v2-spec.md]:

$$P(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3 \quad \text{where} \quad t \in [0, 1]$$

#### B. Directional Normals and the Right-Hand Rule
Every vector drawn possesses an inherent heading based on the path array indexing sequence [universal-vtt-v2-spec.md]. UVTT v2 utilizes this heading to compile directional blockages (such as ledges, one-way windows, or mirror surfaces) using clockwise normal projections [universal-vtt-v2-spec.md]:

Given a vector drawn from coordinates $P_1(x_1, y_1)$ to $P_2(x_2, y_2)$ [universal-vtt-v2-spec.md]:

$$\Delta x = x_2 - x_1, \quad \Delta y = y_2 - y_1$$

The clockwise, Right-Hand normal projection ($\vec{n}_{\text{right}}$) and left-hand normal projection ($\vec{n}_{\text{left}}$) calculate as [universal-vtt-v2-spec.md]:

$$\vec{n}_{\text{right}} = (\Delta y, -\Delta x), \quad \vec{n}_{\text{left}} = (-\Delta y, \Delta x)$$

*   **Rule for Exporters:** When a user draws a one-way vision barrier, your exporter must arrange the coordinate drawing sequence so that the target blockage face lines up with the positive clockwise halfspace [universal-vtt-v2-spec.md]. If the user swaps the block face direction, the exporter should simply reverse the array indexing sequence and swap the Bézier control handles ($P_1 \leftrightarrow P_2$) to flip normal projections $180^\circ$ [universal-vtt-v2-spec.md].

---

### 📐 2. Geometric Sanity Gates & Vector Optimizations

Before writing geometry arrays to disk, your exporter engine must run the following two validation algorithms to prevent runtime leaks and performance degradation:

#### A. Vertex Snapping (Light Leak Prevention)
GMs and cartographers frequently place wall vectors by hand [universal-vtt-v2-spec.md]. Microscopic coordinate offsets at wall junctions (e.g. $x_1 = 12.00$ vs $x_2 = 12.03$) will create single-pixel cracks, causing VTT raycasting engines to leak dynamic light through solid dungeon corners [universal-vtt-v2-spec.md].

**The Snapping Algorithm:**
1.  Initialize a global vertex index registry for the map.
2.  Define a constant tolerance $D_{\text{snap}} = 0.05 \text{ map units}$ (grid units/feet/meters) [universal-vtt-v2-spec.md].
3.  For each vector path segment processed, compare the coordinates of its endpoints ($x_{\text{node}}, y_{\text{node}}$) against all existing entries in the registry.
4.  If the Euclidean distance is within tolerance:
    $$\sqrt{(x_{\text{node}} - x_{\text{registry}})^2 + (y_{\text{node}} - y_{\text{registry}})^2} \le D_{\text{snap}}$$
5.  Coerce the active coordinates to match the registry values exactly, mathematically sealing the corner [universal-vtt-v2-spec.md].

#### B. Collinear Path Simplification
Segmented drawing (such as drawing four individual straight line vectors to construct a simple hallway wall) creates redundant move commands and floating index keys, wasting GPU computation [universal-vtt-v2-spec.md].

**The Simplification Algorithm:**
Your exporter must traverse adjacent line coordinates and merge colinear segments [universal-vtt-v2-spec.md]. For three sequential points ($P_0, P_1, P_2$), calculate the slopes ($m_1$ and $m_2$):

$$m_1 = \frac{y_1 - y_0}{x_1 - x_0}, \quad m_2 = \frac{y_2 - y_1}{x_2 - x_1}$$

If $|m_1 - m_2| \le \epsilon$ (where $\epsilon = 10^{-5}$ represents a rounding buffer), the points are collinear [universal-vtt-v2-spec.md]. Delete $P_1$ and compile a single cohesive path segment from $P_0$ straight to $P_2$, decreasing vector payload overhead drastically [universal-vtt-v2-spec.md].

---

### 📁 3. Modular Compound ZIP Packaging Pipeline

To resolve memory constraints on lower-spec tablets or browser viewports, UVTT v2 mandates a highly efficient, localized subdirectory package topology [universal-vtt-v2-spec.md]. Exporters must discard monolithic centralized `/assets/` schemes in favor of isolated sub-folders [universal-vtt-v2-spec.md].

#### A. Compound Package Structure
All resources for individual levels inside a multi-floor campaign ZIP (`.uvtt2z` or `.uvtt2k`) must be grouped within their own slugified maps directory:

```text
my-compound-archive.uvtt2z/     # Root Archive Container ZIP
├── manifest.json              # Lightweight global index manifest (describing slugs and paths)
├── preview.webp               # High-compression 512x512 preview image
├── manifest.hash              # Mandatory cryptographic validation index
└── maps/                      # Isolated campaign directory
    ├── ground-floor/          # Slugified folder name for first floor
    │   ├── manifest.json      # Local level metrics
    │   ├── geometry.json      # Local SVG geometries
    │   ├── entities.json      # Local interactive triggers (lights, audio, weather)
    │   ├── map.webp           # Full-fidelity premium image
    │   └── basemap.webp       # Capped 50px-grid watermarked fallback image
    └── damp-cellar/           # Slugified folder name for cellar
        ├── manifest.json
        ├── geometry.json
        ├── entities.json
        ├── map.webp
        └── basemap.webp
```

#### B. Strict Path Slugification
To prevent cross-operating system file pathing bugs and URI parsing failures inside VTT engines, all nested directories must be strictly slugified using the official standard:
$$\text{Slugify}(S) = \text{RegExReplace}\left(\text{Lower}(S), \text{"/[^a-z0-9]+/g"}, \text{"-"} \right)$$

#### C. Local URI Rewriting Protocol
When compiling a Compound Archive, the exporter must scan all teleport triggered endpoints inside `entities.json` [universal-vtt-v2-spec.md]. Any relative map links (`relative://`) pointing to sibling files in the workspace must be rewritten as internal local campaign endpoints (`internal://`) pointing directly to their target sub-directory slug [universal-vtt-v2-spec.md]:
*   *Before Rewrite:* `"uri": "relative://tavern_cellar.uvtt2z#lz_ladder_staircase"` [universal-vtt-v2-spec.md]
*   *After Compound Rewrite:* `"uri": "internal://tavern-cellar#lz_ladder_staircase"` [universal-vtt-v2-spec.md]

---

### 🛡️ 4. Cryptographic Asset Signing (The `manifest.hash` Engine)

To protect your software platform and premium creators from unauthorized asset modification, code injection, or malicious vector scripts inside the ZIP, exporters must generate a root validation receipt [universal-vtt-v2-spec.md]:

1.  **Iterate and Digest:** Immediately following the compression of all unencrypted layout and binary files, your exporter must iterate through the ZIP entries, computing the cryptographic **SHA-256 hash** of every individual file byte array.
2.  **Order and Write:** Write the computed hashes into a flat, newline-separated text file named **`manifest.hash`** at the root of the archive [universal-vtt-v2-spec.md].
3.  **Format Mapping:** Lines must use the standard dual-space formatting:
    ```text
    SHA-256_Checksum  File_Path
    ```
    *Sample Receipt Layout:*
    ```text
    1a812b5f4c4683e1985f698ef0ac87715335aad4866af8da293d2754ff127d94  manifest.json
    7f0c9b7eadb0727e1a1d5761afded97a476e4de6eec7efa2c024a6db2c88c348  maps/cellar/geometry.json
    048f056bd417dbd334c6570ae7a7eb5591e43163a2c684d5bc7ba2cdabdcce2b  maps/cellar/map.webp
    ```
4.  **Save in Root:** Save the compiled `manifest.hash` in the archive root directory [universal-vtt-v2-spec.md]. Client VTT importers will calculate local digests and reject the entire archive if any files mismatch, securing the platform from code injection exploits [universal-vtt-v2-spec.md].

By integrating these precision geometric cleanups, SVG curves, localized compound directories, and hash validation signatures directly into your export engine, you guarantee your software exports the most secure, responsive, and performance-optimized campaign maps in the TTRPG industry [universal-vtt-v2-spec.md]!
