# Patentability Analysis and Draft Application Package

Date: 2026-04-03
Project: The On Looker
Prepared as: Technical patentability assessment and filing-ready draft package (not legal advice).

## 1. Scope and Method

This package includes:

1. novelty and non-obviousness analysis
2. prior-art screening across patent, scientific, and industry sources
3. claim strategy and draft claim set
4. draft specification with enablement-oriented detail
5. draft abstract and technical drawing descriptions
6. filing and prosecution response framework

Important limitation:

- This environment cannot directly file with a patent office or submit office-action responses. Filing and prosecution actions require a registered patent practitioner and official portal access.

## 2. Prior Art Search Summary

## 2.1 Patent Search Evidence

Automated Google Patents XHR query attempts in this run returned HTTP 503 and no machine-readable candidates.

Recovered via direct web query page parsing, representative patent-family candidates include:

1. CN116482227B - Pipeline corrosion monitoring method, device and system
2. CA3075085C (WO/EP/US family visibility) - GE Inspection Technologies candidate relating to asset data/optimization context
3. CN113339787B - Digital twin related industrial optimization candidate
4. CN110530638B - Digital twin damage detection/diagnosis candidate
5. Additional digital twin monitoring families shown in query results

Patent search takeaway:

- The field is active and crowded around digital twin monitoring and corrosion-related analytics.
- Distinction must focus on specific integrated mechanisms, not broad digital twin or ML language.

## 2.2 Scientific and Technical Literature Evidence

Literature candidate corpus:

- 32 candidates from OpenAlex query set

Representative references:

1. 10.1109/TIE.2019.2931491 - RUL estimation of subsea pipeline systems
2. 10.1016/S0308-0161(98)00006-4 - probabilistic remaining life with corrosion defects
3. 10.1115/1.4047173 - physics-informed neural approaches for corrosion-fatigue modeling
4. 10.1016/j.engfailanal.2022.106951 - review of data-mining corrosion prediction for pipelines
5. 10.2523/IPTC-22584-MS - synthetic casing corrosion prediction via digital twin concept
6. 10.1016/j.ress.2024.110456 - digital twin Bayesian framework for corrosion fatigue life prediction

Literature search takeaway:

- Prior art clearly covers corrosion modeling, RUL estimation, and digital twin maintenance workflows.
- Patentability case should emphasize your concrete confidence-governed output override and mission-control coupling pattern.

## 2.3 Industry/Standards Sources

Representative baseline references:

1. ISO 9223 atmospheric corrosivity classification
2. AMPP/NACE practice references

Standards takeaway:

- Standards can support non-obvious implementation details if your system transforms standard-style factors into unique confidence-governed, operationally auditable workflows.

## 3. Novelty and Non-Obviousness Assessment

## 3.1 Candidate Inventive Features

1. Confidence-governed fallback that modifies production outputs before publication (design rate and risk) when confidence is below threshold
2. Unified calibration framework combining region pack multipliers, material calibration, and asset exposure profile
3. Integrated uncertainty-band computation tied to region sigma and confidence floor
4. Mission-control digital twin coupling where prediction outputs directly generate playback and export metadata
5. Export-to-audit linkage in a tenant-scoped workflow that ties analytics, visualization, and compliance evidence

## 3.2 Preliminary Patentability View

Novelty:

- Moderate potential, if claims are narrowed to the specific confidence-fallback + mission-control coupling workflow.

Non-obviousness:

- Moderate risk in broad form.
- Improved position if claims emphasize specific sequencing, thresholds, and governance behavior not commonly claimed together.

Subject matter eligibility:

- Improve eligibility posture by grounding claims in concrete data transformations, system modules, and operational controls rather than abstract analytics statements.

## 4. Draft Claim Strategy

## 4.1 Independent Claims (Draft)

Claim 1 (Method)

A computer-implemented method comprising:

1. receiving infrastructure material, environment, and asset-type inputs;
2. selecting a regional calibration pack and a material calibration profile;
3. computing an environmental severity score using multiple environmental factors;
4. computing a design corrosion rate, a risk score, and an estimated lifespan;
5. computing uncertainty bands and a calibration confidence value for at least the design corrosion rate and risk score;
6. when the calibration confidence is below a threshold, automatically applying a conservative fallback policy that increases at least one of the design corrosion rate and risk score relative to a non-fallback output; and
7. outputting a simulation result including fallback status and uncertainty information.

Claim 2 (System)

A system comprising one or more processors and memory storing instructions that cause the processors to:

1. execute the method of Claim 1; and
2. generate a digital twin payload including timeline and hotspot metadata based on the simulation result;
3. enforce an overlay-accuracy gate for twin generation; and
4. generate an export artifact linked to an audit event containing tenant-scoped context.

Claim 3 (Computer-readable medium)

A non-transitory computer-readable medium storing instructions that cause one or more processors to perform the method of Claim 1.

## 4.2 Dependent Claim Set (Draft)

Claim 4

The method of Claim 1, wherein the regional calibration pack includes temperature, humidity, chloride, ultraviolet, microbiologically influenced corrosion, and soil resistivity multipliers.

Claim 5

The method of Claim 1, wherein the confidence value is computed from region confidence floor, material sensitivity, and severity score.

Claim 6

The method of Claim 1, wherein uncertainty bands include lower and upper bounds and a confidence level for each major output metric.

Claim 7

The method of Claim 1, wherein fallback activation updates recalibration scheduling metadata.

Claim 8

The system of Claim 2, wherein export generation supports at least PDF and MP4 formats and records fallback renderer metadata when a media encoder is unavailable.

Claim 9

The system of Claim 2, wherein tenant membership and simulation-to-tenant binding are validated before playback or export.

Claim 10

The method of Claim 1, further comprising auto-selecting a regional calibration pack when no explicit region is provided.

Claim 11

The method of Claim 1, wherein criticality level modifies at least one risk or design-rate output.

Claim 12

The system of Claim 2, wherein audit queries can verify successful export events for a given simulation and tenant.

## 5. Draft Specification

## 5.1 Title

Adaptive Multi-Factor Corrosion Prediction and Mission-Control Digital Twin System with Confidence-Governed Fallback.

## 5.2 Technical Field

The disclosure relates to predictive infrastructure analytics, corrosion-risk modeling, digital twin generation, and operational compliance automation.

## 5.3 Background

Conventional systems often produce nominal predictions without robust confidence-governed output control and without strong coupling between model outputs, digital twin operations, and auditable export workflows.

## 5.4 Summary

Embodiments provide:

1. calibrated corrosion prediction using region/material/asset factors
2. uncertainty and confidence quantification
3. threshold-triggered conservative fallback
4. twin/playback/export orchestration
5. tenant-scoped audit traceability

## 5.5 Brief Description of Drawings (Textual)

Figure 1

System block diagram including:

1. input normalization module
2. calibration selection module
3. severity and rate computation module
4. confidence and fallback governance module
5. twin/playback/export module
6. audit and tenant-access module

Figure 2

Data-flow sequence showing:

1. request ingestion
2. prediction and uncertainty generation
3. confidence threshold evaluation
4. optional fallback override
5. twin payload generation
6. export artifact generation
7. audit event persistence and query

Figure 3

Fallback control flow:

1. confidence >= threshold path (nominal)
2. confidence < threshold path (conservative override)
3. downstream publication behavior

Figure 4

Tenant-scoped access and export verification workflow.

## 5.6 Detailed Description (Embodiment)

Embodiment A:

1. Receive material/environment/asset/criticality/region-hint fields.
2. Normalize material key and asset profile key.
3. Resolve region key by canonical map or auto-selection heuristics.
4. Compute severity score from environmental factors and region multipliers.
5. Compute corrosion rate and design corrosion rate from material and asset factors.
6. Compute risk score and lifespan estimate.
7. Compute uncertainty intervals and calibration confidence.
8. If confidence < threshold, apply fallback by increasing conservative outputs and flagging fallback state.
9. Publish result with uncertainty and fallback metadata.
10. Generate twin metadata and playback timeline from result.
11. Export artifact and store audit event link for verification.

Embodiment B:

1. The system supports alternate rendering backends and preserves pipeline continuity with renderer-fallback metadata.
2. Tenant access controls are enforced before playback and export operations.

## 5.7 Enablement and Best Mode Notes

Enablement support provided by:

1. explicit profile/calibration structures
2. deterministic calculation flow
3. concrete threshold/fallback behavior
4. concrete output structures for uncertainty and metadata
5. reproducible gateway test scripts and artifacts

Best mode (current implementation):

- global calibrated model version with region packs, uncertainty computation, confidence-triggered fallback, and mission-control twin/export orchestration.

## 5.8 Draft Abstract

A computer-implemented system and method for corrosion prediction and digital twin operations is disclosed. The method receives material, environmental, and asset data; applies regional and material calibration profiles; computes corrosion-related outputs and uncertainty bands; computes calibration confidence; and applies a conservative fallback policy when confidence is below a threshold. The resulting outputs are transformed into digital twin playback and export artifacts, with tenant-scoped access controls and auditable event linkage. The disclosed architecture improves operational reliability by combining uncertainty-aware prediction governance with mission-control visualization workflows.

## 6. Prosecution Readiness and Office Action Framework

## 6.1 Anticipated Rejection Types

1. 35 U.S.C. 101 / abstract idea style rejection
2. 35 U.S.C. 102 novelty rejection over digital twin/corrosion references
3. 35 U.S.C. 103 obviousness combinations across corrosion prediction and digital twin workflow references
4. 35 U.S.C. 112 clarity/support issues on claim terms

## 6.2 Response Strategy Template

For novelty/obviousness:

1. Map each cited reference to claim limitations.
2. Show missing limitation in each reference or combination, especially:
   - confidence-threshold-triggered conservative override sequence
   - uncertainty-linked operational publication behavior
   - twin/export/audit coupling under tenant governance
3. Add dependent fallback language that captures implementation-specific ordering.

For subject-matter eligibility:

1. Emphasize concrete technical pipeline and transformed machine outputs.
2. Tie claims to practical system control and reliability improvements.

For 112 support:

1. Align terminology across claims and specification.
2. Provide explicit definitions for confidence threshold, fallback, and uncertainty bands.

## 7. Filing Plan (Practical)

1. Prepare inventor declarations, assignment chain, and applicant data.
2. File provisional application with this disclosure, figures, and claim scaffold.
3. Expand to non-provisional within statutory window.
4. Conduct jurisdictional strategy review (US-first vs PCT-first).

Not executable from this runtime:

- direct patent-office filing and official prosecution correspondence.

## 8. Recommended Next Actions

1. Have patent counsel perform a formal claim chart versus top 10 patent references.
2. Convert textual figure descriptions into formal patent drawings.
3. Finalize inventor list and ownership assignments.
4. File provisional package immediately to secure priority date.
5. Prepare non-provisional with narrowed independent claims and broader dependent coverage.
