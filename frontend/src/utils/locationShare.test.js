import { buildLocationSharePath, buildLocationShareUrl, slugifyLocationSegment } from "./locationShare";

test("slugifies city and barrio names for share URLs", () => {
  expect(slugifyLocationSegment("Cartagena")).toBe("cartagena");
  expect(slugifyLocationSegment("Casco Antiguo")).toBe("casco-antiguo");
  expect(slugifyLocationSegment("L'Hospitalet de Llobregat")).toBe("l-hospitalet-de-llobregat");
});

test("builds city-only share URL", () => {
  expect(buildLocationSharePath("Cartagena")).toBe("/api/share/location/cartagena");
});

test("builds city+barrio share URL", () => {
  expect(buildLocationSharePath("Cartagena", "Casco Antiguo")).toBe("/api/share/location/cartagena/casco-antiguo");
  expect(buildLocationShareUrl("Cartagena", "Casco Antiguo")).toBe("https://cacaradar.es/api/share/location/cartagena/casco-antiguo");
});
