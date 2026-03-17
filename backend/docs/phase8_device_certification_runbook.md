# Phase 8 Device Certification Runbook

This runbook covers physical-device certification for immersive mission control where CI cannot emulate headset sensors.

## Scope

- Oculus / Meta Quest browser (`immersive-vr`)
- HoloLens WebXR host (`immersive-ar`)
- Desktop browser fallback

## Preconditions

- Backend API is running with `alembic upgrade head` applied.
- Frontend mission control route is available at `/visualization/mission-control`.
- Test tenant has at least one simulation bound to the same tenant.

## Test Matrix

1. Desktop Browser Baseline
- Open mission control and generate twin.
- Prepare playback and move timeline slider from start to finish.
- Export both `pdf` and `mp4`.
- Verify audit trail contains `visualization.export` success events.

2. Oculus / Meta Quest (VR)
- Open mission control from headset browser.
- Confirm `WebXR` status shows VR support.
- Enter VR session.
- Validate no tenant data appears outside active tenant simulation context.
- Exit session and verify playback controls remain functional.

3. HoloLens (AR)
- Open mission control from HoloLens browser host.
- Confirm `WebXR` status shows AR support.
- Enter AR session.
- Validate hotspot overlays align with timeline severity transitions.
- Exit session and verify app recovers to ready state.

## Acceptance Criteria

- Twin generation and playback succeed for all devices in scope.
- XR session start/end transitions complete without runtime errors.
- Export events are recorded with tenant id and simulation id.
- No cross-tenant visualization access is possible.

## Evidence Collection

- Screenshot of mission control status panel per device.
- API response payloads for `/visualization/twin`, `/visualization/playback`, `/visualization/export`.
- Audit log response snippet containing successful `visualization.export` entries.
