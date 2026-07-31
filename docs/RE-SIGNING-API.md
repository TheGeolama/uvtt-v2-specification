# UVTT v2 Re-Signing & Watermarking API Blueprint

## 1. Introduction

While the standard UVTT v2 dual-file encryption system (`.uvtt2z` and `.uvtt2k`) provides robust security against casual theft, advanced storefronts require a method to track bad actors who purchase a campaign, decrypt it, and distribute the unlocked files.

The **Re-Signing API** solves this by dynamically unpacking a master campaign, injecting a cryptographic watermark tied to the purchaser's identity, and re-encrypting the archive on the fly before delivery.

---

## 2. The Re-Signing Workflow (Traitor Tracing)

When a storefront implements the Re-Signing API, the distribution model shifts from static to dynamic:

1. **Master Vaulting:** The storefront holds a "Master" `.uvtt2z` and its associated Master Key in a highly secure, private S3 bucket.
2. **Purchase Trigger:** User `JaneDoe123` purchases the campaign.
3. **Dynamic Decryption:** The backend temporarily decrypts the Master Archive in RAM.
4. **Watermark Injection:** The API modifies the internal `manifest.json` to include a hidden `license` block containing the user's ID, a timestamp, and a cryptographic signature. (Advanced implementations may also utilize steganography on the `.webp` assets).
5. **Re-Encryption (The Re-Sign):** The API re-encrypts the modified archive using a **brand-new, unique AES-256-GCM key** generated exclusively for `JaneDoe123`.
6. **Delivery:** The user receives a personalized `.uvtt2z` and their unique `.uvtt2k` key.

If `JaneDoe123` strips the encryption and uploads the raw files to a piracy site, the creator can download the pirated files, check the `manifest.json`, and instantly identify the leaker.

---

## 3. API Handshake Structure

This endpoint is intended for server-to-server communication (e.g., between a storefront's web frontend and a dedicated Rust or Go-based cryptographic backend worker).

### 3.1 The Re-Sign Request

The storefront commands the worker to generate a personalized payload.

    POST /api/v1/crypto/re-sign
    Authorization: Bearer <Internal_Service_Token>
    Content-Type: application/json

    {
      "master_product_id": "uvtt-master-8899",
      "licensee": {
        "user_id": "usr_998877",
        "username": "JaneDoe123",
        "transaction_id": "tx_abc123"
      }
    }

### 3.2 The Watermarked `manifest.json`

During the process, the worker injects this block into the archive's internal `manifest.json`:

    "license": {
      "issued_to": "usr_998877",
      "transaction": "tx_abc123",
      "signature": "a1b2c3d4e5f6...[SHA-256 Hash]...0f9e8d7c"
    }

### 3.3 The Response

The worker completes the encryption and returns temporary, pre-signed download URLs for the user's unique files.

    {
      "status": "success",
      "delivery": {
        "payload_url": "https://cdn.store.com/downloads/temp/usr_998877_campaign.uvtt2z?token=xyz",
        "key_url": "https://cdn.store.com/downloads/temp/usr_998877_campaign.uvtt2k?token=xyz",
        "expires_in": 3600
      }
    }

---

## 4. Performance & Infrastructure Considerations

Re-encrypting a 500MB `.uvtt2z` file is CPU-intensive. Storefront developers must not execute this process on their main web-serving thread.

- **Asynchronous Workers:** The Re-Signing API should be deployed as a background queue (e.g., AWS SQS triggering a Lambda function, or a dedicated Go worker pool).
- **Streaming Encryption:** To prevent RAM exhaustion, the cryptographic worker must use chunked streaming (reading the master file, injecting the watermark, encrypting the chunk, and writing to the output stream simultaneously). Do not attempt to hold a 1GB campaign entirely in memory during the re-sign process.
