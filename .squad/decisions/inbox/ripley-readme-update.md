# Decision: README Documentation Alignment Post-PR #5

**Author:** Ripley (Lead)  
**Date:** 2025-02-24  
**Status:** Implemented  
**Scope:** Documentation

## Decision
Update README.md to reflect the module structure changes introduced in PR #5.

## Context
PR #5 restructured the workshop modules to follow a clearer pedagogical narrative:
- Module 1: DI wins (structured extraction)
- Module 2: DI falls short (unstructured/semantic documents)
- Module 3: CU's superpower (custom & inferred fields)

The README still referenced the old module descriptions, creating confusion for learners and contributors.

## Changes
| Section | Before | After |
|---------|--------|-------|
| Module 1 | "OCR & Layout" | "Structured Extraction — When DI Wins" |
| Module 2 | "Prebuilt Models" | "Unstructured Documents — When DI Falls Short" |
| Module 3 | "Custom Fields" | "Custom & Inferred Fields — CU's Unique Power" |
| Tech Stack (Frontend) | "Jinja2 + HTMX + Alpine.js" | "Jinja2 + Alpine.js" |
| Architecture | "FastAPI (Jinja2 + HTMX)" | "FastAPI (Jinja2 + Alpine.js)" |

## Rationale
1. **Accuracy:** Module descriptions must match actual implementation (index.html, templates)
2. **Learner experience:** Consistent narrative — know when/why each service wins
3. **HTMX removal:** App never used HTMX; redundant tech stack entry caused confusion
4. **Conciseness:** Descriptions remain brief but now action-oriented ("When DI wins" vs "How both digitize")

## Implementation Details
- Branch: `docs/update-readme`
- Commit: Conventional commit with Copilot co-author
- All changes isolated to README.md
- No code or test changes

## Verification
- README descriptions now match index.html and template h1 titles
- Tech stack matches actual app dependencies (Alpine.js only)
- Commit message follows project conventions

## Team Impact
- **Learning curve:** Reduced — learners see consistent messaging across README and UI
- **Contributor onboarding:** Improved — docs now match code
- **No breaking changes:** README-only update

## Related Decisions
- PR #5 module restructure (module strategy and implementation)
