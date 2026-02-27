# Bishop — History

## Project Context
Azure IDP Workshop — interactive demo comparing Azure Document Intelligence (DI) and Azure Content Understanding (CU). FastAPI + Alpine.js + Tailwind CSS. Python 3.12 with uv. Deployed to Azure Container Apps. User: Eric Hansen.

## Learnings
- Module strategy directive from Eric: Module 1 = DI wins at structured extraction, Module 2 = needs rework (currently pointless), Module 3 = CU wins at semantic/unstructured understanding
- **Module 1 Issue**: Currently positions OCR/layout as "both services do this equally well." Should pivot to "Structured Extraction — DI's Strength" with prebuilt-invoice scenario, confidence scoring, and determinism emphasis.
- **Module 2 Issue**: Functionally identical to Module 1 (both run prebuilt models on same document). **Solution**: Replace entirely with "Unstructured-to-Semantic" module showing CU's advantage for emails, contracts, mixed-format docs where DI fails.
- **Module 3 Success**: Correctly showcases CU's GenAI superpower. Recommendations: add scenario variety (email, research paper, feedback), enhance token/cost tracking in API trace.
- **DI Win Condition**: Structured forms, predefined fields, high-volume processing, deterministic extraction. Confidence scoring is key differentiator.
- **CU Win Condition**: Unstructured/semantic extraction, novel document types, GenAI inference needed for meaning.
- **Leverage Opportunities**: Confidence scoring visibility (Module 1), markdown output (Module 2), token cost tracking (Module 3), table detection (Module 1).
- **Teaching Principle**: Show DI and CU on same document in each module. Comparison clarifies value proposition. Pedagogical flow: Structured (M1) → Semantic (M2) → Custom Intelligence (M3).
