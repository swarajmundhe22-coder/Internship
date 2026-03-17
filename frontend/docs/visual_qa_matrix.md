# Visual QA Matrix

Scope: Final polish QA for landing, dashboard, and simulations pages.
Date: 2026-03-17

Breakpoints
- Mobile: 390x844
- Tablet: 768x1024
- Desktop: 1440x900

## Screenshot Checklist
- [x] Mobile screenshot: / (hero + story track + operations tiles)
- [x] Tablet screenshot: / (hero pin + right panel stack)
- [x] Desktop screenshot: / (full fold + module flow)
- [x] Mobile screenshot: /dashboard (story intro + analytics cards)
- [x] Tablet screenshot: /dashboard (story track + mission control)
- [x] Desktop screenshot: /dashboard (analytics + storyboard + action cards)
- [x] Mobile screenshot: /simulations (story intro + selectors + controls)
- [x] Tablet screenshot: /simulations (story + control grid + records)
- [x] Desktop screenshot: /simulations (full tactical layout)

## Exact Before/After Diffs
Method
- Before images are true browser captures with a QA baseline override matching pre-adjustment spacing and compact pacing thresholds.
- After images are true browser captures of current tuned state.
- Diff images are pixel-level comparisons generated with pixelmatch.

| State | Before | After | Diff | Mismatch % | Mismatch Pixels |
|---|---|---|---|---:|---:|
| home-mobile | [before](../artifacts/visual_qa/before/home-mobile.png) | [after](../artifacts/visual_qa/after/home-mobile.png) | [diff](../artifacts/visual_qa/diff/home-mobile.png) | 20.137 | 66,284 |
| home-tablet | [before](../artifacts/visual_qa/before/home-tablet.png) | [after](../artifacts/visual_qa/after/home-tablet.png) | [diff](../artifacts/visual_qa/diff/home-tablet.png) | 16.132 | 126,871 |
| home-desktop | [before](../artifacts/visual_qa/before/home-desktop.png) | [after](../artifacts/visual_qa/after/home-desktop.png) | [diff](../artifacts/visual_qa/diff/home-desktop.png) | 10.956 | 141,984 |
| dashboard-mobile | [before](../artifacts/visual_qa/before/dashboard-mobile.png) | [after](../artifacts/visual_qa/after/dashboard-mobile.png) | [diff](../artifacts/visual_qa/diff/dashboard-mobile.png) | 1.044 | 3,437 |
| dashboard-tablet | [before](../artifacts/visual_qa/before/dashboard-tablet.png) | [after](../artifacts/visual_qa/after/dashboard-tablet.png) | [diff](../artifacts/visual_qa/diff/dashboard-tablet.png) | 1.555 | 12,228 |
| dashboard-desktop | [before](../artifacts/visual_qa/before/dashboard-desktop.png) | [after](../artifacts/visual_qa/after/dashboard-desktop.png) | [diff](../artifacts/visual_qa/diff/dashboard-desktop.png) | 1.572 | 20,374 |
| simulations-mobile | [before](../artifacts/visual_qa/before/simulations-mobile.png) | [after](../artifacts/visual_qa/after/simulations-mobile.png) | [diff](../artifacts/visual_qa/diff/simulations-mobile.png) | 3.053 | 10,049 |
| simulations-tablet | [before](../artifacts/visual_qa/before/simulations-tablet.png) | [after](../artifacts/visual_qa/after/simulations-tablet.png) | [diff](../artifacts/visual_qa/diff/simulations-tablet.png) | 43.052 | 338,576 |
| simulations-desktop | [before](../artifacts/visual_qa/before/simulations-desktop.png) | [after](../artifacts/visual_qa/after/simulations-desktop.png) | [diff](../artifacts/visual_qa/diff/simulations-desktop.png) | 45.356 | 587,813 |

Report JSON
- [artifacts/visual_qa/report.json](../artifacts/visual_qa/report.json)

## Intensity Impact Pass (Baseline vs New Brand Intensities)
Baseline Source
- Prior tuned captures: [artifacts/visual_qa/after](../artifacts/visual_qa/after)

Current Source
- New intensity captures: [artifacts/visual_qa_intensity/current](../artifacts/visual_qa_intensity/current)

Diff Output
- Pixel diffs: [artifacts/visual_qa_intensity/diff](../artifacts/visual_qa_intensity/diff)
- Report: [artifacts/visual_qa_intensity/report.json](../artifacts/visual_qa_intensity/report.json)

| State | Baseline | Current | Diff | Change % | Changed Pixels |
|---|---|---|---|---:|---:|
| home-mobile | [baseline](../artifacts/visual_qa/after/home-mobile.png) | [current](../artifacts/visual_qa_intensity/current/home-mobile.png) | [diff](../artifacts/visual_qa_intensity/diff/home-mobile.png) | 1.131 | 3,723 |
| home-tablet | [baseline](../artifacts/visual_qa/after/home-tablet.png) | [current](../artifacts/visual_qa_intensity/current/home-tablet.png) | [diff](../artifacts/visual_qa_intensity/diff/home-tablet.png) | 2.658 | 20,903 |
| home-desktop | [baseline](../artifacts/visual_qa/after/home-desktop.png) | [current](../artifacts/visual_qa_intensity/current/home-desktop.png) | [diff](../artifacts/visual_qa_intensity/diff/home-desktop.png) | 13.415 | 173,854 |
| dashboard-mobile | [baseline](../artifacts/visual_qa/after/dashboard-mobile.png) | [current](../artifacts/visual_qa_intensity/current/dashboard-mobile.png) | [diff](../artifacts/visual_qa_intensity/diff/dashboard-mobile.png) | 70.229 | 231,167 |
| dashboard-tablet | [baseline](../artifacts/visual_qa/after/dashboard-tablet.png) | [current](../artifacts/visual_qa_intensity/current/dashboard-tablet.png) | [diff](../artifacts/visual_qa_intensity/diff/dashboard-tablet.png) | 69.480 | 546,415 |
| dashboard-desktop | [baseline](../artifacts/visual_qa/after/dashboard-desktop.png) | [current](../artifacts/visual_qa_intensity/current/dashboard-desktop.png) | [diff](../artifacts/visual_qa_intensity/diff/dashboard-desktop.png) | 54.658 | 708,363 |
| simulations-mobile | [baseline](../artifacts/visual_qa/after/simulations-mobile.png) | [current](../artifacts/visual_qa_intensity/current/simulations-mobile.png) | [diff](../artifacts/visual_qa_intensity/diff/simulations-mobile.png) | 66.556 | 219,077 |
| simulations-tablet | [baseline](../artifacts/visual_qa/after/simulations-tablet.png) | [current](../artifacts/visual_qa_intensity/current/simulations-tablet.png) | [diff](../artifacts/visual_qa_intensity/diff/simulations-tablet.png) | 59.643 | 469,055 |
| simulations-desktop | [baseline](../artifacts/visual_qa/after/simulations-desktop.png) | [current](../artifacts/visual_qa_intensity/current/simulations-desktop.png) | [diff](../artifacts/visual_qa_intensity/diff/simulations-desktop.png) | 50.381 | 652,938 |

## QA Matrix
| Page | Breakpoint | Layout Spacing | Typography Rhythm | Motion Pacing | Micro-Interactions | Status |
|---|---|---|---|---|---|---|
| / | Mobile | Slightly dense around hero -> reduced outer padding and section gaps | Good after 3-tier token tuning | Reveal started late -> compact start tuned earlier | Buttons/tiles active feedback present | Adjusted |
| / | Tablet | Balanced panel stack spacing | Strong heading/body contrast | Cinematic pacing smooth | Hover/focus states clear | Pass |
| / | Desktop | Balanced with strong rhythm between sections | High readability and hierarchy | Hero + panel pacing cohesive | CTA interactions responsive | Pass |
| /dashboard | Mobile | Good card spacing; no overlap | Consistent body scale and title cadence | Compact pacing tuned for earlier readability | Badge/button interaction stable | Adjusted |
| /dashboard | Tablet | Clear split between pinned context and panels | Strong hierarchy in chapter cards | Smooth handoff between sections | Orbit module chips readable and interactive | Pass |
| /dashboard | Desktop | Comfortable spacing across analytics groups | Dense data remains readable | Section transitions feel continuous | Buttons/chips feel responsive | Pass |
| /simulations | Mobile | Selector panel spacing stable; controls readable | Tactical text rhythm consistent | Compact timing tuned to avoid delayed reveals | Selects/buttons preserve tactile response | Adjusted |
| /simulations | Tablet | Story + control stack balanced | Good emphasis on labels and values | Snappy pacing feels deliberate | Filter and record affordances clear | Pass |
| /simulations | Desktop | Full grid remains structured | No crowding in records/metrics | Strong battle-style movement pacing | Cards and tactical buttons responsive | Pass |

## Adjustments Applied From QA
1. Added compact-mode pacing controls in storytelling hook via data attributes.
2. Landing page: reduced mobile outer padding and tightened section gaps.
3. Landing/dashboard/simulations: tuned compact reveal and beat start thresholds.

## Known Environment Constraint
- OneDrive/Windows readlink EINVAL can block Next build cleanup in this workspace.
- TypeScript validation remains clean and is used as compile safety gate.
