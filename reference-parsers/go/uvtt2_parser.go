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
	"fmt"
	"io"
	"os"
	"strings"
)

// Universal Visibility Enums
const (
	VisibilityVisible = "visible"
	VisibilityGMOnly  = "gm_only"
	VisibilityHidden  = "hidden"
)

// Resolution and Topology Definitions
type Topology struct {
	Type           string   `json:"type"`                      // square, hex, isometric
	Orientation    string   `json:"orientation,omitempty"`     // flat_top, pointy_top
	Offset         string   `json:"offset,omitempty"`          // odd_row, even_row, odd_col, even_col
	IsometricRatio *float64 `json:"isometric_ratio,omitempty"` // typically 0.5 (2:1 projection)
}

type MapOrigin struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

type GridSize struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

type Resolution struct {
	MapOrigin    MapOrigin `json:"map_origin"`
	GridSize     GridSize  `json:"grid_size"`
	UnitsPerGrid float64   `json:"units_per_grid"`
	UnitName     string    `json:"unit_name"`
	Topology     Topology  `json:"topology"`
}

type HardwareProfile struct {
	MinimumPipeline        string `json:"minimum_pipeline"`
	RecommendedPipeline    string `json:"recommended_pipeline"`
	RequiresComputeShaders bool   `json:"requires_compute_shaders"`
}

type EncryptionHandshake struct {
	ClearinghouseURL string `json:"clearinghouse_url"`
	LicenseAuthority string `json:"license_authority"`
	KeySaltChecksum  string `json:"key_salt_checksum"`
}

type MapCatalogNode struct {
	ID     string `json:"id"`
	Name   string `json:"name"`
	Slug   string `json:"slug"`
	Path   string `json:"path"`
	ZIndex int    `json:"z_index"`
}

// manifest.json Model
type Manifest struct {
	FormatVersion       string               `json:"format_version"`
	UVTTVersion         string               `json:"uvtt_version"`
	CampaignName        string               `json:"campaign_name"`
	Author              string               `json:"author"`
	License             string               `json:"license"`
	HardwareProfile     HardwareProfile      `json:"hardware_profile"`
	EncryptionHandshake *EncryptionHandshake `json:"encryption_handshake,omitempty"`
	MapCatalog          []MapCatalogNode     `json:"map_catalog,omitempty"`
}

// geometry.json Model
type HeightRange struct {
	Bottom float64 `json:"bottom"`
	Top    float64 `json:"top"`
}

type PathNode struct {
	Type string     `json:"type"` // move, line, bezier
	X    *float64   `json:"x,omitempty"`
	Y    *float64   `json:"y,omitempty"`
	CP1  *MapOrigin `json:"cp1,omitempty"`
	CP2  *MapOrigin `json:"cp2,omitempty"`
	To   *MapOrigin `json:"to,omitempty"`
}

type DirectionalBlocks struct {
	LeftToRight []string `json:"left_to_right"` // light, sight, movement
	RightToLeft []string `json:"right_to_left"`
}

type WallStates struct {
	Ethereal      bool     `json:"ethereal"`
	DisbelievedBy []string `json:"disbelieved_by,omitempty"`
}

type Wall struct {
	ID                string             `json:"id"`
	Type              string             `json:"type"` // standard, terrain, illusory
	Height            HeightRange        `json:"height"`
	Path              []PathNode         `json:"path"`
	Blocks            []string           `json:"blocks,omitempty"`
	DirectionalBlocks *DirectionalBlocks `json:"directional_blocks,omitempty"`
	States            *WallStates        `json:"states,omitempty"`
	Visibility        string             `json:"visibility,omitempty"`
	SyncID            string             `json:"sync_id,omitempty"`
}

type Portal struct {
	ID      string      `json:"id"`
	Type    string      `json:"type"`               // door
	SubType string      `json:"sub_type,omitempty"` // standard, secret
	State   string      `json:"state"`              // open, closed, locked, broken
	Height  HeightRange `json:"height"`
	Blocks  []string    `json:"blocks"`
	Line    struct {
		P1 MapOrigin `json:"p1"`
		P2 MapOrigin `json:"p2"`
	} `json:"line"`
	Visibility string `json:"visibility,omitempty"`
	SyncID     string `json:"sync_id,omitempty"`
}

type Roof struct {
	ID      string      `json:"id"`
	Type    string      `json:"type"` // roof
	Height  HeightRange `json:"height"`
	Polygon []MapOrigin `json:"polygon"`
	Image   struct {
		URI string `json:"uri"`
	} `json:"image"`
	Visibility string `json:"visibility,omitempty"`
	SyncID     string `json:"sync_id,omitempty"`
}

type Geometry struct {
	FormatVersion string     `json:"format_version"`
	Resolution    Resolution `json:"resolution"`
	Geometry      struct {
		Walls    []Wall   `json:"walls"`
		Portals  []Portal `json:"portals"`
		Overhead []Roof   `json:"overhead,omitempty"`
	} `json:"geometry"`
}

// entities.json Model
type LightCone struct {
	Rotation float64 `json:"rotation"`
	Arc      float64 `json:"arc"`
}

type LightAnimation struct {
	Type              string  `json:"type"` // flicker, pulse
	Speed             float64 `json:"speed"`
	IntensityVariance float64 `json:"intensity_variance"`
}

type Light struct {
	ID       string `json:"id"`
	Type     string `json:"type"` // point, directional
	Position struct {
		X float64 `json:"x"`
		Y float64 `json:"y"`
		Z float64 `json:"z"`
	} `json:"position"`
	Color        string          `json:"color"` // Hex
	BrightRadius float64         `json:"bright_radius"`
	DimRadius    float64         `json:"dim_radius"`
	Decay        string          `json:"decay"` // linear, inverse_square
	Cone         *LightCone      `json:"cone,omitempty"`
	Animation    *LightAnimation `json:"animation,omitempty"`
	Visibility   string          `json:"visibility,omitempty"`
	SyncID       string          `json:"sync_id,omitempty"`
}

type LandingZoneProperties struct {
	Description     string  `json:"description,omitempty"`
	CameraZoomLevel float64 `json:"camera_zoom_level,omitempty"`
}

type LandingZone struct {
	ID             string                `json:"id"`
	Name           string                `json:"name"`
	IsDefault      bool                  `json:"is_default"`
	Coordinates    []float64             `json:"coordinates"` // exactly 2 elements
	HeadingDegrees float64               `json:"heading_degrees"`
	Properties     LandingZoneProperties `json:"properties,omitempty"`
	Visibility     string                `json:"visibility,omitempty"`
	SyncID         string                `json:"sync_id,omitempty"`
}

type PortalDependency struct {
	PortalID            string   `json:"portal_id"`
	AllowedStates       []string `json:"allowed_states"`
	LockFeedbackMessage string   `json:"lock_feedback_message,omitempty"`
}

type EventAction struct {
	TargetID   string      `json:"target_id"`
	ActionType string      `json:"action_type"` // set_property, play_sound, trigger_event
	Property   string      `json:"property,omitempty"`
	Value      interface{} `json:"value,omitempty"`
}

type EventDestination struct {
	Type                    string  `json:"type"` // intra_map, inter_map
	URI                     string  `json:"uri"`
	FadeTransition          string  `json:"fade_transition,omitempty"`
	PredictionTriggerRadius float64 `json:"prediction_trigger_radius,omitempty"`
}

type Event struct {
	ID            string `json:"id"`
	Type          string `json:"type"` // teleport, trap, trigger
	TriggerBounds struct {
		Shape  string      `json:"shape"` // polygon, circle
		Points []MapOrigin `json:"points,omitempty"`
		Center *MapOrigin  `json:"center,omitempty"`
		Radius *float64    `json:"radius,omitempty"`
	} `json:"trigger_bounds"`
	Conditions struct {
		RequiresInteraction bool     `json:"requires_interaction"`
		InteractionKey      string   `json:"interaction_key,omitempty"`
		AllowedModes        []string `json:"allowed_modes,omitempty"`
		IsActive            bool     `json:"is_active,omitempty"`
	} `json:"conditions"`
	Destination      EventDestination  `json:"destination"`
	PortalDependency *PortalDependency `json:"portal_dependency,omitempty"`
	Actions          []EventAction     `json:"actions,omitempty"`
	Visibility       string            `json:"visibility,omitempty"`
	SyncID           string            `json:"sync_id,omitempty"`
}

type AcousticZone struct {
	ID                string    `json:"id"`
	Shape             string    `json:"shape"` // circle, polygon
	Center            MapOrigin `json:"center"`
	Radius            float64   `json:"radius"`
	FadeRadius        float64   `json:"fade_radius"`
	VolumeMax         float64   `json:"volume_max"`
	AudioURI          string    `json:"audio_uri"`
	MuffledByGeometry bool      `json:"muffled_by_geometry,omitempty"`
	Visibility        string    `json:"visibility,omitempty"`
	SyncID            string    `json:"sync_id,omitempty"`
}

type GlobalAudioItem struct {
	URI               string  `json:"uri"`
	Volume            float64 `json:"volume"`
	CrossfadeDuration float64 `json:"crossfade_duration,omitempty"`
}

type AudioBlock struct {
	Music    *GlobalAudioItem `json:"music,omitempty"`
	Ambience *GlobalAudioItem `json:"ambience,omitempty"`
	Zones    []AcousticZone   `json:"zones,omitempty"`
}

type WeatherProperties struct {
	Intensity     float64 `json:"intensity"`
	Speed         float64 `json:"speed"`
	Angle         float64 `json:"angle"`
	Color         string  `json:"color"`
	RenderLayer   string  `json:"render_layer,omitempty"`   // above_overhead, below_overhead, ground_level
	CollisionMode string  `json:"collision_mode,omitempty"` // none, mask_under_overhead, ground_terminate, wall_bounce
	WindInfluence struct {
		InheritGlobal  bool    `json:"inherit_global"`
		InfluenceScale float64 `json:"influence_scale"`
	} `json:"wind_influence,omitempty"`
}

type WeatherEmitter struct {
	ID       string `json:"id"`
	Type     string `json:"type"` // rain, snow, fog, embers, magic
	IsGlobal bool   `json:"is_global"`
	Bounds   *struct {
		Shape  string      `json:"shape"`
		Points []MapOrigin `json:"points"`
	} `json:"bounds,omitempty"`
	Height     *HeightRange      `json:"height,omitempty"`
	Properties WeatherProperties `json:"properties"`
	Visibility string            `json:"visibility,omitempty"`
	SyncID     string            `json:"sync_id,omitempty"`
}

type Entities struct {
	FormatVersion string           `json:"format_version"`
	Lights        []Light          `json:"lights,omitempty"`
	LandingZones  []LandingZone    `json:"landing_zones,omitempty"`
	Events        []Event          `json:"events,omitempty"`
	Audio         *AudioBlock      `json:"audio,omitempty"`
	Emitters      []WeatherEmitter `json:"emitters,omitempty"`
}

// .uvtt2a asset_manifest.json Model
type StandaloneAssetAudio struct {
	ID            string   `json:"id"`
	File          string   `json:"file"`
	Name          string   `json:"name"`
	DefaultVolume float64  `json:"default_volume"`
	IsLoop        bool     `json:"is_loop"`
	Tags          []string `json:"tags,omitempty"`
}

type StandaloneAssetToken struct {
	ID            string `json:"id"`
	File          string `json:"file"`
	Name          string `json:"name"`
	GridFootprint struct {
		WidthInGrids  float64 `json:"width_in_grids"`
		HeightInGrids float64 `json:"height_in_grids"`
	} `json:"grid_footprint"`
	Tags []string `json:"tags,omitempty"`
}

type StandaloneAssetPropAutoEmit struct {
	Type              string          `json:"type"` // light, audio, emitter
	Color             string          `json:"color,omitempty"`
	BrightRadius      float64         `json:"bright_radius,omitempty"`
	DimRadius         float64         `json:"dim_radius,omitempty"`
	Decay             string          `json:"decay,omitempty"`
	Animation         *LightAnimation `json:"animation,omitempty"`
	AudioURI          string          `json:"audio_uri,omitempty"`
	VolumeMax         float64         `json:"volume_max,omitempty"`
	FadeRadius        float64         `json:"fade_radius,omitempty"`
	MuffledByGeometry bool            `json:"muffled_by_geometry,omitempty"`
	EmitterType       string          `json:"emitter_type,omitempty"`
	Properties        interface{}     `json:"properties,omitempty"`
}

type StandaloneAssetProp struct {
	ID            string  `json:"id"`
	File          string  `json:"file"`
	Name          string  `json:"name"`
	DefaultScale  float64 `json:"default_scale,omitempty"`
	GridFootprint struct {
		WidthInGrids  float64 `json:"width_in_grids"`
		HeightInGrids float64 `json:"height_in_grids"`
	} `json:"grid_footprint"`
	Tags      []string                      `json:"tags,omitempty"`
	AutoEmits []StandaloneAssetPropAutoEmit `json:"auto_emits,omitempty"`
}

type AssetManifest struct {
	FormatVersion string `json:"format_version"`
	PackageType   string `json:"package_type"` // asset_pack
	PackName      string `json:"pack_name"`
	Author        string `json:"author"`
	Version       string `json:"version"`
	Assets        struct {
		Audio  []StandaloneAssetAudio `json:"audio,omitempty"`
		Tokens []StandaloneAssetToken `json:"tokens,omitempty"`
		Props  []StandaloneAssetProp  `json:"props,omitempty"`
	} `json:"assets"`
}

// IngestEngine reads, decrypts, and conformance-audits UVTT v2 files
type IngestEngine struct{}

func NewIngestEngine() *IngestEngine {
	return &IngestEngine{}
}

// IngestPackage parses and fully audits a raw zip file stream
func (ie *IngestEngine) IngestPackage(zipBytes []byte, isEncrypted bool, aesKey []byte) (*Manifest, map[string][]byte, error) {
	var err error
	var rawZip []byte

	// 1. Handle Decryption if Encrypted (.uvtt2k)
	if isEncrypted {
		if len(aesKey) == 0 {
			return nil, nil, errors.New("cannot decrypt .uvtt2z envelope without a valid AES-256 key")
		}
		rawZip, err = ie.DecryptGCMEnvelope(zipBytes, aesKey)
		if err != nil {
			return nil, nil, fmt.Errorf("cryptographic envelope decryption failed: %v", err)
		}
	} else {
		rawZip = zipBytes
	}

	// 2. Open ZIP Reader
	reader, err := zip.NewReader(bytes.NewReader(rawZip), int64(len(rawZip)))
	if err != nil {
		return nil, nil, fmt.Errorf("malformed zip container archive: %v", err)
	}

	// Index ZIP contents into memory
	fileMap := make(map[string][]byte)
	for _, f := range reader.File {
		rc, err := f.Open()
		if err != nil {
			return nil, nil, err
		}
		buf := new(bytes.Buffer)
		_, err = io.Copy(buf, rc)
		rc.Close()
		if err != nil {
			return nil, nil, err
		}
		fileMap[f.Name] = buf.Bytes()
	}

	// 3. Cryptographic hash receipt audit against manifest.hash
	hashData, ok := fileMap["manifest.hash"]
	if !ok {
		return nil, nil, errors.New("security validation rejected: missing mandatory integrity receipt 'manifest.hash' in root")
	}

	err = ie.VerifyHashes(fileMap, hashData)
	if err != nil {
		return nil, nil, fmt.Errorf("integrity audit failure: %v", err)
	}

	// 4. Ingest and parse manifest.json
	manifestBytes, ok := fileMap["manifest.json"]
	if !ok {
		return nil, nil, errors.New("format violation: missing global index manifest.json")
	}

	var manifest Manifest
	err = json.Unmarshal(manifestBytes, &manifest)
	if err != nil {
		return nil, nil, fmt.Errorf("manifest json parsing failed: %v", err)
	}

	if manifest.FormatVersion != "2.0.0" || manifest.UVTTVersion != "2.0.0" {
		return nil, nil, fmt.Errorf("incompatible format specification mappings (format: %s, uvtt: %s). Expected '2.0.0'", manifest.FormatVersion, manifest.UVTTVersion)
	}

	// 5. Ingest sub-directories for geometry and entities
	if len(manifest.MapCatalog) == 0 {
		// Single Map Mode (Federated / STANDALONE fallback checks)
		err = ie.AuditMapLayer(fileMap, "")
		if err != nil {
			return nil, nil, err
		}
	} else {
		// Compound Campaign Mode
		for _, node := range manifest.MapCatalog {
			if node.Path == "" {
				return nil, nil, errors.New("sub_maps nodes inside compound catalog must specify a non-empty relative folder 'path'")
			}
			err = ie.AuditMapLayer(fileMap, node.Path)
			if err != nil {
				return nil, nil, fmt.Errorf("nested node '%s' conformance conflict: %v", node.Name, err)
			}
		}
	}

	return &manifest, fileMap, nil
}

func (ie *IngestEngine) DecryptGCMEnvelope(encryptedBytes []byte, aesKey []byte) ([]byte, error) {
	if len(encryptedBytes) < 12 {
		return nil, errors.New("encrypted payload size underflow")
	}

	block, err := aes.NewCipher(aesKey)
	if err != nil {
		return nil, err
	}

	aesgcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	nonce := encryptedBytes[:12]
	ciphertext := encryptedBytes[12:]

	plaintext, err := aesgcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, err
	}

	return plaintext, nil
}

func (ie *IngestEngine) VerifyHashes(fileMap map[string][]byte, hashData []byte) error {
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
			return fmt.Errorf("security alert: untracked file found in archive container: '%s'", name)
		}

		hasher := sha256.New()
		hasher.Write(content)
		computed := hex.EncodeToString(hasher.Sum(nil))

		if computed != expected {
			return fmt.Errorf("checksum validation failure on file '%s'\n  Expected: %s\n  Computed: %s", name, expected, computed)
		}
	}

	return nil
}

func (ie *IngestEngine) AuditMapLayer(fileMap map[string][]byte, path string) error {
	geomPath := path + "geometry.json"
	entPath := path + "entities.json"
	basePath := path + "basemap.webp"

	if _, ok := fileMap[basePath]; !ok {
		return fmt.Errorf("missing standard unencrypted watermarked baseline asset: '%s'", basePath)
	}

	geomBytes, ok := fileMap[geomPath]
	if !ok {
		return fmt.Errorf("missing mandatory layout geometry vector layer: '%s'", geomPath)
	}

	var geom Geometry
	err := json.Unmarshal(geomBytes, &geom)
	if err != nil {
		return fmt.Errorf("geometry file json syntax error: %v", err)
	}

	for _, wall := range geom.Geometry.Walls {
		if wall.Height.Bottom > wall.Height.Top {
			return fmt.Errorf("verticality collision on wall '%s': bottom height (%f) exceeds top threshold (%f)", wall.ID, wall.Height.Bottom, wall.Height.Top)
		}
	}

	if entBytes, ok := fileMap[entPath]; ok {
		var ent Entities
		err := json.Unmarshal(entBytes, &ent)
		if err != nil {
			return fmt.Errorf("entities file json syntax error: %v", err)
		}

		defaultCount := 0
		for _, lz := range ent.LandingZones {
			if lz.IsDefault {
				defaultCount++
			}
		}
		if defaultCount > 1 {
			return fmt.Errorf("topology collision: campaign layout defines multiple default landing zones (%d) in entities block", defaultCount)
		}

		for _, emitter := range ent.Emitters {
			if !emitter.IsGlobal {
				if emitter.Bounds == nil || len(emitter.Bounds.Points) == 0 {
					return fmt.Errorf("physics engine fault: local weather emitter '%s' must map coordinates bounds", emitter.ID)
				}
			}
		}

		if ent.Audio != nil {
			for _, zone := range ent.Audio.Zones {
				if zone.FadeRadius <= 0 {
					return fmt.Errorf("acoustics engine conflict on zone '%s': fade_radius must be a positive non-zero float", zone.ID)
				}
			}
		}
	}

	return nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: uvtt2_parser <path_to_archive.uvtt2z> [path_to_key.uvtt2k]")
		os.Exit(0)
	}

	archivePath := os.Args[1]
	archiveBytes, err := os.ReadFile(archivePath)
	if err != nil {
		fmt.Printf("Error reading target file: %v\n", err)
		os.Exit(1)
	}

	isEncrypted := len(os.Args) >= 3
	var aesKey []byte

	if isEncrypted {
		keyPath := os.Args[2]
		keyBytes, err := os.ReadFile(keyPath)
		if err != nil {
			fmt.Printf("Error reading key file: %v\n", err)
			os.Exit(1)
		}
		// Decode the raw hex string directly into bytes
		keyHex := strings.TrimSpace(string(keyBytes))
		aesKey, err = hex.DecodeString(keyHex)
		if err != nil {
			fmt.Printf("Error decoding hex key: %v\n", err)
			os.Exit(1)
		}
	}

	engine := NewIngestEngine()
	manifest, _, err := engine.IngestPackage(archiveBytes, isEncrypted, aesKey)
	if err != nil {
		fmt.Printf("[-] CONFORMANCE AUDIT REJECTED: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("[+] CONFORMANCE SUCCESS: Loaded campaign '%s' cleanly under UVTT v2 specification!\n", manifest.CampaignName)
}
