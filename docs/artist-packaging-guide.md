# Universal VTT v2: Artist Packaging Guide

## Creating Standalone Asset Archives (`.uvtt2a`)

**Format Version:** 2.0.0  
**Target Audience:** Digital Painters, Token Artists, Audio Designers, and Patreon Creators

---

### 🎨 Introduction: The Era of "Plug-and-Play" Assets

Historically, selling tokens, props, or soundscapes required bundling them into unorganized, raw ZIP folders. When a Gamemaster (GM) purchased your pack, they had to perform a frustrating, repetitive chore: import each image manually, guess the correct grid sizing, configure custom light emissions for torches, and hand-map localized sound loops from scratch.

The **Universal Virtual Tabletop Asset (`.uvtt2a`)** standard changes everything. By packaging your files with a lightweight, artist-friendly metadata sheet (`asset_manifest.json`), your packs become **smart and self-configuring**.

When a GM drops your torch prop onto a map on any conforming virtual tabletop (VTT), the engine instantly scales it to match their grid, ignites a realistic flickering orange fire light, plays a crackling firewood sound loop, and triggers heat embers to drift into the air—all with a single mouse click.

This guide walks you through folder layouts, easy copy-paste metadata templates, and packaging steps to get your artwork `.uvtt2a` certified.

---

### 📂 Step 1: Laying Out Your Folders

Before writing any configuration files, you must organize your artwork and sound files into a clean directory tree. Open a folder on your computer and create the following subdirectories exactly:

```text
my-premium-asset-pack/          # ◄─── Root folder of your asset pack
├── asset_manifest.json         # ◄─── Your smart behavior sheet (described in Step 2)
└── assets/                     # ◄─── Mandatory folder name
    ├── tokens/                 # ◄─── Put character, monster, or vehicle tokens here
    │   └── zombie_grunt.webp
    ├── props/                  # ◄─── Put static furniture, wall fixtures, or map decals here
    │   ├── wall_torch.webp
    │   └── tavern_fireplace.webp
    └── audio/                  # ◄─── Put background music or ambient sound loops here
        ├── campfire_crackle.ogg
        └── tavern_chatter.mp3
```

> 💡 **Artist Pro-Tip:** We strongly recommend exporting your images as **WebP** formats and audio files as **OGG** or **MP3** formats. WebP offers pristine transparency and high-resolution textures at up to $70\%$ smaller file sizes than legacy PNGs, preventing VTT screens from freezing or crashing on lower-spec player hardware.

---

### 📐 Step 2: Drafting the `asset_manifest.json`

The heart of your `.uvtt2a` file is the **`asset_manifest.json`**. This is a simple text file written in JSON that tells VTT software what your files are named, how they should scale, and what dynamic elements they should emit.

Create a new file named `asset_manifest.json` at the root of your pack directory. Below are the three most common artist templates. Simply copy, paste, and customize the text to match your folder files.

#### Template A: Dynamic Prop (Tavern Fireplace with Light, Sound, and Embers)

This template defines an interactive furniture prop. When dropped, it automatically lights up, crackles, and spawns floating soot particles:

```json
{
  "format_version": "2.0.0",
  "package_type": "asset_pack",
  "pack_name": "Tavern & Firelight Essentials Pack",
  "author": "My Artist Name",
  "version": "1.0.0",
  "assets": {
    "props": [
      {
        "id": "prop-tavern-fireplace-01",
        "file": "assets/props/tavern_fireplace.webp",
        "name": "Roaring Stone Hearth Fireplace",
        "default_scale": 100.0,
        "grid_footprint": {
          "width_in_grids": 2.0,
          "height_in_grids": 2.0
        },
        "tags": ["prop", "furniture", "light", "sfx", "emitter"],
        "auto_emits": [
          {
            "type": "light",
            "color": "#f97316",
            "bright_radius": 5.0,
            "dim_radius": 10.0,
            "decay": "inverse_square",
            "animation": {
              "type": "flicker",
              "speed": 1.2,
              "intensity_variance": 0.2
            }
          },
          {
            "type": "audio",
            "audio_uri": "assets/audio/campfire_crackle.ogg",
            "volume_max": 0.8,
            "fade_radius": 6.0,
            "muffled_by_geometry": true
          },
          {
            "type": "emitter",
            "emitter_type": "embers",
            "properties": {
              "intensity": 0.45,
              "speed": 1.5,
              "angle": 270.0,
              "color": "#ff5500"
            }
          }
        ]
      }
    ]
  }
}
```

#### Template B: Sized Character Token (Behemoth Monster)

Standard character tokens usually import at a baseline $1\times1$ scale. For large monsters or vehicles, use the `grid_footprint` parameter to force the VTT to scale the image proportionally across multiple cells (e.g. $3\times3$ cells):

```json
{
  "format_version": "2.0.0",
  "package_type": "asset_pack",
  "pack_name": "Ghul Labyrinth Monster Tokens",
  "author": "My Artist Name",
  "version": "1.0.0",
  "assets": {
    "tokens": [
      {
        "id": "token-zombie-titan-huge",
        "file": "assets/tokens/zombie_grunt.webp",
        "name": "Undead Colossus Titan",
        "grid_footprint": {
          "width_in_grids": 3.0,
          "height_in_grids": 3.0
        },
        "tags": ["token", "monster", "undead", "huge"]
      }
    ]
  }
}
```

#### Template C: Loopable Sound Effects & Background Music

If you publish audio files, use this clean metadata template to standardize defaults for sound boards and ambient controllers:

```json
{
  "format_version": "2.0.0",
  "package_type": "asset_pack",
  "pack_name": "Dungeon Ambiences Volume 1",
  "author": "My Studio Name",
  "version": "1.0.0",
  "assets": {
    "audio": [
      {
        "id": "audio-loop-spooky-crypt",
        "file": "assets/audio/crypt_ambience.ogg",
        "name": "Damp Crypt Dripping Loop",
        "default_volume": 0.5,
        "is_loop": true,
        "tags": ["ambient", "soundscape", "loop", "spooky"]
      }
    ]
  }
}
```

---

### 🧬 Step 3: Understanding Parameter Controls

When setting up your manifest, customize these properties to control how your artwork behaves in the editor workspace:

#### Proportional Sizing (`grid_footprint`)

- **`width_in_grids`** and **`height_in_grids`**: Expressed in whole or half floats (e.g. `2.0`, `1.5`, `3.0`). Sets the exact width and height of the grid bounding footprint when the prop is dragged into the workspace.
- **`default_scale`**: Expressed as a percentage float (`100.0` represents original size).

#### Dynamic Auto-Emissions (`auto_emits`)

You can bind multiple dynamic actions within the array:

- **Lights (`"type": "light"`)**:
  - `color`: Standard hexadecimal color (e.g., `"#f97316"` for warm torch fire, `"#38bdf8"` for cold magic frost).
  - `bright_radius` & `dim_radius`: Distance measured in grid units.
  - `decay`: Set to `"linear"` or `"inverse_square"`. Use `"inverse_square"` for realistic, high-fidelity physical lighting.
  - `animation`: Supports `"type": "flicker"` or `"type": "pulse"`, configured with a decimal `speed` and `intensity_variance`.
- **Acoustics (`"type": "audio"`)**:
  - `audio_uri`: File location of the sound loop (e.g. `assets/audio/creaky_door.ogg`).
  - `fade_radius`: Distance in cells over which the sound fades to silent as the player token moves away.
  - `muffled_by_geometry`: Set to `true` to block sound waves from penetrating closed doors or solid walls.
- **Particles (`"type": "emitter"`)**:
  - `emitter_type`: Sets the shader profile. Choose from `"rain"`, `"snow"`, `"fog"`, `"embers"`, or `"magic"`.
  - `intensity`, `speed`, `angle`, `color`: Configures how particles drift off the prop.

---

### 📦 Step 4: Packaging and Shipping Your Archive

Once your folder directory is finalized and your `asset_manifest.json` is verified, you are ready to compile the final release package.

#### The ZIP Packaging Golden Rule

> ⚠️ **CRITICAL WARNING:** You must compress your files from **INSIDE** your parent directory. If you zip the parent folder itself, the VTT parser will fail to find your manifest in the zip root, rendering the pack invalid.

#### Step-by-Step Compilation:

1.  Open your file manager and navigate to the inside of your `my-premium-asset-pack/` directory.
2.  Select both the `asset_manifest.json` file and the `assets/` subdirectory.
3.  Right-click the highlighted files and choose **Compress** or **Send to Compressed (zipped) Folder**.
4.  Once compiled, rename the output file from `Archive.zip` to your product name ending in **`.uvtt2a`** (e.g. `tavern_firelight_pack.uvtt2a`).

You have successfully packaged a conforming UVTT v2 standalone asset package! You can distribute this `.uvtt2a` archive natively to your backers, Patreon subscribers, or storefront buyers, knowing they can drop your dynamic creations directly into their campaign worlds with zero friction.
