#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import zipfile
import argparse
import base64

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

def print_separator():
    print("=" * 70)

def parse_key(key_str: str) -> bytes:
    """
    Parses a 256-bit (32-byte) key from either a Hex string (64 characters)
    or a Base64 string.
    """
    if not key_str:
        return None
    
    # Try Hex first
    if len(key_str) == 64:
        try:
            return bytes.fromhex(key_str)
        except ValueError:
            pass
            
    # Try Base64 decoding
    try:
        decoded = base64.b64decode(key_str)
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
        
    # Fallback/Direct
    try:
        decoded_utf8 = key_str.encode('utf-8')
        if len(decoded_utf8) == 32:
            return decoded_utf8
    except Exception:
        pass

    raise ValueError(
        "Invalid key format. Key must be a 256-bit key represented as a "
        "64-character Hex string or a 44-character Base64 encoded string."
    )

def decrypt_aes_gcm(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypts payload using AES-256-GCM.
    Assumes standard UVTT v2 binary layout:
    - First 12 bytes: Nonce (IV)
    - Remaining bytes: Ciphertext + 16-byte Authentication Tag
    """
    if len(encrypted_data) < 28: # 12 bytes nonce + 16 bytes tag minimum
        raise ValueError("Payload is too short to be a valid AES-GCM encrypted asset.")
    
    nonce = encrypted_data[:12]
    ciphertext_with_tag = encrypted_data[12:]
    
    aesgcm = AESGCM(key)
    # No associated data used by default for asset files
    return aesgcm.decrypt(nonce, ciphertext_with_tag, None)

def calculate_sha256(data: bytes) -> str:
    """Calculates the SHA-256 hex digest of a byte string."""
    return hashlib.sha256(data).hexdigest()

def validate_asset_bundle(target_path: str, key_bytes: bytes = None, encrypted_files: list = None, strict_decryption: bool = False):
    print_separator()
    print(f"Target: {target_path}")
    print_separator()
    
    is_zip = False
    if os.path.isfile(target_path) and zipfile.is_zipfile(target_path):
        is_zip = True
        print("[*] Detecting file structure: Raw compressed ZIP archive (.uvtt2z) detected.")
    elif os.path.isdir(target_path):
        print("[*] Detecting file structure: Local directory structure detected.")
    else:
        print(f"[-] Error: Target '{target_path}' is not a valid directory or ZIP archive.")
        sys.exit(1)

    manifest_hash_data = {}
    
    # helper to read file contents
    def read_file_from_target(sub_path: str) -> bytes:
        # Standardize sub-path separators
        sub_path = sub_path.replace("\\", "/")
        if is_zip:
            with zipfile.ZipFile(target_path, 'r') as z:
                # ZipFile names are exact match, let's normalize lookup
                namelist = z.namelist()
                normalized_lookup = {name.replace("\\", "/"): name for name in namelist}
                if sub_path in normalized_lookup:
                    return z.read(normalized_lookup[sub_path])
                raise FileNotFoundError(f"{sub_path} not found in zip archive.")
        else:
            full_path = os.path.join(target_path, sub_path)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    return f.read()
            raise FileNotFoundError(f"{sub_path} not found on local disk.")

    # 1. Read manifest.hash
    try:
        manifest_hash_bytes = read_file_from_target("manifest.hash")
        manifest_hash_data = json.loads(manifest_hash_bytes.decode('utf-8'))
        print("[+] manifest.hash successfully loaded.")
    except FileNotFoundError:
        print("[-] Error: 'manifest.hash' not found at target. Cannot verify integrity.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("[-] Error: 'manifest.hash' is corrupted or not valid JSON.")
        sys.exit(1)

    mismatches = 0
    passed_integrity = 0
    decryption_failures = 0
    decryption_passes = 0
    fatal_decryption_errors = 0

    print("\n[+] Initiating asset verification checks:")
    
    # Normalize encrypted files list for comparison
    encrypted_set = set(p.replace("\\", "/") for p in (encrypted_files or []))
    
    for file_path, expected_hash in manifest_hash_data.items():
        normalized_path = file_path.replace("\\", "/")
        print(f"\n  Checking '{normalized_path}':")
        is_expected_encrypted = normalized_path in encrypted_set
        
        try:
            file_bytes = read_file_from_target(normalized_path)
            
            # A. Hash Verification
            actual_hash = calculate_sha256(file_bytes)
            if actual_hash == expected_hash:
                print(f"    [✔] Integrity Check: PASSED (SHA-256 matches: {actual_hash[:16]}...)")
                passed_integrity += 1
            else:
                print(f"    [✘] Integrity Check: FAILED")
                print(f"        Expected: {expected_hash}")
                print(f"        Got:      {actual_hash}")
                mismatches += 1
                
            # B. Decryption Test (if key provided)
            if key_bytes:
                if not HAS_CRYPTOGRAPHY:
                    print("    [!] Decryption Check: SKIPPED (the 'cryptography' library is missing from this python environment)")
                    continue
                
                try:
                    # Attempt to decrypt
                    decrypted = decrypt_aes_gcm(file_bytes, key_bytes)
                    print(f"    [✔] Decryption Test: PASSED (Payload authenticated and decrypted successfully)")
                    decryption_passes += 1
                except Exception as dec_err:
                    # Determine if this failure is fatal
                    if is_expected_encrypted or strict_decryption:
                        print(f"    [✘] Decryption Test: FAILED (Fatal: this file is flagged as encrypted. Error: {str(dec_err)})")
                        fatal_decryption_errors += 1
                    else:
                        print(f"    [!] Decryption Test: WARNING/SKIPPED (Decryption failed; treating as clean unencrypted asset. Error: {str(dec_err)})")
                        decryption_failures += 1
                    
        except FileNotFoundError:
            print(f"    [✘] Integrity Check: FAILED (Asset file is missing from bundle)")
            mismatches += 1
            if is_expected_encrypted:
                fatal_decryption_errors += 1
        except Exception as e:
            print(f"    [✘] Verification Error: {str(e)}")
            mismatches += 1
            if is_expected_encrypted:
                fatal_decryption_errors += 1

    print_separator()
    print("VERIFICATION SUMMARY:")
    print(f"  - Total files verified: {len(manifest_hash_data)}")
    print(f"  - Integrity passes:    {passed_integrity} / {len(manifest_hash_data)}")
    print(f"  - Integrity failures:  {mismatches}")
    
    if key_bytes:
        print(f"  - Decryption passes:   {decryption_passes}")
        print(f"  - Decryption warnings: {decryption_failures}")
        print(f"  - Decryption errors:   {fatal_decryption_errors}")
        
    print_separator()
    
    if mismatches > 0 or fatal_decryption_errors > 0:
        print("STATUS: FAILURE (Validation discrepancies or decryption failures encountered).")
        sys.exit(1)
    else:
        print("STATUS: SUCCESS (All asset checks completed successfully).")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="UVTT v2 Reference Asset Integrity and AES-GCM Decryption Validator"
    )
    parser.add_argument(
        "target",
        help="Path to the .uvtt2z ZIP archive or the local extracted map folder."
    )
    parser.add_argument(
        "-k", "--key",
        help="256-bit symmetric key for AES-GCM decryption tests (64-character Hex or 44-character Base64)."
    )
    parser.add_argument(
        "-e", "--encrypted",
        help="Comma-separated list of relative asset file paths that MUST be verified as encrypted (e.g. assets/premium_map.webp)."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="If set, ANY decryption failure is treated as fatal, even for unlisted assets."
    )
    
    args = parser.parse_args()
    
    key_bytes = None
    if args.key:
        if not HAS_CRYPTOGRAPHY:
            print("[!] Warning: 'cryptography' package is not available. Decryption tests will be skipped.")
        try:
            key_bytes = parse_key(args.key)
        except ValueError as val_err:
            print(f"[-] Error parsing decryption key: {str(val_err)}")
            sys.exit(1)

    encrypted_files = []
    if args.encrypted:
        encrypted_files = [path.strip() for path in args.encrypted.split(",")]

    validate_asset_bundle(args.target, key_bytes, encrypted_files, args.strict)

if __name__ == "__main__":
    main()
