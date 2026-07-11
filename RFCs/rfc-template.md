# RFC-[YYYY]-[MM]: [Your Feature Title]

## 1. Executive Summary
Provide a brief, 2-3 sentence high-level overview of the proposed feature, outlining what technical deficiency it solves and how it fits into the broader UVTT v2 system architecture.

## 2. Technical Motivation
Explain "The Problem" in detail. Why are current v2 standards insufficient? Document concrete rendering bottlenecks, data bloat issues, or interaction gaps in existing tabletop platforms that this feature addresses.

## 3. Detailed Specification & Schema Changes
Provide the exact mathematical definitions and JSON schema adjustments.

### 3.1 JSON Schema Additions
Specify exactly how `manifest.json`, `geometry.json`, or `entities.json` are modified:
```json
{
  "properties": {
    "__vendor_extensions": {
      "type": "object",
      "properties": {
        "example_property": { "type": "number" }
      }
    }
  }
}
```

### 3.2 Mathematical Modeling
Detail any physics equations, vectors, or attenuation curves. Ensure all formulas are fully rendered in standard LaTeX:
$$E = mc^2$$

## 4. Hardware Profile & Performance Impact
Evaluate how the feature performs on modern clients:
* Does this require dynamic GPU shader modifications or compute resources?
* What is the performance profile for WebGL2 vs WebGPU runtimes?
* Document the fallback mechanisms for lower-tier hardware profiles.

## 5. Backward Compatibility & Degradation
State clearly how legacy engines handle this change:
* Does this fit entirely inside the optional `extensions` block?
* How does the `UvttMigrationEngine` down-sample this feature when exporting back to legacy v1 formats?

## 6. Drawbacks & Alternatives Considered
What are the potential negative implications (e.g. increased memory footprint, network payloads, or parser complexity)? What alternative layouts did you reject, and why?
