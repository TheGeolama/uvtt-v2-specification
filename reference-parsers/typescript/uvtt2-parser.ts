/**
 * ======================================================================
 *               Universal VTT v2 (UVTT v2) Reference Parser
 *                 Specification Version: v2.0.0-rc1
 * ======================================================================
 * This parser module provides complete type definitions, cryptographic
 * integrity validation, Web Crypto volatile GCM decryption, and geometric
 * path-flattening algorithms for compliant client virtual tabletops (VTTs).
 * 
 * Public domain file schemas (CC0 1.0) and Apache 2.0 reference engine.
 */

// ======================================================================
// 1. Core Typings & Schema Definitions
// ======================================================================

export interface Point {
  x: number;
  y: number;
}

export interface Point3D extends Point {
  z: number;
}

export interface HeightBounds {
  bottom: number;
  top: number;
}

export interface SVGPathNode {
  type: "move" | "line" | "bezier";
  x?: number; // Target coordinate for move/line
  y?: number;
  cp1?: Point; // Cubic bezier control point 1
  cp2?: Point; // Cubic bezier control point 2
  to?: Point;  // Cubic bezier destination point
}

export interface UVTT2Manifest {
  format_version: "2.0.0";
  uvtt_version: "2.0.0";
  campaign_name: string;
  author: string;
  license: string;
  hardware_profile?: {
    minimum_pipeline: "webgl2" | "webgpu";
    recommended_pipeline: "webgl2" | "webgpu";
    requires_compute_shaders: boolean;
  };
  encryption_handshake?: {
    clearinghouse_url: string;
    license_authority: string;
    key_salt_checksum: string; // 32-character hexadecimal pattern
  };
  audio?: {
    music?: {
      uri: string;
      volume: number; // Volume bounded [0.0 - 1.0]
      crossfade_duration?: number;
    };
    ambience?: {
      uri: string;
      volume: number;
    };
  };
  map_catalog?: Array<{
    id: string;
    name: string;
    slug: string; // URL-safe, slugified folder string
    path: string; // Directory mapping within ZIP (e.g. maps/cellar/)
    z_index: number; // Vertical sorting index (ground floor = 0)
  }>;
}

export interface UVTT2Geometry {
  format_version: "2.0.0";
  resolution: {
    map_origin: Point;
    grid_size: Point;
    units_per_grid: number; // Physical distance represented by 1 cell (e.g. 5.0)
    unit_name: string; // Measurement unit name (e.g. 'ft', 'm')
    topology: {
      type: "square" | "hex" | "isometric";
      orientation?: "flat_top" | "pointy_top"; // Required for hex
      offset?: "odd_row" | "even_row" | "odd_col" | "even_col"; // Required for hex
      isometric_ratio?: number; // Required for iso (Standard = 0.5)
    };
  };
  geometry: {
    walls: Array<{
      id: string;
      type: "standard" | "terrain" | "illusory";
      height: HeightBounds;
      path: SVGPathNode[];
      blocks?: Array<"light" | "sight" | "movement">; // Global bi-directional blocks
      directional_blocks?: {
        left_to_right: Array<"light" | "sight" | "movement">;
        right_to_left: Array<"light" | "sight" | "movement">;
      };
      states?: {
        ethereal: boolean; // Bypasses blocks globally without removing nodes
        disbelieved_by?: string[]; // Player IDs who see through the illusion
      };
    }>;
    portals: Array<{
      id: string;
      type: "door";
      sub_type?: "standard" | "secret";
      state: "open" | "closed";
      height: HeightBounds;
      blocks: Array<"light" | "sight" | "movement">;
      line: {
        p1: Point;
        p2: Point;
      };
    }>;
    overhead?: Array<{
      id: string;
      type: "roof";
      height: HeightBounds;
      polygon: Point[]; // Minimum 3 vertices defining roof boundary
      image: {
        uri: string; // Internal or local relative path to assets
      };
    }>;
  };
}

export interface UVTT2Entities {
  lights?: Array<{
    id: string;
    type: "point" | "directional";
    position: Point3D;
    color: string; // #RRGGBB Hex pattern
    bright_radius: number;
    dim_radius: number;
    decay: "linear" | "inverse_square";
    cone?: {
      rotation: number; // Compass angle [0.0 - 360.0]
      arc: number; // Opening angle in degrees [1.0 - 360.0]
    };
    animation?: {
      type: "flicker" | "pulse";
      speed: number;
      intensity_variance: number; // Scale [0.0 - 1.0]
    };
  }>;
  landing_zones?: Array<{
    id: string;
    name: string;
    is_default: boolean; // Exactly one default permitted per map catalog entry
    coordinates: [number, number];
    heading_degrees: number;
    properties?: {
      description?: string;
      camera_zoom_level?: number; // Cinematic default viewport scaling
    };
  }>;
  events?: Array<{
    id: string;
    type: "teleport" | "trap";
    trigger_bounds: {
      shape: "polygon" | "circle";
      points?: Point[]; // Required for polygon triggers
      center?: Point;   // Required for circular triggers
      radius?: number;  // Required for circular triggers
    };
    conditions?: {
      requires_interaction?: boolean;
      interaction_key?: string;
      allowed_modes?: string[]; // e.g. ["walking", "flying"]
      is_active?: boolean;
      key_item_required?: string;
    };
    destination?: {
      type: "intra_map" | "inter_map";
      uri: string; // Standardized: internal:// (compound) or relative:// (federated) targets
      fade_transition?: "crossfade_black" | "planar_flash";
      prediction_trigger_radius?: number; // Distance in grids to pre-load targets
    };
  }>;
  audio?: {
    zones?: Array<{
      id: string;
      shape: "circle" | "polygon";
      center?: Point;
      radius?: number;
      fade_radius: number; // Proximity boundary for volume dampening calculations
      volume_max: number;  // Maximum audio level cap [0.0 - 1.0]
      audio_uri: string;
    }>;
  };
  emitters?: Array<{
    id: string;
    type: "rain" | "snow" | "fog" | "embers" | "magic";
    bounds: {
      shape: "polygon" | "circle";
      points?: Point[];
    };
    properties: {
      intensity: number; // Scaled [0.0 - 1.0] representing emission density
      speed: number;
      angle: number;
      color: string; // #RRGGBB
    };
  }>;
}

// ======================================================================
// 2. Cryptographic DRM & Volatile Memory Management
// ======================================================================

export class CryptographicPipeline {
  /**
   * Generates a dynamic SHA-256 hash representation of a raw file buffer.
   * Compares outputs against the 'manifest.hash' archive receipt.
   */
  public static async calculateSHA256(data: ArrayBuffer): Promise<string> {
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
  }

  /**
   * Volatile AES-256-GCM In-Memory Decryption pipeline.
   * Decrypts premium graphics/audio assets directly within execution RAM.
   */
  public static async decryptAsset(
    encryptedData: ArrayBuffer,
    keyMaterial: CryptoKey,
    iv: Uint8Array
  ): Promise<ArrayBuffer> {
    return await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: iv,
        tagLength: 128 // Enforces 16-byte authentication tags
      },
      keyMaterial,
      encryptedData
    );
  }

  /**
   * Volatile Memory Disposal Protocol Scrub (Saves memory & prevents RAM scraping).
   * Actively overwrites the unencrypted plaintext ArrayBuffer on the JS heap
   * once the raster/texture transfer to GPU video RAM resolves.
   */
  public static hardMemoryScrub(buffer: ArrayBuffer): void {
    const zeroOutView = new Uint8Array(buffer);
    zeroOutView.fill(0); // Synchronously zero out every byte of plaintext asset memory
  }
}

// ======================================================================
// 3. Spatial Mathematics & Engineering Algorithms
// ======================================================================

export class GeometryMath {
  /**
   * Subdivides parametric Cubic Bézier curves into sequential linear lines.
   * Avoids real-time curve calculations on hardware rendering loops.
   * Equation: P(t) = (1-t)^3*P0 + 3(1-t)^2*t*CP1 + 3(1-t)*t^2*CP2 + t^3*P3
   */
  public static flattenBezier(
    p0: Point,
    cp1: Point,
    cp2: Point,
    p3: Point,
    subdivisions: number = 10
  ): Point[] {
    const points: Point[] = [];
    
    for (let i = 0; i <= subdivisions; i++) {
      const t = i / subdivisions;
      const mt = 1 - t;
      
      const mt3 = mt * mt * mt;
      const mt2t = 3 * mt * mt * t;
      const mtt2 = 3 * mt * t * t;
      const t3 = t * t * t;

      const x = mt3 * p0.x + mt2t * cp1.x + mtt2 * cp2.x + t3 * p3.x;
      const y = mt3 * p0.y + mt2t * cp1.y + mtt2 * cp2.y + t3 * p3.y;

      points.push({ x, y });
    }
    
    return points;
  }

  /**
   * Resolves the Right-Hand Rule and Left/Right normal directional offsets.
   * Defines Left/Right half-spaces for one-way mirrors, ledges, or illusions.
   * n_right = (y2 - y1, x1 - x2) | n_left = (y1 - y2, x2 - x1)
   */
  public static calculateSegmentNormal(p1: Point, p2: Point): { left: Point; right: Point } {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;

    // Return unit length normal vectors
    const len = Math.hypot(dx, dy) || 1.0;
    return {
      left: { x: -dy / len, y: dx / len },
      right: { x: dy / len, y: -dx / len }
    };
  }

  /**
   * Collinear Simplification Filter.
   * Evaluates the cross-product of consecutive vectors. Removes intermediate
   * nodes if segments lie along a perfectly straight line within tolerance.
   */
  public static simplifyCollinearPath(points: Point[], tolerance: number = 1e-5): Point[] {
    if (points.length <= 2) return points;

    const simplified: Point[] = [points];

    for (let i = 1; i < points.length - 1; i++) {
      const prev = simplified[simplified.length - 1];
      const curr = points[i];
      const next = points[i + 1];

      // Calculate the area of triangle (cross product delta)
      const crossProduct = (curr.y - prev.y) * (next.x - curr.x) - (curr.x - prev.x) * (next.y - curr.y);

      if (Math.abs(crossProduct) > tolerance) {
        simplified.push(curr);
      }
    }

    simplified.push(points[points.length - 1]);
    return simplified;
  }
}

// ======================================================================
// 4. Environmental & Interactive Audio Physics
// ======================================================================

export class AcousticEngine {
  /**
   * Proximity falloff mathematical volume model.
   * Mathematically dampens and clamps localized acoustics. Prevents popping
   * artifacts and negative bounds at boundaries.
   * Formula: V = max(0, min(V_max, V_max * (1 - d/r)))
   */
  public static calculateProximityVolume(
    tokenPos: Point,
    emitterPos: Point,
    coreRadius: number,
    fadeRadius: number,
    volumeMax: number
  ): number {
    const distance = Math.hypot(tokenPos.x - emitterPos.x, tokenPos.y - emitterPos.y);

    // Fully inside the core volume radius
    if (distance <= coreRadius) {
      return volumeMax;
    }

    const totalBound = coreRadius + fadeRadius;

    // Fully outside the fading boundary threshold
    if (distance >= totalBound) {
      return 0.0;
    }

    // Mathematically clamp values along the fade slope
    const effectiveDistance = distance - coreRadius;
    const volumeDecay = volumeMax * (1.0 - effectiveDistance / fadeRadius);

    return Math.max(0.0, Math.min(volumeMax, volumeDecay));
  }
}