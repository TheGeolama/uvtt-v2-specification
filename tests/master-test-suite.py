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
4. Built-in JWKS & ZKS Edge Clearinghouse Mock Server daemon.
5. Cryptographic signature, entitlement scope, expiration, and revocation checks.
======================================================================
"""

import os
import sys
import json
import math
import hashlib
import hmac
import zipfile
import argparse
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import HTTPServer, BaseHTTPRequestHandler

# Set up optional cryptography & JWT imports for the ZKS tests
try:
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
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
COLOR_CYAN = "\033[36m"

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
    def __init__(self, archive_path, quiet=False):
        self.archive_path = archive_path
        self.quiet = quiet
        self.temp_dir = None
        self.files_map = {}
        self.manifest_data = None

    def run_all(self):
        log_info(f"Initiating full validation sequence for: {self.archive_path}", self.quiet)
        if not os.path.exists(self.archive_path):
            log_error(f"Target archive not found: {self.archive_path}")
            return False

        if not zipfile.is_zipfile(self.archive_path):
            log_error("Target file is not a valid ZIP container archive (.uvtt2z / .gvtt).")
            return False

        try:
            with zipfile.ZipFile(self.archive_path, 'r') as zf:
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
                # The manifest.hash and manifest.json (in some modes) are excluded from active verification loop to avoid circular locks
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
        geom_path = f"{path}geometry.json" if not standalone else "geometry.json"
        ent_path = f"{path}entities.json" if not standalone else "entities.json"
        base_path = f"{path}basemap.webp" if not standalone else "basemap.webp"

        # Validate basemap
        if base_path not in self.files_map:
            log_error(f"Missing baseline raster texture asset: {base_path}")
            return False

        # Validate geometry
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

        # Validate entities if present
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
        # Resolve variables
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

        # Check Hex details
        if grid_type == "hex":
            orientation = topology.get("orientation")
            offset = topology.get("offset")
            if orientation not in ["flat_top", "pointy_top"] or offset not in ["odd_row", "even_row", "odd_col", "even_col"]:
                log_error(f"Malformed hexagonal offset layout configuration (orientation: {orientation}, offset: {offset})")
                return False

        # Check Isometric details
        if grid_type == "isometric":
            ratio = topology.get("isometric_ratio", 0.5)
            if not (0.0 < ratio <= 1.0):
                log_error(f"Invalid isometric skew calibration index: {ratio}. Must sit within (0.0, 1.0].")
                return False

        # Validate vector paths
        geometry = geom.get("geometry", {})
        walls = geometry.get("walls", [])
        for wall in walls:
            wall_id = wall.get("id", "unnamed")
            wall_type = wall.get("type", "standard")
            height = wall.get("height", {})
            path = wall.get("path", [])

            # Check Z-height orientation
            bottom = height.get("bottom", 0.0)
            top = height.get("top", 0.0)
            if bottom > top:
                log_error(f"Verticality conflict on wall '{wall_id}': Bottom height ({bottom}) exceeds Top boundary ({top}).")
                return False

            # Check SVG Vector paths
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

            # Check Right-Hand Rule indicators
            dir_blocks = wall.get("directional_blocks")
            if dir_blocks:
                if "left_to_right" not in dir_blocks or "right_to_left" not in dir_blocks:
                    log_error(f"Directional wall '{wall_id}' must define both 'left_to_right' and 'right_to_left' blocks.")
                    return False

        return True

    def validate_entities_schema(self, ent):
        # Validate Landing Zones (Spawns)
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

        # Validate Portals & Events
        events = ent.get("events", [])
        for ev in events:
            ev_id = ev.get("id", "unnamed")
            dest = ev.get("destination", {})
            rad_pred = dest.get("prediction_trigger_radius", 0.0)
            if rad_pred < 0.0:
                log_error(f"Dynamic pre-slicing window threshold index on '{ev_id}' must be a positive float value: {rad_pred}")
                return False

        # Validate Acoustic Sound Zones
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
# SECTION 2: CRYPTOGRAPHIC ZKS VERIFICATION & DAEMON
# =====================================================================

class MockZKSWorkerHandler(BaseHTTPRequestHandler):
    """
    Simulates a live serverless edge worker (Cloudflare Worker) performing JWT verification,
    JWKS public key hosting, and dynamic HMAC-SHA256 key derivations.
    """
    retailer_master_secret = b"RETAILER_MASTER_CRITICAL_SECRET_2026_07_11"
    revocations_db = {
        # SHA-256 hash of 'TX-REFUNDED-999'
        "revocation:7146af0ad6796308efa99275fa5ac9df9d757494ea6618c9ca84629d56be9cc1": {
            "revoked_at": "2026-07-11T12:00:00Z",
            "reason": "Customer Refund Processing"
        }
    }
    rsa_key_pair = None
    jwks_json = "{}"

    @classmethod
    def generate_signing_keys(cls):
        if not HAS_CRYPTO:
            return
        # Generate raw 2048-bit RSA keys
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.rsa_key_pair = private_key
        
        # Format keys to conform to JWKS requirements
        public_key = private_key.public_key()
        numbers = public_key.public_numbers()
        
        # Base64url helper encoding standard
        def b64url(val):
            import base64
            # Convert integer to bytes then encode
            byte_len = (val.bit_length() + 7) // 8
            b = val.to_bytes(byte_len, byteorder='big')
            return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')

        cls.jwks_json = json.dumps({
            "keys": [{
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "kid": "mock-signing-key-01",
                "n": b64url(numbers.n),
                "e": b64url(numbers.e)
            }]
        }, indent=2)

    def log_message(self, format, *args):
        # Prevent spamming console logs during parallel daemon runs
        pass

    def do_GET(self):
        if self.path == "/.well-known/jwks.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(self.jwks_json.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/v1/drm/handshake":
            self.handle_handshake()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_handshake(self):
        # 1. Parse body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            res = {"status": "error", "error_code": "MALFORMED_PAYLOAD", "message": "Payload body is not valid JSON."}
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        product_sku = payload.get("product_sku")
        key_salt_checksum = payload.get("key_salt_checksum")

        # 2. Check SKU and salt parameter
        if not product_sku:
            self.send_error_response(400, "MISSING_SKU", "The product_sku parameter is required.")
            return

        if not key_salt_checksum or len(key_salt_checksum) != 32:
            self.send_error_response(400, "MALFORMED_SALT", "The key_salt_checksum parameter must be a 32-character hexadecimal string.")
            return

        # 3. Check Auth header
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            self.send_error_response(401, "TOKEN_MISSING", "Bearer authorization token required.")
            return

        token = auth_header.split(" ")[1]

        # 4. Parse token claims and verify signature
        if not HAS_CRYPTO:
            self.send_error_response(500, "LIBS_MISSING", "Cryptographic modules missing on host.")
            return

        try:
            public_key = self.rsa_key_pair.public_key()
            decoded_claims = jwt.decode(token, public_key, algorithms=["RS256"], options={"verify_aud": False})
        except jwt.ExpiredSignatureError:
            self.send_error_response(401, "TOKEN_EXPIRED", "The provided authorization token has expired.")
            return
        except jwt.InvalidTokenError as e:
            self.send_error_response(401, "TOKEN_INVALID", f"Signature validation failed: {e}")
            return

        # 5. Assert entitlements
        user_entitlements = decoded_claims.get("entitlements", [])
        if product_sku not in user_entitlements:
            self.send_error_response(403, "INSUFFICIENT_ENTITLEMENTS", f"The provided license token does not authorize access to the requested {product_sku}.")
            return

        # 6. Check revocation database
        transaction_id = decoded_claims.get("tx_id", "untracked")
        hashed_tx = hashlib.sha256(transaction_id.encode("utf-8")).hexdigest()
        revocation_key = f"revocation:{hashed_tx}"

        if revocation_key in self.revocations_db:
            self.send_error_response(403, "TRANSACTION_REVOKED", "This license receipt has been revoked due to refund processing or security flag.")
            return

        # 7. HMAC-SHA256 derivation
        derivation_input = f"{product_sku}{key_salt_checksum}".encode("utf-8")
        derived_key = hmac.new(self.retailer_master_secret, derivation_input, hashlib.sha256).hexdigest()

        # Success response
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        res = {
            "status": "success",
            "decryption_key_hex": derived_key,
            "algorithm": "AES-GCM",
            "key_length_bits": 256
        }
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def send_error_response(self, status, error_code, msg):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        res = {
            "status": "error",
            "error_code": error_code,
            "message": msg
        }
        self.wfile.write(json.dumps(res).encode("utf-8"))


class CryptographicHandshakeSuite:
    """
    Fires the five required integration test scenarios against either the
    built-in local daemon thread or a live remote Worker endpoint.
    """
    def __init__(self, target_url, master_secret_bytes=None):
        self.target_url = target_url
        self.master_secret_bytes = master_secret_bytes or b"RETAILER_MASTER_CRITICAL_SECRET_2026_07_11"
        self.valid_token = None
        self.expired_token = None
        self.wrong_sku_token = None
        self.revoked_token = None

    def forge_test_tokens(self, rsa_private_key):
        if not HAS_CRYPTO:
            return
        import time
        now = int(time.time())

        # 1. Valid Token
        self.valid_token = jwt.encode({
            "sub": "user_happy_path",
            "entitlements": ["SKU-DUNGEON-001"],
            "tx_id": "TX-SUCCESSFUL-111",
            "iat": now - 10,
            "exp": now + 3600
        }, rsa_private_key, algorithm="RS256", headers={"kid": "mock-signing-key-01"})

        # 2. Expired Token
        self.expired_token = jwt.encode({
            "sub": "user_expired",
            "entitlements": ["SKU-DUNGEON-001"],
            "tx_id": "TX-EXPIRED-222",
            "iat": now - 3600,
            "exp": now - 10
        }, rsa_private_key, algorithm="RS256", headers={"kid": "mock-signing-key-01"})

        # 3. Wrong SKU Token
        self.wrong_sku_token = jwt.encode({
            "sub": "user_wrong_scope",
            "entitlements": ["SKU-DUNGEON-002"],
            "tx_id": "TX-WRONG-SKU-333",
            "iat": now - 10,
            "exp": now + 3600
        }, rsa_private_key, algorithm="RS256", headers={"kid": "mock-signing-key-01"})

        # 4. Revoked Token
        self.revoked_token = jwt.encode({
            "sub": "user_revoked",
            "entitlements": ["SKU-DUNGEON-001"],
            "tx_id": "TX-REFUNDED-999",
            "iat": now - 10,
            "exp": now + 3600
        }, rsa_private_key, algorithm="RS256", headers={"kid": "mock-signing-key-01"})

    def fire_request(self, token, payload, expected_status):
        req = Request(self.target_url, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        data_bytes = json.dumps(payload).encode("utf-8")
        
        try:
            with urlopen(req, data=data_bytes) as res:
                body = res.read().decode("utf-8")
                return res.status, json.loads(body)
        except HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                return e.code, json.loads(body)
            except Exception:
                return e.code, {"message": body}
        except Exception as e:
            return 0, {"message": str(e)}

    def run_handshake_tests(self):
        if not HAS_CRYPTO:
            log_warn("Symmetric testing components are bypassed because 'cryptography' or 'PyJWT' are missing.")
            return False

        print(f"\n{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}")
        print(f"{COLOR_BOLD}         ZKS Clearinghouse Token Authorization Integration Suite       {COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}")
        print(f"Target Endpoint : {self.target_url}")
        print(f"Master Secret   : {self.master_secret_bytes.decode('utf-8')[:4]}...*************************************************")
        print(f"{COLOR_BLUE}----------------------------------------------------------------------{COLOR_RESET}")

        all_passed = True

        # Test Case 1: Standard Authorized Handshake (Happy Path)
        payload_tc1 = {"product_sku": "SKU-DUNGEON-001", "key_salt_checksum": "a8f3b2d1c0e9f8a7b6c5d4e3f2a1b0c9"}
        status, res = self.fire_request(self.valid_token, payload_tc1, 200)
        
        # Calculate local key derivation to verify worker's mathematical determinism
        der_input = f"{payload_tc1['product_sku']}{payload_tc1['key_salt_checksum']}".encode("utf-8")
        local_key = hmac.new(self.master_secret_bytes, der_input, hashlib.sha256).hexdigest()

        if status == 200 and res.get("decryption_key_hex") == local_key:
            print(f"[*] Running Test Case 1: Valid JWT with authorized SKU...")
            print(f"  {COLOR_GREEN}[PASS] Handshake successful. Derived Key: {res.get('decryption_key_hex')}{COLOR_RESET}")
        else:
            print(f"[*] Running Test Case 1: Valid JWT with authorized SKU...")
            print(f"  {COLOR_RED}[FAIL] Server derived key mismatch or bad HTTP code: {status} {res}{COLOR_RESET}")
            all_passed = False

        # Test Case 2: Block Expired Authorization Tokens (Security Gate)
        status, res = self.fire_request(self.expired_token, payload_tc1, 401)
        if status == 401 and res.get("error_code") == "TOKEN_EXPIRED":
            print(f"[*] Running Test Case 2: Block Expired Authorization Tokens...")
            print(f"  {COLOR_GREEN}[PASS] Endpoint correctly blocked expired token. Reason: {res.get('message')}{COLOR_RESET}")
        else:
            print(f"[*] Running Test Case 2: Block Expired Authorization Tokens...")
            print(f"  {COLOR_RED}[FAIL] Expired token was not correctly intercepted: {status} {res}{COLOR_RESET}")
            all_passed = False

        # Test Case 3: Entitlement Verification Mismatch (Scope Gate)
        status, res = self.fire_request(self.wrong_sku_token, payload_tc1, 403)
        if status == 403 and res.get("error_code") == "INSUFFICIENT_ENTITLEMENTS":
            print(f"[*] Running Test Case 3: Entitlement Verification Mismatch...")
            print(f"  {COLOR_GREEN}[PASS] Endpoint blocked unauthorized SKU request. Code: {res.get('error_code')}{COLOR_RESET}")
        else:
            print(f"[*] Running Test Case 3: Entitlement Verification Mismatch...")
            print(f"  {COLOR_RED}[FAIL] Unauthorized product request was bypassed: {status} {res}{COLOR_RESET}")
            all_passed = False

        # Test Case 4: Revocation Matching (Active Fallback Gate)
        status, res = self.fire_request(self.revoked_token, payload_tc1, 403)
        if status == 403 and res.get("error_code") == "TRANSACTION_REVOKED":
            print(f"[*] Running Test Case 4: Revocation Matching (Active Fallback Gate)...")
            print(f"  {COLOR_GREEN}[PASS] Blocked refunded transaction. Access denied: {res.get('message')}{COLOR_RESET}")
        else:
            print(f"[*] Running Test Case 4: Revocation Matching (Active Fallback Gate)...")
            print(f"  {COLOR_RED}[FAIL] Revoked transaction bypassed database filters: {status} {res}{COLOR_RESET}")
            all_passed = False

        # Test Case 5: Mathematical Integrity and Nonce Assertion
        payload_tc5 = {"product_sku": "SKU-DUNGEON-001", "key_salt_checksum": "INVALID_CHARS!!!"}
        status, res = self.fire_request(self.valid_token, payload_tc5, 400)
        if status == 400 and res.get("error_code") == "MALFORMED_SALT":
            print(f"[*] Running Test Case 5: Mathematical Integrity Assertions...")
            print(f"  {COLOR_GREEN}[PASS] Blocked malformed salt parameter. Reason: {res.get('message')}{COLOR_RESET}")
        else:
            print(f"[*] Running Test Case 5: Mathematical Integrity Assertions...")
            print(f"  {COLOR_RED}[FAIL] Malformed salt request reached key derivations: {status} {res}{COLOR_RESET}")
            all_passed = False

        print(f"{COLOR_BLUE}======================================================================{COLOR_RESET}")
        if all_passed:
            print(f"   {COLOR_BOLD}{COLOR_GREEN}CONFORMANCE INTEGRATION RESULTS: ALL TEST CASES PASSED (5 / 5)   {COLOR_RESET}")
            print(f"   Edge token signature & SKU mapping match specification contracts.")
        else:
            print(f"   {COLOR_BOLD}{COLOR_RED}CONFORMANCE INTEGRATION FAILURE: CHECK GATE ERRORS{COLOR_RESET}")
        print(f"{COLOR_BLUE}======================================================================{COLOR_RESET}\n")

        return all_passed

# =====================================================================
# SECTION 3: SYSTEM SELF-TEST AND MOCK CAMPAIGN VALIDATION
# =====================================================================

def execute_programmatic_self_test():
    """
    Executes mock program validations to test geometric schema parsing and
    decryption handshake flows without external disk or server dependencies.
    """
    log_info("Initializing internal programmatic self-tests...")
    
    # 1. Test standard programmatic geometric constraints with valid values
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

    # 2. Test Z-height vertical check
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
                    "height": {"bottom": 12.0, "top": 5.0}, # Conflict: bottom > top
                    "path": [{"type": "move", "x": 0, "y": 0}, {"type": "line", "x": 10, "y": 10}]
                }
            ],
            "portals": []
        }
    }
    if checker.validate_geometry_schema(failing_geometry):
        log_error("Self-Test Failed: Geometrical validator missed a Z-axis height conflict (bottom > top).")
        return False

    # 3. Test entities schema validator
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

    # 4. Test Single-Default Landing Zone Limit
    failing_entities = {
        "landing_zones": [
            {"id": "lz1", "coordinates": [5.0, 5.0], "is_default": True, "heading_degrees": 90.0},
            {"id": "lz2", "coordinates": [10.0, 10.0], "is_default": True, "heading_degrees": 180.0} # Fault: Multiple defaults
        ]
    }
    if checker.validate_entities_schema(failing_entities):
        log_error("Self-Test Failed: Validator missed multi-default landing zone violations.")
        return False

    log_success("Internal programmatic checks: ALL SCHEMAS CONFORM!")
    return True


# =====================================================================
# SECTION 4: MAIN EXECUTOR & CLI ROUTING
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="UVTT v2 Master Conformance & Cryptographic Verification Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "archive", nargs="?", default=None,
        help="Path to a target .uvtt2z or .gvtt campaign package to validate."
    )
    parser.add_argument(
        "-s", "--self-test", action="store_true",
        help="Execute the suite's built-in programmatic self-tests and cryptographic check pipelines."
    )
    parser.add_argument(
        "--handshake", action="store_true",
        help="Execute cryptographic edge clearinghouse verification handshakes."
    )
    parser.add_argument(
        "--url", default=None,
        help="Target Worker URL for ZKS handshake testing. If omitted, spins up a local mock server."
    )
    parser.add_argument(
        "--secret", default="RETAILER_MASTER_CRITICAL_SECRET_2026_07_11",
        help="The Retailer Master Secret for key derivation calculations."
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress informational logs; report output highlights and failures only."
    )

    args = parser.parse_args()

    # Clear output screen header
    if not args.quiet:
        print(f"{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}")
        print(f"{COLOR_BOLD}       UVTT v2 System-Agnostic Verification & Conformance Suite       {COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_BLUE}======================================================================{COLOR_RESET}")

    # No arguments provided fallback
    if not args.archive and not args.self_test and not args.handshake:
        parser.print_help()
        sys.exit(0)

    success = True

    # Execution Phase 1: Programmatic Self-Tests
    if args.self_test:
        if not execute_programmatic_self_test():
            success = False

    # Execution Phase 2: Live or Mock Cryptographic Handshake Pipeline
    if args.handshake:
        if not HAS_CRYPTO:
            log_error("Cryptographic libraries ('PyJWT' or 'cryptography') are missing. Cannot run ZKS handshake suite.")
            sys.exit(1)

        server_thread = None
        target_endpoint = args.url

        # Spin up local mock background daemon if no endpoint is specified
        if not target_endpoint:
            log_info("No target Worker URL provided. Initializing local Mock Edge server...", args.quiet)
            MockZKSWorkerHandler.generate_signing_keys()
            MockZKSWorkerHandler.retailer_master_secret = args.secret.encode("utf-8")
            
            # Spin up on random open local port
            local_server = HTTPServer(("127.0.0.1", 0), MockZKSWorkerHandler)
            port = local_server.server_port
            target_endpoint = f"http://127.0.0.1:{port}/v1/drm/handshake"
            
            server_thread = threading.Thread(target=local_server.serve_forever, daemon=True)
            server_thread.start()
            log_info(f"Local Mock server active on port {port}.", args.quiet)

        # Execute tests
        suite = CryptographicHandshakeSuite(target_endpoint, args.secret.encode("utf-8"))
        
        # If we spun up a local server, we feed the matching private key to forge mock JWTs
        if server_thread:
            suite.forge_test_tokens(MockZKSWorkerHandler.rsa_key_pair)
        else:
            # If testing a live server, we'd need its real signing key or predefined signed tokens.
            # For automation checks against live systems without raw private keys, we verify basic auth errors.
            log_warn("Testing a live Worker URL. Forging mock JWTs using default keys (may trigger validation errors).")
            # Generate fake rsa key to test live pipeline rejection mechanics
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            suite.forge_test_tokens(private_key)

        if not suite.run_handshake_tests():
            success = False

    # Execution Phase 3: Archive Conformance Checks
    if args.archive:
        checker = UVTT2ConformanceChecker(args.archive, args.quiet)
        if not checker.run_all():
            success = False

    # Final summary output
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
