#!/usr/bin/env python3
"""
Conforming UVTT v2 Campaign Archive Builder
Generates a fully compliant multi-level Compound Campaign archive in standard unencrypted
(.uvtt2z) format, or an encrypted DRM payload (.uvtt2z) alongside its physical key (.uvtt2k).
"""

import os
import sys
import json
import hashlib
import zipfile
import argparse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Attempt importing cryptography for AES-GCM
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def calculate_sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def generate_map_image(grid_size=70, grid_count=10, name="Level", watermark=None) -> Image.Image:
    size = grid_size * grid_count
    img = Image.new("RGB", (size, size), color=(235, 220, 195))
    draw = ImageDraw.Draw(img)

    # Draw grid lines
    grid_color = (200, 180, 150)
    for i in range(grid_count + 1):
        offset = i * grid_size
        draw.line([(offset, 0), (offset, size)], fill=grid_color, width=1)
        draw.line([(0, offset), (size, offset)], fill=grid_color, width=1)

    # Draw walls
    wall_color = (40, 50, 70)
    draw.rectangle([grid_size * 2, grid_size * 2, grid_size *
                   8, grid_size * 8], outline=wall_color, width=4)
    draw.rectangle([grid_size * 4, grid_size * 4, grid_size * 6,
                   grid_size * 6], fill=(180, 160, 130), outline=wall_color, width=3)

    # Text overlay
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((grid_size * 3, grid_size * 1.2),
              f"Three-Story Tavern - {name}", fill=(50, 50, 50), font=font)

    if watermark:
        draw.text((grid_size * 3, grid_size * 5),
                  watermark, fill=(180, 50, 50), font=font)

    return img


def create_campaign_archive(output_path: str, drm: bool, key_hex: str):
    print(
        f"[*] Starting UVTT v2 Campaign packaging pipeline. Output target: {output_path}")

    zip_buffer = BytesIO()
    files_to_hash = {}

    grid_px = 70
    grid_units = 5

    # 1. Root Level lightweight manifest.json
    root_manifest = {
        "format_version": "2.0.0",
        "uvtt_version": "2.0.0",
        "campaign_name": "The Rusty Anchor Tavern",
        "author": "TheGeolama",
        "license": "CC-BY-NC-4.0",
        "hardware_profile": {
            "minimum_pipeline": "webgl2",
            "recommended_pipeline": "webgpu",
            "requires_compute_shaders": False
        },
        "map_catalog": [
            {
                "id": "cellar",
                "name": "The Damp Wine Cellar",
                "slug": "cellar",
                "path": "maps/cellar/",
                "z_index": -1
            },
            {
                "id": "ground_floor",
                "name": "The Bustling Common Room",
                "slug": "ground_floor",
                "path": "maps/ground_floor/",
                "z_index": 0
            },
            {
                "id": "second_floor",
                "name": "The Quiet Guest Rooms",
                "slug": "second_floor",
                "path": "maps/second_floor/",
                "z_index": 1
            }
        ]
    }

    root_manifest_bytes = json.dumps(root_manifest, indent=2).encode("utf-8")
    files_to_hash["manifest.json"] = root_manifest_bytes

    # Generate preview.webp
    preview_img = generate_map_image(grid_size=grid_px, grid_count=10, name="Preview").resize(
        (512, 512), Image.Resampling.LANCZOS)
    preview_bytes = BytesIO()
    preview_img.save(preview_bytes, format="WEBP", quality=80)
    files_to_hash["preview.webp"] = preview_bytes.getvalue()

    # Shared Audio Loop Assets
    files_to_hash["assets/global_music.ogg"] = b"MOCK_OGG_AUDIO_GLOBAL_MUSIC"
    files_to_hash["assets/global_ambience.ogg"] = b"MOCK_OGG_AUDIO_GLOBAL_AMBIENCE"
    files_to_hash["assets/sfx_dripping_water.ogg"] = b"MOCK_OGG_AUDIO_DRIPPING_WATER"

    # Define floors configurations
    floors = [
        {"id": "cellar", "name": "The Damp Wine Cellar", "path": "maps/cellar/"},
        {"id": "ground_floor", "name": "The Bustling Common Room",
            "path": "maps/ground_floor/"},
        {"id": "second_floor", "name": "The Quiet Guest Rooms",
            "path": "maps/second_floor/"}
    ]

    for floor in floors:
        path = floor["path"]
        name = floor["name"]
        print(f"[*] Packaging level directory: {path}")

        # Localized sub-map manifest.json
        sub_manifest = {
            "format_version": "2.0.0",
            "uvtt_version": "2.0.0",
            "campaign_name": name,
            "author": "TheGeolama",
            "license": "CC-BY-NC-4.0",
            "hardware_profile": {
                "minimum_pipeline": "webgl2",
                "recommended_pipeline": "webgpu",
                "requires_compute_shaders": False
            }
        }
        files_to_hash[f"{path}manifest.json"] = json.dumps(
            sub_manifest, indent=2).encode("utf-8")

        # Localized geometry.json
        geometry_data = {
            "format_version": "2.0.0",
            "resolution": {
                "map_origin": {"x": 0.0, "y": 0.0},
                "grid_size": {"x": float(grid_px), "y": float(grid_px)},
                "units_per_grid": float(grid_units),
                "unit_name": "ft",
                "topology": {
                    "type": "square",
                    "orientation": "flat_top",
                    "offset": "odd_row"
                }
            },
            "geometry": {
                "walls": [
                    {
                        "id": f"wall_outer_boundary_{floor['id']}",
                        "type": "standard",
                        "height": {"bottom": 0.0, "top": 12.0},
                        "blocks": ["light", "sight", "movement"],
                        "path": [
                            {"type": "move", "x": 2.0 *
                                grid_units, "y": 2.0 * grid_units},
                            {"type": "line", "x": 8.0 *
                                grid_units, "y": 2.0 * grid_units},
                            {"type": "line", "x": 8.0 *
                                grid_units, "y": 8.0 * grid_units},
                            {"type": "line", "x": 2.0 *
                                grid_units, "y": 8.0 * grid_units},
                            {"type": "line", "x": 2.0 *
                                grid_units, "y": 2.0 * grid_units}
                        ]
                    }
                ],
                "portals": [
                    {
                        "id": f"door_main_{floor['id']}",
                        "type": "door",
                        "sub_type": "standard",
                        "state": "closed",
                        "height": {"bottom": 0.0, "top": 8.0},
                        "blocks": ["light", "sight", "movement"],
                        "line": {
                            "p1": {"x": 5.0 * grid_units - 1.0, "y": 2.0 * grid_units},
                            "p2": {"x": 5.0 * grid_units + 1.0, "y": 2.0 * grid_units}
                        }
                    }
                ],
                "overhead": []
            }
        }
        files_to_hash[f"{path}geometry.json"] = json.dumps(
            geometry_data, indent=2).encode("utf-8")

        # Localized entities.json
        entities_data = {
            "format_version": "2.0.0",
            "lights": [
                {
                    "id": f"torch_{floor['id']}_01",
                    "type": "point",
                    "position": {"x": 5.0 * grid_units, "y": 5.0 * grid_units, "z": 6.5},
                    "color": "#ff8800",
                    "bright_radius": 15.0,
                    "dim_radius": 30.0,
                    "decay": "inverse_square",
                    "animation": {
                        "type": "flicker",
                        "speed": 1.5,
                        "intensity_variance": 0.15
                    }
                }
            ],
            "landing_zones": [
                {
                    "id": f"lz_stairs_arrival_{floor['id']}",
                    "name": "Stairs Landing",
                    "is_default": True,
                    "coordinates": [5.0 * grid_units, 2.5 * grid_units],
                    "heading_degrees": 180.0,
                    "properties": {
                        "description": f"Landing Zone on {name}",
                        "camera_zoom_level": 1.1
                    }
                }
            ],
            "events": [],
            "audio": {"zones": []},
            "emitters": []
        }
        files_to_hash[f"{path}entities.json"] = json.dumps(
            entities_data, indent=2).encode("utf-8")

        # Create localized images (map.webp and basemap.webp)
        map_img = generate_map_image(
            grid_size=grid_px, grid_count=10, name=floor["id"].upper())
        map_bytes = BytesIO()
        map_img.save(map_bytes, format="WEBP", quality=90)
        files_to_hash[f"{path}map.webp"] = map_bytes.getvalue()

        fallback_img = generate_map_image(
            grid_size=50, grid_count=10, name=floor["id"].upper() + " FALLBACK", watermark="PREVIEW")
        fallback_bytes = BytesIO()
        fallback_img.save(fallback_bytes, format="WEBP", quality=50)
        files_to_hash[f"{path}basemap.webp"] = fallback_bytes.getvalue()

    # 3. Create manifest.hash integrity registry for all packed files
    print("[*] Generating cryptographic manifest.hash registry...")
    hash_lines = []
    for f_path in sorted(files_to_hash.keys()):
        checksum = calculate_sha256(files_to_hash[f_path])
        hash_lines.append(f"{f_path}:{checksum}")
        print(f"  └─ {f_path}: {checksum}")

    manifest_hash_bytes = ("\n".join(hash_lines) + "\n").encode("utf-8")

    # 4. Pack into standard unencrypted ZIP buffer
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write manifest.hash first
        zf.writestr("manifest.hash", manifest_hash_bytes)
        for f_path, data in files_to_hash.items():
            zf.writestr(f_path, data)

    raw_zip_bytes = zip_buffer.getvalue()

    # 5. Save output or encrypt as dual-file payload
    if drm:
        print("[*] DRM mode enabled. Encrypting the entire zipped package...")
        if not HAS_CRYPTO:
            print(
                "[!] ERROR: cryptography package is missing. Cannot compile encrypted archive.")
            sys.exit(1)

        # Generate random key if not provided
        if not key_hex:
            key_bytes = os.urandom(32)
            key_hex = key_bytes.hex()
        else:
            key_bytes = bytes.fromhex(key_hex)

        aesgcm = AESGCM(key_bytes)
        nonce = os.urandom(12)
        encrypted_raw = aesgcm.encrypt(nonce, raw_zip_bytes, None)
        final_payload = nonce + encrypted_raw

        # Determine paths
        base_name, _ = os.path.splitext(output_path)
        payload_path = f"{base_name}.uvtt2z"
        key_path = f"{base_name}.uvtt2k"

        # Write Payload
        with open(payload_path, "wb") as out_f:
            out_f.write(final_payload)
        # Write Physical Key
        with open(key_path, "w") as k_f:
            k_f.write(key_hex)

        print(f"[+] Cryptographic packaging complete.")
        print(f"    Payload: {payload_path} ({len(final_payload)} bytes)")
        print(f"    Key:     {key_path} (64-char Hex String)")
    else:
        with open(output_path, "wb") as out_f:
            out_f.write(raw_zip_bytes)
        print(
            f"[+] Packaging complete. Archive written successfully to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Three-Story Tavern Conforming Builder")
    parser.add_argument(
        "-o", "--output", default="tavern_three_story.uvtt2z", help="Output path")
    parser.add_argument("--drm", action="store_true",
                        help="Encrypt payload and generate a .uvtt2k physical key.")
    parser.add_argument("--key", default=None,
                        help="Specific 64-character hex key to use. If omitted, a random key is generated.")

    args = parser.parse_args()
    create_campaign_archive(args.output, args.drm, args.key)
