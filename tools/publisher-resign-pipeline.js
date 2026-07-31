/**
 * publisher-resign-pipeline.js
 *
 * Automated Server-Side Publisher Re-signing Pipeline.
 * Implements the UVTT v2 Storefront Dynamic Re-signing standard.
 *
 * This module:
 * 1. Derives a random, unique AES-256-GCM encryption key on-demand for the buyer.
 * 2. Injects a cryptographic watermark and user license into manifest.json.
 * 3. Encrypts premium graphics and Tier 3 audio loops into the secure `/protected/` path.
 * 4. Compiles the root integrity manifest ledger (manifest.hash) with SHA-256 checksums.
 * 5. Returns the encrypted `.uvtt2z` binary package and the raw `.uvtt2k` string for storefront delivery.
 */

const crypto = require('crypto');
const path = require('path');
const fs = require('fs');

// We use adm-zip for zero-dependency zip manipulation across Node environments
const AdmZip = require('adm-zip');

class PublisherResigningPipeline {
  constructor() {
    // Pipeline is now stateless; AES keys are generated dynamically per transaction.
  }

  /**
   * Encrypts arbitrary asset buffer using authenticated AES-256-GCM.
   * Format: [12-byte IV] + [Ciphertext] + [16-byte GCM Auth Tag]
   *
   * @param {Buffer} dataBuffer - Raw unencrypted asset.
   * @param {Buffer} aesKey - Randomly generated 32-byte symmetric key.
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
   * Ingests unencrypted master elements, applies watermarks, performs AES-256-GCM encryption
   * on premium layers, compiles manifest.hash, and builds a dual-file container payload.
   *
   * @param {Object} params
   * @param {string} params.userId - Storefront purchaser ID for watermarking.
   * @param {string} params.transactionId - Storefront transaction receipt ID.
   * @param {Buffer} params.highResMap - Raw, full-fidelity WebP/PNG master image.
   * @param {Object} params.manifest - Global root manifest metadata index.
   * @param {Object} params.geometry - Wall, portal, and overhead height geometry vectors.
   * @param {Object} params.entities - Lights, sound zones, and weather particle emitters.
   * @param {Object} [params.audioMap] - Optional map of { "filename.ogg": <Buffer> } unencrypted Tier 3 audio.
   * @returns {Promise<Object>} Object containing { packageBuffer (the .uvtt2z), keyString (the .uvtt2k) }
   */
  async resignAndCompile({ userId, transactionId, highResMap, manifest, geometry, entities, audioMap = {} }) {
    // 1. Generate a brand new, unique AES-256 key for this transaction
    const aesKey = crypto.randomBytes(32);
    const keyStringHex = aesKey.toString('hex');

    const zip = new AdmZip();

    // 2. Inject Watermark License into the Manifest
    const timestamp = new Date().toISOString();
    const signatureMaterial = `${userId}:${transactionId}:${timestamp}`;
    const signatureHash = crypto.createHash('sha256').update(signatureMaterial).digest('hex');

    const localizedManifest = { ...manifest };
    localizedManifest.license = `Watermarked | Issued to: ${userId} | TX: ${transactionId} | SIG: ${signatureHash}`;

    // 3. Add JSON metadata (geometry, entities, manifest) to the archive
    zip.addFile('manifest.json', Buffer.from(JSON.stringify(localizedManifest, null, 2)));
    zip.addFile('maps/ground_floor/geometry.json', Buffer.from(JSON.stringify(geometry, null, 2)));
    zip.addFile('maps/ground_floor/entities.json', Buffer.from(JSON.stringify(entities, null, 2)));

    // 4. Process the unencrypted Public Layer (basemap.webp)
    const mockBasemapBuffer = Buffer.from(highResMap.toString('base64').substring(0, 100) + `_BAS_MOP_WATERMARK_ID_${userId}_TX_${transactionId}`);
    zip.addFile('assets/basemap.webp', mockBasemapBuffer);

    // 5. Encrypt the premium visual asset
    const encryptedMapBuffer = this.encryptAssetGCM(highResMap, aesKey);
    zip.addFile('protected/map.webp.enc', encryptedMapBuffer);

    // 6. Encrypt optional Tier 3 localized audio loops
    for (const [filename, audioBuffer] of Object.entries(audioMap)) {
      const encryptedAudio = this.encryptAssetGCM(audioBuffer, aesKey);
      zip.addFile(`protected/${filename}.enc`, encryptedAudio);
    }

    // 7. Traverse ZIP directories, compute SHA-256 hashes, and generate manifest.hash
    const zipEntries = zip.getEntries();
    const hashLines = [];

    for (const entry of zipEntries) {
      const fileData = entry.getData();
      const sha256Hash = crypto.createHash('sha256').update(fileData).digest('hex');
      hashLines.push(`${entry.entryName}:${sha256Hash}`);
    }

    const manifestHashContent = hashLines.join('\n') + '\n';
    zip.addFile('manifest.hash', Buffer.from(manifestHashContent));

    // Return the final packaged binary buffer and the hex key string
    return {
      packageBuffer: zip.toBuffer(),
      keyStringHex: keyStringHex
    };
  }
}

module.exports = { PublisherResigningPipeline };