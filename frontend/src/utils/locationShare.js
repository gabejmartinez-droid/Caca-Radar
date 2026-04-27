import { HOSTED_WEB_URL } from "../config";

export function slugifyLocationSegment(value) {
  return String(value || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "espana";
}

export function buildLocationSharePath(city, barrio = "") {
  const citySlug = slugifyLocationSegment(city);
  const barrioSlug = barrio ? slugifyLocationSegment(barrio) : "";
  return barrioSlug
    ? `/api/share/location/${citySlug}/${barrioSlug}`
    : `/api/share/location/${citySlug}`;
}

export function buildLocationShareUrl(city, barrio = "") {
  return `${HOSTED_WEB_URL}${buildLocationSharePath(city, barrio)}`;
}

export function buildLocationImageUrl(city, barrio = "") {
  const citySlug = slugifyLocationSegment(city);
  const barrioSlug = barrio ? slugifyLocationSegment(barrio) : "";
  return barrioSlug
    ? `${HOSTED_WEB_URL}/api/share-image/location/${citySlug}/${barrioSlug}`
    : `${HOSTED_WEB_URL}/api/share-image/location/${citySlug}`;
}
