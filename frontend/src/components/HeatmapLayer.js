import { useEffect, useMemo, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";

const HEAT_OPTIONS = {
  radius: 26,
  blur: 18,
  maxZoom: 17,
  max: 1.0,
  minOpacity: 0.18,
  gradient: {
    0.0: "rgba(66, 165, 245, 0)",
    0.2: "#42A5F5",
    0.45: "#66BB6A",
    0.7: "#FFA726",
    1.0: "#FF5252"
  }
};

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getReportWeight(report) {
  const confidence = clamp((report.confidence ?? report.confidence_score ?? 50) / 100, 0, 1);
  const validations = clamp((report.validation_count || 0) * 0.14, 0, 0.45);
  const netVotes = clamp(((report.upvotes || 0) - (report.downvotes || 0)) * 0.05, -0.15, 0.3);
  const freshnessBoost = report.freshness === "Fresca" ? 0.18 : report.freshness === "En proceso" ? 0.08 : 0;
  return clamp(0.35 + (confidence * 0.4) + validations + netVotes + freshnessBoost, 0.18, 1);
}

function buildHeatData(reports) {
  const buckets = new Map();

  reports.forEach((report) => {
    const lat = Number(report.latitude);
    const lng = Number(report.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    const key = `${lat.toFixed(5)},${lng.toFixed(5)}`;
    const pointWeight = getReportWeight(report);
    const existing = buckets.get(key);

    if (existing) {
      existing.weight += pointWeight;
      existing.count += 1;
      return;
    }

    buckets.set(key, { lat, lng, weight: pointWeight, count: 1 });
  });

  return Array.from(buckets.values(), ({ lat, lng, weight, count }) => {
    const aggregateWeight = clamp((weight / count) + (Math.log2(count + 1) * 0.2), 0.2, 1);
    return [lat, lng, aggregateWeight];
  });
}

export function HeatmapLayer({ reports, visible }) {
  const map = useMap();
  const heatLayerRef = useRef(null);
  const heatData = useMemo(() => buildHeatData(reports), [reports]);

  useEffect(() => {
    if (!visible) {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
        heatLayerRef.current = null;
      }
      return;
    }

    if (heatLayerRef.current) {
      heatLayerRef.current.setLatLngs(heatData);
    } else {
      heatLayerRef.current = L.heatLayer(heatData, HEAT_OPTIONS).addTo(map);
    }

    return () => {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
        heatLayerRef.current = null;
      }
    };
  }, [heatData, visible, map]);

  return null;
}
