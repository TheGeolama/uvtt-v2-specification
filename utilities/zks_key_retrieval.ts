/**
 * UVTT v2 - Zero-Knowledge-Storage (ZKS) Key Retrieval Utility (TypeScript Web Reference)
 * 
 * This module demonstrates how a modern browser-based client (such as a web-platform VTT client or 
 * web worker) can securely authenticate with the Cloudflare Worker ZKS Clearinghouse to retrieve 
 * symmetric decryption keys for premium map assets.
 * 
 * This client-side code utilizes the standard, hardware-accelerated W3C Web Crypto (SubtleCrypto) API 
 * to perform the HMAC-SHA256 signing operations entirely in-memory without external dependencies.
 */

export interface ZksKeyResponse {
  map_id: string;
  decryption_key: string;  // Hex or Base64 encoded symmetric AES key
  expires_at?: number;
  [key: string]: any;
}

export interface ZksRequestParams {
  clearinghouseUrl: string;
  mapId: string;
  licenseId: string;
  licenseSecret: string;
}

/**
 * Helper to convert an ArrayBuffer directly into a hexadecimal string.
 */
function bufferToHex(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  return Array.from(bytes)
    .map(byte => byte.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * Generates a cryptographically signed HMAC request to fetch an asset decryption key
 * natively in the browser or inside a Web Worker.
 * 
 * @param params Handshake credential and routing parameters.
 * @returns A promise resolving to the JSON response containing the decryption key.
 */
export async function fetchZksDecryptionKey(params: ZksRequestParams): Promise<ZksKeyResponse> {
  const { clearinghouseUrl, mapId, licenseId, licenseSecret } = params;

  if (!window?.crypto?.subtle) {
    throw new Error(
      "Crypto Error: W3C SubtleCrypto API is not supported in this environment. " +
      "Ensure the application is running over a secure connection (HTTPS) or localhost."
    );
  }

  const encoder = new TextEncoder();

  // 1. Generate transient anti-replay handshake values
  const timestamp = Math.floor(Date.now() / 1000); // POSIX timestamp in seconds
  
  // A cryptographically secure 16-byte random nonce converted to a hex string
  const nonceBytes = new Uint8Array(16);
  window.crypto.getRandomValues(nonceBytes);
  const nonce = bufferToHex(nonceBytes.buffer);

  // 2. Construct the message payload
  // Format: <map_id>:<license_id>:<timestamp>:<nonce>
  const messageString = `${mapId}:${licenseId}:${timestamp}:${nonce}`;
  const messageData = encoder.encode(messageString);

  try {
    // 3. Sign the message locally using W3C SubtleCrypto HMAC-SHA256
    const secretKeyData = encoder.encode(licenseSecret);

    // Import the raw license secret into a cryptographically secure KeyObject
    const cryptoKey = await window.crypto.subtle.importKey(
      "raw",
      secretKeyData,
      {
        name: "HMAC",
        hash: { name: "SHA-256" }
      },
      false, // Key is non-extractable for runtime safety
      ["sign"]
    );

    // Perform signing operation
    const signatureBuffer = await window.crypto.subtle.sign(
      "HMAC",
      cryptoKey,
      messageData
    );

    const signature = bufferToHex(signatureBuffer);

    // 4. Compile URL with secure tracking query parameters
    const baseUrl = clearinghouseUrl.replace(/\/$/, "");
    const targetUrl = new URL(`${baseUrl}/retrieve`);
    
    targetUrl.searchParams.set("map_id", mapId);
    targetUrl.searchParams.set("license_id", licenseId);
    targetUrl.searchParams.set("timestamp", timestamp.toString());
    targetUrl.searchParams.set("nonce", nonce);
    targetUrl.searchParams.set("signature", signature);

    console.log(`[*] Preparing SubtleCrypto request for Map ID: ${mapId}...`);
    console.log(`[*] Generated Nonce: ${nonce}`);
    console.log(`[*] Generated Timestamp: ${timestamp}`);
    console.log(`[*] Generated Signature: ${signature}`);

    // 5. Execute secure asynchronous fetch request
    const response = await fetch(targetUrl.toString(), {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "X-Client-Platform": "UVTT-v2-Web-Client/1.0"
      }
    });

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.error) {
          errorMessage = errorData.error;
        }
      } catch {
        const textError = await response.text();
        if (textError) errorMessage = textError;
      }
      throw new Error(`Clearinghouse rejected handshake: ${errorMessage}`);
    }

    const payload: ZksKeyResponse = await response.json();
    console.log("[+] Handshake successful. Decrypted response payload received.");
    return payload;

  } catch (error) {
    console.error("[-] ZKS Handshake failure:", error);
    throw error;
  }
}
