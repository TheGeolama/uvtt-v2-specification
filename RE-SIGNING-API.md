# UVTT v2 Storefront Re-Signing API Specification
**Version:** 2.0.0-rc2  
**Standard:** Universal VTT v2 (UVTT v2) DRM & Security Subsystem  
**License:** Public Domain / Creative Commons CC0 1.0 Universal  

---

## 1. Architectural Overview & Data Flow

To support the **Split-Resolution Encryption Model** without vendor lock-in, online digital marketplaces (e.g., DriveThruRPG, Patreon, or custom storefronts) must deploy an automated server-side **Publisher Re-signing API**. 

This API intercepts raw unencrypted master map packages uploaded by cartographers, dynamically processes them, derives unique cryptographic keys using a **Zero-Knowledge-Storage (ZKS) model**, encrypts full-fidelity raster graphics and audio assets, generates a tamper-proof integrity receipt (`manifest.hash`), and outputs a standard-compliant, streamable `.uvtt2z` campaign archive.

```mermaid
graph TD
    A[Publisher / Cartographer] -->|Uploads Raw Master Map .zip / .uvtt2| B[(Storefront Database)]
    B -->|Stores Raw WebP, JSON Layout, SKU ID| C[Re-signing API Ingestion]
    
    C -->|Split-Resolution Processing| D["Down-sample base map to 50px/grd<br>and burn order/SKU watermark"]
    C -->|ZKS Key Derivation| E["Derive encryption key via<br>HMAC-SHA256 in volatile RAM"]
    
    E --> F["Encrypt high-res maps and<br>audio assets via AES-256-GCM<br>under /protected/"]
    
    D --> G["Compile directories, generate<br>SHA-256 hash list (manifest.hash)"]
    F --> G
    
    G -->|Packages into final .uvtt2z| H[End-User Client VTT / GoVTT]

    %% Color Styling for Visual Polish %%
    style A fill:#f1f5f9,stroke:#64748b,stroke-width:2px,color:#1e293b
    style B fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1
    style C fill:#f3e8ff,stroke:#7e22ce,stroke-width:2px,color:#6b21a8
    style D fill:#fee2e2,stroke:#b91c1c,stroke-width:2px,color:#991b1b
    style E fill:#fff7ed,stroke:#c2410c,stroke-width:2px,color:#9a3412
    style F fill:#fff7ed,stroke:#c2410c,stroke-width:2px,color:#9a3412
    style G fill:#dcfce7,stroke:#15803d,stroke-width:2px,color:#166534
    style H fill:#f1f5f9,stroke:#64748b,stroke-width:2px,color:#1e293b
```

---

## 2. OpenAPI 3.0.3 Contract

This API contract standardizes the secure endpoint structure used by digital storefront backends to dynamically re-sign and compile protected map packages during customer checkouts.

```yaml
openapi: 3.0.3
info:
  title: UVTT v2 Automated Storefront Re-signing API
  version: 2.0.0-rc2
  description: >
    Automated backend pipeline to ingest raw cartography assets, execute the 
    Split-Resolution Encryption Model, dynamically generate cryptographic manifest receipts,
    and output secure, streamable .uvtt2z campaign packages.
paths:
  /v1/publisher/resign:
    post:
      summary: Re-sign and Package a UVTT v2 Campaign Archive
      description: >
        Ingests unencrypted master metadata (manifest, geometry, entities), processes the raw 
        graphics into a low-resolution watermarked fallback, encrypts the full-fidelity assets 
        using AES-256-GCM, compiles the manifest.hash integrity receipt, and bundles them into 
        a standard-compliant ZIP stream.
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - product_sku
                - transaction_id
                - manifest_json
                - geometry_json
                - entities_json
                - master_map_image
              properties:
                product_sku:
                  type: string
                  description: The unique product identifier matching the storefront store catalog.
                  example: "SKU-90218-PTOLUS"
                transaction_id:
                  type: string
                  description: The unique transaction ID associated with the customer's purchase.
                  example: "TX-7719302-XYZ"
                manifest_json:
                  type: string
                  format: binary
                  description: The global campaign metadata index JSON file (manifest.json).
                geometry_json:
                  type: string
                  format: binary
                  description: The static vector, height-aware geometry JSON file (geometry.json).
                entities_json:
                  type: string
                  format: binary
                  description: The interactive entities, lighting, weather, and audio JSON file (entities.json).
                master_map_image:
                  type: string
                  format: binary
                  description: The raw, high-resolution full-fidelity WebP or PNG source map image.
                audio_loops:
                  type: array
                  items:
                    type: string
                    format: binary
                  description: Optional Tier 3 localized audio loops or ambient tracks to package under the protected layer.
      responses:
        '200':
          description: A perfectly compiled, cryptographically-signed binary .uvtt2z archive.
          headers:
            Content-Disposition:
              schema:
                type: string
                example: 'attachment; filename="SKU-90218-PTOLUS.uvtt2z"'
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary
        '400':
          description: Malformed payload parameters or missing required coordinate parameters.
          content:
            application/json:
              schema:
                type: object
                properties:
                  error_code:
                    type: string
                    example: "INVALID_METADATA_SCHEMA"
                  message:
                    type: string
                    example: "Topology Error: Map entities file defines multiple default landing zones."
        '500':
          description: Internal cryptographic or image-processing server failure.
          content:
            application/json:
              schema:
                type: object
                properties:
                  error_code:
                    type: string
                    example: "CRYPTOGRAPHIC_PIPELINE_ERROR"
                  message:
                    type: string
                    example: "Failed to initialize secure hardware acceleration context for WebCrypto."
```

---

## 3. Core Security & Cryptographic Compliance Mandates

To remain strictly compliant with the **UVTT v2 DRM Subsystem Specification**, storefront implementations of this API blueprint must enforce the following three engineering mandates:

### 3.1. Zero-Knowledge-Storage (ZKS) Key Derivation
The storefront server **must never** store the derived decryption keys in a database. Instead, the symmetric encryption key is calculated entirely in volatile, temporary CPU memory on-demand using standard HMAC-SHA256 calculations based on a secure, locally-held master secret:

$$K_{\text{derive}} = \text{HMAC-SHA256}(S_{\text{master}}, \text{SKU} + \text{Salt})$$

This derived key is then used to initialize the `AES-256-GCM` encryption cipher. The key itself is instantly flushed from the server's heap memory once the compression stream finishes, eliminating database-compromise vulnerabilities.

### 3.2. Split-Resolution Processing
The API must dynamically scale down and watermark the high-resolution source map to compile the unencrypted public fallback image:
*   **Grid Calibration:** The pipeline must parse `geometry.json` to extract scale boundaries.
*   **Resolution Cap:** The unencrypted **`basemap.webp`** must be dynamically scaled down to **exactly 50 pixels per grid square** (calculating the ratio dynamically from the geometry scale).
*   **Visible Watermarking:** A semi-transparent watermark containing a rotated transaction hash (e.g., `TX-7719302-XYZ`) must be burned directly into the raw pixels of `basemap.webp` during the export pass, rendering the fallback useless for high-quality printing or unauthorized redistribution.

### 3.3. Root Archive Integrity Signatures (`manifest.hash`)
To block any post-export vector manipulation, script injection, or malicious payload alterations, the API must generate a root validation receipt:
*   Immediately following the compression of all files, the API iterates through the ZIP archive, computing the SHA-256 hash of every individual file.
*   These mappings are written into a flat, newline-separated text file named **`manifest.hash`** at the root of the archive:

```text
manifest.json:77752e7989cb4f59a1adb421547d132f...
maps/ground_floor/geometry.json:adce97f1edae4b55b43815ade4a8a59f...
maps/ground_floor/entities.json:d6835abe4a2949e293896fd4a7048626...
assets/basemap.webp:c680ed6e981c49f79dfc88e9a5587703...
protected/map.webp.enc:cd399708853b5a9422dba17dbbfcd72d...
```

*   When a client VTT attempts to import the resulting `.uvtt2z` file, it calculates local checksums and asserts they match this receipt exactly before executing any vector coordinates, securing the platform from code injection exploits.
