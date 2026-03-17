# The On Lookers Brand Input Pack

This file lists the optional inputs needed to replace procedural placeholders with custom-crafted brand assets and direction.

## 1) Visual Assets
Place files under frontend/public/brand/

- onlookers-mark.svg
  - Usage: transition/logo motif overlays
  - Preferred: monochrome SVG
- planet-normal.jpg
  - Usage: normal map for WebGL hero sphere
  - Preferred: seamless 2k texture
- transition-noise.png
  - Usage: transition grain/noise mask (reserved for next pass)
  - Preferred: tileable grayscale 1k

## 2) Art Direction Inputs
Provide per route family if possible.

- Home: desired emotional tone in 3 words
- Dashboard: desired emotional tone in 3 words
- Simulations: desired emotional tone in 3 words
- Reports: desired emotional tone in 3 words
- Admin: desired emotional tone in 3 words

## 3) Motion Signature Inputs
For each item, provide a value from 1 to 10.

- Transition aggressiveness
- Camera movement intensity
- Parallax intensity
- UI pulse intensity
- Cinematic glow intensity

## 4) Typography Inputs
- Preferred display font candidates (2-3)
- Preferred body font candidates (2-3)
- Preferred numeral style: technical | editorial | neutral

## 5) Brand Constraints
- Elements to avoid (colors, motifs, pacing styles)
- Accessibility constraints (reduce motion policy, contrast priorities)
- Any references that should not be mirrored

## Current Integration Points
- Brand config: frontend/utils/brandDirection.ts
- Route transitions: frontend/pages/_app.tsx
- WebGL scene direction: frontend/components/CinematicWebGLBackdrop.tsx
- Route micro-timing: frontend/hooks/useRouteCinematicTimeline.ts
- Scroll choreography timing: frontend/hooks/useCinematicScrollChoreography.ts
