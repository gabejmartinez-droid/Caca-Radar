import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";
import axios from "axios";

const API = "/api";

export default function NotificationChecker() {
  const { user } = useAuth();
  const checked = useRef(false);

  useEffect(() => {
    if (!user || checked.current) return;
    checked.current = true;

    const checkNotifications = async () => {
      try {
        const { data } = await axios.get(`${API}/notifications`, { withCredentials: true });
        for (const n of data) {
          if (n.type === "rank_change") {
            const isPromotion = RANK_ORDER.indexOf(n.new_rank) < RANK_ORDER.indexOf(n.old_rank);
            if (isPromotion) {
              toast.success(`Has ascendido a ${n.new_rank}`, { duration: 6000 });
            } else {
              toast.info(`Tu rango ha cambiado a ${n.new_rank}`, { duration: 6000 });
            }
          }
        }
        if (data.length > 0) {
          await axios.post(`${API}/notifications/read`, {}, { withCredentials: true });
        }
      } catch {
        // silently fail
      }
    };

    checkNotifications();
  }, [user]);

  return null;
}

// Rank order from highest to lowest
const RANK_ORDER = [
  "Director General de la Cagada Nacional",
  "Comisario Principal del Apocalipsis Canino",
  "Comisario de Heces Urbanas",
  "Inspector Jefe del Marrón",
  "Inspector de Truños",
  "Subinspector del Mojón",
  "Oficial de Deposiciones",
  "Policía de la Caca",
  "Agente de Excrementos",
  "Aspirante Cagón",
];
