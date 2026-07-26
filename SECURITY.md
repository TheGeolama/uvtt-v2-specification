### 🛡️ Security Policy

#### Supported Versions
Only the active release branch of the **Universal Virtual Tabletop v2 (UVTT v2) Specification** and the **UVTT v2 Upgrader Web App** are actively monitored for security vulnerabilities.

| Version | Supported |
| ------ | ------ |
| v2.0.x | ✅ Yes |
| v1.x.x | ❌ No |

Legacy V1 files (.dd2vtt, .df2vtt) do not implement cryptographic signatures, hash index verifications, or secure zero-knowledge access controls and are fundamentally considered insecure. All platforms are strongly urged to migrate to the UVTT v2 standard to protect creator assets and secure user platforms [45].

---

#### Reporting a Vulnerability
We take the security of TTRPG creators, digital artists, and platform developers extremely seriously [46]. If you discover a security vulnerability, **please do not open a public GitHub issue [46].** Instead, report it through one of the following secure channels:

1.  **GitHub Private Vulnerability Reporting:** Navigate to the **Security** tab of the repository on GitHub and click **"Report a vulnerability"** [46].
2.  **Encrypted Security Email:** Send an encrypted email to security@universalvtt.org using our PGP key (available on major keyservers) [46].

Please include the following information in your report [47]:
*  A detailed description of the vulnerability [47].
*  A proof-of-concept (PoC) payload, script, or step-by-step instructions to reproduce [47].
*  The potential impact (e.g., unauthorized asset decryption, signature bypass, denial of service) [47].
*  Any details regarding your operating environment (browser, hardware pipeline, VTT platform) [47].

---

#### 🔒 High-Priority Target Areas
The UVTT v2 specification implements several security-sensitive boundaries [47]. Security researchers should focus their audits particularly on these sub-systems:

##### 1. Zero-Knowledge-Storage (ZKS) Clearinghouse & Revocations
The ZKS Clearinghouse acts as the decentralized edge authorization plane (running on Cloudflare Workers and KV storage) to resolve decryption keys deterministically for premium assets without exposing raw credentials database records [48].
*   **Threat Vectors:** Key leakage, bypass of token signatures, timing attacks during authorization handshakes, database injection in seed/revocation management scripts, or failure of the client-side background revocation sync protocol (failure to flush keys from native vaults and RAM when refunded) [48, 172].

##### 2. Cryptographic Asset Integrity (manifest.hash)
The integrity pipeline relies on the browser's native **Web Crypto API** or backend parsers to compute SHA-256 digests for all files packaged inside `.uvtt2z` or `.uvtt2k` containers, compiled inside the root `manifest.hash` text file [49].
*   **Threat Vectors:** Bypass of signature verification, SHA-256 preimage/collision attacks allowing silent swapping of vector triggers or asset files, or tampering with the container structure without invalidating the manifest hash index [49].

##### 3. Parser, Decryption, & Volatile Memory Runtimes
The Go reference parser and TypeScript reference parser implement AES-256-GCM decryption for secure `.uvtt2k` campaign archives [49, 84].
*   **Threat Vectors:** Initialization Vector (IV) / nonce reuse in AES-GCM decryption [50], prototype pollution, heap/buffer overflows in ZIP extraction [50], or memory leakage of raw decrypted assets in WebGL/WebGPU texture cache due to failure of the **Volatile Memory Disposal Protocol** (e.g., failing to revoke Blob URLs or actively zero-overwrite decrypted ArrayBuffers) [16, 50].

---

#### Our Disclosure Process
We adhere to standard coordinated vulnerability disclosure (CVD) practices [50]:
1.  **Acknowledgement:** We will acknowledge receipt of your report within **48 hours** and assign a primary security coordinator [50].
2.  **Triage & Validation:** We will investigate and attempt to reproduce the issue. We aim to complete triage and provide a status update within **7 days** [50].
3.  **Remediation:** If validated, we will work on a patch. Our goal is to release a security update within **30 days** of validation [50].
4.  **Advisory:** We will publish a Security Advisory (GHSA / CVE) detailing the vulnerability, crediting you for the discovery (if desired), and providing upgrade instructions for downstream platforms [50].

---

#### 🛡️ Safe Harbor
Any research conducted in good faith under this policy is protected by our Safe Harbor agreement [51]. We will not pursue legal action or encourage third parties to pursue legal action against researchers who [51]:
*  Do not exploit the vulnerability beyond what is strictly necessary to prove its existence [51].
*  Do not compromise, view, or modify user data or premium creator assets [51].
*  Provide us a reasonable period to address the issue before making any public disclosure (90-day standard) [51].
*  Comply with all local, state, and federal laws during their research [51].
