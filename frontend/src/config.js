// API base URL — uses env var if set, otherwise falls back to hosted backend.
// Capacitor loads from capacitor://localhost so relative /api breaks native networking.
const DEFAULT_BACKEND_URL = "https://caca-radar.preview.emergentagent.com";
export const API = (process.env.REACT_APP_BACKEND_URL || DEFAULT_BACKEND_URL) + "/api";
