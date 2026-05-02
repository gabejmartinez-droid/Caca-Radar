import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const MAP_MARKER_STYLES = {
  active: { color: "#FF6B6B", radius: 7, fillOpacity: 0.8 },
  flagged: { color: "#FFA726", radius: 6, fillOpacity: 0.7 },
  archived: { color: "#66BB6A", radius: 5, fillOpacity: 0.45 },
};

export default function MunicipalityMapCard({ mapData, title = "Mapa del municipio", subtitle }) {
  if (!mapData?.points?.length || !mapData?.bounds) {
    return (
      <div className="bg-white rounded-2xl shadow-sm p-6 text-center text-[#8D99AE]">
        No hay reportes geolocalizados para mostrar en el mapa.
      </div>
    );
  }

  const bounds = [
    [mapData.bounds.south, mapData.bounds.west],
    [mapData.bounds.north, mapData.bounds.east],
  ];
  const isSinglePoint =
    mapData.bounds.south === mapData.bounds.north &&
    mapData.bounds.west === mapData.bounds.east;
  const center = [mapData.bounds.center_lat, mapData.bounds.center_lng];

  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
      <div className="p-5 border-b border-[#8D99AE]/10">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-lg font-bold text-[#2B2D42]">{title}</h2>
            <p className="text-sm text-[#8D99AE]">
              {subtitle || `Vista general de los reportes en ${mapData.municipality} a nivel ciudad.`}
            </p>
          </div>
          <div className="flex gap-2 flex-wrap text-xs">
            <span className="inline-flex items-center gap-1 rounded-full bg-[#FF6B6B]/10 text-[#FF6B6B] px-3 py-1 font-bold">
              <span className="w-2 h-2 rounded-full bg-[#FF6B6B]" /> Activos {mapData.active_reports}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-[#FFA726]/10 text-[#C77800] px-3 py-1 font-bold">
              <span className="w-2 h-2 rounded-full bg-[#FFA726]" /> Reportados {mapData.flagged_reports}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-[#66BB6A]/10 text-[#2E7D32] px-3 py-1 font-bold">
              <span className="w-2 h-2 rounded-full bg-[#66BB6A]" /> Archivados {mapData.archived_reports}
            </span>
          </div>
        </div>
      </div>

      <div className="h-[420px]">
        <MapContainer
          {...(isSinglePoint ? { center, zoom: 14 } : { bounds, boundsOptions: { padding: [28, 28] } })}
          className="h-full w-full"
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {mapData.points.map((point) => {
            const style = MAP_MARKER_STYLES[point.type] || MAP_MARKER_STYLES.active;
            return (
              <CircleMarker
                key={point.id}
                center={[point.lat, point.lng]}
                radius={style.radius}
                pathOptions={{
                  color: style.color,
                  fillColor: style.color,
                  fillOpacity: style.fillOpacity,
                  weight: 2,
                }}
              />
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
