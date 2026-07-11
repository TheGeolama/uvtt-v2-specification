package uvtt

import (
	"archive/zip"
	"crypto/aes"
	"crypto/cipher"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"strings"
)

// ============================================================================
// Core UVTT v2 Schema Definitions
// ============================================================================

// HardwareProfile defines minimum GPU and shader requirements
type HardwareProfile struct {
	MinimumPipeline        string `json:"minimum_pipeline"`
	RecommendedPipeline    string `json:"recommended_pipeline"`
	RequiresComputeShaders bool   `json:"requires_compute_shaders"`
}

// GridTopology defines the grid geometric layout
type GridTopology struct {
	Type           string  `json:"type"`            // "square", "hex", "isometric"
	Orientation    string  `json:"orientation"`     // "flat_top", "pointy_top"
	Offset         string  `json:"offset"`          // "odd_row", "even_row", "odd_col", "even_col"
	IsometricRatio float64 `json:"isometric_ratio"` // e.g. 0.5 (2:1 projection)
}

// Resolution defines grid sizing and physical scaling
type Resolution struct {
	MapOrigin    Point        `json:"map_origin"`
	GridSize     Point        `json:"grid_size"`
	UnitsPerGrid float64      `json:"units_per_grid"`
	UnitName     string       `json:"unit_name"`
	Topology     GridTopology `json:"topology"`
}

// Point represents a basic 2D coordinate node
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// Height defines the bottom and top bounds on the Z-axis
type Height struct {
	Bottom float64 `json:"bottom"`
	Top    float64 `json:"top"`
}

// PathNode models a single segment in an SVG-style path
type PathNode struct {
	Type string `json:"type"` // "move", "line", "bezier"
	X    float64 `json:"x,omitempty"`
	Y    float64 `json:"y,omitempty"`
	CP1  *Point  `json:"cp1,omitempty"`
	CP2  *Point  `json:"cp2,omitempty"`
	To   *Point  `json:"to,omitempty"`
}

// DirectionalBlocks represents material line-of-sight blockage orientations
type DirectionalBlocks struct {
	LeftToRight []string `json:"left_to_right"` // "light", "sight", "movement"
	RightToLeft []string `json:"right_to_left"`
}

// Wall represents an architectural blocking vector with height verticality
type Wall struct {
	ID                string            `json:"id"`
	Type              string            `json:"type"` // "standard", "terrain", "illusory"
	Height            Height            `json:"height"`
	Path              []PathNode        `json:"path"`
	DirectionalBlocks DirectionalBlocks `json:"directional_blocks"`
	States            map[string]any    `json:"states"`
}

// Portal represents standard interactive doors or secret passages
type Portal struct {
	ID     string     `json:"id"`
	Type   string     `json:"type"`     // "door", "window"
	SubType string    `json:"sub_type"` // "secret", "standard"
	State  string     `json:"state"`    // "closed", "open", "locked"
	Height Height     `json:"height"`
	Path   []PathNode `json:"path"`
}

// Overhead defines a structural ceiling/roof polygon
type Overhead struct {
	ID      string  `json:"id"`
	Type    string  `json:"type"` // "roof"
	Height  Height  `json:"height"`
	Polygon []Point `json:"polygon"`
	Image   struct {
		Format string `json:"format"`
		URI    string `json:"uri"`
	} `json:"image"`
}

// EncryptionHandshake defines keys and endpoint structures for clearinghouse access
type EncryptionHandshake struct {
	ClearinghouseURL string `json:"clearinghouse_url"`
	LicenseAuthority string `json:"license_authority"`
	KeySaltChecksum  string `json:"key_salt_checksum"`
}

// Manifest represents the parsed manifest.json (The Indexer)
type Manifest struct {
	UVTT_Version        string              `json:"uvtt_version"`
	ProductSKU          string              `json:"product_sku"`
	HardwareProfile     HardwareProfile     `json:"hardware_profile"`
	Resolution          Resolution          `json:"resolution"`
	EncryptionHandshake EncryptionHandshake `json:"encryption_handshake,omitempty"`
	Extensions          map[string]any      `json:"extensions"`
}

// Geometry represents the parsed geometry.json (The Heavy Lifter)
type Geometry struct {
	Walls    []Wall     `json:"walls"`
	Portals  []Portal   `json:"portals"`
	Overhead []Overhead `json:"overhead"`
}

// Destination represents spatial teleport targets
type Destination struct {
	Type              string `json:"type"` // "intra_map", "inter_map"
	TargetMapID       string `json:"target_map_id,omitempty"`
	TargetCoordinates Point  `json:"target_coordinates"`
	TargetZ           float64 `json:"target_z"`
	TargetRotation    float64 `json:"target_rotation"`
	LandingMode       string  `json:"landing_mode,omitempty"` // "absolute", "relative_offset", "target_region"
	Offset            *Point  `json:"offset,omitempty"`
	TargetEventID     string  `json:"target_event_id,omitempty"`
	FadeTransition    string  `json:"fade_transition,omitempty"`
}

// TeleportEvent represents a triggers bounds mapping inter/intra map movement
type TeleportEvent struct {
	ID                     string         `json:"id"`
	Type                   string         `json:"type"` // "teleport"
	TriggerBounds          PolygonTrigger `json:"trigger_bounds"`
	PredictionTriggerRadius float64        `json:"prediction_trigger_radius,omitempty"` // Custom cartographer buffer grid size
	Conditions             map[string]any `json:"conditions"`
	Destination            Destination    `json:"destination"`
}

// PolygonTrigger represents the geometric shape bounds for triggers
type PolygonTrigger struct {
	Shape  string  `json:"shape"` // "polygon", "circle"
	Points []Point `json:"points,omitempty"`
	Center *Point  `json:"center,omitempty"`
	Radius float64 `json:"radius,omitempty"`
}

// GlobalAudio defines Tier 1 and 2 background streams
type GlobalAudio struct {
	URI               string  `json:"uri"`
	Volume            float64 `json:"volume"`
	Loop              bool    `json:"loop"`
	CrossfadeDuration float64 `json:"crossfade_duration,omitempty"`
}

// LocalizedAudioZone defines Tier 3 localized soundscapes
type LocalizedAudioZone struct {
	ID           string         `json:"id"`
	URI          string         `json:"uri"`
	VolumeMax    float64        `json:"volume_max"`
	Loop         bool           `json:"loop"`
	Bounds       PolygonTrigger `json:"bounds"`
	FadeRadius   float64        `json:"fade_radius"`
}

// WeatherEmitter defines particle zones
type WeatherEmitter struct {
	ID        string         `json:"id"`
	Type      string         `json:"type"` // "rain", "snow", "fog", "embers", "magic"
	Bounds    PolygonTrigger `json:"bounds"`
	Intensity float64        `json:"intensity"`
	Speed     float64        `json:"speed"`
	Angle     float64        `json:"angle"`
	Color     string         `json:"color"` // Hex string e.g. "#00bcd4"
}

// SpawnPoint represents a player starting viewport anchor
type SpawnPoint struct {
	ID         string  `json:"id"`
	Name       string  `json:"name"`
	IsDefault  bool    `json:"is_default"`
	Position   Point   `json:"position"`
	Z          float64 `json:"z"`
	HeadingDeg float64 `json:"heading_degrees"`
	Properties struct {
		Description     string  `json:"description"`
		CameraZoomLevel float64 `json:"camera_zoom_level"`
	} `json:"properties"`
}

// Entities represents the parsed entities.json (The Interactive Layer)
type Entities struct {
	Lights      []any                `json:"lights"` // Kept for backwards compatibility
	Teleports   []TeleportEvent      `json:"teleports"`
	AudioZones  []LocalizedAudioZone `json:"audio_zones"`
	Weather     []WeatherEmitter     `json:"weather_emitters"`
	SpawnPoints []SpawnPoint         `json:"spawn_points"`
}

// ============================================================================
// The Unified UVTT v2 Package Parser
// ============================================================================

// Package represents a mounted and validated UVTT v2 Archive Container
type Package struct {
	Manifest *Manifest
	Geometry *Geometry
	Entities *Entities
	zipFile  *zip.ReadCloser
	filesMap map[string]*zip.File
}

// OpenPackage loads, decrypts, and cryptographically verifies a .uvtt2z zip file
func OpenPackage(archivePath string) (*Package, error) {
	rc, err := zip.OpenReader(archivePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open ZIP archive: %w", err)
	}

	pkg := &Package{
		zipFile:  rc,
		filesMap: make(map[string]*zip.File),
	}

	for _, f := range rc.File {
		pkg.filesMap[f.Name] = f
	}

	// 1. Cryptographic Hash Integrity Verification
	if err := pkg.verifyIntegrity(); err != nil {
		rc.Close()
		return nil, fmt.Errorf("cryptographic integrity check failed: %w", err)
	}

	// 2. Parse unencrypted manifest.json
	manifestFile, ok := pkg.filesMap["manifest.json"]
	if !ok {
		rc.Close()
		return nil, errors.New("missing root manifest.json inside archive")
	}

	manifestReader, err := manifestFile.Open()
	if err != nil {
		rc.Close()
		return nil, fmt.Errorf("failed to open manifest.json: %w", err)
	}
	defer manifestReader.Close()

	var manifest Manifest
	if err := json.NewDecoder(manifestReader).Decode(&manifest); err != nil {
		rc.Close()
		return nil, fmt.Errorf("failed to decode manifest.json: %w", err)
	}
	pkg.Manifest = &manifest

	// 3. Parse unencrypted geometry.json
	geometryFile, ok := pkg.filesMap["geometry.json"]
	if !ok {
		rc.Close()
		return nil, errors.New("missing geometry.json inside archive")
	}

	geometryReader, err := geometryFile.Open()
	if err != nil {
		rc.Close()
		return nil, fmt.Errorf("failed to open geometry.json: %w", err)
	}
	defer geometryReader.Close()

	var geometry Geometry
	if err := json.NewDecoder(geometryReader).Decode(&geometry); err != nil {
		rc.Close()
		return nil, fmt.Errorf("failed to decode geometry.json: %w", err)
	}
	pkg.Geometry = &geometry

	// 4. Parse unencrypted entities.json
	entitiesFile, ok := pkg.filesMap["entities.json"]
	if !ok {
		rc.Close()
		return nil, errors.New("missing entities.json inside archive")
	}

	entitiesReader, err := entitiesFile.Open()
	if err != nil {
		rc.Close()
		return nil, fmt.Errorf("failed to open entities.json: %w", err)
	}
	defer entitiesReader.Close()

	var entities Entities
	if err := json.NewDecoder(entitiesReader).Decode(&entities); err != nil {
		rc.Close()
		return nil, fmt.Errorf("failed to decode entities.json: %w", err)
	}
	pkg.Entities = &entities

	// 5. Run runtime catalog structural constraints (e.g. Unique Default Spawn)
	if err := pkg.validateSpawns(); err != nil {
		rc.Close()
		return nil, fmt.Errorf("validation error: %w", err)
	}

	return pkg, nil
}

// Close releases the underlying ZIP file locks
func (p *Package) Close() error {
	if p.zipFile != nil {
		return p.zipFile.Close()
	}
	return nil
}

// ============================================================================
// Cryptographic Integrity Verification Pipeline (Section 4.2)
// ============================================================================

func (p *Package) verifyIntegrity() error {
	hashFile, ok := p.filesMap["manifest.hash"]
	if !ok {
		return errors.New("missing cryptographic integrity receipt: manifest.hash not found in root")
	}

	r, err := hashFile.Open()
	if err != nil {
		return fmt.Errorf("failed to open manifest.hash: %w", err)
	}
	defer r.Close()

	content, err := io.ReadAll(r)
	if err != nil {
		return fmt.Errorf("failed to read manifest.hash: %w", err)
	}

	// Parse manifest.hash lines mapping paths to SHA-256 digests
	expectedHashes := make(map[string]string)
	lines := strings.Split(string(content), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, " ", 2)
		if len(parts) != 2 {
			continue
		}
		digest := strings.TrimSpace(parts[0])
		filePath := strings.TrimSpace(parts[1])
		expectedHashes[filePath] = digest
	}

	// Verify all files present in the ZIP container match the root receipt hashes
	for _, file := range p.zipFile.File {
		if file.Name == "manifest.hash" {
			continue // Skip receipt check on itself
		}

		expectedHash, listed := expectedHashes[file.Name]
		if !listed {
			return fmt.Errorf("security breach: file %q inside archive is unlisted in manifest.hash", file.Name)
		}

		fr, err := file.Open()
		if err != nil {
			return fmt.Errorf("failed to open %q for hashing: %w", file.Name)
		}

		hasher := sha256.New()
		if _, err := io.Copy(hasher, fr); err != nil {
			fr.Close()
			return fmt.Errorf("failed to calculate hash for %q: %w", file.Name, err)
		}
		fr.Close()

		computedHash := hex.EncodeToString(hasher.Sum(nil))
		if computedHash != expectedHash {
			return fmt.Errorf("security breach: computed checksum for %q (%s) does not match receipt (%s)", file.Name, computedHash, expectedHash)
		}
	}

	return nil
}

// validateSpawns asserts there is at most exactly one default landing zone
func (p *Package) validateSpawns() error {
	defaultCount := 0
	for _, sp := range p.Entities.SpawnPoints {
		if sp.IsDefault {
			defaultCount++
		}
	}
	if defaultCount > 1 {
		return errors.New("topology error: map defines multiple default spawn points")
	}
	return nil
}

// ============================================================================
// Zero-Knowledge Clearinghouse Key Derivation & Decryption (Section 6 & 2.2)
// ============================================================================

// DeriveDecryptionKey executes the edge clearinghouse HMAC key generation
func DeriveDecryptionKey(retailerMasterSecret string, productSKU string, keySalt string) []byte {
	mac := hmac.New(sha256.New, []byte(retailerMasterSecret))
	mac.Write([]byte(productSKU + keySalt))
	return mac.Sum(nil)
}

// DecryptAsset performs an in-memory AES-256-GCM decryption for secure streaming
func (p *Package) DecryptAsset(assetPath string, symmetricKey []byte) ([]byte, error) {
	file, ok := p.filesMap[assetPath]
	if !ok {
		return nil, fmt.Errorf("requested asset %q not found in package", assetPath)
	}

	// Safety gating: Verify the premium asset belongs in the secured subdirectory
	if !strings.HasPrefix(assetPath, "protected/") {
		return nil, fmt.Errorf("security constraint: asset %q is not marked as protected", assetPath)
	}

	fr, err := file.Open()
	if err != nil {
		return nil, fmt.Errorf("failed to open encrypted file: %w", err)
	}
	defer fr.Close()

	ciphertext, err := io.ReadAll(fr)
	if err != nil {
		return nil, fmt.Errorf("failed to read encrypted file: %w", err)
	}

	block, err := aes.NewCipher(symmetricKey)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize AES block cipher: %w", err)
	}

	aesGCM, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize AES GCM: %w", err)
	}

	nonceSize := aesGCM.NonceSize()
	if len(ciphertext) < nonceSize {
		return nil, errors.New("malformed cipher block: payload smaller than standard nonce threshold")
	}

	nonce, payload := ciphertext[:nonceSize], ciphertext[nonceSize:]
	plaintext, err := aesGCM.Open(nil, nonce, payload, nil)
	if err != nil {
		return nil, fmt.Errorf("decryption failed (invalid key or tampered block): %w", err)
	}

	return plaintext, nil
}

// ============================================================================
// Spatial Audio Math & Boundary Clamping Helpers (Section 5)
// ============================================================================

// CalculateVolumeFalloff determines dampening using boundary-clamped linear falloff math
// Formula: V = max(0, min(V_max, V_max * (1 - d/r)))
func CalculateVolumeFalloff(distance, fadeRadius, volumeMax float64) float64 {
	if fadeRadius <= 0 {
		return 0
	}
	if distance >= fadeRadius {
		return 0
	}
	if distance <= 0 {
		return volumeMax
	}
	vol := volumeMax * (1.0 - (distance / fadeRadius))
	// Clamp limits safely to eliminate HTML5/Web Audio API popping or indexing faults
	return math.Max(0.0, math.Min(volumeMax, vol))
}
