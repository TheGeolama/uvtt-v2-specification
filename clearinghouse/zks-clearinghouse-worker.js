/**
 * zks-clearinghouse-worker.js
 *
 * Cloudflare Serverless Edge Worker.
 * Implements the Zero-Knowledge-Storage (ZKS) key clearinghouse standard
 * as defined in Section 6.3 of the UVTT v2 specification.
 *
 * It is completely stateless and derives symmetric keys in-memory on-demand,
 * eliminating database upkeep costs for publishers and cartographers.
 */

// We simulate Cloudflare's environment. In production, wrangler secrets are bound to 'global'.
const MOCK_RETAILER_MASTER_SECRET = "RETAILER_SECRET_KEY_abc123xyz789";

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

/**
 * Main request interceptor
 * @param {Request} request
 */
async function handleRequest(request) {
  const url = new URL(request.url);

  // Router for local handshakes
  if (url.pathname === '/v1/drm/handshake' && request.method === 'POST') {
    return handleHandshake(request);
  }

  // Graceful fallback for unknown paths
  return new Response(JSON.stringify({
    error: "NOT_FOUND",
    message: "Requested endpoint path is unhandled by the UVTT v2 Clearinghouse."
  }), {
    status: 404,
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * Processes the cryptographic license handshake
 * @param {Request} request
 */
async function handleHandshake(request) {
  const headers = new Headers({
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*' // Enable cross-origin calls for VTT web client instances
  });

  try {
    const body = await request.json();
    const { product_sku, key_salt_checksum, authorization_token } = body;

    // 1. Mandatory Input validation
    if (!product_sku || typeof product_sku !== 'string') {
      return new Response(JSON.stringify({
        error: "INVALID_PARAMETER",
        message: "The product_sku parameter is required and must be a string."
      }), { status: 400, headers });
    }

    if (!key_salt_checksum || !/^[0-9a-fA-F]{32}$/.test(key_salt_checksum)) {
      return new Response(JSON.stringify({
        error: "INVALID_SALT",
        message: "The key_salt_checksum parameter must be a 32-character hexadecimal string."
      }), { status: 400, headers });
    }

    if (!authorization_token || typeof authorization_token !== 'string') {
      return new Response(JSON.stringify({
        error: "UNAUTHORIZED",
        message: "A valid OAuth/JWT authorization_token is required to verify entitlements."
      }), { status: 401, headers });
    }

    // 2. JWT Signature & Expiry Audits (Simulated for zero-dependency edge runtimes)
    // In production, use standard subtle.crypto to import and verify public RSA/ECDSA JWKS keys.
    if (authorization_token.includes("expired")) {
      return new Response(JSON.stringify({
        error: "EXPIRED_TOKEN",
        message: "The provided authorization token has expired."
      }), { status: 401, headers });
    }

    if (authorization_token.includes("unauthorized_sku")) {
      return new Response(JSON.stringify({
        error: "INSUFFICIENT_ENTITLEMENTS",
        message: "Your customer account does not hold an active purchase entitlement for this SKU."
      }), { status: 403, headers });
    }

    // 3. Fraud / Revocation Ledger Check (Edge KV Store)
    // In production, we query wrangler bound KV namespace, e.g.: await REVOCATIONS.get(authorization_token)
    if (authorization_token.includes("revoked")) {
      return new Response(JSON.stringify({
        error: "LICENSE_REVOKED",
        message: "This license receipt has been revoked due to refund processing or security flag."
      }), { status: 403, headers });
    }

    // 4. Zero-Knowledge-Storage Key Derivation using WebCrypto API
    // Derived Key = HMAC-SHA256(MasterSecret, SKU + Salt)
    const encoder = new TextEncoder();
    const secretKeyData = encoder.encode(MOCK_RETAILER_MASTER_SECRET);
    const messageData = encoder.encode(product_sku + key_salt_checksum);

    // Import master secret raw bytes into subtle crypto HMAC object
    const hmacKey = await crypto.subtle.importKey(
      "raw",
      secretKeyData,
      { name: "HMAC", hash: { name: "SHA-256" } },
      false,
      ["sign"]
    );

    const signatureBuffer = await crypto.subtle.sign(
      "HMAC",
      hmacKey,
      messageData
    );

    // Convert Buffer to Hex String
    const derivedKeyHex = Array.from(new Uint8Array(signatureBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');

    // Clean up temporary variables from memory synchronously
    // (JavaScript VM handles garbage collection, but we keep our stack clean)
    
    return new Response(JSON.stringify({
      status: "SUCCESS",
      derived_key: derivedKeyHex,
      algorithm: "AES-256-GCM",
      expires_in: 3600 // Inform client key is transient and should expire in 1 hour
    }), { status: 200, headers });

  } catch (error) {
    return new Response(JSON.stringify({
      error: "INTERNAL_SERVER_ERROR",
      message: `An unexpected error occurred during edge key derivation: ${error.message}`
    }), { status: 500, headers });
  }
}
