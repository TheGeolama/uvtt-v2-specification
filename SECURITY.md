# Security Policy for UVTT v2

## 1. Introduction

Security is a foundational pillar of the UVTT v2 ecosystem. Because the V2 standard involves parsing compressed archives (`.uvtt2z`), handling cryptographic keys (`.uvtt2k`), and rendering complex spatial data, we take vulnerability reports extremely seriously.

This document outlines our supported versions, how to report a vulnerability, and our established threat model.

---

## 2. Supported Versions

We only provide security updates for the current major release pipeline.

| Version | Supported | Notes                                              |
| ------- | --------- | -------------------------------------------------- |
| v2.x.x  | ✅ Yes    | Current active standard and Upgrader platform.     |
| v1.x.x  | ❌ No     | Legacy standard (Flat JSON). Please upgrade to v2. |

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability within the UVTT v2 Upgrader, the Desktop Pro engine, or the core Specification, **please do not report it on the public GitHub issue tracker.**

Instead, please use the following secure channels:

1. **Email:** Send your report to `[Insert Security Email Address Here]`.
2. **Template:** Please format your report using the structure defined in our `SECURITY_DISCLOSURE_TEMPLATE.md` file.

**Response Timeline:** We will acknowledge receipt of your vulnerability report within 48 hours and strive to provide a remediation timeline within 7 days.

---

## 4. Threat Model and Scope

To help security researchers understand our architecture, please review what is (and is not) considered a valid security vulnerability within the UVTT v2 ecosystem.

### ✅ In Scope (Valid Vulnerabilities)

- **Zip Bombs / Resource Exhaustion:** A maliciously crafted `.uvtt2z` archive that intentionally causes memory exhaustion or a denial-of-service (DoS) when parsed by the Upgrader.
- **Arbitrary Code Execution (ACE) / XSS:** A `.uvtt2z` archive containing poisoned JSON fields (e.g., a malicious payload in `manifest.author`) that successfully executes unauthorized JavaScript in the Web SPA or Go backend in the Desktop Pro app.
- **Path Traversal:** A malicious archive attempting to use relative paths (e.g., `../../etc/passwd`) within the `assets/` directory to read or write files outside the intended sandbox.
- **Cryptographic Failures:** Flaws in how the Desktop Pro app generates the AES-256-GCM encryption envelope or manages IVs/Salts.

### ❌ Out of Scope (Not Considered Vulnerabilities)

- **Creator Key Leaks:** If a creator accidentally uploads their `.uvtt2k` key file to a public forum alongside their payload, this is user error, not a platform vulnerability.
- **Browser Sandbox Limits:** The Web SPA Upgrader crashing because a user attempted to load a 4 GB map on a machine with 2 GB of RAM. (This is an OS/Browser limitation; users should upgrade to Desktop Pro for streaming massive files).
- **Volatile RAM Inspection:** Extracting a decrypted premium map by running a memory debugger (like Cheat Engine) against the VTT client. Once a user legally provides a key, the data must exist in RAM to be rendered by the GPU. Preventing OS-level memory inspection is outside the scope of this cartography standard.
