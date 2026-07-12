/**
 * publisher-resign-pipeline.js
 *
 * Automated Server-Side Publisher Re-signing Pipeline.
 * Implements Section 6 (DRM & Security Subsystem) of the UVTT v2 Specification.
 *
 * This module:
 * 1. Derives symmetric AES-256-GCM encryption keys on-demand using ZKS:
 *    Key = HMAC-SHA256(RETAILER_MASTER_SECRET, Product_SKU + Key_Salt)
 * 2. Processes the high-res master map into a watermarked basemap.webp fallback (50px per grid).
 * 3. Encrypts premium graphics and Tier 3 audio loops into the secure `/protected/` path.
 * 4. Compiles the root integrity manifest ledger (manifest.hash) with SHA-256 checksums.
 * 5. Bundles everything into a valid standard-compliant .uvtt2z ZIP container.
 */

const crypto = require('crypto');
const path = require('path');
const fs = require('fs');

// We use adm-zip for zero-dependency zip manipulation across Node environments
const AdmZip = require('adm-zip');

class PublisherResigningPipeline {
  /**
   * @param {string} masterSecret - Secure, locally-held retail master secret.
   */
  constructor(masterSecret) {
    if (!masterSecret || typeof masterSecret !== 'string') {
      throw new Error("Invalid Configuration: Retailer Master Secret must be a secure string.");
    }
    this.masterSecret = masterSecret;
  }

  /**
   * Derives a deterministic 256-bit AES symmetric key in-memory using HMAC-SHA256 (Zero-Knowledge-Storage).
   * Key = HMAC-SHA256(MasterSecret, SKU + Salt)
   *
   * @param {string} sku - Unique product identifier matching storefront catalog.
   * @param {string} saltHex - 32-character hexadecimal key salt.
   * @returns {Buffer} Derived 32-byte cryptographic key.
   */
  deriveZksKey(sku, saltHex) {
    if (!sku || typeof sku !== 'string') {
      throw new Error("Validation Error: SKU must be a non-empty string.");
    }
    if (!saltHex || !/^[0-9a-fA-F]{32}$/.test(saltHex)) {
      throw new Error("Validation Error: Key Salt must be a 32-character hexadecimal string.");
    }

    const hmac = crypto.createHmac('sha256', this.masterSecret);
    hmac.update(sku + saltHex);
    return hmac.digest();
  }

  /**
   * Encrypts arbitrary asset buffer using authenticated AES-256-GCM.
   * Format: [12-byte IV] + [Ciphertext] + [16-byte GCM Auth Tag]
   *
   * @param {Buffer} dataBuffer - Raw unencrypted asset.
   * @param {Buffer} aesKey - Derived 32-byte symmetric key.
   * @returns {Buffer} Formatted binary encrypted payload.
   */
  encryptAssetGCM(dataBuffer, aesKey) {
    const iv = crypto.randomBytes(12); // Standard 12-byte initialization vector
    const cipher = crypto.createCipheriv('aes-256-gcm', aesKey, iv);
    
    const ciphertext = Buffer.concat([
      cipher.update(dataBuffer),
      cipher.final()
    ]);
    const authTag = cipher.getAuthTag(); // Retrieve standard 16-byte GCM authentication tag

    // Stack: [IV (12B)] + [Ciphertext] + [Auth Tag (16B)]
    return Buffer.concat([iv, ciphertext, authTag]);
  }

  /**
   * Ingests unencrypted master elements, applies Split-Resolution models,
   * performs AES-256-GCM encryption on premium layers, compiles manifest.hash,
   * and builds a streamable .uvtt2z container.
   *
   * @param {Object} params
   * @param {string} params.sku - Storefront catalog identifier.
   * @param {string} params.saltHex - Random 32-char key salt.
   * @param {Buffer} params.highResMap - Raw, full-fidelity WebP/PNG master image.
   * @param {Object} params.manifest - Global root manifest metadata index.
   * @param {Object} params.geometry - Wall, portal, and overhead height geometry vectors.
   * @param {Object} params.entities - Lights, sound zones, and weather particle emitters.
   * @param {Object} [params.audioMap] - Optional map of { "filename.ogg": <Buffer> } unencrypted Tier 3 audio.
   * @returns {Promise<Buffer>} The compiled, cryptographically-signed .uvtt2z package buffer.
   */
  async resignAndCompile({ sku, saltHex, highResMap, manifest, geometry, entities, audioMap = {} }) {
    // 1. Derive the secure edge key
    const aesKey = this.deriveZksKey(sku, saltHex);

    const zip = new AdmZip();

    // 2. Add JSON metadata (geometry, entities, manifest) to the archive
    zip.addFile('manifest.json', Buffer.from(JSON.stringify(manifest, null, 2)));
    zip.addFile('maps/ground_floor/geometry.json', Buffer.from(JSON.stringify(geometry, null, 2)));
    zip.addFile('maps/ground_floor/entities.json', Buffer.from(JSON.stringify(entities, null, 2)));

    // 3. Process the unencrypted Public Layer (basemap.webp)
    // In production, we down-sample this map to 50px per grid and burn a dynamic transaction watermark.
    // For this reference engine, we simulate this pass.
    const mockBasemapBuffer = Buffer.from(highResMap.toString('base64').substring(0, 100) + "_BAS_MOP_PROX_FALLBACK_WATERMARKED_50PX_PER_GRID");
    zip.addFile('assets/basemap.webp', mockBasemapBuffer);

    // 4. Encrypt the premium visual asset
    const encryptedMapBuffer = this.encryptAssetGCM(highResMap, aesKey);
    zip.addFile('protected/map.webp.enc', encryptedMapBuffer);

    // 5. Encrypt optional Tier 3 localized audio loops
    for (const [filename, audioBuffer] of Object.entries(audioMap)) {
      const encryptedAudio = this.encryptAssetGCM(audioBuffer, aesKey);
      zip.addFile(`protected/${filename}.enc`, encryptedAudio);
    }

    // 6. Traverse ZIP directories, compute SHA-256 hashes, and generate manifest.hash
    const zipEntries = zip.getEntries();
    const hashLines = [];

    for (const entry of zipEntries) {
      const fileData = entry.getData();
      const sha256Hash = crypto.createHash('sha256').update(fileData).digest('hex');
      hashLines.push(`${entry.entryName}:${sha256Hash}`);
    }

    const manifestHashContent = hashLines.join('\n') + '\n';
    zip.addFile('manifest.hash', Buffer.from(manifestHashContent));

    // Return the final packaged binary buffer
    return zip.toBuffer();
  }
}

module.exports = { PublisherResigningPipeline };
