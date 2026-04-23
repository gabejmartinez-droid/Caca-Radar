export function isWithinSpain(lat, lng) {
  const latitude = Number(lat);
  const longitude = Number(lng);
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return false;
  return latitude >= 27.0 && latitude <= 44.0 && longitude >= -19.0 && longitude <= 5.0;
}
