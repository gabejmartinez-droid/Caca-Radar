import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import axios from "axios";
import { toast } from "sonner";
import { MapPin, Plus, User, LogIn, X, Camera, Flag, ThumbsUp, ThumbsDown, Clock, CheckCircle, Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { 
  Drawer, 
  DrawerContent, 
  DrawerHeader, 
  DrawerTitle, 
  DrawerDescription,
  DrawerFooter,
  DrawerClose 
} from "../components/ui/drawer";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import "leaflet/dist/leaflet.css";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

// Madrid center
const DEFAULT_CENTER = [40.4168, -3.7038];
const DEFAULT_ZOOM = 14;

// Calculate marker age category
function getMarkerCategory(createdAt) {
  const created = new Date(createdAt);
  const now = new Date();
  const hoursDiff = (now - created) / (1000 * 60 * 60);
  
  if (hoursDiff < 24) return "recent";
  if (hoursDiff < 72) return "moderate";
  return "old";
}

// Create custom marker icon
function createMarkerIcon(category) {
  const colors = {
    recent: "#FF5252",
    moderate: "#FFA726",
    old: "#66BB6A"
  };
  
  const color = colors[category];
  const pulseClass = category === "recent" ? "marker-recent" : "";
  
  return L.divIcon({
    className: "custom-marker-wrapper",
    html: `<div class="custom-marker ${pulseClass}" style="width: 32px; height: 32px; background-color: ${color};">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2">
        <circle cx="12" cy="12" r="3"/>
      </svg>
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16]
  });
}

// Map markers component
function MapMarkers({ reports, onMarkerClick }) {
  const map = useMap();
  const markersRef = useRef([]);

  useEffect(() => {
    // Clear existing markers
    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];

    // Add new markers
    reports.forEach(report => {
      const category = getMarkerCategory(report.created_at);
      const icon = createMarkerIcon(category);
      
      const marker = L.marker([report.latitude, report.longitude], { icon })
        .addTo(map)
        .on("click", () => onMarkerClick(report));
      
      markersRef.current.push(marker);
    });

    return () => {
      markersRef.current.forEach(marker => map.removeLayer(marker));
    };
  }, [reports, map, onMarkerClick]);

  return null;
}

// Location finder component
function LocationFinder({ onLocationFound }) {
  const map = useMapEvents({
    locationfound(e) {
      map.flyTo(e.latlng, 16);
      onLocationFound(e.latlng);
    },
    locationerror() {
      toast.error("No se pudo obtener tu ubicación");
    }
  });

  useEffect(() => {
    map.locate({ enableHighAccuracy: true });
  }, [map]);

  return null;
}

export default function MapPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [showReportDrawer, setShowReportDrawer] = useState(false);
  const [showDetailsDrawer, setShowDetailsDrawer] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [myVote, setMyVote] = useState(null);
  const fileInputRef = useRef(null);

  // Fetch reports
  const fetchReports = async () => {
    try {
      const { data } = await axios.get(`${API}/reports`, { withCredentials: true });
      setReports(data);
    } catch (error) {
      console.error("Error fetching reports:", error);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Handle marker click
  const handleMarkerClick = async (report) => {
    setSelectedReport(report);
    setShowDetailsDrawer(true);
    
    // Check if user has voted
    try {
      const { data } = await axios.get(`${API}/reports/${report.id}/my-vote`, { withCredentials: true });
      setMyVote(data.vote?.vote_type || null);
    } catch {
      setMyVote(null);
    }
  };

  // Handle photo selection
  const handlePhotoSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error("La foto es demasiado grande (max 5MB)");
        return;
      }
      setPhotoFile(file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  // Submit report
  const handleSubmitReport = async () => {
    if (!userLocation) {
      toast.error("No se pudo obtener tu ubicación");
      return;
    }

    setLoading(true);
    try {
      // Create report
      const { data: report } = await axios.post(`${API}/reports`, {
        latitude: userLocation.lat,
        longitude: userLocation.lng
      }, { withCredentials: true });

      // Upload photo if selected
      if (photoFile) {
        const formData = new FormData();
        formData.append("file", photoFile);
        await axios.post(`${API}/reports/${report.id}/photo`, formData, {
          withCredentials: true,
          headers: { "Content-Type": "multipart/form-data" }
        });
      }

      toast.success("Reporte enviado correctamente");
      setShowReportDrawer(false);
      setPhotoFile(null);
      setPhotoPreview(null);
      fetchReports();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al enviar el reporte");
    } finally {
      setLoading(false);
    }
  };

  // Handle vote
  const handleVote = async (voteType) => {
    if (!selectedReport) return;
    
    setLoading(true);
    try {
      await axios.post(`${API}/reports/${selectedReport.id}/vote`, {
        vote_type: voteType
      }, { withCredentials: true });
      
      setMyVote(voteType);
      toast.success(voteType === "still_there" ? "Confirmado que sigue ahí" : "Marcado como limpio");
      
      // Refresh reports
      fetchReports();
      
      // Update selected report
      const { data } = await axios.get(`${API}/reports/${selectedReport.id}`, { withCredentials: true });
      setSelectedReport(data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al votar");
    } finally {
      setLoading(false);
    }
  };

  // Handle flag
  const handleFlag = async () => {
    if (!selectedReport) return;
    
    try {
      await axios.post(`${API}/reports/${selectedReport.id}/flag`, {}, { withCredentials: true });
      toast.success("Reporte marcado como inapropiado");
      setShowDetailsDrawer(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al marcar el reporte");
    }
  };

  // Format date
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffHours < 1) return "Hace menos de 1 hora";
    if (diffHours < 24) return `Hace ${diffHours} hora${diffHours > 1 ? "s" : ""}`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `Hace ${diffDays} día${diffDays > 1 ? "s" : ""}`;
    
    return date.toLocaleDateString("es-ES");
  };

  return (
    <div className="h-full w-full relative" data-testid="map-page">
      {/* Map */}
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        className="h-full w-full"
        zoomControl={false}
        data-testid="map-container"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LocationFinder onLocationFound={setUserLocation} />
        <MapMarkers reports={reports} onMarkerClick={handleMarkerClick} />
      </MapContainer>

      {/* Header */}
      <div className="absolute top-4 left-4 right-4 z-[1000] flex justify-between items-center">
        <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg px-4 py-2 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-[#FF6B6B]" />
          <span className="font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>Caca Radar</span>
        </div>
        
        <div className="flex gap-2">
          {user ? (
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="bg-white/95 backdrop-blur-sm shadow-lg border-0"
              data-testid="logout-btn"
            >
              <User className="w-4 h-4 mr-1" />
              {user.name || "Usuario"}
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/login")}
              className="bg-white/95 backdrop-blur-sm shadow-lg border-0"
              data-testid="login-btn"
            >
              <LogIn className="w-4 h-4 mr-1" />
              Entrar
            </Button>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-28 left-4 z-[1000] bg-white/95 backdrop-blur-sm rounded-xl shadow-lg p-3">
        <div className="flex flex-col gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#FF5252]"></div>
            <span className="text-[#2B2D42]">Reciente (&lt;24h)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#FFA726]"></div>
            <span className="text-[#2B2D42]">1-3 días</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#66BB6A]"></div>
            <span className="text-[#2B2D42]">&gt;3 días</span>
          </div>
        </div>
      </div>

      {/* FAB - Report Button */}
      <button
        onClick={() => setShowReportDrawer(true)}
        className="fixed bottom-8 left-1/2 -translate-x-1/2 px-8 py-4 bg-[#FF6B6B] text-white rounded-full shadow-lg font-bold text-lg flex items-center gap-2 z-[1000] hover:bg-[#FF5252] hover:-translate-y-1 transition-all duration-200"
        style={{ fontFamily: 'Nunito, sans-serif' }}
        data-testid="report-btn"
      >
        <Plus className="w-5 h-5" />
        Reportar
      </button>

      {/* Report Drawer */}
      <Drawer open={showReportDrawer} onOpenChange={setShowReportDrawer}>
        <DrawerContent className="rounded-t-3xl" data-testid="report-drawer">
          <DrawerHeader className="text-center">
            <DrawerTitle className="text-xl font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>
              Reportar caca de perro
            </DrawerTitle>
            <DrawerDescription className="text-[#8D99AE]">
              Tu ubicación se añadirá automáticamente
            </DrawerDescription>
          </DrawerHeader>

          <div className="px-4 pb-4">
            {/* Location indicator */}
            <div className="flex items-center justify-center gap-2 p-4 bg-[#F8F9FA] rounded-xl mb-4">
              <MapPin className="w-5 h-5 text-[#FF6B6B]" />
              {userLocation ? (
                <span className="text-sm text-[#2B2D42]">
                  {userLocation.lat.toFixed(6)}, {userLocation.lng.toFixed(6)}
                </span>
              ) : (
                <span className="text-sm text-[#8D99AE]">Obteniendo ubicación...</span>
              )}
            </div>

            {/* Photo upload */}
            <input
              type="file"
              accept="image/*"
              capture="environment"
              ref={fileInputRef}
              onChange={handlePhotoSelect}
              className="hidden"
              data-testid="photo-input"
            />
            
            {photoPreview ? (
              <div className="relative mb-4">
                <img
                  src={photoPreview}
                  alt="Preview"
                  className="w-full h-48 object-cover rounded-xl"
                />
                <button
                  onClick={() => {
                    setPhotoFile(null);
                    setPhotoPreview(null);
                  }}
                  className="absolute top-2 right-2 p-1 bg-black/50 rounded-full text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full p-8 border-2 border-dashed border-[#8D99AE]/30 rounded-xl flex flex-col items-center gap-2 text-[#8D99AE] hover:border-[#FF6B6B] hover:text-[#FF6B6B] transition-colors mb-4"
                data-testid="add-photo-btn"
              >
                <Camera className="w-8 h-8" />
                <span>Añadir foto (opcional)</span>
              </button>
            )}
          </div>

          <DrawerFooter className="pt-0">
            <Button
              onClick={handleSubmitReport}
              disabled={loading || !userLocation}
              className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-6 rounded-xl text-lg font-bold"
              style={{ fontFamily: 'Nunito, sans-serif' }}
              data-testid="submit-report-btn"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                "Enviar reporte"
              )}
            </Button>
            <DrawerClose asChild>
              <Button variant="ghost" className="text-[#8D99AE]">Cancelar</Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>

      {/* Details Drawer */}
      <Drawer open={showDetailsDrawer} onOpenChange={setShowDetailsDrawer}>
        <DrawerContent className="rounded-t-3xl" data-testid="details-drawer">
          <DrawerHeader>
            <DrawerTitle className="text-xl font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>
              Detalles del reporte
            </DrawerTitle>
          </DrawerHeader>

          {selectedReport && (
            <div className="px-4 pb-4">
              {/* Photo */}
              {selectedReport.photo_url && (
                <div className="mb-4 rounded-xl overflow-hidden">
                  <img
                    src={`${API}/files/${selectedReport.photo_url}`}
                    alt="Foto del reporte"
                    className="w-full h-48 object-cover"
                    data-testid="report-photo"
                  />
                </div>
              )}

              {/* Info */}
              <div className="bg-[#F8F9FA] rounded-xl p-4 mb-4">
                <div className="flex items-center gap-2 text-[#8D99AE] mb-2">
                  <Clock className="w-4 h-4" />
                  <span className="text-sm">{formatDate(selectedReport.created_at)}</span>
                </div>
                <div className="flex gap-4">
                  <div className="flex items-center gap-1">
                    <ThumbsUp className="w-4 h-4 text-[#FF5252]" />
                    <span className="text-sm font-medium text-[#2B2D42]">
                      {selectedReport.still_there_count || 0} sigue ahí
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <CheckCircle className="w-4 h-4 text-[#66BB6A]" />
                    <span className="text-sm font-medium text-[#2B2D42]">
                      {selectedReport.cleaned_count || 0} limpio
                    </span>
                  </div>
                </div>
              </div>

              {/* Vote buttons */}
              {!myVote ? (
                <div className="flex gap-3 mb-4">
                  <Button
                    onClick={() => handleVote("still_there")}
                    disabled={loading}
                    className="flex-1 bg-[#FF5252] hover:bg-[#E53935] text-white py-6 rounded-xl"
                    data-testid="vote-still-there-btn"
                  >
                    <ThumbsUp className="w-5 h-5 mr-2" />
                    Sigue ahí
                  </Button>
                  <Button
                    onClick={() => handleVote("cleaned")}
                    disabled={loading}
                    className="flex-1 bg-[#66BB6A] hover:bg-[#4CAF50] text-white py-6 rounded-xl"
                    data-testid="vote-cleaned-btn"
                  >
                    <CheckCircle className="w-5 h-5 mr-2" />
                    Ya limpio
                  </Button>
                </div>
              ) : (
                <div className="bg-[#F8F9FA] rounded-xl p-4 mb-4 text-center">
                  <span className="text-[#8D99AE]">
                    Ya votaste: {myVote === "still_there" ? "Sigue ahí" : "Ya limpio"}
                  </span>
                </div>
              )}

              {/* Flag button */}
              <Button
                variant="ghost"
                onClick={handleFlag}
                className="w-full text-[#8D99AE] hover:text-[#FF5252]"
                data-testid="flag-report-btn"
              >
                <Flag className="w-4 h-4 mr-2" />
                Reportar contenido inapropiado
              </Button>
            </div>
          )}

          <DrawerFooter className="pt-0">
            <DrawerClose asChild>
              <Button variant="ghost" className="text-[#8D99AE]">Cerrar</Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </div>
  );
}
