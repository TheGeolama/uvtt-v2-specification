# Universal VTT v2: VTT Graphics & Shader Cookbook

## High-Performance WebGPU/WebGL2 Rendering, Physics Engines, and Acoustic Occlusion

**Format Version:** 2.0.0  
**Target Audience:** Virtual Tabletop Developers, Graphics Engineers, and Front-End Viewport Authors

---

### 🏛️ Executive Summary

The **Universal Virtual Tabletop v2 (UVTT v2)** specification establishes an advanced, hardware-accelerated viewport standard targeting modern GPU rendering frameworks (WebGPU and WebGL2).

Implementing these features requires translating raw JSON parameters into optimized shaders, math models, and physics controllers. This cookbook provides production-ready shader structures, physics algorithms, and math recipes for 3D lighting, localized acoustics, and GPU weather particle systems.

---

### 💡 1. 3D Illumination Shader Recipes

UVTT v2 supports point and directional light sources positioned in 3D coordinate space $(X, Y, Z)$. The graphics engine must calculate realistic physical falloff decay, directional sector boundaries, and dynamic flicker animations.

```text
       Point Light source with 3D Z-elevation offset
                     * (X_light, Y_light, Z_light)
                    /|
                   / |
                  /  | Vector distance (d) in 3D space
                 /   |
                /    |
               /     |
              /______|_
             (X_token, Y_token, Z_token = 0)
```

#### A. The Math Model: Inverse-Square 3D Decay

The distance ($d$) between a 3D light node and a token on the 2D floor grid includes the light's height elevation ($Z_{\text{light}}$):

$$d = \sqrt{(x_{\text{token}} - x_{\text{light}})^2 + (y_{\text{token}} - y_{\text{light}})^2 + (z_{\text{token}} - z_{\text{light}})^2}$$

The physical intensity ($I$) at the target point uses the inverse-square decay formula:

$$I = \frac{I_0}{d^2}$$

#### B. WebGPU (WGSL) Fragment Shader for Point Light

This WGSL fragment shader calculates dynamic lighting values, incorporating inverse-square decay, directional arc boundaries, and flicker noise:

```wgsl
struct LightProperties {
    position: vec3<f32>,
    color: vec3<f32>,
    bright_radius: f32,
    dim_radius: f32,
    decay_type: u32,       // 1 = linear, 2 = inverse_square
    cone_rotation: f32,    // Degrees (0 to 360)
    cone_arc: f32,         // Degrees (0 to 360)
    flicker_noise: f32     // Dynamic variance calculated on CPU
};

@fragment
fn fs_main(@location(0) token_pos: vec3<f32>, @builtin(position) coord: vec4<f32>) -> @location(0) vec4<f32> {
    let light = LightProperties(
        vec3<f32>(15.0, 12.0, 6.5),
        vec3<f32>(0.97, 0.45, 0.08),
        15.0, 30.0, 2, 180.0, 120.0, 0.85
    );

    // 1. Calculate 3D Euclidean distance
    let diff = token_pos - light.position;
    let dist = length(diff);

    if (dist > light.dim_radius) {
        discard; // Out of bounds
    }

    // 2. Directional cone clipping (For directional lights)
    if (light.cone_arc < 360.0) {
        let dir = normalize(diff.xy);
        let cone_rad = radians(light.cone_rotation);
        let center_dir = vec2<f32>(cos(cone_rad), sin(cone_rad));

        let cos_angle = dot(dir, center_dir);
        let half_arc_rad = radians(light.cone_arc * 0.5);

        if (cos_angle < cos(half_arc_rad)) {
            discard; // Outside of light beam cone
        }
    }

    // 3. Compute Decay Intensity
    var intensity = 1.0;
    if (light.decay_type == 2u) {
        // Physical inverse square: I = I0 / d^2
        let d_clamped = max(dist, 1.0); // Prevent divide-by-zero
        intensity = 1.0 / (d_clamped * d_clamped);
    } else {
        // Linear: Fades evenly from bright_radius to dim_radius
        if (dist > light.bright_radius) {
            let range = light.dim_radius - light.bright_radius;
            intensity = 1.0 - ((dist - light.bright_radius) / range);
        }
    }

    // Apply CPU-derived flicker noise to mimic flickering flames
    let final_color = light.color * intensity * light.flicker_noise;
    return vec4<f32>(final_color, 1.0);
}
```

---

### 🔊 2. Acoustic Raycasting & Volume Occlusion Math

Localized sound zones (like a crackling hearth or a dripping water fountain) fade naturally as tokens move away. Furthermore, sound is blocked by solid geometry, which we resolve through raycasting.

```text
   [ LISTENER TOKEN ] ───────── Raycast Intersect ─────────► [ ACOUSTIC SOURCE ]
                                      │
                                ┌─────┴─────┐
                                │   WALL    │  ◄── Apply wall.muffling_factor
                                └───────────┘
```

#### A. Acoustic Clamping Formula

Proximity sound volume decay must be mathematically clamped to prevent volume overflows or negative coefficients:

$$V = \max\left(0, \min\left(V_{\text{max}}, V_{\text{max}} \times \left(1 - \frac{d}{r}\right)\right)\right)$$

Where $V$ represents the resulting output playback volume, $V_{\text{max}}$ is the maximum volume cap, $d$ is the shortest Euclidean distance to the sound zone boundary, and $r$ represents the outer `fade_radius`. If $d \ge r$, then $V = 0.0$.

#### B. Volume Muffling Raycast Intersection

If `muffled_by_geometry` is set to `true`, the VTT engine must execute an intersection test between the listener token $T(x_t, y_t)$ and the audio emitter source $S(x_s, y_s)$:

1.  **Ray Equation:** Define the sound path as a line segment $L(t) = T + t(S - T)$ where $t \in [0, 1]$.
2.  **Wall Intersections:** Check if $L(t)$ intersects any standard wall or closed door segment $W$ defined in `geometry.json` (drawn from $P_0$ to $P_1$):
    $$x_w(u) = P_0.x + u(P_1.x - P_0.x), \quad y_w(u) = P_0.y + u(P_1.y - P_0.y) \quad \text{where} \quad u \in [0, 1]$$
3.  **The Intersection Formula:** Solve for $t$ and $u$:
    $$t = \frac{(P_0.x - T.x)(P_0.y - P_1.y) - (P_0.y - T.y)(P_0.x - P_1.x)}{(S.x - T.x)(P_0.y - P_1.y) - (S.y - T.y)(P_0.x - P_1.x)}$$
    $$u = \frac{(S.x - T.x)(P_0.y - T.y) - (S.y - T.y)(P_0.x - T.x)}{(S.x - T.x)(P_0.y - P_1.y) - (S.y - T.y)(P_0.x - P_1.x)}$$
4.  **Muffling Application:** If an intersection exists ($0 \le t \le 1$ and $0 \le u \le 1$), the path is blocked. Apply the wall's `audio_muffling` scalar (typically `0.4` for hollow doors, or `0.8` for solid stone walls) to dynamically decrease volume:
    $$V_{\text{final}} = V \times (1.0 - \text{muffling\_factor})$$

---

### ☁️ 3. GPU Weather Particle Systems

Weather emitters (rain, snow, fog, embers) are simulated on the GPU to maximize rendering frame rates. Emitters can inherit global wind vectors and sort particle depth over overhead roof layers.

#### A. Fluid Dynamics: Wind-Vector Inheritance

The final velocity vector ($\vec{v}_{\text{particle}}$) of a particle is calculated by scaling the base velocity against the global wind vector defined inside the `extensions.environment` block of `manifest.json`:

$$\vec{v}_{\text{particle}} = \vec{v}_{\text{emitter\_base}} + \left(\text{influence\_scale} \times \vec{v}_{\text{global\_wind}}\right)$$

#### B. WebGPU (WGSL) Vertex Shader for Weather Particles

This WGSL vertex shader computes particle motion, blending global wind inheritance, and clamping particle height boundaries:

```wgsl
struct Particle {
    position: vec3<f32>,
    velocity: vec2<f32>,
    lifetime: f32,
    max_lifetime: f32
};

struct GlobalUniforms {
    global_wind: vec2<f32>,
    time: f32,
    frame_delta: f32
};

@group(0) @binding(0) var<uniform> uniforms: GlobalUniforms;
@group(0) @binding(1) var<storage, read_write> particles: array<Particle>;

@compute @workgroup_size(64)
fn cs_animate_weather(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let index = global_id.x;
    var p = particles[index];

    if (p.lifetime >= p.max_lifetime) {
        // Reset/Respawn particle at top emitter height boundary plane
        p.position = vec3<f32>(spawn_random_xy(), 40.0); // Z-Top = 40.0
        p.lifetime = 0.0;
    } else {
        // 1. Calculate final velocity with global wind vector inheritance
        let influence_scale = 1.2;
        let wind_offset = uniforms.global_wind * influence_scale;
        let final_velocity = p.velocity + wind_offset;

        // 2. Update position using frame delta time
        p.position.x += final_velocity.x * uniforms.frame_delta;
        p.position.y += final_velocity.y * uniforms.frame_delta;
        p.position.z -= 9.8 * uniforms.frame_delta; // Gravity drift along Z-axis

        // 3. Evaluate Ground Termination collision check
        let z_bottom = 0.0;
        if (p.position.z <= z_bottom) {
            // Trigger impact splash and schedule particle reset
            p.lifetime = p.max_lifetime;
        }

        p.lifetime += uniforms.frame_delta;
    }

    particles[index] = p;
}
```

#### C. GPU Depth-Sorting Layers (`render_layer`)

To ensure weather graphics blend cleanly with roofs and overhead canopies, developers must implement the following canvas sorting rules based on the emitter's `render_layer` enum:

1.  **`"above_overhead"`**: Render the weather viewport buffer at the absolute top of the GPU render stack (Z-Index $\ge 1000$). Weather remains visible over roof layers, regardless of opacity.
2.  **`"below_overhead"`**: Render the weather buffer underneath the roof canopies. If a descending weather particle intersects an active roof boundary defined in `geometry.json`'s `overhead` array, evaluate the roof's current opacity. If the roof is visible, apply an alpha mask of `0.0` to the weather particle's fragment shader, preventing rain from bleeding through ceilings.
3.  **`"ground_level"`**: Render weather particles directly on the baseline canvas under tokens and props (Z-Index $\approx 10$), allowing effects like ground mist or lava embers to float beneath the feet of character tokens.
