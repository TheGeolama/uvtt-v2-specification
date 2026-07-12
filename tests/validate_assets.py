#!/usr/bin/env python3
"""
UVTT v2 DRM Asset Validation Template
======================================
This boilerplate script demonstrates how to programmatically validate the integrity
of split-resolution assets within a UVTT v2 (.uvtt2z) ZIP package or an extracted 
directory structure against the cryptographic SHA-256 hashes defined in the 'manifest.hash' file.

Use this as a reference implementation when building import pipelines for your VTT engine.
"""

import os
import sys
import json
import hashlib
import zipfile
from pathlib import Path
from typing import Dict, Tuple, Union

# Exit codes for automation pipelines
EXIT_SUCCESS = 0
EXIT_ERR_USAGE = 1
EXIT_ERR_FILE_NOT_FOUND = 2
EXIT_ERR_HASH_MISMATCH = 3
EXIT_ERR_INVALID_FORMAT = 4

def calculate_sha256(data: bytes) -> str:
    """Calculates the hex-encoded SHA-256 signature of binary data."""
    return hashlib.sha256(data).hexdigest()

def validate_extracted_dir(dir_path: Path) -> Tuple[bool, str, Dict[str, str]]:
    """
    Validates assets in an extracted directory structure.
    Expects 'manifest.hash' at the root of the directory.
    """
    hash_file_path = dir_path / "manifest.hash"
    if not hash_file_path.exists():
        return False, f"DRM Error: 'manifest.hash' not found at root {dir_path}", {}

    try:
        with open(hash_file_path, "r", encoding="utf-8") as f:
            # Assumes JSON format: {"assets/filename.ext": "sha256_hash_hex"}
            expected_hashes = json.load(f)
    except Exception as e:
        return False, f"DRM Error: Failed to parse 'manifest.hash' as JSON: {e}", {}

    results = {}
    mismatches = 0

    for asset_rel_path, expected_hash in expected_hashes.items():
        # Sanitize path to prevent directory traversal
        sanitized_rel_path = Path(asset_rel_path).relative_to(Path(asset_rel_path).anchor)
        full_asset_path = dir_path / sanitized_rel_path

        if not full_asset_path.exists():
            results[asset_rel_path] = "MISSING"
            mismatches += 1
            continue

        try:
            with open(full_asset_path, "rb") as f:
                asset_bytes = f.read()
            actual_hash = calculate_sha256(asset_bytes)
            if actual_hash.lower() == expected_hash.lower():
                results[asset_rel_path] = "VALID"
            else:
                results[asset_rel_path] = f"INVALID (Expected: {expected_hash[:8]}..., Got: {actual_hash[:8]}...)"
                mismatches += 1
        except Exception as e:
            results[asset_rel_path] = f"ERROR READING: {e}"
            mismatches += 1

    if mismatches > 0:
        return False, f"Validation failed with {mismatches} mismatching/missing asset(s).", results
    return True, "All assets verified successfully.", results

def validate_zip_archive(zip_path: Path) -> Tuple[bool, str, Dict[str, str]]:
    """
    Validates assets inside an unextracted .uvtt2z ZIP archive.
    """
    if not zipfile.is_zipfile(zip_path):
        return False, f"Invalid ZIP Archive: {zip_path} is corrupt or not a valid ZIP file.", {}

    results = {}
    mismatches = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Check for manifest.hash
        namelist = zf.namelist()
        hash_file_name = next((name for name in namelist if Path(name).name == "manifest.hash"), None)
        
        if not hash_file_name:
            return False, "DRM Error: 'manifest.hash' missing from ZIP package roots.", {}

        try:
            with zf.open(hash_file_name) as f:
                expected_hashes = json.loads(f.read().decode("utf-8"))
        except Exception as e:
            return False, f"DRM Error: Failed to parse 'manifest.hash' from ZIP: {e}", {}

        # Normalize ZipInfo paths
        zip_files_dict = {name.replace("\\", "/"): name for name in namelist}

        for asset_rel_path, expected_hash in expected_hashes.items():
            # Standardize path separators for archive lookup
            std_rel_path = asset_rel_path.replace("\\", "/")
            
            # Find matching file in zip namelist
            matching_key = next((k for k in zip_files_dict if k.endswith(std_rel_path)), None)

            if not matching_key:
                results[asset_rel_path] = "MISSING"
                mismatches += 1
                continue

            try:
                with zf.open(zip_files_dict[matching_key]) as f:
                    asset_bytes = f.read()
                actual_hash = calculate_sha256(asset_bytes)
                if actual_hash.lower() == expected_hash.lower():
                    results[asset_rel_path] = "VALID"
                else:
                    results[asset_rel_path] = f"INVALID (Expected: {expected_hash[:8]}..., Got: {actual_hash[:8]}...)"
                    mismatches += 1
            except Exception as e:
                results[asset_rel_path] = f"ERROR DECOMPRESSING: {e}"
                mismatches += 1

    if mismatches > 0:
        return False, f"Validation failed with {mismatches} mismatching/missing asset(s).", results
    return True, "All assets verified successfully.", results

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_assets.py <path_to_uvtt2z_or_extracted_dir>", file=sys.stderr)
        sys.exit(EXIT_ERR_USAGE)

    target_path = Path(sys.argv[1]).resolve()
    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}", file=sys.stderr)
        sys.exit(EXIT_ERR_FILE_NOT_FOUND)

    print("=" * 60)
    print(f"Target: {target_path.name}")
    print("=" * 60)

    if target_path.is_dir():
        print("[*] Detecting directory structure. Starting live folder scan...")
        success, message, results = validate_extracted_dir(target_path)
    else:
        print("[*] Detecting file structure. Initiating ZIP archive validation...")
        success, message, results = validate_zip_archive(target_path)

    # Output detailed report
    print("\n[+] Verification Report:")
    for filepath, status in results.items():
        print(f"  - {filepath}: {status}")

    print("\n" + "=" * 60)
    if success:
        print(f"SUCCESS: {message}")
        print("=" * 60)
        sys.exit(EXIT_SUCCESS)
    else:
        print(f"FAILURE: {message}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(EXIT_ERR_HASH_MISMATCH)

if __name__ == "__main__":
    main()
