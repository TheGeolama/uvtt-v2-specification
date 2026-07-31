---
name: "🐛 Compliance or Schema Bug"
about: "Report a schema validation error, parser discrepancy, or compliance bug with the UVTT v2 specification."
title: "[BUG] "
labels: ["bug: compliance"]
assignees: ""
---

### 📝 Description of Discrepancy

Provide a clear, descriptive overview of the compliance discrepancy or validation failure. (e.g., "The Go validator allows multiple `is_default: true` landing zones, violating schema constraints.")

### 🧩 Affected Specification Layer

Identify where the bug/discrepancy lies:

- [ ] `manifest.schema.json`
- [ ] `geometry.schema.json`
- [ ] `entities.schema.json`
- [ ] `assets.schema.json`
- [ ] Go Reference Parser (`validate_conformance.go` / `uvtt2_parser.go`)
- [ ] TypeScript/JS Reference Parser (`uvtt2-parser.ts`)
- [ ] Dual-File Cryptography (`.uvtt2k` / AES-256-GCM Handlers)
- [ ] Other (please specify):

---

### 🔄 Reproducible Scenario & Payload

#### Steps to Reproduce:

1. Load/parse the attached `.uvtt2z` asset or JSON payload.
2. Execute validation using [Tool/Parser Name & Version].
3. Observe behavior.

#### Sample JSON Payload (Minimal Reproducible Example):

```json
// Paste the minimal JSON schema or map data that triggers the error here
```

---

### ⚖️ Expected vs. Actual Behavior

- **Expected Behavior:** (e.g., "Validation should fail with a 'Multiple default landing zones' error.")
- **Actual Behavior:** (e.g., "Validation passes and the parser selects the last default landing zone in the array.")

---

### 💻 Environment Context

- **VTT App / Tooling Name:**
- **Parser Language / Library:** (e.g., Go Reference Parser v2.0.0-rc1, custom Rust parser)
- **Host OS / Runtime Environment:**
