# UVTT v2 Storefront & Distribution Blueprint

## 1. Introduction

The UVTT v2 ecosystem was built from the ground up to protect creator content. By utilizing AES-256-GCM encryption, the standard allows creators to distribute massive, multi-floor campaigns securely.

This blueprint outlines how digital storefronts, Patreon creators, and automated API systems should handle the distribution of premium UVTT v2 assets.

---

## 2. The Dual-File Distribution Model

When a premium campaign is exported from an authoring tool (like the Desktop Pro Upgrader), it generates two files:

1. **The Payload (`campaign.uvtt2z`):** A large, encrypted ZIP container containing all the high-resolution media and geometry.
2. **The Key (`campaign.uvtt2k`):** A microscopic text file containing the symmetric decryption key.

**The Golden Rule of V2 Distribution:** The Payload is cheap and public; the Key is premium and private.

---

## 3. Tier 1: Platform Distribution (Patreon, Discord, Ko-fi)

For independent creators relying on subscription platforms, you do not need to build a custom API. You simply split the files across your subscription tiers.

- **Public / Free Tier:** Post the heavy `.uvtt2z` Payload file publicly. Because it is encrypted, it acts as a secure, unplayable teaser. It can be mirrored, shared, and torrented without compromising your intellectual property.
- **Premium / Subscriber Tier:** Attach the tiny `.uvtt2k` Key file to a locked, patron-only post.

When your subscribers want to play, they download both files and load them into their VTT. If their subscription lapses, they keep what they paid for, but they cannot unlock new payloads without the new keys.

---

## 4. Tier 2: Automated Storefronts (DriveThruRPG, Custom Sites)

For dedicated VTT storefronts, the dual-file system massively reduces server bandwidth costs.

Because the `.uvtt2z` Payload is encrypted, it does not require an authenticated download pipeline. You can host these massive files on cheap, edge-cached public CDNs (like Cloudflare or AWS CloudFront).

### The Storefront Workflow

1. **Asset Hosting:** Storefront hosts `campaign.uvtt2z` on a public CDN bucket.
2. **Key Vaulting:** Storefront securely vaults the `campaign.uvtt2k` string in a private database, mapped to the product ID.
3. **User Purchase:** User buys the campaign.
4. **Delivery:** \* The storefront redirects the user to download the Payload directly from the cheap public CDN.
   - The storefront serves the `.uvtt2k` Key file exclusively through an authenticated, rate-limited user dashboard.

---

## 5. Tier 3: Advanced API & Dynamic Key Resolution

For seamless integration, VTT platforms (like Foundry or Roll20) can implement dynamic key resolution to save users from manually downloading and managing `.uvtt2k` files.

### The Handshake Architecture

A VTT platform can ping a Storefront API to fetch a user's keys automatically.

**1. OAuth Authorization:**
The user links their Storefront account to their VTT client via standard OAuth 2.0.

**2. Key Request (VTT -> Storefront):**
When the user imports a `campaign.uvtt2z` file, the VTT reads the manifest to identify the Storefront ID, then sends a request:

    POST /api/v1/vault/resolve-key
    Authorization: Bearer <User_OAuth_Token>
    Content-Type: application/json

    {
      "product_id": "uvtt-prod-8899",
      "vtt_client_id": "foundry-vtt-client"
    }

**3. Verification & Response (Storefront -> VTT):**
The storefront verifies the user owns the product and returns the key stream securely:

    {
      "status": "success",
      "key_stream": "e4b3c2a1...[hex string]...9f8d7e6c"
    }

**4. Volatile Injection:**
The VTT injects this key directly into its Web Crypto API or Service Worker to decrypt the map in RAM, bypassing the physical `.uvtt2k` file entirely.

---

## 6. Security Constraints for Developers

- **Never cache decrypted assets:** VTTs and storefronts must never write decrypted `.webp` or `.json` files to a user's permanent storage. Decryption must happen dynamically in volatile RAM.
- **Key Rotation:** If a creator's key is compromised, they must re-export a new `.uvtt2z` payload with a new key. Because the encryption is symmetric AES-256-GCM, keys cannot be retroactively revoked on existing payloads.
