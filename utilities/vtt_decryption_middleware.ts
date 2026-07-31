/**
 * UVTT v2 - Standard VTT-side Decryption Middleware
 * 
 * Demonstrates how client-side VTT engines can parse the AES-GCM encrypted assets (like .webp maps),
 * extract the initialization vector (IV), perform hardware-accelerated decryption via W3C Web Crypto
 * using a raw hex string from a `.uvtt2k` key file, and instantiate a secure Blob URL for immediate render injection.
 */

export interface DecryptionOptions {
  keyHex: string;          // 256-bit AES key as a hex string (from a .uvtt2k file or Storefront API)
  encryptedBuffer: ArrayBuffer; // Raw binary of the encrypted asset
  mimeType?: string;       // Default is "image/webp"
}

/**
 * Helper: Converts a hex string to an ArrayBuffer
 */
function hexToBuffer(hex: string): Uint8Array {
  const cleanHex = hex.replace(/^0x/i, "");
  if (cleanHex.length % 2 !== 0) {
    throw new Error("Invalid hex string length for key conversion.");
  }
  const view = new Uint8Array(cleanHex.length / 2);
  for (let i = 0; i < view.length; i++) {
    view[i] = parseInt(cleanHex.substring(i * 2, i * 2 + 2), 16);
  }
  return view;
}

/**
 * Standard VTT Decryption Middleware: Decrypts raw AES-GCM asset data
 * and compiles a temporary Blob URL that can be assigned to standard HTML <img> tags.
 */
export async function decryptAssetToBlobUrl(options: DecryptionOptions): Promise<string> {
  const { keyHex, encryptedBuffer, mimeType = "image/webp" } = options;

  if (!window?.crypto?.subtle) {
    throw new Error("SubtleCrypto API is not supported in this secure context (HTTPS/localhost required).");
  }

  // 1. Validate file payload dimensions. AES-GCM requires minimum 12 bytes IV + 16 bytes Auth Tag + Ciphertext.
  if (encryptedBuffer.byteLength < 28) {
    throw new Error("Ciphertext payload is truncated or invalid.");
  }

  // 2. Extract the 12-byte Initialization Vector (Nonce/IV) prefixed at the beginning of the file
  const iv = new Uint8Array(encryptedBuffer, 0, 12);

  // 3. Extract the remaining ciphertext (which includes the trailing 16-byte GCM authentication tag)
  const ciphertext = new Uint8Array(encryptedBuffer, 12);

  try {
    // 4. Import the raw hex key into a SubtleCrypto CryptoKey object for AES-GCM decryption
    const rawKeyBytes = hexToBuffer(keyHex);
    const cryptoKey = await window.crypto.subtle.importKey(
      "raw",
      rawKeyBytes,
      { name: "AES-GCM" },
      false, // Key remains non-extractable in memory for security
      ["decrypt"]
    );

    // 5. Execute hardware-accelerated decryption and integrity authentication
    const decryptedBuffer = await window.crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: iv,
        tagLength: 128 // 128-bit authentication tag is standard
      },
      cryptoKey,
      ciphertext
    );

    // 6. Instantiate a memory-safe binary Blob from the decrypted buffer
    const decryptedBlob = new Blob([decryptedBuffer], { type: mimeType });

    // 7. Generate a local Object URL to immediately stream into map layout engines
    const blobUrl = URL.createObjectURL(decryptedBlob);
    console.log(`[✔] Cryptographic verification complete. Compiled secure asset Blob URL: ${blobUrl}`);
    
    // Volatile Memory Scrubbing
    rawKeyBytes.fill(0);
    
    return blobUrl;

  } catch (error) {
    console.error("[-] DRM Authentication Failure: Corrupted payload or unauthorized decryption key.");
    throw error;
  }
}

/**
 * ============================================================================
 * COMPLEMENTARY MIDDLEWARE: WebGL/WebGPU High-Performance Decryption Pipeline
 * ============================================================================
 * 
 * Optimized specifically for real-time graphics pipelines. Instead of generating a heavy,
 * DOM-dependent Blob URL, this middleware compiles the decrypted bytes directly into an
 * ImageBitmap. This avoids main-thread decoding lag and loads textures directly to WebGPU/WebGL
 * coordinate space, implementing memory scrubbing techniques to prevent GPU memory bloat.
 */

export interface WebGpuTextureLoaderOptions {
  keyHex: string;
  encryptedBuffer: ArrayBuffer;
}

export interface WebGpuTexturePayload {
  imageBitmap: ImageBitmap;
  width: number;
  height: number;
  cleanup: () => void; // Call this once texture is committed to GPU memory to avoid memory leaks
}

/**
 * WebGL/WebGPU Decryption Middleware: Extracts, decrypts, and decodes binary graphics data
 * directly into an offscreen ImageBitmap ready for GPU texture upload.
 */
export async function decryptAssetToGpuTexture(options: WebGpuTextureLoaderOptions): Promise<WebGpuTexturePayload> {
  const { keyHex, encryptedBuffer } = options;

  if (!window?.crypto?.subtle) {
    throw new Error("SubtleCrypto API is not supported in this secure context.");
  }

  // 1. Extract 12-byte IV and ciphertext
  const iv = new Uint8Array(encryptedBuffer, 0, 12);
  const ciphertext = new Uint8Array(encryptedBuffer, 12);

  try {
    // 2. Import raw symmetric key
    const rawKeyBytes = hexToBuffer(keyHex);
    const cryptoKey = await window.crypto.subtle.importKey(
      "raw",
      rawKeyBytes,
      { name: "AES-GCM" },
      false,
      ["decrypt"]
    );

    // 3. Decrypt ciphertext payload
    const decryptedBuffer = await window.crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: iv,
        tagLength: 128
      },
      cryptoKey,
      ciphertext
    );

    // 4. Instantly compile raw decrypted buffer to Blob
    const decryptedBlob = new Blob([decryptedBuffer], { type: "image/webp" });

    // 5. Decode the image off-thread into an ImageBitmap.
    // This shifts WebP rasterization and decompression completely off the main thread.
    const imageBitmap = await createImageBitmap(decryptedBlob);

    // 6. Construct structured payload with explicit garbage-collection (volatile memory scrubbing) hooks
    const payload: WebGpuTexturePayload = {
      imageBitmap: imageBitmap,
      width: imageBitmap.width,
      height: imageBitmap.height,
      cleanup: () => {
        // Volatile memory scrubbing: aggressively close the ImageBitmap to free hardware resources
        imageBitmap.close();
        console.log("[✔] Volatile memory scrubbing: Released decrypted offscreen ImageBitmap from host memory.");
      }
    };

    // Clean up temporary key bytes
    rawKeyBytes.fill(0);

    console.log(`[✔] Decrypted asset rasterized off-thread: ${payload.width}x${payload.height}px.`);
    return payload;

  } catch (error) {
    console.error("[-] GPU Texture Decryption Failure:", error);
    throw error;
  }
}