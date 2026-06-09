# Patient Log Analyzer

This is a low-visibility scenario demo for a Content Understanding-only patient
treatment log analyzer. It is intentionally not listed as a numbered workshop
module. Open it directly at:

```text
/patient-log
```

## Goal

Show how Azure AI Content Understanding can:

- segment a scanned patient-log packet into document sections;
- route patient-log/body-diagram sections to a treatment-log analyzer;
- reason over visual marks on body diagrams and spinal palpation sections;
- return structured findings, missing-information notes, and ambiguity notes;
- export derived JSON to the browser without server-side storage.

This demo does not use Document Intelligence. The output is semantic evidence,
not coordinate-perfect layout evidence. Use DI plus CU later if production
workflows require exact bounding regions, table geometry, or audit coordinates.

## Azure resources

Reuse the existing Azure AI Services / Foundry resource from the IDP workshop.
Do not create a new Foundry resource for this demo.

Required app settings:

```text
AI_SERVICES_ENDPOINT=<existing idp-workshop-ai endpoint>
AI_SERVICES_KEY=<optional, if not using managed identity>
ADMIN_API_KEY=<required to create/update analyzers from the web app>
CU_COMPLETION_MODEL=gpt-5.2
CU_COMPLETION_DEPLOYMENT=gpt-5.2
CU_EMBEDDING_MODEL=text-embedding-3-large
CU_EMBEDDING_DEPLOYMENT=text-embedding-3-large
```

Keep `gpt-4.1` deployed as a fallback while validating `gpt-5.2`. The app
uses `gpt-5.2` by default for new patient-log analyzers.

The analyzer IDs are intentionally short and document-type based:

- `patient_log_classifier`
- `patient_log_treatment`

The analyzer setup endpoint is protected by `ADMIN_API_KEY` because it creates
or replaces analyzer resources using the app's Azure identity. Leave
`ADMIN_API_KEY` unset to disable analyzer mutation in a public deployment, or
configure it as a Container Apps secret when analyzer setup should be available.

## Foundry project and model IaC

The runtime app calls resource-level Content Understanding analyzer endpoints on
the existing `idp-workshop-ai` resource. However, the portal experience can
require a Foundry project for authoring and model deployment workflows. The
deployment templates therefore also create a project under the same resource:

```text
foundryProjectName=patient-log-demo
foundryProjectDisplayName=Patient Log Demo
```

This project is for portal/model-authoring UX. It does not replace the
resource-level API endpoint used by the app, and it does not require a separate
Foundry resource.

The IaC deploys `gpt-5.2` as the default CU completion model and keeps
`gpt-4.1` as a fallback while the newer model is validated. If `gpt-5.2` is not
available in the subscription/region, switch `CU_COMPLETION_MODEL` and
`CU_COMPLETION_DEPLOYMENT` back to the fallback deployment.

## Content Understanding Studio demo

Use Content Understanding Studio when you want to demonstrate visual authoring
inside the Azure portal experience.

1. Open Content Understanding Studio.
2. Create a project using **Classify and route with custom categories**.
3. Select the existing `idp-workshop-ai` Foundry/Azure AI Services resource.
4. Use an external/manual sample from OneDrive. Do not upload or commit real
   patient/customer samples into this repository.
5. Create categories matching the app definitions:
   - `patient_treatment_log`
   - `palpation_body_diagram`
   - `claim_or_cover_sheet`
   - `invoice_or_billing`
   - `correspondence`
   - `other`
6. Build a treatment-log analyzer with fields for visit entries, body diagram
   findings, spinal palpation findings, missing entries, ambiguity notes, and
   an overall summary.
7. Route `patient_treatment_log` and `palpation_body_diagram` categories to the
   treatment-log analyzer.
8. Test against the external sample packet.

The `/patient-log` page exposes the JSON analyzer definitions used by the app so
you can compare the portal project configuration with the direct API version.

## Privacy and persistence

- Real patient/customer samples stay external and manual-only.
- The app processes uploads request-by-request.
- Raw uploads are not stored by the app.
- Patient-log outputs are not indexed into Azure AI Search.
- The only persistence path is explicit browser-side JSON export/download.

## Testing strategy

Repository tests use mocked API responses and synthetic fixture data only. Live
smoke tests should verify that the page loads and controls render, not that real
patient documents are analyzed.
