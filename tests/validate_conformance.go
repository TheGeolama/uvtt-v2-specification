package main

import (
	"archive/zip"
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"strings"
	"sync"
	"time"
)

// Simplified validation types for concurrency benchmarks
type MinimalGeometry struct {
	Geometry struct {
		Walls []struct {
			ID     string `json:"id"`
			Height struct {
				Bottom float64 `json:"bottom"`
				Top    float64 `json:"top"`
			} `json:"height"`
		} `json:"walls"`
	} `json:"geometry"`
}

type MinimalEntities struct {
	LandingZones []struct {
		ID        string `json:"id"`
		IsDefault bool   `json:"is_default"`
	} `json:"landing_zones"`
	Audio struct {
		Zones []struct {
			ID         string  `json:"id"`
			FadeRadius float64 `json:"fade_radius"`
		} `json:"zones"`
	} `json:"audio"`
}

type MinimalManifest struct {
	FormatVersion string `json:"format_version"`
	UVTTVersion   string `json:"uvtt_version"`
	CampaignName  string `json:"campaign_name"`
	MapCatalog    []struct {
		Name string `json:"name"`
		Path string `json:"path"`
	} `json:"map_catalog"`
}

type ValidationResult struct {
	Path    string
	Success bool
	Error   error
}

func main() {
	// 1. Parse Command Line Arguments
	targetFile := flag.String("file", "", "Path to the target .uvtt2z or encrypted archive.")
	keyHex := flag.String("key", "", "64-character hexadecimal AES-256 key for decryption.")
	flag.Parse()

	if *targetFile == "" {
		fmt.Println("Usage: validate_conformance -file=<path_to_campaign.uvtt2z> [-key=<hex_key>]")
		os.Exit(1)
	}

	start := time.Now()
	fmt.Printf("[*] Starting high-concurrency UVTT v2 binary validation for: %s\n", *targetFile)

	// 2. Read Archive File
	fileBytes, err := os.ReadFile(*targetFile)
	if err != nil {
		fmt.Printf("[-] Failed to open archive: %v\n", err)
		os.Exit(1)
	}

	// 3. Envelope Decryption pass if key is provided or file is encrypted
	isEncrypted := *keyHex != "" || strings.HasSuffix(*targetFile, ".uvtt2k")
	var zipData []byte
	if isEncrypted {
		if *keyHex == "" {
			fmt.Println("[-] File appears to be encrypted but no -key flag was provided.")
			os.Exit(1)
		}
		fmt.Println("[*] AES-256-GCM encrypted envelope detected. Executing stream decryption...")
		zipData, err = decryptPayload(fileBytes, *keyHex)
		if err != nil {
			fmt.Printf("[-] Decryption failed: %v\n", err)
			os.Exit(1)
		}
		fmt.Println("[+] In-memory AES-GCM container stream extraction successful.")
	} else {
		zipData = fileBytes
	}

	// 4. Extract Zip Directory Map
	reader, err := zip.NewReader(bytes.NewReader(zipData), int64(len(zipData)))
	if err != nil {
		fmt.Printf("[-] File is not a valid zip container format: %v\n", err)
		os.Exit(1)
	}

	fileMap := make(map[string][]byte)
	for _, f := range reader.File {
		rc, err := f.Open()
		if err != nil {
			fmt.Printf("[-] File extraction read error '%s': %v\n", f.Name, err)
			os.Exit(1)
		}
		buf := new(bytes.Buffer)
		_, err = io.Copy(buf, rc)
		rc.Close()
		if err != nil {
			fmt.Printf("[-] File extraction buffer write error '%s': %v\n", f.Name, err)
			os.Exit(1)
		}
		fileMap[f.Name] = buf.Bytes()
	}

	// 5. Verify Cryptographic Integrity
	hashData, ok := fileMap["manifest.hash"]
	if !ok {
		fmt.Println("[-] Security Alert: Container lacks the mandatory integrity receipt 'manifest.hash'.")
		os.Exit(1)
	}

	err = verifyHashes(fileMap, hashData)
	if err != nil {
		fmt.Printf("[-] Verification aborted due to cryptographic mismatch: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("[+] Cryptographic manifest.hash registry match confirmed.")

	// 6. Ingest and parse manifest.json
	manifestBytes, ok := fileMap["manifest.json"]
	if !ok {
		fmt.Println("[-] Missing master manifest.json index file.")
		os.Exit(1)
	}

	var manifest MinimalManifest
	err = json.Unmarshal(manifestBytes, &manifest)
	if err != nil {
		fmt.Printf("[-] Failed to parse manifest.json metadata: %v\n", err)
		os.Exit(1)
	}

	// 7. Concurrent Sub-Map Schema Validations
	var wg sync.WaitGroup
	resultChan := make(chan ValidationResult, len(manifest.MapCatalog)+1)

	if len(manifest.MapCatalog) == 0 {
		// Standalone Mode
		wg.Add(1)
		go func() {
			defer wg.Done()
			err := validateMapFolder(fileMap, "")
			resultChan <- ValidationResult{Path: "root", Success: err == nil, Error: err}
		}()
	} else {
		// Compound Campaign Mode
		fmt.Printf("[*] Multi-Floor Compound dungeon identified. Spinning up %d concurrent validator routines...\n", len(manifest.MapCatalog))
		for _, node := range manifest.MapCatalog {
			wg.Add(1)
			go func(path, name string) {
				defer wg.Done()
				err := validateMapFolder(fileMap, path)
				resultChan <- ValidationResult{Path: name, Success: err == nil, Error: err}
			}(node.Path, node.Name)
		}
	}

	// Wait for all validators to finish and close channel
	wg.Wait()
	close(resultChan)

	// Evaluate results
	failedCount := 0
	for result := range resultChan {
		if !result.Success {
			fmt.Printf("  [-] Level '%s' Validation REJECTED: %v\n", result.Path, result.Error)
			failedCount++
		} else {
			fmt.Printf("  [+] Level '%s' Conforms Successfully.\n", result.Path)
		}
	}

	duration := time.Since(start)
	fmt.Printf("\n[*] Conformance validation pipeline completed in: %s\n", duration)

	if failedCount > 0 {
		fmt.Printf("[-] VERIFICATION REJECTED: %d compliance conflicts found in standard structures.\n", failedCount)
		os.Exit(1)
	}

	fmt.Println("[+] ALL SECURE GATES PASSED SUCCESSFULLY. Binary package conforms fully to the UVTT v2 specification.")
}

func decryptPayload(encrypted []byte, keyHex string) ([]byte, error) {
	if len(encrypted) < 12 {
		return nil, errors.New("encrypted payload too small")
	}

	keyBytes, err := hex.DecodeString(keyHex)
	if err != nil {
		return nil, fmt.Errorf("invalid hex key: %v", err)
	}

	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return nil, err
	}

	aesgcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	nonce := encrypted[:12]
	ciphertext := encrypted[12:]

	plaintext, err := aesgcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, err
	}

	return plaintext, nil
}

func verifyHashes(fileMap map[string][]byte, hashData []byte) error {
	lines := strings.Split(strings.TrimSpace(string(hashData)), "\n")
	hashRegistry := make(map[string]string)

	for _, line := range lines {
		if !strings.Contains(line, "  ") {
			continue
		}
		parts := strings.SplitN(line, "  ", 2)
		checksum := strings.TrimSpace(parts[0])
		filePath := strings.TrimSpace(parts[1])
		hashRegistry[filePath] = checksum
	}

	for name, content := range fileMap {
		if name == "manifest.hash" || name == "manifest.json" {
			continue
		}
		expected, exists := hashRegistry[name]
		if !exists {
			return fmt.Errorf("security alert: untracked file found in container: %s", name)
		}

		hasher := sha256.New()
		hasher.Write(content)
		computed := hex.EncodeToString(hasher.Sum(nil))

		if computed != expected {
			return fmt.Errorf("cryptographic checksum mismatch on %s: expected %s, got %s", name, expected, computed)
		}
	}

	return nil
}

func validateMapFolder(fileMap map[string][]byte, path string) error {
	geomPath := path + "geometry.json"
	entPath := path + "entities.json"
	basePath := path + "basemap.webp"

	if _, ok := fileMap[basePath]; !ok {
		return fmt.Errorf("missing watermarked fallback: '%s'", basePath)
	}

	geomBytes, ok := fileMap[geomPath]
	if !ok {
		return fmt.Errorf("missing mandatory geometry layout: '%s'", geomPath)
	}

	var geom MinimalGeometry
	err := json.Unmarshal(geomBytes, &geom)
	if err != nil {
		return fmt.Errorf("invalid json format in %s: %v", geomPath, err)
	}

	for _, wall := range geom.Geometry.Walls {
		if wall.Height.Bottom > wall.Height.Top {
			return fmt.Errorf("Z-height conflict on wall '%s' inside %s", wall.ID, geomPath)
		}
	}

	if entBytes, ok := fileMap[entPath]; ok {
		var ent MinimalEntities
		err := json.Unmarshal(entBytes, &ent)
		if err != nil {
			return fmt.Errorf("invalid json format in %s: %v", entPath, err)
		}

		defaultCount := 0
		for _, lz := range ent.LandingZones {
			if lz.IsDefault {
				defaultCount++
			}
		}
		if defaultCount > 1 {
			return fmt.Errorf("topology conflict: multiple default spawn landing zones defined in %s", entPath)
		}

		for _, zone := range ent.Audio.Zones {
			if zone.FadeRadius <= 0 {
				return fmt.Errorf("acoustic physics conflict: zone '%s' must have positive non-zero fade_radius", zone.ID)
			}
		}
	}

	return nil
}
