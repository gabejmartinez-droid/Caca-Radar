import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Trophy, MapPin, ArrowLeft, Crown, Medal, Award, Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

function RankIcon({ rank }) {
  if (rank === 1) return <Crown className="w-5 h-5 text-yellow-500" />;
  if (rank === 2) return <Medal className="w-5 h-5 text-gray-400" />;
  if (rank === 3) return <Award className="w-5 h-5 text-amber-600" />;
  return <span className="w-5 h-5 flex items-center justify-center text-sm font-bold text-[#8D99AE]">{rank}</span>;
}

export default function LeaderboardPage() {
  const { user } = useAuth();
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();

  const [national, setNational] = useState([]);
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState(null);
  const [cityLeaderboard, setCityLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.subscription_active) {
      navigate("/subscribe");
      return;
    }
    fetchData();
  }, [user, navigate]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [natRes, citiesRes] = await Promise.all([
        axios.get(`${API}/leaderboard/national`, { withCredentials: true }),
        axios.get(`${API}/leaderboard/cities`, { withCredentials: true })
      ]);
      setNational(natRes.data);
      setCities(citiesRes.data);
    } catch (err) {
      if (err.response?.status === 403) navigate("/subscribe");
    } finally {
      setLoading(false);
    }
  };

  const fetchCityLeaderboard = async (cityName) => {
    setSelectedCity(cityName);
    try {
      const { data } = await axios.get(`${API}/leaderboard/city/${encodeURIComponent(cityName)}`, { withCredentials: true });
      setCityLeaderboard(data);
    } catch (err) {
      toast.error("Error loading city leaderboard");
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-[#FF6B6B]" />
    </div>
  );

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? 'rtl' : 'ltr'}`} data-testid="leaderboard-page">
      <div className="p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-lg mx-auto px-4 pb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-[#FF6B6B] rounded-full flex items-center justify-center">
            <Trophy className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>Leaderboard</h1>
        </div>

        <Tabs defaultValue="national" className="w-full">
          <TabsList className="w-full mb-4">
            <TabsTrigger value="national" className="flex-1" data-testid="tab-national">Nacional</TabsTrigger>
            <TabsTrigger value="city" className="flex-1" data-testid="tab-city">Por Ciudad</TabsTrigger>
          </TabsList>

          <TabsContent value="national">
            <div className="space-y-2">
              {national.length === 0 ? (
                <p className="text-center text-[#8D99AE] py-8">No hay datos todavía</p>
              ) : national.map((entry) => (
                <div key={entry.rank} className={`flex items-center gap-3 p-4 bg-white rounded-xl shadow-sm ${entry.rank <= 3 ? 'border-l-4 border-[#FF6B6B]' : ''}`} data-testid={`national-rank-${entry.rank}`}>
                  <RankIcon rank={entry.rank} />
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-[#2B2D42] truncate">{entry.display_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-[#FF6B6B]">{entry.total_score}</p>
                    <p className="text-xs text-[#8D99AE]">{entry.report_count} reportes / {entry.vote_count} votos</p>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="city">
            {!selectedCity ? (
              <div className="space-y-2">
                {cities.length === 0 ? (
                  <p className="text-center text-[#8D99AE] py-8">No hay ciudades con reportes</p>
                ) : cities.map((city) => (
                  <button key={city.name} onClick={() => fetchCityLeaderboard(city.name)} className="w-full flex items-center gap-3 p-4 bg-white rounded-xl shadow-sm hover:bg-[#F8F9FA] transition-colors text-left" data-testid={`city-${city.name}`}>
                    <MapPin className="w-5 h-5 text-[#FF6B6B]" />
                    <div className="flex-1">
                      <p className="font-semibold text-[#2B2D42]">{city.name}</p>
                      <p className="text-xs text-[#8D99AE]">{city.province}</p>
                    </div>
                    <span className="text-sm font-bold text-[#FF6B6B]">{city.report_count}</span>
                  </button>
                ))}
              </div>
            ) : (
              <div>
                <Button variant="ghost" size="sm" onClick={() => { setSelectedCity(null); setCityLeaderboard([]); }} className="mb-4 text-[#8D99AE]">
                  <ArrowLeft className="w-4 h-4 mr-1" /> {selectedCity}
                </Button>
                <div className="space-y-2">
                  {cityLeaderboard.length === 0 ? (
                    <p className="text-center text-[#8D99AE] py-8">No hay datos para esta ciudad</p>
                  ) : cityLeaderboard.map((entry) => (
                    <div key={entry.rank} className={`flex items-center gap-3 p-4 bg-white rounded-xl shadow-sm ${entry.rank <= 3 ? 'border-l-4 border-[#FF6B6B]' : ''}`}>
                      <RankIcon rank={entry.rank} />
                      <div className="flex-1 min-w-0"><p className="font-semibold text-[#2B2D42] truncate">{entry.display_name}</p></div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-[#FF6B6B]">{entry.total_score}</p>
                        <p className="text-xs text-[#8D99AE]">{entry.report_count} / {entry.vote_count}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
