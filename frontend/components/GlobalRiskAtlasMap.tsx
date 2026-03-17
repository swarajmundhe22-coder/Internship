import { useMemo, useState } from "react";

import DeckGL from "@deck.gl/react";
import { ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import Map, { NavigationControl } from "react-map-gl";

import { AtlasOverlayPoint } from "../types/domain";

type GlobalRiskAtlasMapProps = {
  points: AtlasOverlayPoint[];
};

const INITIAL_VIEW_STATE = {
  latitude: 20,
  longitude: 0,
  zoom: 1.2,
  pitch: 25,
  bearing: 0
};

function colorForSeverity(severity: AtlasOverlayPoint["severity"]): [number, number, number, number] {
  if (severity === "red") {
    return [239, 68, 68, 200];
  }
  if (severity === "yellow") {
    return [250, 204, 21, 190];
  }
  return [34, 197, 94, 185];
}

export function GlobalRiskAtlasMap({ points }: GlobalRiskAtlasMapProps) {
  const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;
  const [hovered, setHovered] = useState<{ x: number; y: number; point: AtlasOverlayPoint } | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<AtlasOverlayPoint | null>(null);

  const layers = useMemo(() => {
    const scatter = new ScatterplotLayer<AtlasOverlayPoint>({
      id: "atlas-severity-points",
      data: points,
      pickable: true,
      radiusUnits: "pixels",
      getPosition: (point: AtlasOverlayPoint) => [point.longitude, point.latitude],
      getRadius: (point: AtlasOverlayPoint) => 12 + point.score * 30,
      getFillColor: (point: AtlasOverlayPoint) => colorForSeverity(point.severity),
      getLineColor: [225, 235, 245, 220],
      lineWidthUnits: "pixels",
      lineWidthMinPixels: 1
    });

    const labels = new TextLayer<AtlasOverlayPoint>({
      id: "atlas-labels",
      data: points,
      pickable: false,
      getPosition: (point: AtlasOverlayPoint) => [point.longitude, point.latitude],
      getText: (point: AtlasOverlayPoint) => point.label,
      getSize: 12,
      sizeUnits: "pixels",
      getColor: [230, 241, 255, 210],
      getPixelOffset: [0, -24],
      getTextAnchor: "middle",
      getAlignmentBaseline: "center"
    });

    return [scatter, labels];
  }, [points]);

  if (!mapboxToken) {
    return (
      <div className="relative h-[460px] overflow-hidden rounded-xl border border-lagoon/35 bg-slatewash/35 p-5">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(0,229,255,0.18),transparent_45%),radial-gradient(circle_at_75%_35%,rgba(239,68,68,0.14),transparent_45%),linear-gradient(125deg,rgba(12,17,25,0.95),rgba(19,26,38,0.92))]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(0,229,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(0,229,255,0.06)_1px,transparent_1px)] bg-[size:36px_36px] opacity-50" />
        <div className="relative z-10 grid h-full place-items-center text-center text-sm text-softwhite/80">
          <div>
            <p className="hud-label text-[11px]">Atlas Map Scaffold</p>
            <p className="mt-2 max-w-md">
              Set NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN to enable live Mapbox tiles. Deck.gl overlay layers are already wired and will render automatically once token is present.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-[460px] overflow-hidden rounded-xl border border-lagoon/35">
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller
        layers={layers}
        onHover={(info) => {
          const point = info.object as AtlasOverlayPoint | undefined;
          if (!point || typeof info.x !== "number" || typeof info.y !== "number") {
            setHovered(null);
            return;
          }
          setHovered({ x: info.x, y: info.y, point });
        }}
        onClick={(info) => {
          const point = info.object as AtlasOverlayPoint | undefined;
          setSelectedPoint(point ?? null);
        }}
      >
        <Map
          mapboxAccessToken={mapboxToken}
          mapStyle="mapbox://styles/mapbox/dark-v11"
          attributionControl={false}
          reuseMaps
        >
          <NavigationControl position="top-right" />
        </Map>
      </DeckGL>

      {hovered && (
        <div
          className="pointer-events-none absolute z-10 rounded-md border border-lagoon/50 bg-black/80 px-3 py-2 text-xs text-softwhite"
          style={{ left: hovered.x + 10, top: hovered.y + 10 }}
          data-testid="atlas-tooltip"
        >
          <p className="font-semibold">{hovered.point.label}</p>
          <p>Severity: {hovered.point.severity}</p>
          <p>Score: {hovered.point.score.toFixed(2)}</p>
        </div>
      )}

      {selectedPoint && (
        <div className="absolute bottom-3 left-3 right-3 z-10 rounded-md border border-neoviolet/45 bg-slatewash/80 p-3 text-xs text-softwhite/90" data-testid="atlas-selected-point">
          <p className="font-semibold text-softwhite">Selected Hotspot: {selectedPoint.label}</p>
          <p>Severity: {selectedPoint.severity}</p>
          <p>Coordinates: {selectedPoint.latitude.toFixed(2)}, {selectedPoint.longitude.toFixed(2)}</p>
          <p>Risk score: {selectedPoint.score.toFixed(2)}</p>
        </div>
      )}
    </div>
  );
}
