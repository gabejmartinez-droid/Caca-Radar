import { translations } from "../i18n/translations";
import { getRankLabel } from "./ranks";

const makeT = (lang) => (key) => {
  const value = key.split(".").reduce((current, part) => current?.[part], translations[lang]);
  return value ?? key;
};

test("localizes backend rank names through stable rank keys", () => {
  expect(getRankLabel("Aspirante Cagón", makeT("en"))).toBe("Poop Cadet");
  expect(getRankLabel("Director General de la Cagada Nacional", makeT("de"))).toBe(
    "Generaldirektor der nationalen Kack-Krise"
  );
  expect(getRankLabel("Comisario Principal del Apocalipsis Canino", makeT("eu"))).toBe(
    "Txakur Apokalipsiaren Komisario Nagusia"
  );
});
