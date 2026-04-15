import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";

const HEAT_OPTIONS = {
  radius: 30,
  blur: 20,
  maxZoom: 17,
  max: 1.0,
  gradient: { 0.0: "#66BB6A", 0.3: "#FFA726", 0.6: "#FF6B6B", 1.0: "#FF5252" }
};

function buildHeatData(reports) {
  return reports.map((r) => {
    const hoursAge = (Date.now() - new Date(r.created_at).getTime()) / (1000 * 60 * 60);
    const intensity = hoursAge < 24 ? 1.0 : hoursAge < 72 ? 0.6 : 0.3;
    return [r.latitude, r.longitude, intensity];
  });
}

export function HeatmapLayer({ reports, visible }) {
  const map = useMap();
  const heatLayerRef = useRef(null);

  useEffect(() => {
    if (!visible) {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
        heatLayerRef.current = null;
      }
      return;
    }

    const heatData = buildHeatData(reports);

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
  }, [reports, visible, map]);

  return null;
}
