#!/usr/bin/env python3
"""
Zero-Knowledge-Storage (ZKS) Key Retrieval Utility
--------------------------------------------------
This script provides virtual tabletop (VTT) developers with a boilerplate template
to programmatically retrieve AES-GCM asset decryption keys from the UVTT v2 Cloudflare 
Worker Clearinghouse.

The client authenticates without exposing raw credentials by signing a transient
request payload (using HMAC-SHA256) with their license token, ensuring a secure 
zero-knowledge-style proof of entitlement at the edge database level.

Dependencies:
    - Python 3.8+ (Uses only standard libraries: urllib, json, hmac, hashlib, base64)

Usage:
    python3 zks_key_retrieval.py --map-id <map-uuid> --license <license-key> --endpoint <worker-url>
"""

import sys
import os
import json
import time
import hmac
import hashlib
import base64
import argparse
import urllib.request
import urllib.error

# Default configuration values
DEFAULT_CLEARINGHOUSE_ENDPOINT = "https://zks-clearinghouse.thegeolama.workers.dev"

def generate_auth_signature(license_key: str, map_id: str, timestamp: int, nonce: str) -> str:
    """
    Generates a secure, transient HMAC-SHA256 signature to authenticate the request.
    This prevents replay attacks (via timestamp/nonce) and verifies license ownership
    without sending the raw license key over the wire.
    """
    # Create the message string by joining request metadata
    message = f"{map_id}:{timestamp}:{nonce}".encode("utf-8")
    
    # Use the license key as the symmetric HMAC key
    key = license_key.encode("utf-8")
    
    # Compute the SHA-256 HMAC digest
    signature_bytes = hmac.new(key, message, hashlib.sha256).digest()
    
    # Return as a clean hex string
    return signature_bytes.hex()

def fetch_decryption_key(endpoint: str, map_id: str, license_key: str, verbose: bool = False) -> str:
    """
    Contacts the Cloudflare Worker clearinghouse and requests the 256-bit AES decryption key
    for a specified map asset using signed cryptographic handshakes.
    """
    # Normalize endpoint URL
    url = endpoint.rstrip("/") + "/v1/key/retrieve"
    
    # Generate anti-replay and security params
    timestamp = int(time.time())
    nonce = base64.b64encode(os.urandom(16)).decode("utf-8")
    
    # Generate the cryptographic signature using the secret license key
    signature = generate_auth_signature(license_key, map_id, timestamp, nonce)
    
    # Construct the JSON payload
    payload = {
        "map_id": map_id,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": signature
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "UVTT-v2-ZKS-Client/1.0"
    }
    
    if verbose:
        print(f"[*] Clearinghouse Endpoint: {url}")
        print(f"[*] Map Identifier:        {map_id}")
        print(f"[*] Nonce Token:           {nonce}")
        print(f"[*] Signature (HMAC):      {signature}")
        print(f"[*] Contacting Cloudflare Worker edge nodes...")
        
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            response_data = response.read().decode("utf-8")
            
            if status_code == 200:
                parsed_res = json.loads(response_data)
                
                # The clearinghouse returns the 256-bit key in Hex or Base64 formats
                decryption_key = parsed_res.get("decryption_key")
                key_format = parsed_res.get("format", "hex")
                
                if not decryption_key:
                    raise ValueError("Clearinghouse response parsed successfully but contained no decryption_key field.")
                    
                if verbose:
                    print(f"[+] Key successfully fetched! (Format: {key_format})")
                return decryption_key
            else:
                raise urllib.error.HTTPError(url, status_code, "Unexpected response status", headers, None)
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"\n[✘] HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        if error_body:
            try:
                # Attempt to extract error message from JSON response
                err_json = json.loads(error_body)
                print(f"    Reason: {err_json.get('error', error_body)}", file=sys.stderr)
            except json.JSONDecodeError:
                print(f"    Raw Error Response: {error_body}", file=sys.stderr)
        raise
    except urllib.error.URLError as e:
        print(f"\n[✘] Connection/DNS Error: Failed to contact the clearinghouse.", file=sys.stderr)
        print(f"    Details: {e.reason}", file=sys.stderr)
        raise
    except json.JSONDecodeError:
        print(f"\n[✘] Content Error: Clearinghouse returned non-JSON response payload.", file=sys.stderr)
        raise

def main():
    parser = argparse.ArgumentParser(
        description="Zero-Knowledge-Storage (ZKS) dynamic key retrieval boilerplate utility for UVTT v2 assets.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-m", "--map-id", 
        required=True, 
        help="The unique ID/UUID of the map asset."
    )
    parser.add_argument(
        "-l", "--license", 
        required=True, 
        help="The creator or platform license token used for sign-auth generation."
    )
    parser.add_argument(
        "-e", "--endpoint", 
        default=DEFAULT_CLEARINGHOUSE_ENDPOINT, 
        help=f"The Cloudflare Worker endpoint URL (default: {DEFAULT_CLEARINGHOUSE_ENDPOINT})."
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable detailed diagnostic logging."
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("           UVTT v2 ZKS Key Retrieval Client Boilerplate")
    print("=" * 70)
    
    try:
        key = fetch_decryption_key(
            endpoint=args.endpoint,
            map_id=args.map_id,
            license_key=args.license,
            verbose=args.verbose
        )
        
        print("\n========================= RETRIEVED ASSET KEY =========================")
        print(f"Decryption Key: {key}")
        print("=======================================================================")
        print("[✔] Success! Copy this key directly to your 'validate_assets_v2.py' script.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[✘] Fatal Error during key retrieval processing: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
