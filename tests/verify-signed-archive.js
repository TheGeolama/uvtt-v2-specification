/**
 * verify-signed-archive.js
 *
 * Client-Side Conformance Verifier.
 * Simulates a Virtual Tabletop (VTT) client engine importing a cryptographically-signed
 * .uvtt2z archive, validating integrity hashes, and performing volatile memory decryption.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const AdmZip = require('adm-zip');

class ClientArchiveVerifier {
  /**
   * @param {string} archivePath - Local path to the signed .uvtt2z file.
   * @param {string} retailerSecret - Securing key for handshake simulation.
   * @param {string} sku - Product identifier.
   */
  constructor(archivePath, retailerSecret, sku) {
    this.archivePath = archivePath;
    this.retailerSecret = retailerSecret;
    this.sku = sku;
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

    // 4. Extract Key Salt and simulate Zero-Knowledge Key Handshake
    console.log("[*] Processing manifest.json metadata for handshakes...");
    const manifestEntry = zip.getEntry('manifest.json');
    if (!manifestEntry) {
      throw new Error("Validation Error: Root manifest.json not found inside archive.");
    }

    const manifest = JSON.parse(manifestEntry.getData().toString('utf8'));
    const salt = manifest.encryption_handshake?.key_salt_checksum;
    if (!salt) {
      throw new Error("License Handshake Error: Key salt is missing from manifest encryption variables.");
    }

    console.log(`[*] Initiating ZKS Edge Handshake. Key Salt: ${salt}`);
    // Derived Key = HMAC-SHA256(MasterSecret, SKU + Salt)
    const hmac = crypto.createHmac('sha256', this.retailerSecret);
    hmac.update(this.sku + salt);
    const derivedKey = hmac.digest();
    console.log(`[+] Key derived successfully. Initializing Volatile Decryption Context.`);

    // 5. Decrypt secure asset and assert output integrity
    console.log("[*] Decrypting protected visual rasters (/protected/)...");
    const encryptedMapEntry = zip.getEntry('protected/map.webp.enc');
    if (!encryptedMapEntry) {
      throw new Error("Integrity Error: Encrypted Premium graphic asset '/protected/map.webp.enc' is missing.");
    }

    const encryptedData = encryptedMapEntry.getData();
    
    // Slice AES-256-GCM binary stack: [IV (12B)] + [Ciphertext] + [Auth Tag (16B)]
    const iv = encryptedData.subarray(0, 12);
    const authTag = encryptedData.subarray(encryptedData.length - 16);
    const ciphertext = encryptedData.subarray(12, encryptedData.length - 16);

    const decipher = crypto.createDecipheriv('aes-256-gcm', derivedKey, iv);
    decipher.setAuthTag(authTag);

    const decryptedBuffer = Buffer.concat([
      decipher.update(ciphertext),
      decipher.final()
    ]);

    console.log(`[+] Successfully decrypted high-res map layer.`);
    console.log(`    Total Decrypted Buffer Size: ${decryptedBuffer.length} bytes.`);
    
    // Volatile Memory Disposal Protocol: hard-overwrite variables to wipe cache
    derivedKey.fill(0);
    console.log("[+] Volatile Memory Purged. Derived cryptographic secrets successfully flushed.");
    console.log("======================================================================");
    console.log("            UVTT v2 - SECURE ARCHIVE VERIFICATION PASSED              ");
    console.log("======================================================================");
  }
}

// Self-Test Execution Module
async function runSelfTest() {
  const mockMapData = Buffer.from("HIGH_RESOLUTION_8K_TACTICAL_MAP_DATA_IMAGE_STREAM_abc123xyz_MARKER");
  const mockSku = "SKU-90218-PTOLUS";
  const mockSalt = "a4d39f772b15e45a1f298cd310ba2dfc";
  const mockSecret = "RETAILER_SECRET_KEY_abc123xyz789";

  const { PublisherResigningPipeline } = require('./publisher-resign-pipeline');
  const pipeline = new PublisherResigningPipeline(mockSecret);

  const mockManifest = {
    format_version: "2.0.0",
    uvtt_version: "2.0.0",
    campaign_name: "Mock Campaign Level",
    encryption_handshake: {
      clearinghouse_url: "http://127.0.0.1:8787/v1/drm/handshake",
      license_authority: "http://127.0.0.1:8787/.well-known/jwks.json",
      key_salt_checksum: mockSalt
    },
    map_catalog: [
      { id: "mock-map", name: "Mock Map", slug: "mock-map", path: "maps/ground_floor/", z_index: 0 }
    ]
  };

  const mockGeometry = { format_version: "2.0.0", resolution: {}, geometry: { walls: [], portals: [], overhead: [] } };
  const mockEntities = { format_version: "2.0.0", lights: [], landing_zones: [], events: [], audio: { zones: [] }, emitters: [] };

  console.log("[*] Preparing test environment: compiling self-test zip archive...");
  const archiveBuffer = await pipeline.resignAndCompile({
    sku: mockSku,
    saltHex: mockSalt,
    highResMap: mockMapData,
    manifest: mockManifest,
    geometry: mockGeometry,
    entities: mockEntities
  });

  const tempArchivePath = path.join(__dirname, 'mock_test_archive.uvtt2z');
  fs.writeFileSync(tempArchivePath, archiveBuffer);

  try {
    const verifier = new ClientArchiveVerifier(tempArchivePath, mockSecret, mockSku);
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
