/**
 * UVTT v2 ZKS Server-Side Revocation List Manager
 * 
 * An administrative CLI tool to manage the privacy-preserving SHA-256 transaction revocation registry
 * stored inside Cloudflare Workers KV.
 * 
 * Features:
 *   1. Hash Raw Transaction IDs (SHA-256) to maintain customer/player privacy.
 *   2. Generate Bulk JSON files for Cloudflare KV import.
 *   3. Direct Edge integration recipes using wrangler CLI wrappers.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// Helper: Compute SHA-256 Hash of a string (preserves privacy at the edge)
function hashTransaction(txId) {
    if (!txId) return '';
    return crypto.createHash('sha256').update(txId.trim()).digest('hex');
}

// Command execution helper to print help documentation
function printHelp() {
    console.log(`
\x1b[1;34m======================================================================\x1b[0m
\x1b[1m         ZKS Edge Clearinghouse Revocation Registry Manager           \x1b[0m
\x1b[1;34m======================================================================\x1b[0m
Usage:
  node manage_revocations.js <command> [arguments]

Commands:
  \x1b[32mhash <tx_id>\x1b[0m
    Hash a single transaction ID into its privacy-preserving SHA-256 representation.

  \x1b[32madd <tx_id> <reason>\x1b[0m
    Hash and stage a single revoked transaction ID with metadata in the local registry.

  \x1b[32mcompile\x1b[0m
    Compile all staged local revocations into a Cloudflare KV bulk upload JSON format.

  \x1b[32mpush\x1b[0m
    Generate and print the shell commands needed to execute wrangler bulk push to the edge.

Local Registry Path: ./local_revocations.json
    `);
}

// File Paths
const REGISTRY_FILE = path.join(process.cwd(), 'local_revocations.json');

// Initialize local JSON database if missing
function loadRegistry() {
    if (!fs.existsSync(REGISTRY_FILE)) {
        return { revocations: [] };
    }
    try {
        const data = fs.readFileSync(REGISTRY_FILE, 'utf8');
        return JSON.parse(data);
    } catch (err) {
        console.error(`\x1b[31m[ERROR] Failed to load local registry: ${err.message}\x1b[0m`);
        return { revocations: [] };
    }
}

function saveRegistry(registry) {
    try {
        fs.writeFileSync(REGISTRY_FILE, JSON.stringify(registry, null, 2), 'utf8');
    } catch (err) {
        console.error(`\x1b[31m[ERROR] Failed to save local registry: ${err.message}\x1b[0m`);
    }
}

// Main logic routing
const args = process.argv.slice(2);
const command = args[0];

if (!command) {
    printHelp();
    process.exit(0);
}

switch (command) {
    case 'hash': {
        const txId = args[1];
        if (!txId) {
            console.error('\x1b[31m[ERROR] Missing transaction ID argument. Usage: node manage_revocations.js hash <tx_id>\x1b[0m');
            process.exit(1);
        }
        const hash = hashTransaction(txId);
        console.log(`\n\x1b[1mOriginal Transaction ID:\x1b[0m ${txId}`);
        console.log(`\x1b[1mPrivacy-Preserving Hash:\x1b[0m \x1b[32m${hash}\x1b[0m\n`);
        break;
    }

    case 'add': {
        const txId = args[1];
        const reason = args[2] || 'No reason provided';
        if (!txId) {
            console.error('\x1b[31m[ERROR] Missing transaction ID argument. Usage: node manage_revocations.js add <tx_id> "<reason>"\x1b[0m');
            process.exit(1);
        }

        const hash = hashTransaction(txId);
        const registry = loadRegistry();

        // Check if already revoked
        const exists = registry.revocations.some(r => r.hash === hash);
        if (exists) {
            console.log(`\x1b[33m[INFO] Transaction is already registered as revoked: ${hash}\x1b[0m`);
            process.exit(0);
        }

        registry.revocations.push({
            tx_id_raw_preview: txId.substring(0, 4) + '***' + txId.substring(txId.length - 4), // Store preview only for debugging
            hash: hash,
            revoked_at: new Date().toISOString(),
            reason: reason
        });

        saveRegistry(registry);
        console.log(`\x1b[32m[SUCCESS] Staged revocation for transaction ID. Hash: ${hash}\x1b[0m`);
        break;
    }

    case 'compile': {
        const registry = loadRegistry();
        if (registry.revocations.length === 0) {
            console.log('\x1b[33m[WARNING] Local registry is empty. Add revocations first.\x1b[0m');
            process.exit(0);
        }

        // Format for Cloudflare KV bulk upload: Array of { key: string, value: string }
        const bulkPayload = registry.revocations.map(r => ({
            key: `revocation:${r.hash}`,
            value: JSON.stringify({
                revoked_at: r.revoked_at,
                reason: r.reason
            })
        }));

        const outPath = path.join(process.cwd(), 'bulk_revocations.json');
        fs.writeFileSync(outPath, JSON.stringify(bulkPayload, null, 2), 'utf8');
        console.log(`\x1b[32m[SUCCESS] Compiled ${bulkPayload.length} bulk records to: ${outPath}\x1b[0m`);
        break;
    }

    case 'push': {
        console.log(`
\x1b[1;34m======================================================================\x1b[0m
\x1b[1m           Cloudflare Edge Revocation Sync Execution Guide            \x1b[0m
\x1b[1;34m======================================================================\x1b[0m

To deploy the compiled revocation list to your live serverless database,
execute these terminal commands in your workspace root:

\x1b[1;33m1. Compile the payload to bulk format:\x1b[0m
   node manage_revocations.js compile

\x1b[1;33m2. Publish the data to the Production KV Namespace:\x1b[0m
   npx wrangler kv:bulk put bulk_revocations.json --binding=DRM_REVOCATIONS_KV

\x1b[1;33m3. (Optional) Publish the data to the Local Preview KV Namespace:\x1b[0m
   npx wrangler kv:bulk put bulk_revocations.json --binding=DRM_REVOCATIONS_KV --preview
        `);
        break;
    }

    default:
        console.error(`\x1b[31m[ERROR] Unknown command: ${command}\x1b[0m`);
        printHelp();
        process.exit(1);
}
