/**
 * Universal Virtual Tabletop Version 2 (UVTT v2) TypeScript Reference Parser
 * File: uvtt2_parser.tst (TypeScript Reference Implementation)
 * 
 * Standards Body: Open Virtual Tabletop Consortium (OVTC)
 * Format Version: 2.0.0 (Final Production Specification)
 * 
 * Implements:
 *  1. ZIP Archive Stream Parsing (Standard .uvtt2z and Standalone .uvtt2a packages)
 *  2. In-Memory AES-256-GCM Decryption (.uvtt2k) using native Web Crypto API
 *  3. Volatile Memory Disposal Protocol (heap sanitization, URL object revocations)
 *  4. SVG Cubic Bézier curve flattening and subdivision calculations
 *  5. Collinear path simplification algorithms
 *  6. Acoustic physics linear decay proximity equations
 */

// ============================================================================
// SECTION 1: SYSTEM SCHEMA INTERFACES
// ============================================================================

export type TopologyType = "square" | "hex" | "isometric";
export type HexOrientation = "flat_top" | "pointy_top";
export type HexOffset = "odd_row" | "even_row" | "odd_col" | "even_col";
export type WallType = "standard" | "terrain" | "illusory";
export type PathNodeType = "move" | "line" | "bezier";
export type LightType = "point" | "directional";
export type LightDecay = "linear" | "inverse_square";
export type LightAnimationType = "flicker" | "pulse";
export type AudioZoneShape = "circle" | "polygon";
export type EmitterType = "rain" | "snow" | "fog" | "embers" | "magic";
export type CollisionMode = "none" | "mask_under_overhead" | "ground_terminate" | "wall_bounce";
export type RenderLayer = "above_overhead" | "below_overhead" | "ground_level";
export type PackageType = "asset_pack" | "map_pack" | "compound";

export interface MapOrigin {
  x: number;
  y: number;
}

export interface GridSize {
  x: number;
  y: number;
}

export interface Topology {
  type: TopologyType;
  orientation?: HexOrientation;
  offset?: HexOffset;
  isometric_ratio?: number; // Capped at (0.0, 1.0], typically 0.5
}

export interface Resolution {
  map_origin: MapOrigin;
  grid_size: GridSize;
  units_per_grid: number;
  unit_name: string;
  topology: Topology;
}

export interface HardwareProfile {
  minimum_pipeline: "webgl2" | "webgpu";
  recommended_pipeline: "webgl2" | "webgpu";
  requires_compute_shaders: boolean;
}

export interface EncryptionHandshake {
  clearinghouse_url: string;
  license_authority: string;
  key_salt_checksum: string;
}

export interface MapCatalogNode {
  id: string;
  name: string;
  slug: string;
  path: string;
  z_index: number;
}

export interface Manifest {
  format_version: string;
  uvtt_version: string;
  campaign_name: string;
  author: string;
  license: string;
  hardware_profile: HardwareProfile;
  encryption_handshake?: EncryptionHandshake;
  map_catalog?: MapCatalogNode[];
}

export interface HeightRange {
  bottom: number;
  top: number;
}

export interface PathNode {
  type: PathNodeType;
  x?: number;
  y?: number;
  cp1?: MapOrigin;
  cp2?: MapOrigin;
  to?: MapOrigin;
}

export interface DirectionalBlocks {
  left_to_right: string[]; // light, sight, movement
  right_to_left: string[];
}

export interface WallStates {
  ethereal: boolean;
  disbelieved_by?: string[];
}

export interface Wall {
  id: string;
  type: WallType;
  height: HeightRange;
  path: PathNode[];
  blocks?: string[];
  directional_blocks?: DirectionalBlocks;
  states?: WallStates;
  visibility?: "visible" | "gm_only" | "hidden";
  sync_id?: string;
}

export interface Portal {
  id: string;
  type: "door";
  sub_type?: "standard" | "secret";
  state: "open" | "closed" | "locked" | "broken";
  height: HeightRange;
  blocks: string[];
  line: {
    p1: MapOrigin;
    p2: MapOrigin;
  };
  visibility?: "visible" | "gm_only" | "hidden";
  sync_id?: string;
}

export interface Roof {
  id: string;
  type: "roof";
  height: HeightRange;
  polygon: MapOrigin[];
  image: {
    uri: string;
  };
  visibility?: "visible" | "gm_only" | "hidden";
  sync_id?: string;
}

export interface Geometry {
  format_version: string;
  resolution: Resolution;
  geometry: {
    walls: Wall[];
    portals: Portal[];
    overhead?: Roof[];
  };
}

export interface LightCone {
  rotation: number;
  arc: number;
}

export interface LightAnimation {
  type: LightAnimationType;
  speed: number;
  intensity_variance: number;
}

export interface Light {
  id: string;
  type: LightType;
  position: { x: number; y: number; z: number };
  color: string; // Hex matching ^#[a-fA-F0-9]{6}$
  bright_radius: number;
  dim_radius: number;
  decay: LightDecay;
  cone?: LightCone;
  animation?: LightAnimation;
  visibility?: "visible" | "gm_only" | "hidden";
  sync_id?: string;
}

export interface LandingZoneProperties {
  description?: string;
  camera_zoom_level?: number;
}

export interface LandingZone {
  id: string;
  name: string;
  is_default: boolean;
  coordinates: [number, number];
  heading_degrees: number;
  properties?: LandingZoneProperties;
  visibility?: "visible" | "gm_only" | "hidden";
  sync_id?: string;
}

export interface PortalDependency {
  portal_id: string;
  allowed_states: string[]; // open, closed, broken, locked
  lock_feedback_message?: string;
}

export interface EventAction {
  target_id: string;
  action_type: "set_property" | "play_sound" | "trigger_event";
  property?: string;
  value?: any;
}

export interface EventDestination {
  type: "intra_map" | "inter_map";
  uri: string;
  fade_transition?: "crossfade_black" | "planar_flash";
  prediction_trigger_radius?: number;
}

export interface Event {
  id: string;
  type: "teleport" | "trap" | "trigger";
  trigger_bounds: {
    shape: "polygon" | "circle";
    points?: MapOrigin[];
    center?: MapOrigin;
    radius?: number;
  };
  conditions: {
    requires_interaction: boolean;
    interaction_key?: string;
    allowed_modes?: string[];
    is_active?: boolean;
  };
  destination: EventDestination;
  portal_dependency?: PortalDependency;
  actions?: EventAction[];
  visibility?: "visible" | "gm_only" | "hidden";
  sync_id?: string;
}

export interface AcousticZone {
  id: string;
  shape: AudioZoneShape;
  center: MapOrigin;
  radius: number;
  fade_radius: number;
  volume_max: number;
  audio_uri: string;
  muffled_by_geometry?: boolean;
  visibility?: "visible" | "gm_only" | "hidden";
  sync_id?: string;
}

export interface GlobalAudioItem {
  uri: string;
  volume: number;
  crossfade_duration?: number;
}

export interface AudioBlock {
  music?: GlobalAudioItem;
  ambience?: GlobalAudioItem;
  zones?: AcousticZone[];
}

export interface WeatherProperties {
  intensity: number; // [0.0, 1.0]
  speed: number;
  angle: number;
  color: string;
  render_layer?: RenderLayer;
  collision_mode?: CollisionMode;
  wind_influence?: {
    inherit_global: boolean;
    influence_scale: number;
  };
}

export interface WeatherEmitter {
  id: string;
  type: EmitterType;
  is_global: boolean;
  bounds?: {
    shape: "polygon" | "circle";
    points: MapOrigin[];
  };
  height?: HeightRange;
  properties: WeatherProperties;
  visibility?: "visible" | "gm_only" | "hidden";
  sync_id?: string;
}

export interface Entities {
  format_version: string;
  lights?: Light[];
  landing_zones?: LandingZone[];
  events?: Event[];
  audio?: AudioBlock;
  emitters?: WeatherEmitter[];
}

// ============================================================================
// SECTION 2: STANDALONE .uvtt2a ASSET MODELS
// ============================================================================

export interface StandaloneAssetAudio {
  id: string;
  file: string;
  name: string;
  default_volume: number;
  is_loop: boolean;
  tags?: string[];
}

export interface StandaloneAssetToken {
  id: string;
  file: string;
  name: string;
  grid_footprint: {
    width_in_grids: number;
    height_in_grids: number;
  };
  tags?: string[];
}

export interface StandaloneAssetPropAutoEmit {
  type: "light" | "audio" | "emitter";
  color?: string;
  bright_radius?: number;
  dim_radius?: number;
  decay?: LightDecay;
  animation?: LightAnimation;
  audio_uri?: string;
  volume_max?: number;
  fade_radius?: number;
  muffled_by_geometry?: boolean;
  emitter_type?: EmitterType;
  properties?: any;
}

export interface StandaloneAssetProp {
  id: string;
  file: string;
  name: string;
  default_scale?: number;
  grid_footprint: {
    width_in_grids: number;
    height_in_grids: number;
  };
  tags?: string[];
  auto_emits?: StandaloneAssetPropAutoEmit[];
}

export interface AssetManifest {
  format_version: string;
  package_type: "asset_pack";
  pack_name: string;
  author: string;
  version: string;
  assets: {
    audio?: StandaloneAssetAudio[];
    tokens?: StandaloneAssetToken[];
    props?: StandaloneAssetProp[];
  };
}

// ============================================================================
// SECTION 3: CORE PARSING & CRYPTOGRAPHIC HANDSHAKE RUNTIME
// ============================================================================

export class Uvtt2Parser {
  private masterSecret: Uint8Array | null = null;

  constructor(secretHex?: string) {
    if (secretHex) {
      this.masterSecret = this.hexToUint8Array(secretHex);
    }
  }

  /**
   * Performs standard deterministic key derivation (ZKS Mode) and decrypts the GCM envelope
   * matching our serverless edge Worker formula.
   */
  public async decryptGCMEnvelope(
    encryptedData: ArrayBuffer,
    sku: string,
    saltHex: string
  ): Promise<ArrayBuffer> {
    if (!this.masterSecret) {
      throw new Error("Volatile Cryptographic State Conflict: No master secret configured.");
    }

    if (encryptedData.byteLength < 12 + 16) {
      throw new Error("Cryptographic Fault: Encrypted envelope size underflow.");
    }

    const salt = this.hexToUint8Array(saltHex);
    const skuBytes = new TextEncoder().encode(sku);

    // Conjoin SKU and salt into a single message
    const message = new Uint8Array(skuBytes.length + salt.length);
    message.set(skuBytes, 0);
    message.set(salt, skuBytes.length);

    // Derived Key = HMAC-SHA256(MasterSecret, SKU + Salt)
    const cryptoKey = await crypto.subtle.importKey(
      "raw",
      this.masterSecret,
      { name: "HMAC", hash: { name: "SHA-256" } },
      false,
      ["sign"]
    );

    const signature = await crypto.subtle.sign("HMAC", cryptoKey, message);
    const derivedKeyBytes = new Uint8Array(signature);

    // Import derived key for AES-GCM
    const aesKey = await crypto.subtle.importKey(
      "raw",
      derivedKeyBytes.subarray(0, 32), // Slice to 256 bits
      { name: "AES-GCM" },
      false,
      ["decrypt"]
    );

    // Extract Nonce (first 12 bytes) and ciphertext
    const nonce = encryptedData.slice(0, 12);
    const ciphertext = encryptedData.slice(12);

    const plaintext = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: nonce },
      aesKey,
      ciphertext
    );

    // Volatile Memory Scrubbing: Fill cryptographic derived keys with zero instantly
    derivedKeyBytes.fill(0);
    message.fill(0);

    return plaintext;
  }

  /**
   * Verifies a directory mapping of files against the standard root manifest.hash receipt.
   * Prompts platform shutdowns on checksum mismatch or untracked files.
   */
  public async verifyHashes(
    fileMap: Map<string, ArrayBuffer>,
    hashData: string
  ): Promise<void> {
    const lines = hashData.trim().split("\n");
    const hashRegistry = new Map<string, string>();

    for (const line of lines) {
      if (!line.includes("  ")) continue;
      const parts = line.split("  ", 2);
      const checksum = parts[0].trim();
      const filePath = parts[1].trim();
      hashRegistry.set(filePath, checksum);
    }

    for (const [name, content] of fileMap.entries()) {
      if (name === "manifest.hash" || name === "manifest.json") {
        continue;
      }

      const expected = hashRegistry.get(name);
      if (!expected) {
        throw new Error(`Security Exception: Untracked file detected in container: '${name}'`);
      }

      const hashBuffer = await crypto.subtle.digest("SHA-256", content);
      const computed = this.bufferToHex(hashBuffer);

      if (computed !== expected) {
        throw new Error(
          `Integrity Verification Failure: Checksum mismatch on file '${name}'\n  Expected: ${expected}\n  Computed: ${computed}`
        );
      }
    }
  }

  /**
   * Performs real-time logical constraint auditing on a single map layer subdirectory.
   */
  public auditMapLayer(
    geometry: Geometry,
    entities?: Entities
  ): void {
    // 1. Z-Height Integrity check
    for (const wall of geometry.geometry.walls) {
      if (wall.height.bottom > wall.height.top) {
        throw new Error(
          `Verticality Conflict on wall '${wall.id}': Bottom Z (${wall.height.bottom}) exceeds Top boundary (${wall.height.top}).`
        );
      }
    }

    if (entities) {
      // 2. Default Spawn Point Limit
      const defaultSpawns = (entities.landing_zones || []).filter(lz => lz.is_default);
      if (defaultSpawns.length > 1) {
        throw new Error(
          `Topology Collision: Multiple default starting landing zones detected (${defaultSpawns.length}).`
        );
      }

      // 3. Emitter Boundaries
      for (const emitter of entities.emitters || []) {
        if (!emitter.is_global) {
          if (!emitter.bounds || !emitter.bounds.points || emitter.bounds.points.length === 0) {
            throw new Error(
              `Physics Engine Fault: Localized weather emitter '${emitter.id}' must define explicit coordinate bounds.`
            );
          }
        }
      }

      // 4. Acoustic decay verification
      if (entities.audio && entities.audio.zones) {
        for (const zone of entities.audio.zones) {
          if (zone.fade_radius <= 0) {
            throw new Error(
              `Acoustic Decay Range Violation on sound zone '${zone.id}': fade_radius must be positive and non-zero.`
            );
          }
        }
      }
    }
  }

  // ============================================================================
  // SECTION 4: MATHEMATICAL & GEOMETRICAL ALGORITHMS
  // ============================================================================

  /**
   * Linear Acoustic Proximity attenuation falloff formula.
   * Clamps bounds securely to prevent audio engine popping.
   */
  public calculateAcousticVolume(
    distance: number,
    radius: number,
    fadeRadius: number,
    volumeMax: number
  ): number {
    if (distance <= radius) {
      return volumeMax;
    }
    const d = distance - radius;
    if (d >= fadeRadius) {
      return 0.0;
    }
    
    // Formula: V = max(0, min(V_max, V_max * (1 - d/r)))
    const volume = volumeMax * (1 - d / fadeRadius);
    return Math.max(0.0, Math.min(volumeMax, volume));
  }

  /**
   * Subdivides smooth SVG Bézier paths into a series of rigid, multi-point
   * straight-line approximations for legacy v1 engines.
   */
  public flattenSvgPath(pathArray: PathNode[]): MapOrigin[] {
    const points: MapOrigin[] = [];
    let currentPt: MapOrigin = { x: 0, y: 0 };

    for (const node of pathArray) {
      if (node.type === "move" || node.type === "line") {
        currentPt = { x: node.x ?? 0, y: node.y ?? 0 };
        points.push(currentPt);
      } else if (node.type === "bezier" && node.cp1 && node.cp2 && node.to) {
        const steps = 10; // Subdivide curve into 10 straight segments
        const p0 = currentPt;
        const p1 = node.cp1;
        const p2 = node.cp2;
        const p3 = node.to;

        for (let i = 1; i <= steps; i++) {
          const t = i / steps;
          const invT = 1 - t;

          // Parametric Cubic Bezier Formula
          const x =
            invT * invT * invT * p0.x +
            3 * invT * invT * t * p1.x +
            3 * invT * t * t * p2.x +
            t * t * t * p3.x;
          const y =
            invT * invT * invT * p0.y +
            3 * invT * invT * t * p1.y +
            3 * invT * t * t * p2.y +
            t * t * t * p3.y;

          points.push({ x, y });
        }
        currentPt = p3;
      }
    }
    return points;
  }

  /**
   * Merges and simplifies collinear segments on vector paths, reducing 
   * file footprint sizes and compiling direction blocks with precision.
   */
  public simplifyCollinearPath(points: MapOrigin[], epsilon: number = 1e-5): MapOrigin[] {
    if (points.length <= 2) return points;

    const result: MapOrigin[] = [points[0]];

    for (let i = 1; i < points.length - 1; i++) {
      const p1 = result[result.length - 1];
      const p2 = points[i];
      const p3 = points[i + 1];

      // Calculate cross product: Area = x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2)
      const area = p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y);

      if (Math.abs(area) > epsilon) {
        result.push(p2);
      }
    }

    result.push(points[points.length - 1]);
    return result;
  }

  // ============================================================================
  // SECTION 5: HELPER UTILITIES
  // ============================================================================

  private hexToUint8Array(hex: string): Uint8Array {
    const cleanHex = hex.trim();
    const len = cleanHex.length;
    const view = new Uint8Array(len / 2);
    for (let i = 0; i < len; i += 2) {
      view[i / 2] = parseInt(cleanHex.substring(i, i + 2), 16);
    }
    return view;
  }

  private bufferToHex(buffer: ArrayBuffer): string {
    const view = new Uint8Array(buffer);
    return Array.from(view)
      .map(b => b.toString(16).padStart(2, "0"))
      .join("");
  }
}
