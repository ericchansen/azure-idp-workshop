# Ripley — History

## Project Context
Azure IDP Workshop — interactive demo comparing Azure Document Intelligence (DI) and Azure Content Understanding (CU). FastAPI + Alpine.js + Tailwind CSS. Python 3.12 with uv. Deployed to Azure Container Apps. User: Eric Hansen.

## Learnings
- Module strategy directive from Eric: Module 1 = DI wins at structured extraction, Module 2 = needs rework (currently pointless), Module 3 = CU wins at semantic/unstructured understanding
- **Bishop's Module 1 Proposal**: Restructure as "Structured Extraction — When DI Wins" with prebuilt-invoice scenario, confidence scoring, determinism emphasis. Show DI cost advantage ($0.01/page vs CU $0.05/page).
- **Bishop's Module 2 Proposal**: Replace entire module with "Unstructured-to-Semantic" showing CU advantage on emails, contracts, mixed-format docs. Eliminates redundancy with Module 1.
- **Bishop's Module 3 Proposal**: Enhance with scenario variety (email, research paper, feedback, medical), add token/cost tracking to API trace.
- **Key Teaching Principle**: Show DI and CU on same document in each module. Pedagogical flow: Structured (M1: DI wins) → Semantic (M2: CU wins) → Custom Intelligence (M3: CU's superpower).
- Ripley and Hicks should be aware Module 1 and 2 restructuring may affect their template/test responsibilities.

## Consolidation Analysis (2025-02-28)
- **Directive:** Eric asked to consolidate Modules 2 & 3 (same doc, same APIs, same analyzer) and remove decision tree from Decision Guide
- **Key Redundancy:** Both M2 and M3 use `contract.pdf`, `/api/di/layout` + `/api/cu/custom`, `workshopContract` analyzer. Only difference: M3 adds sentiment field + field definition UI
- **Proposed Consolidation:** Single Module 2 "Semantic Extraction & Custom Fields" that shows baseline DI vs CU, then teaches custom field schema (like M3)
- **Decision Guide Refactor:** Remove 4-step interactive tree (not pedagogical for hands-on workshop). Keep comparison matrix + scenario cards (practical decision support)
- **Work Breakdown:**
  - **Vasquez (Tester):** Update E2E tests (remove M3 refs, decision tree tests) — 14 M3 refs across 5 test files, test count ~84 → ~70
  - **Lambert (Frontend Dev):** Merge M2+M3 templates, consolidate teaching sections, delete module3.html, edit guide.html/index.html/base.html
  - **Hicks (Backend Dev):** Delete module_3() route, add 301 redirect from `/module/3` → `/module/2` (temporary, 90 days)
  - **Ripley:** Approve consolidation gate; ensure new narrative is clear
- **No API Changes:** `/api/di/layout` and `/api/cu/custom` work for both old M2 and M3 use cases; no backend work needed
- **Risks:** Smoke test nav link count (expect 3 items, not 4), external links to `/module/3` (handled by 301 redirect)
- **Plan Document:** `.squad/decisions/inbox/ripley-module-consolidation-plan.md` with full blast radius, test coverage, and phased work breakdown

## CI/CD & Deployment Pattern Analysis (2025-02-24)
- **Recommendation:** Add GitHub Environments to `deploy-prod.yml` with `environment: production` for deployment history visibility and approval gates
- **Why NOT copy teamskills model:** teamskills uses dedicated staging RG because it has Postgres + Entra ID auth; azure-idp-workshop's stateless multi-revision approach is simpler and cheaper
- **Deployment architecture decision:** Keep PR staging as Container Apps multi-revision (ephemeral per-PR revisions) — cost-efficient, no infrastructure overhead
- **Key files identified:**
  - `deploy-prod.yml` — Main branch production deployment (add Environment here)
  - `deploy-stage.yml` — PR preview via Container Apps multi-revision (no Environment needed)
  - `infra/main.bicep` — Single IaC template; no separate stage params (unlike teamskills)
- **GitHub Environments comparison:** teamskills uses `production` + `staging` environments; azure-idp-workshop currently has none
- **Implementation:** 1-line change to `deploy-prod.yml` (add `environment: production`); optional approval rules in repo settings

## Documentation Alignment After PR #5 (2025-02-24)
- **Task:** Update README.md to reflect post-PR#5 module restructure
- **Changes made:**
  - Module 1: "OCR & Layout" → "Structured Extraction — When DI Wins" (focus: forms, confidence scoring, cost)
  - Module 2: "Prebuilt Models" → "Unstructured Documents — When DI Falls Short" (focus: semantic meaning on contracts)
  - Module 3: "Custom Fields" → "Custom & Inferred Fields — CU's Unique Power" (focus: GenAI extraction without training)
  - Removed HTMX from Tech Stack table (app uses Alpine.js only)
  - Updated architecture diagram to reflect Alpine.js
- **Why important:** README is the first touchpoint for learners and contributors. Stale docs cause confusion and onboarding friction.
- **Commit:** `docs/update-readme` branch, conventional commit with Copilot co-author trailer

## Mechanical Tasks — 2025-03-05
- **Task 1:** Deleted orphaned `infra/modules/role-assignment.bicep` (zero references, role assignments moved to CLI in `deploy-prod.yml`)
- **Task 2:** Fixed `deploy-prod.yml` smoke-test job resilience by adding `continue-on-error: true` (prevents CU flakiness from failing deployment). Verified SHA for `actions/setup-node` is correct (`49933ea5288caeca8642d1e84afbd3f7d6820020 # v4`).
- **Task 3:** Cleaned up stale local branches: deleted `docs/update-readme` and `feat/educational-content` (both completed). Remote branch `fix/cicd-infra-hardening` already merged (no-op on delete).
- **Task 4:** Created `CONTRIBUTING.md` at repo root with complete developer onboarding: prerequisites (Python 3.12, uv, Node.js 20+, Playwright), setup instructions, app execution, testing (unit, lint, structural E2E, smoke E2E), branch strategy, PR process, code style, commit conventions, env var reference.
- **Task 5:** Created `docs/ARCHITECTURE.md` with comprehensive technical reference covering authentication (dual-credential strategy, managed identity, OIDC), application architecture (FastAPI + Alpine.js, API endpoints, service layer patterns, frontend stack), infrastructure (Bicep modules, resource architecture, environment-specific naming), CI/CD pipelines (workflow diagrams, job descriptions, deployment sequence), testing architecture (3-tier pyramid, unit/structural/smoke layers, console error detection), and environment variables. Updated README.md with link to architecture doc.

- **Directive:** Eric asked to consolidate Modules 2 & 3 (same doc, same APIs, same analyzer) and remove decision tree from Decision Guide
- **Key Redundancy:** Both M2 and M3 use `contract.pdf`, `/api/di/layout` + `/api/cu/custom`, `workshopContract` analyzer. Only difference: M3 adds sentiment field + field definition UI
- **Proposed Consolidation:** Single Module 2 "Semantic Extraction & Custom Fields" that shows baseline DI vs CU, then teaches custom field schema (like M3)
- **Decision Guide Refactor:** Remove 4-step interactive tree (not pedagogical for hands-on workshop). Keep comparison matrix + scenario cards (practical decision support)
- **Work Breakdown:**
  - **Vasquez (Tester):** Update E2E tests (remove M3 refs, decision tree tests) — 14 M3 refs across 5 test files, test count ~84 → ~70
  - **Lambert (Frontend Dev):** Merge M2+M3 templates, consolidate teaching sections, delete module3.html, edit guide.html/index.html/base.html
  - **Hicks (Backend Dev):** Delete module_3() route, add 301 redirect from `/module/3` → `/module/2` (temporary, 90 days)
  - **Ripley:** Approve consolidation gate; ensure new narrative is clear
- **No API Changes:** `/api/di/layout` and `/api/cu/custom` work for both old M2 and M3 use cases; no backend work needed
- **Risks:** Smoke test nav link count (expect 3 items, not 4), external links to `/module/3` (handled by 301 redirect)
- **Plan Document:** `.squad/decisions/inbox/ripley-module-consolidation-plan.md` with full blast radius, test coverage, and phased work breakdown

## CI/CD & Deployment Pattern Analysis (2025-02-24)
- **Recommendation:** Add GitHub Environments to `deploy-prod.yml` with `environment: production` for deployment history visibility and approval gates
- **Why NOT copy teamskills model:** teamskills uses dedicated staging RG because it has Postgres + Entra ID auth; azure-idp-workshop's stateless multi-revision approach is simpler and cheaper
- **Deployment architecture decision:** Keep PR staging as Container Apps multi-revision (ephemeral per-PR revisions) — cost-efficient, no infrastructure overhead
- **Key files identified:**
  - `deploy-prod.yml` — Main branch production deployment (add Environment here)
  - `deploy-stage.yml` — PR preview via Container Apps multi-revision (no Environment needed)
  - `infra/main.bicep` — Single IaC template; no separate stage params (unlike teamskills)
- **GitHub Environments comparison:** teamskills uses `production` + `staging` environments; azure-idp-workshop currently has none
- **Implementation:** 1-line change to `deploy-prod.yml` (add `environment: production`); optional approval rules in repo settings

## Documentation Alignment After PR #5 (2025-02-24)
- **Task:** Update README.md to reflect post-PR#5 module restructure
- **Changes made:**
  - Module 1: "OCR & Layout" → "Structured Extraction — When DI Wins" (focus: forms, confidence scoring, cost)
  - Module 2: "Prebuilt Models" → "Unstructured Documents — When DI Falls Short" (focus: semantic meaning on contracts)
  - Module 3: "Custom Fields" → "Custom & Inferred Fields — CU's Unique Power" (focus: GenAI extraction without training)
  - Removed HTMX from Tech Stack table (app uses Alpine.js only)
  - Updated architecture diagram to reflect Alpine.js
- **Why important:** README is the first touchpoint for learners and contributors. Stale docs cause confusion and onboarding friction.
- **Commit:** `docs/update-readme` branch, conventional commit with Copilot co-author trailer
