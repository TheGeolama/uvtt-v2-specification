# 🛡️ Security Policy

## Supported Versions

Only the active release branch of the **Universal Virtual Tabletop v2 (UVTT v2) Specification** and the **UVTT v2 Upgrader Web App** are actively monitored for security vulnerabilities. 

| Version | Supported |
| ------- | --------- |
| v2.0.x  | ✅ Yes    |
| v1.x.x  | ❌ No     |

Legacy V1 files (`.dd2vtt`, `.df2vtt`) do not implement cryptographic signatures or zero-knowledge access controls and are fundamentally considered insecure. All platforms are strongly urged to migrate to the UVTT v2 standard to protect creator assets.

---

## Reporting a Vulnerability

We take the security of TTRPG creators, digital artists, and platform developers extremely seriously. If you discover a security vulnerability, **please do not open a public GitHub issue.** Instead, report it through one of the following secure channels:

1. **GitHub Private Vulnerability Reporting:** Navigate to the **Security** tab of the repository on GitHub and click **"Report a vulnerability"**.
2. **Encrypted Security Email:** Send an encrypted email to `security@universalvtt.org` using our PGP key (available on major keyservers).

Please include the following information in your report:
* A detailed description of the vulnerability.
* A proof-of-concept (PoC) payload, script, or step-by-step instructions to reproduce.
* The potential impact (e.g., unauthorized asset decryption, signature bypass, denial of service).
* Any details regarding your operating environment (browser, hardware pipeline, VTT platform).

---

## 🔒 High-Priority Target Areas

The UVTT v2 specification implements several security-sensitive boundaries. Security researchers should focus their audits particularly on these sub-systems:

### 1. Zero-Knowledge-Storage (ZKS) Clearinghouse
The ZKS Clearinghouse acts as the decentralized edge authorization plane (running on Cloudflare Workers and KV storage) to resolve decryption keys for premium assets without exposing raw credentials.
* **Threat Vectors:** Key leakage, bypass of token verification, unauthorized access to the revocation registry, database injection in seed/revocation management scripts, or side-channel timing attacks during authorization handshakes.

### 2. Cryptographic Web Crypto Asset Signing & Integrity
The split-resolution architecture relies on the browser's native **Web Crypto API** to compute SHA-256 digests for all files inside the `assets/` directory (compiled inside `manifest.hash`).
* **Threat Vectors:** Bypass of signature verification, SHA-256 preimage/collision attacks allowing silent swapping of premium graphic/audio files with malicious binaries, or tampering with the zipped package geometry structures without invalidating the manifest hash.

### 3. Parser & Decryption Runtime Vulnerabilities
The Go reference parser (`uvtt2_parser.go`) and TypeScript reference parser (`uvtt2-parser.ts`) implement AES-GCM decryption for secure asset bundles.
* **Threat Vectors:** Replay attacks, IV reuse (nonce reuse) in AES-GCM decryption, heap/buffer overflows in Go parsing, prototype pollution in TypeScript, or memory leakage of raw decrypted assets in WebGPU texture memory (failure of the volatile memory scrubbing cycles).

---

## Our Disclosure Process

We adhere to standard coordinated vulnerability disclosure (CVD) practices:

1. **Acknowledgement:** We will acknowledge receipt of your report within **48 hours** and assign a primary security coordinator.
2. **Triage & Validation:** We will investigate and attempt to reproduce the issue. We aim to complete triage and provide a status update within **7 days**.
3. **Remediation:** If validated, we will work on a patch. Our goal is to release a security update within **30 days** of validation.
4. **Advisory:** We will publish a Security Advisory (GHSA / CVE) detailing the vulnerability, crediting you for the discovery (if desired), and providing upgrade instructions for downstream platforms.

---

## 🛡️ Safe Harbor

Any research conducted in good faith under this policy is protected by our Safe Harbor agreement. We will not pursue legal action or encourage third parties to pursue legal action against researchers who:
* Do not exploit the vulnerability beyond what is strictly necessary to prove its existence.
* Do not compromise, view, or modify user data or premium creator assets.
* Provide us a reasonable period to address the issue before making any public disclosure (90-day standard).
* Comply with all local, state, and federal laws during their research.
