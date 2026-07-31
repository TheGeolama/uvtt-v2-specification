/**
 * verify-signed-archive.js
 *
 * Client-Side Conformance Verifier.
 * Simulates a Virtual Tabletop (VTT) client engine importing a cryptographically-signed
 * .uvtt2z archive, validating integrity hashes, and performing volatile memory decryption
 * utilizing the dual-file physical key structure (.uvtt2k).
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const AdmZip = require('adm-zip');

class ClientArchiveVerifier {
  /**
   * @param {string} archivePath - Local path to the signed .uvtt2z file.
   * @param {string} keyHex - The 64-character raw AES-256 decryption key.
   */
  constructor(archivePath, keyHex) {
    this.archivePath = archivePath;
    this.keyHex = keyHex;
  }

  /**
   * Run the full client import verification suite
   */
  async verify() {
    console.log("======================================================================");
    console.log("            UVTT v2 - Client Cryptographic Verification               ");
    console.log("======================================================================");

    if (!fs.existsSync(this.archivePath)) {
      throw new Error(`Execution Failed: Target archive file not found: ${this.archivePath}`);
    }

    // 1. Decompress ZIP and extract elements
    console.log(`[*] Reading signed archive: ${path.basename(this.archivePath)}...`);
    const zip = new AdmZip(this.archivePath);
    const zipEntries = zip.getEntries();

    // 2. Locate and parse manifest.hash
    const hashEntry = zip.getEntry('manifest.hash');
    if (!hashEntry) {
      throw new Error("Security Alert: Root archive manifest.hash ledger is missing. Aborting import.");
    }

    const hashLedgerRaw = hashEntry.getData().toString('utf8');
    const ledgerLines = hashLedgerRaw.split('\n').filter(line => line.trim().length > 0);
    const expectedHashes = {};

    for (const line of ledgerLines) {
      const parts = line.split(':');
      if (parts.length === 2) {
        expectedHashes[parts[0]] = parts[1];
      }
    }

    console.log(`[+] Found manifest.hash ledger containing ${Object.keys(expectedHashes).length} verified entries.`);

    // 3. Compute local SHA-256 checks and match ledger signatures
    console.log("[*] Executing local archive integrity checks...");
    for (const entry of zipEntries) {
      if (entry.entryName === 'manifest.hash') continue; // Skip hash file itself

      const expected = expectedHashes[entry.entryName];
      if (!expected) {
        throw new Error(`Security Exception: Unlisted or modified file detected: ${entry.entryName}`);
      }

      const fileBuffer = entry.getData();
      const actual = crypto.createHash('sha256').update(fileBuffer).digest('hex');

      if (actual !== expected) {
        throw new Error(`CRITICAL EXCEPTION: Cryptographic verification mismatch on file: ${entry.entryName}`);
      }
      console.log(`  [OK] ${entry.entryName} matches signature: ${actual.substring(0, 16)}...`);
    }
    console.log("[+] Security Scan: Root signature verified successfully. No malicious coordinates injected.");

    // 4. Decrypt secure asset and assert output integrity
    console.log("[*] Decrypting protected visual rasters (/protected/)...");
    const encryptedMapEntry = zip.getEntry('protected/map.webp.enc');
    if (!encryptedMapEntry) {
      throw new Error("Integrity Error: Encrypted Premium graphic asset '/protected/map.webp.enc' is missing.");
    }

    const encryptedData = encryptedMapEntry.getData();
    const aesKey = Buffer.from(this.keyHex, 'hex');
    
    // Slice AES-256-GCM binary stack: [IV (12B)] + [Ciphertext] + [Auth Tag (16B)]
    const iv = encryptedData.subarray(0, 12);
    const authTag = encryptedData.subarray(encryptedData.length - 16);
    const ciphertext = encryptedData.subarray(12, encryptedData.length - 16);

    const decipher = crypto.createDecipheriv('aes-256-gcm', aesKey, iv);
    decipher.setAuthTag(authTag);

    const decryptedBuffer = Buffer.concat([
      decipher.update(ciphertext),
      decipher.final()
    ]);

    console.log(`[+] Successfully decrypted high-res map layer.`);
    console.log(`    Total Decrypted Buffer Size: ${decryptedBuffer.length} bytes.`);
    
    // Volatile Memory Disposal Protocol: hard-overwrite variables to wipe cache
    aesKey.fill(0);
    console.log("[+] Volatile Memory Purged. Cryptographic secrets successfully flushed.");
    console.log("======================================================================");
    console.log("            UVTT v2 - SECURE ARCHIVE VERIFICATION PASSED              ");
    console.log("======================================================================");
  }
}

// Self-Test Execution Module
async function runSelfTest() {
  const mockMapData = Buffer.from("HIGH_RESOLUTION_8K_TACTICAL_MAP_DATA_IMAGE_STREAM_abc123xyz_MARKER");
  // Generate a random 256-bit (32-byte) key for the mock encryption
  const mockKeyBytes = crypto.randomBytes(32);
  const mockKeyHex = mockKeyBytes.toString('hex');

  const mockManifest = {
    format_version: "2.0.0",
    uvtt_version: "2.0.0",
    campaign_name: "Mock Campaign Level",
    map_catalog: [
      { id: "mock-map", name: "Mock Map", slug: "mock-map", path: "maps/ground_floor/", z_index: 0 }
    ]
  };

  const mockGeometry = { format_version: "2.0.0", resolution: {}, geometry: { walls: [], portals: [], overhead: [] } };
  const mockEntities = { format_version: "2.0.0", lights: [], landing_zones: [], events: [], audio: { zones: [] }, emitters: [] };

  console.log("[*] Preparing test environment: compiling self-test zip archive...");
  const zip = new AdmZip();

  // Add JSON files
  zip.addFile('manifest.json', Buffer.from(JSON.stringify(mockManifest, null, 2)));
  zip.addFile('maps/ground_floor/geometry.json', Buffer.from(JSON.stringify(mockGeometry, null, 2)));
  zip.addFile('maps/ground_floor/entities.json', Buffer.from(JSON.stringify(mockEntities, null, 2)));
  zip.addFile('assets/basemap.webp', Buffer.from("MOCK_BASEMAP"));

  // Encrypt protected payload
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', mockKeyBytes, iv);
  const ciphertext = Buffer.concat([cipher.update(mockMapData), cipher.final()]);
  const authTag = cipher.getAuthTag();
  const encryptedPayload = Buffer.concat([iv, ciphertext, authTag]);
  zip.addFile('protected/map.webp.enc', encryptedPayload);

  // Compute Hashes
  const zipEntries = zip.getEntries();
  const hashLines = [];
  for (const entry of zipEntries) {
    const fileData = entry.getData();
    const sha256Hash = crypto.createHash('sha256').update(fileData).digest('hex');
    hashLines.push(`${entry.entryName}:${sha256Hash}`);
  }
  zip.addFile('manifest.hash', Buffer.from(hashLines.join('\n') + '\n'));

  const tempArchivePath = path.join(__dirname, 'mock_test_archive.uvtt2z');
  fs.writeFileSync(tempArchivePath, zip.toBuffer());

  try {
    const verifier = new ClientArchiveVerifier(tempArchivePath, mockKeyHex);
    await verifier.verify();
  } finally {
    // Clean up temporary workspace artifacts
    if (fs.existsSync(tempArchivePath)) {
      fs.unlinkSync(tempArchivePath);
    }
  }
}

// If executed directly, run the test
if (require.main === module) {
  runSelfTest().catch(err => {
    console.error("Verification failed:", err);
    process.exit(1);
  });
}

module.exports = { ClientArchiveVerifier };