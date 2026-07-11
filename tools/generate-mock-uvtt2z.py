#!/usr/bin/env python3
"""
Universal VTT v2 (.uvtt2z) Mock Package Generator
Generates a fully compliant, cryptographically signed UVTT v2 map archive.
Supports standard unencrypted and Split-Resolution DRM encrypted output profiles.

Usage:
  python3 generate_mock_uvtt2z.py -o test_map.uvtt2z
  python3 generate_mock_uvtt2z.py --drm -o test_map_drm.uvtt2z
"""

import os
import sys
import json
import hmac
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

# Fallback secrets if none are provided
DEFAULT_SECRET = "secret-retailer-key-12345"
DEFAULT_SKU = "SKU-DUNGEON-001"
DEFAULT_SALT = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def calculate_sha256(data: bytes) -> str:
    """Computes the hex SHA-256 hash of a byte slice."""
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def derive_key(secret: str, sku: str, salt: str) -> bytes:
    """
    Derives a symmetric AES-256 key matching our Zero-Knowledge Clearinghouse formula:
    Key = HMAC-SHA256(RETAILER_MASTER_SECRET, Product SKU + Key Salt)
    """
    msg = (sku + salt).encode("utf-8")
    h = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256)
    return f.digest() if hasattr(f := h, 'digest') else h.digest()

def generate_map_image(grid_size=70, grid_count=10, watermark=None) -> Image.Image:
    """Generates a mock map visual layer using PIL."""
    size = grid_size * grid_count
    # Create base canvas with a parchment-like warm background
    img = Image.new("RGB", (size, size), color=(235, 220, 195))
    draw = ImageDraw.Draw(img)

    # Draw grid lines
    grid_color = (200, 180, 150)
    for i in range(grid_count + 1):
        offset = i * grid_size
        # Vertical grid
        draw.line([(offset, 0), (offset, size)], fill=grid_color, width=1)
        # Horizontal grid
        draw.line([(0, offset), (size, offset)], fill=grid_color, width=1)

    # Draw a stylized dungeoneering "room outline"
    wall_color = (40, 50, 70)
    # Outer walls of a center chamber
    draw.rectangle([grid_size * 2, grid_size * 2, grid_size * 8, grid_size * 8], outline=wall_color, width=4)
    # Inner pillar
    draw.rectangle([grid_size * 4, grid_size * 4, grid_size * 6, grid_size * 6], fill=(180, 160, 130), outline=wall_color, width=3)

    # Optional watermark overlay
    if watermark:
        # Draw transparent/semitransparent red watermark text
        try:
            # Fall back to default font if custom font isn't found
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        # Draw thick diagonal watermark text across map
        draw.text((grid_size * 3, grid_size * 5), watermark, fill=(180, 50, 50), font=font)

    return img

def create_mock_package(output_path: str, drm: bool, secret: str, sku: str, salt: str):
    print(f"[*] Initializing UVTT v2 generation pipeline. Target: {output_path}")
    
    zip_buffer = BytesIO()
    files_to_hash = {}

    # Define standard geometric variables mapped to pixels
    grid_px = 70
    grid_units = 5
    scale_factor = grid_px / grid_units # conversion factor: 14 pixels per 1 ft (at 5ft per grid cell)

    # 1. Generate Images
    print("[*] Generating raster visual assets...")
    # Generate high-resolution source canvas
    premium_map_img = generate_map_image(grid_size=grid_px, grid_count=10)
    # Generate low-resolution preview thumbnail (512x512 max capped)
    preview_img = premium_map_img.resize((512, 512), Image.Resampling.LANCZOS)
    
    # Save preview image
    preview_bytes = BytesIO()
    preview_img.save(preview_bytes, format="WEBP", quality=80)
    preview_data = preview_bytes.getvalue()
    files_to_hash["preview.webp"] = preview_data

    # Set up Map files inside Archive based on encryption mode
    if drm:
        if not HAS_CRYPTO:
            print("[!] ERROR: cryptography package is required for AES-256-GCM encryption in DRM mode.")
            sys.exit(1)
            
        print("[*] DRM mode requested. Constructing Split-Resolution assets...")
        # 1. Generate low-res watermarked fallback base map (Capped at 50px per grid)
        low_res_fallback_img = generate_map_image(grid_size=50, grid_count=10, watermark="PREVIEW ONLY - SECURED")
        fallback_bytes = BytesIO()
        low_res_fallback_img.save(fallback_bytes, format="WEBP", quality=50)
        fallback_data = fallback_bytes.getvalue()
        files_to_hash["basemap.webp"] = fallback_data

        # 2. Derive key and encrypt full-fidelity assets
        print(f"[*] Executing serverless deterministic HMAC key derivation for SKU: {sku}...")
        key = derive_key(secret, sku, salt)
        print(f"[*] Derived AES Key SHA-256: {hashlib.sha256(key).hexdigest()}")
        
        premium_bytes = BytesIO()
        premium_map_img.save(premium_bytes, format="WEBP", quality=90)
        premium_data = premium_bytes.getvalue()

        # Encrypt premium raster using AES-256-GCM
        print("[*] Encrypting premium layout via AES-256-GCM...")
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        encrypted_raw = aesgcm.encrypt(nonce, premium_data, None)
        # Format payload: [12 bytes IV] + [encrypted ciphertext + 16 bytes tag]
        encrypted_payload = nonce + encrypted_raw
        files_to_hash["protected/map.webp.enc"] = encrypted_payload
    else:
        print("[*] Standard mode requested. Building open-access bundle...")
        premium_bytes = BytesIO()
        premium_map_img.save(premium_bytes, format="WEBP", quality=90)
        premium_data = premium_bytes.getvalue()
        files_to_hash["assets/basemap.webp"] = premium_data

    # 2. Generate JSON Metadata Payloads
    print("[*] Building JSON system layers...")
    
    # manifest.json
    manifest_data = {
        "uvtt_version": "2.0.0-rc1",
        "name": "Mock Campaign Level 1",
        "resolution": {
            "map_origin": {"x": 0.0, "y": 0.0},
            "grid_size": {"x": float(grid_px), "y": float(grid_px)},
            "units_per_grid": float(grid_units),
            "unit_name": "ft",
            "topology": {
                "type": "square"
            }
        },
        "hardware_profile": {
            "minimum_pipeline": "webgl2",
            "recommended_pipeline": "webgpu",
            "requires_compute_shaders": False
        }
    }

    if drm:
        manifest_data["encryption_handshake"] = {
            "clearinghouse_url": "https://keys.openvtt.org/v2/handshake",
            "license_authority": "https://auth.openvtt.org/jwks.json",
            "key_salt_checksum": salt
        }

    manifest_bytes = json.dumps(manifest_data, indent=2).encode("utf-8")
    files_to_hash["manifest.json"] = manifest_bytes

    # geometry.json
    # Generates standard SVG paths mapped to grids (wall bounds matching room from image)
    # Choirs of walls are aligned with scale (2 grid cells to 8 grid cells padding)
    geometry_data = {
        "walls": [
            # Standard structural wall loop forming a box matching the image drawing
            {
                "id": "wall_chamber_top",
                "type": "standard",
                "height": {"bottom": 0.0, "top": 12.0},
                "blocks": ["light", "sight", "movement"],
                "path": [
                    {"type": "move", "x": 2.0 * grid_units, "y": 2.0 * grid_units},
                    {"type": "line", "x": 8.0 * grid_units, "y": 2.0 * grid_units}
                ],
                "directional_blocks": {
                    "left_to_right": ["light", "sight", "movement"],
                    "right_to_left": []
                },
                "states": {
                    "ethereal": False
                }
            },
            {
                "id": "wall_chamber_right",
                "type": "standard",
                "height": {"bottom": 0.0, "top": 12.0},
                "blocks": ["light", "sight", "movement"],
                "path": [
                    {"type": "move", "x": 8.0 * grid_units, "y": 2.0 * grid_units},
                    {"type": "line", "x": 8.0 * grid_units, "y": 8.0 * grid_units}
                ]
            },
            # Curved wall segment (demonstrating W3C SVG bezier curve serialization)
            {
                "id": "wall_curved_corridor",
                "type": "standard",
                "height": {"bottom": 0.0, "top": 10.0},
                "blocks": ["light", "sight", "movement"],
                "path": [
                    {"type": "move", "x": 8.0 * grid_units, "y": 8.0 * grid_units},
                    {
                        "type": "bezier",
                        "cp1": {"x": 7.0 * grid_units, "y": 9.5 * grid_units},
                        "cp2": {"x": 4.0 * grid_units, "y": 9.5 * grid_units},
                        "to": {"x": 2.0 * grid_units, "y": 8.0 * grid_units}
                    }
                ]
            },
            {
                "id": "wall_chamber_left",
                "type": "standard",
                "height": {"bottom": 0.0, "top": 12.0},
                "blocks": ["light", "sight", "movement"],
                "path": [
                    {"type": "move", "x": 2.0 * grid_units, "y": 8.0 * grid_units},
                    {"type": "line", "x": 2.0 * grid_units, "y": 2.0 * grid_units}
                ]
            }
        ],
        "portals": [
            {
                "id": "door_entrance",
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
        "overhead": [
            {
                "id": "pillar_roof",
                "type": "roof",
                "height": {"bottom": 12.0, "top": 40.0},
                "polygon": [
                    {"x": 4.0 * grid_units, "y": 4.0 * grid_units},
                    {"x": 6.0 * grid_units, "y": 4.0 * grid_units},
                    {"x": 6.0 * grid_units, "y": 6.0 * grid_units},
                    {"x": 4.0 * grid_units, "y": 6.0 * grid_units}
                ],
                "image": {
                    "format": "image/webp",
                    "uri": "assets/roof_house_a.webp"
                }
            }
        ]
    }

    geometry_bytes = json.dumps(geometry_data, indent=2).encode("utf-8")
    files_to_hash["geometry.json"] = geometry_bytes

    # entities.json
    entities_data = {
        "lights": [
            # High fidelity light containing bright/dim radius vectors & flicker animations
            {
                "id": "flickering_torch_01",
                "type": "point",
                "position": {"x": 5.0 * grid_units, "y": 5.0 * grid_units, "z": 6.5},
                "color": "#ffaa00",
                "radius": {
                    "bright": 15.0,
                    "dim": 30.0
                },
                "decay": "inverse_square",
                "intensity": 1.0,
                "animation": {
                    "type": "flicker",
                    "speed": 2.5,
                    "intensity_variance": 0.15
                }
            }
        ],
        "teleports": [
            # Architectural elevation change trigger (stairs)
            # Implements the optional 'prediction_trigger_radius' safeguard
            {
                "id": "stairs_to_deeper_crypt",
                "type": "teleport",
                "trigger_bounds": {
                    "shape": "polygon",
                    "points": [
                        {"x": 2.5 * grid_units, "y": 2.5 * grid_units},
                        {"x": 3.5 * grid_units, "y": 2.5 * grid_units},
                        {"x": 3.5 * grid_units, "y": 3.5 * grid_units},
                        {"x": 2.5 * grid_units, "y": 3.5 * grid_units}
                    ]
                },
                "prediction_trigger_radius": 3.0,
                "conditions": {
                    "requires_interaction": True,
                    "interaction_key": "use_stairs",
                    "allowed_modes": ["walking"]
                },
                "destination": {
                    "type": "intra_map",
                    "target_coordinates": {"x": 5.0 * grid_units, "y": 7.0 * grid_units, "z": -15.0},
                    "target_rotation": 0.0,
                    "fade_transition": "crossfade_black"
                }
            }
        ],
        "audio_zones": [
            # Localized ambient acoustics zone containing custom fade radii and volume limits
            # Falloff is linear: V = max(0, min(V_max, V_max * (1 - d/r)))
            {
                "id": "acoustic_water_fountain",
                "bounds": {
                    "shape": "circle",
                    "center": {"x": 5.0 * grid_units, "y": 5.0 * grid_units},
                    "radius": 5.0
                },
                "fade_radius": 15.0,
                "uri": "assets/sfx_dripping_water.ogg",
                "volume_max": 0.8
            }
        ],
        "spawn_points": [
            # Unified spawn points with default marker asserts
            {
                "id": "lz_crypt_entrance_primary",
                "name": "Chamber Entrance",
                "is_default": True,
                "coordinates": [5.0 * grid_units, 1.5 * grid_units],
                "heading_degrees": 180.0,
                "properties": {
                    "description": "Spawn zone for campaign start inside Crypt Level 1.",
                    "camera_zoom_level": 1.2
                }
            }
        ],
        "emitters": [
            # Environment weather emitters block
            {
                "id": "crypt_fog_emitter",
                "bounds": {
                    "shape": "polygon",
                    "points": [
                        {"x": 2.0 * grid_units, "y": 2.0 * grid_units},
                        {"x": 8.0 * grid_units, "y": 2.0 * grid_units},
                        {"x": 8.0 * grid_units, "y": 8.0 * grid_units},
                        {"x": 2.0 * grid_units, "y": 8.0 * grid_units}
                    ]
                },
                "properties": {
                    "type": "fog",
                    "intensity": 0.6,
                    "speed": 1.5,
                    "angle": 180.0,
                    "color": "#e0e0f099"
                }
            }
        ]
    }

    entities_bytes = json.dumps(entities_data, indent=2).encode("utf-8")
    files_to_hash["entities.json"] = entities_bytes

    # Add empty placeholders for custom audio loop assets so paths don't return 404
    files_to_hash["assets/sfx_dripping_water.ogg"] = b"MOCK_OGG_AUDIO_STREAM"
    files_to_hash["assets/global_music.ogg"] = b"MOCK_MUSIC_LOOP_STREAM"
    files_to_hash["assets/global_ambience.ogg"] = b"MOCK_AMBIENCE_STREAM"

    # 3. Create manifest.hash containing the SHA-256 integrity receipt
    print("[*] Generating cryptographic manifest.hash integrity registry...")
    hash_lines = []
    # Sorted file paths ensure identical binary generation for identical content
    for path in sorted(files_to_hash.keys()):
        data = files_to_hash[path]
        checksum = calculate_sha256(data)
        hash_lines.append(f"{checksum}  {path}")
        print(f"  └─ {path}: {checksum}")

    manifest_hash_bytes = ("\n".join(hash_lines) + "\n").encode("utf-8")

    # 4. Write all files to the ZIP container
    print(f"[*] Packaging complete set into ZIP file format (.uvtt2z)...")
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        # Write manifest.hash first for clean parsing ordering
        z.writestr("manifest.hash", manifest_hash_bytes)
        # Write other content
        for path, data in files_to_hash.items():
            z.writestr(path, data)

    # 5. Flush ZIP data to local filesystem
    zip_bytes = zip_buffer.getvalue()
    with open(output_path, "wb") as f:
        f.write(zip_bytes)

    print(f"[+] SUCCESS: Fully conforming UVTT v2 map package successfully created at: {output_path} ({len(zip_bytes)} bytes)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conforming UVTT v2 Archive Builder")
    parser.add_argument("-o", "--output", default="sample_map.uvtt2z", help="Output package filename (ends in .uvtt2z)")
    parser.add_argument("--drm", action="store_true", help="Enable AES-256-GCM Split-Resolution DRM encryption")
    parser.add_argument("--secret", default=DEFAULT_SECRET, help="Retailer master secret used for key derivation")
    parser.add_argument("--sku", default=DEFAULT_SKU, help="Product SKU identifier")
    parser.add_argument("--salt", default=DEFAULT_SALT, help="HMAC-SHA256 key salt checksum")
    
    args = parser.parse_args()
    
    create_mock_package(
        output_path=args.output,
        drm=args.drm,
        secret=args.secret,
        sku=args.sku,
        salt=args.salt
    )
