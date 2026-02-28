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
