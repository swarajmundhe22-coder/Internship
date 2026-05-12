# Frontend Architecture Audit & Implementation Specification

## Executive Summary
A comprehensive frontend architecture audit was conducted to identify UI/UX deficiencies, technical debt, and missing real-time data implementations. This document outlines the findings and the specific implementation specification to address these issues.

## 1. Performance & Scalability

### 1.1 Lazy Loading
- **Action:** Identify every import of `three`, `@babylonjs`, `deck.gl`, and `mapbox-gl` in the codebase.
- **Implementation:** Replace each direct import with `next/dynamic` using `{ ssr: false }` and a custom loading skeleton that matches the visual footprint of the component.
- **Validation:** Measure the initial bundle before and after with `webpack-bundle-analyzer`; commit only when the total first-load JS drops by ≥ 25%.
- **Governance:** Add a lint rule (`eslint-plugin-next`) that fails CI if any of these libraries is imported statically.

### 1.2 State Management
- **Action:** Audit the React component tree for contexts deeper than two levels that update ≥ 5 times per second.
- **Implementation:** Migrate each context to an atomic store: Zustand for cross-component slices, Jotai for atom-family streams.
- **Validation:** Ensure selectors are referentially stable; write a unit test that asserts the number of re-renders remains ≤ 1 when the store updates 1000 items in a 50 ms interval.
- **Governance:** Provide TypeScript types for every atom/slice; enforce with `tsc --noEmit` in CI.

### 1.3 Web Workers
- **Action:** Create a dedicated worker file (`streaming.worker.ts`) that imports only the parsers needed for websocket/Firebase payloads.
- **Implementation:** Establish a transferable message protocol: worker sends `{ frameId, interpolatedData }` as ArrayBuffer to avoid cloning cost. Implement a back-pressure mechanism: if the UI thread has > 3 unprocessed frames, drop intermediate frames and interpolate on the client.
- **Validation:** Benchmark thread-to-main throughput with Chrome DevTools; target ≥ 60 fps on a 4× CPU slowdown profile.

## 2. Accessibility

### 2.1 Canvas ARIA Fallbacks
- **Action:** For every WebGL/Canvas component, generate a hidden DOM table that updates whenever the scene graph changes.
- **Implementation:** Include `role="img"` and `aria-label` describing the number of objects and their spatial relationship (e.g., "3D scene: 12 drones, altitude 120 m").
- **Validation:** Write a `jest-axe` test that verifies no critical violations (impact="serious") exist after each scene mutation.

### 2.2 Reduced Motion Support
- **Action:** Wrap all `framer-motion` motion components with a hook that reads `useReducedMotion()`.
- **Implementation:** When true, replace spring transitions with opacity 0→1 over 50 ms.
- **Validation:** Provide a Storybook story that toggles the OS-level preference; capture a visual snapshot for both states in Chromatic.

### 2.3 Contrast Validation
- **Action:** Run the neon/hud color palette through the APCA contrast calculator; record WCAG 2.1 ratios for every color pair used in text-on-background.
- **Implementation:** Generate an accessible variant palette (suffix "-a11y") with ≥ 4.5:1 contrast; update Tailwind config and replace class names in situ.
- **Governance:** Add a `style-dictionary` build step that fails if any new color token falls below the threshold.

## 3. Design System

### 3.1 Color Scales
- **Action:** Refactor Tailwind custom colors into 9-step scales (100–900).
- **Implementation:** Align with L* in CIELAB (100 = 95 L*, 900 = 15 L*). Expose each scale as CSS variables (`--color-primary-500`) for runtime theming.
- **Validation:** Provide a story that switches themes in < 50 ms without FOIT.

### 3.2 Typography Enforcement
- **Action:** Create semantic components `Heading`, `Body`, `Label`.
- **Implementation:** Apply fixed font-family, size, line-height, and letter-spacing tokens.
- **Governance:** Write an eslint rule that disallows raw `<p>`, `<h1-6>`, or `<span>` elements; auto-fix violations to the semantic counterparts.

### 3.3 Grid Boundaries
- **Action:** Define a `Layout3D` container.
- **Implementation:** Use `isolation: isolate`, `position: relative`, z-index scope 0–100, and `overflow: hidden`.
- **Validation:** Enforce via CSS containment; add a visual regression test that asserts no 3D element bleeds outside its bounding box at 375 px and 1920 px viewports.

## 4. Testing & Quality Gates

### 4.1 Accessibility Testing
- **Action:** Integrate `jest-axe` into the existing Jest suite.
- **Implementation:** Run on every component that renders DOM or canvas fallback.
- **Governance:** Set the error threshold to 0 serious violations; block pull-request merge if violated.

### 4.2 Visual Regression
- **Action:** Configure Playwright to capture full-page screenshots of all cinematic components at 3 breakpoints.
- **Implementation:** Use `pixelmatch` with threshold 0.2.
- **Governance:** Fail CI if > 50 pixels differ from baseline without an approved Chromatic review.

### 4.3 Performance Budgets
- **Action:** Add a `budget.json` to the repo.
- **Implementation Rules:**
  - First-load bundle ≤ 250 kB gzipped
  - Largest Contentful Paint ≤ 2.5 s on Moto G4 throttling
  - Time to Interactive ≤ 5 s
- **Governance:** Run `lighthouse-ci` on every PR; auto-comment results and block merge if any metric regresses by > 5%.
