### 2026-03-03T22:21Z: User directive — Consolidate Module 2 and Module 3
**By:** Eric Hansen (via Copilot)
**What:** Module 2 (Unstructured Documents) and Module 3 (Custom Fields) use the same document (contract.pdf), same APIs (`/api/di/layout` + `/api/cu/custom`), same analyzer (`workshopContract`), and nearly identical custom fields. They should be combined into a single module. The only difference is Module 3 adds a `sentiment` field and shows the field definition UI.
**Why:** User observation — the modules are redundant. Same demo, different framing. Should be one module.

### 2026-03-03T22:21Z: User directive — Remove interactive decision tree
**By:** Eric Hansen (via Copilot)
**What:** The interactive decision tree on the Decision Guide page is "silly" — remove it.
**Why:** User preference — the step-by-step wizard doesn't add value.
