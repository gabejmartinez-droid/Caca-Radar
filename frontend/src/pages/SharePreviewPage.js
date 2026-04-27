import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { LanguageSelector } from "../components/LanguageSelector";
import { buildLocationImageUrl, buildLocationShareUrl } from "../utils/locationShare";

export default function SharePreviewPage() {
  const [searchParams] = useSearchParams();
  const city = searchParams.get("city") || "Madrid";
  const barrio = searchParams.get("barrio") || "";

  const previewUrl = useMemo(() => buildLocationImageUrl(city, barrio), [city, barrio]);
  const shareUrl = useMemo(() => buildLocationShareUrl(city, barrio), [city, barrio]);
  const label = barrio ? `${city} — ${barrio}` : city;

  return (
    <div className="min-h-screen bg-[#F8F9FA] px-4 py-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-black text-[#2B2D42]">Share preview</h1>
            <p className="text-sm text-[#5C677D]">{label}</p>
          </div>
          <LanguageSelector />
        </div>
        <div className="bg-white rounded-2xl shadow-sm p-4">
          <img src={previewUrl} alt={label} className="w-full h-auto rounded-xl border border-[#8D99AE]/10" />
          <div className="mt-4 text-sm text-[#5C677D] break-all">{shareUrl}</div>
        </div>
      </div>
    </div>
  );
}
