package main

import (
	"archive/zip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// Manifest matches the root metadata structure of manifest.json in UVTT v2
type Manifest struct {
	UVTTVersion     string           `json:"uvtt_version"`
	HardwareProfile *HardwareProfile `json:"hardware_profile,omitempty"`
	Extensions      map[string]any   `json:"extensions,omitempty"`
}

type HardwareProfile struct {
	MinimumPipeline        string `json:"minimum_pipeline"`
	RecommendedPipeline    string `json:"recommended_pipeline"`
	RequiresComputeShaders bool   `json:"requires_compute_shaders"`
}

// Entities represents the interactive layer schema from entities.json
type Entities struct {
	LandingZones []LandingZone `json:"landing_zones,omitempty"`
}

type LandingZone struct {
	ID             string         `json:"id"`
	Name           string         `json:"name"`
	IsDefault      bool           `json:"is_default"`
	Coordinates    []float64      `json:"coordinates"` // [x, y] or [x, y, z]
	HeadingDegrees float64        `json:"heading_degrees"`
	Properties     *LZProperties  `json:"properties,omitempty"`
}

type LZProperties struct {
	Description     string  `json:"description,omitempty"`
	CameraZoomLevel float64 `json:"camera_zoom_level,omitempty"`
}

func main() {
	filePath := flag.String("file", "", "Path to the .uvtt2z or .gvtt archive to validate")
	flag.Parse()

	if *filePath == "" {
		fmt.Println("❌ Error: Missing required flag -file")
		os.Exit(1)
	}

	fmt.Printf("🔍 Initiating UVTT v2 Conformance Verification: %s\n", filepath.Base(*filePath))

	err := validateArchive(*filePath)
	if err != nil {
		fmt.Printf("❌ CONFORMANCE FAILURE: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ CONFORMANCE SUCCESS: File complies with the UVTT v2.0.0-rc1 standard.")
}

func validateArchive(archivePath string) error {
	// 1. Open the ZIP container
	r, err := zip.OpenReader(archivePath)
	if err != nil {
		return fmt.Errorf("failed to open file as zip container: %w", err)
	}
	defer r.Close()

	// Map to track present files inside the zip
	zipFiles := make(map[string]*zip.File)
	for _, f := range r.File {
		zipFiles[f.Name] = f
	}

	// 2. Assert minimum directory tree files exist (excluding deep compound layout checks)
	requiredRootFiles := []string{"manifest.json", "geometry.json", "entities.json", "preview.webp", "manifest.hash"}
	for _, reqFile := range requiredRootFiles {
		if _, ok := zipFiles[reqFile]; !ok {
			return fmt.Errorf("missing core package specification file: '%s'", reqFile)
		}
	}

	// 3. Parse and Verify manifest.hash cryptographic integrity receipt
	hashFile, err := zipFiles["manifest.hash"].Open()
	if err != nil {
		return fmt.Errorf("failed to open manifest.hash receipt: %w", err)
	}
	defer hashFile.Close()

	declaredHashes, err := parseHashReceipt(hashFile)
	if err != nil {
		return fmt.Errorf("failed to parse manifest.hash: %w", err)
	}

	// Check that everything listed in manifest.hash matches reality
	for relPath, declaredHash := range declaredHashes {
		zipFile, ok := zipFiles[relPath]
		if !ok {
			return fmt.Errorf("file declared in manifest.hash does not exist in ZIP: %s", relPath)
		}

		computedHash, err := computeSHA256(zipFile)
		if err != nil {
			return fmt.Errorf("failed to calculate checksum for %s: %w", relPath, err)
		}

		if computedHash != declaredHash {
			return fmt.Errorf("cryptographic mismatch for '%s': expected %s, computed %s", relPath, declaredHash, computedHash)
		}
	}

	// Assert there are no unlisted files inside the ZIP container (except manifest.hash itself)
	for name := range zipFiles {
		if name == "manifest.hash" {
			continue
		}
		if _, declared := declaredHashes[name]; !declared {
			return fmt.Errorf("unlisted file discovered inside ZIP archive (not declared in manifest.hash): '%s'", name)
		}
	}
	fmt.Println("🔒 Cryptographic Integrity: OK (SHA-256 hashes successfully matching manifest.hash)")

	// 4. Validate manifest.json Structure
	mFile, err := zipFiles["manifest.json"].Open()
	if err != nil {
		return fmt.Errorf("failed to open manifest.json: %w", err)
	}
	defer mFile.Close()

	var manifest Manifest
	if err := json.NewDecoder(mFile).Decode(&manifest); err != nil {
		return fmt.Errorf("malformed JSON syntax inside manifest.json: %w", err)
	}

	if manifest.UVTTVersion == "" {
		return fmt.Errorf("manifest.json validation error: missing 'uvtt_version'")
	}
	fmt.Printf("📦 Format Profile: UVTT %s\n", manifest.UVTTVersion)

	// 5. Validate entities.json & Landing Zone Constraints
	eFile, err := zipFiles["entities.json"].Open()
	if err != nil {
		return fmt.Errorf("failed to open entities.json: %w", err)
	}
	defer eFile.Close()

	var entities Entities
	if err := json.NewDecoder(eFile).Decode(&entities); err != nil {
		return fmt.Errorf("malformed JSON syntax inside entities.json: %w", err)
	}

	// Validate Landing Zones Constraint (Maximum or exactly 1 default entry)
	defaultCount := 0
	for _, lz := range entities.LandingZones {
		if lz.IsDefault {
			defaultCount++
		}
	}
	if defaultCount > 1 {
		return fmt.Errorf("topology validation error: multiple default landing zones declared in entities.json (%d found)", defaultCount)
	}
	fmt.Printf("🚩 Landing Zones: OK (Found %d zone(s), %d designated as default)\n", len(entities.LandingZones), defaultCount)

	return nil
}

// parseHashReceipt reads flat newline-separated hash maps from the manifest.hash stream
func parseHashReceipt(r io.Reader) (map[string]string, error) {
	content, err := io.ReadAll(r)
	if err != nil {
		return nil, err
	}

	hashes := make(map[string]string)
	lines := strings.Split(string(content), "\n")
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}

		parts := strings.Fields(trimmed)
		if len(parts) < 2 {
			continue // Skip malformed rows
		}

		// The standard format is: <sha256_hash> <relative_filepath>
		hash := parts[0]
		relPath := strings.Join(parts[1:], " ") // Rejoin in case of spaces in paths
		hashes[relPath] = strings.ToLower(hash)
	}
	return hashes, nil
}

// computeSHA256 reads a zip file entry and calculates its SHA-256 string checksum
func computeSHA256(f *zip.File) (string, error) {
	rc, err := f.Open()
	if err != nil {
		return "", err
	}
	defer rc.Close()

	h := sha256.New()
	if _, err := io.Copy(h, rc); err != nil {
		return "", err
	}

	return hex.EncodeToString(h.Sum(nil)), nil
}
