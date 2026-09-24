/**
 * seed_revocations.js
 * Programmatic seeding utility for the UVTT v2 DRM Revocation Cloudflare KV Namespace.
 * Generates bulk JSON payloads conforming to Cloudflare's Bulk KV Import format.
 *
 * Usage:
 *   node seed_revocations.js
 *   wrangler kv:bulk put bulk_revocations.json --binding=DRM_REVOCATIONS_KV
 */

const fs = require('fs');
const crypto = require('crypto');

// Sample list of refunded or fraudulent transaction IDs to revoke
const rawRefundedTransactions = [
  "TX-98234-A78B",
  "TX-10492-C92D",
  "TX-88301-M10X",
  "TX-55412-Z88K",
  "TX-31902-L14P"
];

function generateKvPayload() {
  console.log("[*] Initializing UVTT v2 DRM Revocation Seeder...");
  
  const bulkPayload = rawRefundedTransactions.map(txId => {
    // We store the keys as SHA-256 hashes of the Transaction IDs (or order hashes) 
    // to preserve player privacy at the edge.
    const txHash = crypto.createHash('sha256').update(txId).digest('hex');
    
    return {
      key: `revocation:${txHash}`,
      value: JSON.stringify({
        revoked: true,
        reason: "Refund Processed",
        timestamp: new Date().toISOString()
      })
    };
  });

  const outputFilename = 'bulk_revocations.json';
  fs.writeFileSync(outputFilename, JSON.stringify(bulkPayload, null, 2));
  
  console.log(`[+] SUCCESS: Generated bulk KV payload for ${bulkPayload.length} transactions.`);
  console.log(`    Saved to: ${outputFilename}`);
  console.log(`\nTo import this into your Cloudflare environment, run:`);
  console.log(`    wrangler kv:bulk put ${outputFilename} --binding=DRM_REVOCATIONS_KV`);
}

generateKvPayload();
