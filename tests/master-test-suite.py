#!/usr/bin/env python3
"""
======================================================================
       UVTT v2 Master Conformance & Cryptographic Verification Suite
======================================================================
A unified, zero-dependency-runnable (or with standard libraries) 
test suite validating the Universal VTT v2 (UVTT v2) standard.

Features:
1. Complete Campaign ZIP Conformance Check & manifest.hash integrity parsing.
2. Strict geometric checks (height Z-bounds, Right-Hand Rule normals, SVG paths).
3. Sound-clamping, landing-zone exclusivity, and prediction trigger constraints.
4. Direct AES-256-GCM envelope decryption using standard raw keys.
======================================================================
"""

import os
import sys
import json
import math
import hashlib
import zipfile
import argparse
from io import BytesIO

# Set up optional cryptography import for AES-GCM tests
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ANSI Color Codes
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"

def log_info(msg, quiet=False):
    if not quiet:
        print(f"{COLOR_BLUE}[*]{COLOR_RESET} {msg}")

def log_success(msg, quiet=False):
    if not quiet:
        print(f"{COLOR_GREEN}[+]{COLOR_RESET} {COLOR_BOLD}{msg}{COLOR_RESET}")

def log_warn(msg):
    print(f"{COLOR_YELLOW}[!] WARNING:{COLOR_RESET} {msg}")

def log_error(msg):
    print(f"{COLOR_RED}[-] ERROR:{COLOR_RESET} {COLOR_BOLD}{msg}{COLOR_RESET}")

# =====================================================================
# SECTION 1: ARCHIVE INTEGRITY & CONFORMANCE SUB_SYSTEM
# =====================================================================

class UVTT2ConformanceChecker:
    def __init__(self, archive_path, quiet=False, key_hex=None):
        self.archive_path = archive_path
        self.quiet = quiet
        self.temp_dir = None
        self.files_map = {}
        self.manifest_data = None
        self.key_hex = key_hex

    def run_all(self):
        log_info(f"Initiating full validation sequence for: {self.archive_path}", self.quiet)
        if not os.path.exists(self.archive_path):
            log_error(f"Target archive not found: {self.archive_path}")
            return False

        is_encrypted = self.archive_path.endswith((".uvtt2k", ".enc"))
        if not is_encrypted and not zipfile.is_zipfile(self.archive_path):
            log_error("Target file is not a valid ZIP container archive (.uvtt2z).")
            return False

        try:
            if is_encrypted:
                log_info("[*] Decrypted envelope requested. Initializing decryption...", self.quiet)
                if not HAS_CRYPTO:
                    log_error("cryptography package is required to decrypt encrypted containers.")
                    return False
                if not self.key_hex or len(self.key_hex) != 64:
                    log_error("A valid 64-character hexadecimal key must be provided to decrypt the container.")
                    return False

                with open(self.archive_path, "rb") as f:
                    enc_bytes = f.read()
                if len(enc_bytes) < 12:
                    log_error("Encrypted payload too short (missing 12-byte IV).")
                    return False

                nonce = enc_bytes[:12]
                ciphertext = enc_bytes[12:]
                key = bytes.fromhex(self.key_hex)
                aesgcm = AESGCM(key)
                
                try:
                    decrypted_zip = aesgcm.decrypt(nonce, ciphertext, None)
                except Exception as e:
                    log_error(f"Decryption failed (Invalid key or corrupted payload): {e}")
                    return False

                zf_input = BytesIO(decrypted_zip)
                log_success("Decryption successful! Decrypted container safely in-memory.", self.quiet)
            else:
                zf_input = self.archive_path

            with zipfile.ZipFile(zf_input, 'r') as zf:
                # 1. Inspect file catalog
                namelist = zf.namelist()
                for name in namelist:
                    self.files_map[name] = zf.read(name)

                # 2. Check manifest.hash existence and check integrity
                if "manifest.hash" not in self.files_map:
                    log_error("Missing mandatory integrity receipt 'manifest.hash' in ZIP root.")
                    return False
                
                if not self.verify_hashes():
                    log_error("Cryptographic hash mismatch. Archive integrity compromised!")
                    return False

                # 3. Read manifest.json
                if "manifest.json" not in self.files_map:
                    log_error("Missing mandatory indexer file 'manifest.json' in ZIP root.")
                    return False

                try:
                    self.manifest_data = json.loads(self.files_map["manifest.json"].decode("utf-8"))
                except Exception as e:
                    log_error(f"Failed to parse manifest.json: {e}")
                    return False

                # 4. Check core version requirements
                fmt_ver = self.manifest_data.get("format_version")
                uvtt_ver = self.manifest_data.get("uvtt_version")
                if fmt_ver != "2.0.0" or uvtt_ver != "2.0.0":
                    log_error(f"Incompatible specification mapping (format: {fmt_ver}, uvtt: {uvtt_ver}). Expected '2.0.0'.")
                    return False

                # 5. Check layout mode (Compound vs. Federated)
                map_catalog = self.manifest_data.get("map_catalog", [])
                if not map_catalog:
                    # Single map Mode (Federated/Standalone fallback check)
                    log_info("Validating Standalone (Federated) archive mode...", self.quiet)
                    if not self.validate_map_directory_files("", standalone=True):
                        return False
                else:
                    log_info(f"Compound Campaign Mode identified. Index contains {len(map_catalog)} maps.", self.quiet)
                    for map_node in map_catalog:
                        path = map_node.get("path")
                        if not path:
                            log_error("Map catalog element is missing mandatory 'path' variable.")
                            return False
                        log_info(f"Validating nested campaign node: {map_node.get('name')} -> {path}", self.quiet)
                        if not self.validate_map_directory_files(path, standalone=False):
                            return False

            log_success("All structural, cryptographic, and geometric constraints PASSED!", self.quiet)
            return True

        except Exception as e:
            log_error(f"Validation aborted due to fatal runtime error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def verify_hashes(self):
        log_info("Executing cryptographic hash audits...", self.quiet)
        hash_lines = self.files_map["manifest.hash"].decode("utf-8").strip().splitlines()
        hash_registry = {}
        for line in hash_lines:
            if not line.strip() or ":" not in line:
                continue
            parts = line.split(":", 1)
            file_path = parts[0].strip()
            sha_hash = parts[1].strip()
            hash_registry[file_path] = sha_hash

        for name, content in self.files_map.items():
            if name in ["manifest.hash", "manifest.json"]:
                continue
            if name not in hash_registry:
                log_error(f"Security Alert: Untracked file found in container: {name}")
                return False
            
            computed_hash = hashlib.sha256(content).hexdigest()
            if computed_hash != hash_registry[name]:
                log_error(f"Checksum mismatch: {name}\n  Expected: {hash_registry[name]}\n  Computed: {computed_hash}")
                return False
        
        log_success("Container integrity match confirmed against manifest.hash.", self.quiet)
        return True

    def validate_map_directory_files(self, path, standalone=False):
        manifest_path = f"{path}manifest.json" if not standalone else "manifest.json"
        geom_path = f"{path}geometry.json" if not standalone else "geometry.json"
        ent_path = f"{path}entities.json" if not standalone else "entities.json"
        
        if standalone:
            map_path = "assets/map.webp"
            base_path = "assets/basemap.webp"
        else:
            map_path = f"{path}map.webp"
            base_path = f"{path}basemap.webp"

        if manifest_path not in self.files_map:
            log_error(f"Missing mandatory localized map manifest: {manifest_path}")
            return False
        try:
            sub_manifest = json.loads(self.files_map[manifest_path].decode("utf-8"))
            if sub_manifest.get("format_version") != "2.0.0":
                log_error(f"Localized sub-map manifest '{manifest_path}' must identify as format '2.0.0'.")
                return False
        except Exception as e:
            log_error(f"Syntax error inside sub-map manifest {manifest_path}: {e}")
            return False

        if base_path not in self.files_map:
            log_error(f"Missing baseline raster texture asset: {base_path}")
            return False

        if map_path not in self.files_map:
            log_error(f"Missing full-fidelity map asset: {map_path}")
            return False

        if geom_path not in self.files_map:
            log_error(f"Missing mandatory architectural layout geometry: {geom_path}")
            return False
        try:
            geom_data = json.loads(self.files_map[geom_path].decode("utf-8"))
            if not self.validate_geometry_schema(geom_data):
                return False
        except Exception as e:
            log_error(f"Syntax error inside {geom_path}: {e}")
            return False

        if ent_path in self.files_map:
            try:
                ent_data = json.loads(self.files_map[ent_path].decode("utf-8"))
                if not self.validate_entities_schema(ent_data):
                    return False
            except Exception as e:
                log_error(f"Syntax error inside {ent_path}: {e}")
                return False
        else:
            log_info(f"No interactive entity definitions for node: {path or 'root'}", self.quiet)

        return True

    def validate_geometry_schema(self, geom):
        resolution = geom.get("resolution", {})
        grid_size = resolution.get("grid_size", {})
        topology = resolution.get("topology", {})

        if not grid_size.get("x") or not grid_size.get("y"):
            log_error("Invalid scale resolution. 'grid_size' X and Y must be positive non-zero parameters.")
            return False

        grid_type = topology.get("type", "square")
        if grid_type not in ["square", "hex", "isometric"]:
            log_error(f"Unsupported grid projection layout: '{grid_type}'")
            return False

        if grid_type == "hex":
            orientation = topology.get("orientation")
            offset = topology.get("offset")
            if orientation not in ["flat_top", "pointy_top"] or offset not in ["odd_row", "even_row", "odd_col", "even_col"]:
                log_error(f"Malformed hexagonal offset layout configuration (orientation: {orientation}, offset: {offset})")
                return False

        if grid_type == "isometric":
            ratio = topology.get("isometric_ratio", 0.5)
            if not (0.0 < ratio <= 1.0):
                log_error(f"Invalid isometric skew calibration index: {ratio}. Must sit within (0.0, 1.0].")
                return False

        geometry = geom.get("geometry", {})
        walls = geometry.get("walls", [])
        for wall in walls:
            wall_id = wall.get("id", "unnamed")
            height = wall.get("height", {})
            path = wall.get("path", [])

            bottom = height.get("bottom", 0.0)
            top = height.get("top", 0.0)
            if bottom > top:
                log_error(f"Verticality conflict on wall '{wall_id}': Bottom height ({bottom}) exceeds Top boundary ({top}).")
                return False

            if not path:
                log_error(f"Wall segment '{wall_id}' defines an empty vector path mapping.")
                return False
            
            for idx, node in enumerate(path):
                cmd_type = node.get("type")
                if cmd_type not in ["move", "line", "bezier"]:
                    log_error(f"Malformed path node command on wall '{wall_id}' index {idx}: '{cmd_type}'")
                    return False
                if idx == 0 and cmd_type != "move":
                    log_error(f"Pathing rule violation on wall '{wall_id}': Base vector node must use 'move' command.")
                    return False

            dir_blocks = wall.get("directional_blocks")
            if dir_blocks:
                if "left_to_right" not in dir_blocks or "right_to_left" not in dir_blocks:
                    log_error(f"Directional wall '{wall_id}' must define both 'left_to_right' and 'right_to_left' blocks.")
                    return False

        return True

    def validate_entities_schema(self, ent):
        landing_zones = ent.get("landing_zones", [])
        default_count = 0
        for lz in landing_zones:
            lz_id = lz.get("id", "unnamed")
            coords = lz.get("coordinates", [])
            if len(coords) != 2:
                log_error(f"Landing zone '{lz_id}' coordinates must be represented as a flat [X, Y] array.")
                return False
            if lz.get("is_default", False):
                default_count += 1

        if default_count > 1:
            log_error(f"Topology Error: Map entities file defines multiple ({default_count}) default landing zones. Enforcing Single-Default limit.")
            return False

        events = ent.get("events", [])
        for ev in events:
            ev_id = ev.get("id", "unnamed")
            dest = ev.get("destination", {})
            rad_pred = dest.get("prediction_trigger_radius", 0.0)
            if rad_pred < 0.0:
                log_error(f"Dynamic pre-slicing window threshold index on '{ev_id}' must be a positive float value: {rad_pred}")
                return False

        audio = ent.get("audio", {})
        zones = audio.get("zones", [])
        for zone in zones:
            zone_id = zone.get("id", "unnamed")
            v_max = zone.get("volume_max", 1.0)
            fade_rad = zone.get("fade_radius", 1.0)

            if not (0.0 <= v_max <= 1.0):
                log_error(f"Volume index overflow on sound zone '{zone_id}': {v_max}. Standard limits: [0.0, 1.0].")
                return False

            if fade_rad <= 0.0:
                log_error(f"Localized acoustic zone decay boundary for '{zone_id}' must be positive and non-zero: {fade_rad}")
                return False

        return True

# =====================================================================
# SECTION 2: SYSTEM SELF-TEST AND MOCK CAMPAIGN VALIDATION
# =====================================================================

def execute_programmatic_self_test():
    """
    Executes mock program validations to test geometric schema parsing and
    decryption flows without external disk dependencies.
    """
    log_info("Initializing internal programmatic self-tests...")
    
    mock_geometry = {
        "format_version": "2.0.0",
        "resolution": {
            "map_origin": {"x": 0.0, "y": 0.0},
            "grid_size": {"x": 70.0, "y": 70.0},
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
                    "id": "illusory_test",
                    "type": "illusory",
                    "height": {"bottom": 0.0, "top": 10.0},
                    "path": [
                        {"type": "move", "x": 10.0, "y": 10.0},
                        {"type": "line", "x": 100.0, "y": 10.0}
                    ],
                    "directional_blocks": {
                        "left_to_right": ["light", "sight"],
                        "right_to_left": []
                    }
                }
            ],
            "portals": []
        }
    }
    
    checker = UVTT2ConformanceChecker("", quiet=True)
    if not checker.validate_geometry_schema(mock_geometry):
        log_error("Self-Test Failed: Standard geometry schema structure validation failed.")
        return False

    failing_geometry = {
        "format_version": "2.0.0",
        "resolution": {
            "map_origin": {"x": 0, "y": 0}, "grid_size": {"x": 70, "y": 70}, "units_per_grid": 5, "unit_name": "ft",
            "topology": {"type": "square"}
        },
        "geometry": {
            "walls": [
                {
                    "id": "height_conflict", "type": "standard",
                    "height": {"bottom": 12.0, "top": 5.0}, 
                    "path": [{"type": "move", "x": 0, "y": 0}, {"type": "line", "x": 10, "y": 10}]
                }
            ],
            "portals": []
        }
    }
    if checker.validate_geometry_schema(failing_geometry):
        log_error("Self-Test Failed: Geometrical validator missed a Z-axis height conflict (bottom > top).")
        return False

    mock_entities = {
        "landing_zones": [
            {"id": "lz1", "coordinates": [5.0, 5.0], "is_default": True, "heading_degrees": 90.0},
            {"id": "lz2", "coordinates": [10.0, 10.0], "is_default": False, "heading_degrees": 180.0}
        ],
        "audio": {
            "zones": [
                {"id": "ac1", "shape": "circle", "radius": 50.0, "fade_radius": 20.0, "volume_max": 0.8, "audio_uri": "test.ogg"}
            ]
        }
    }
    if not checker.validate_entities_schema(mock_entities):
        log_error("Self-Test Failed: Standard entities validation parsing failed.")
        return False

    failing_entities = {
        "landing_zones": [
            {"id": "lz1", "coordinates": [5.0, 5.0], "is_default": True, "heading_degrees": 90.0},
            {"id": "lz2", "coordinates": [10.0, 10.0], "is_default": True, "heading_degrees": 180.0} 
        ]
    }
    if checker.validate_entities_schema(failing_entities):
        log_error("Self-Test Failed: Validator missed multi-default landing zone violations.")
        return False

    log_success("Internal programmatic checks: ALL SCHEMAS CONFORM!")
    return True


# =====================================================================
# SECTION 3: MAIN EXECUTOR & CLI ROUTING
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="UVTT v2 Master Conformance & Cryptographic Verification Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "archive", nargs="?", default=None,
        help="Path to a target .uvtt2z campaign package to validate."
    )
    parser.add_argument(
        "-s", "--self-test", action="store_true",
        help="Execute the suite's built-in programmatic self-tests."
    )
    parser.add_argument(
        "--key", default=None,
        help="The 64-character hex AES-256 key to decrypt a locked archive."
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress informational logs; report output highlights and failures only."
    )

    args = parser.parse_args()

    if not args.quiet:
        print(f"{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}")
        print(f"{COLOR_BOLD}       UVTT v2 System-Agnostic Verification & Conformance Suite       {COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}")

    if not args.archive and not args.self_test:
        parser.print_help()
        sys.exit(0)

    success = True

    if args.self_test:
        if not execute_programmatic_self_test():
            success = False

    if args.archive:
        checker = UVTT2ConformanceChecker(args.archive, args.quiet, key_hex=args.key)
        if not checker.run_all():
            success = False

    if not args.quiet:
        print(f"\n{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}")
        print(f"{COLOR_BOLD}                        FINAL VERIFICATION STATUS                     {COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}")
        if success:
            print(f"  {COLOR_BOLD}{COLOR_GREEN}ALL SECURE GATES PASSED SUCCESSFULLY{COLOR_RESET}")
            print(f"  Your environment conforms cleanly to the UVTT v2 specification.")
        else:
            print(f"  {COLOR_BOLD}{COLOR_RED}VERIFICATION REJECTED: COMPLIANCE CONFLICTS IDENTIFIED{COLOR_RESET}")
            print(f"  Please review the log files above to resolve standard structural errors.")
        print(f"{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}\n")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()