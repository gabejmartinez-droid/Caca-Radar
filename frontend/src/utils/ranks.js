export const RANK_IDS = {
  ASPIRANTE_CAGON: "aspiranteCagon",
  AGENTE_EXCREMENTOS: "agenteExcrementos",
  POLICIA_CACA: "policiaCaca",
  OFICIAL_DEPOSICIONES: "oficialDeposiciones",
  SUBINSPECTOR_MOJON: "subinspectorMojon",
  INSPECTOR_TRUNOS: "inspectorTrunos",
  INSPECTOR_JEFE_MARRON: "inspectorJefeMarron",
  COMISARIO_HECES_URBANAS: "comisarioHecesUrbanas",
  COMISARIO_APOCALIPSIS_CANINO: "comisarioApocalipsisCanino",
  DIRECTOR_CAGADA_NACIONAL: "directorCagadaNacional",
};

export const DEFAULT_RANK_ID = RANK_IDS.ASPIRANTE_CAGON;

export const RANKS = [
  { id: RANK_IDS.ASPIRANTE_CAGON, key: "ranks.aspiranteCagon", es: "Aspirante Cagón" },
  { id: RANK_IDS.AGENTE_EXCREMENTOS, key: "ranks.agenteExcrementos", es: "Agente de Excrementos" },
  { id: RANK_IDS.POLICIA_CACA, key: "ranks.policiaCaca", es: "Policía de la Caca" },
  { id: RANK_IDS.OFICIAL_DEPOSICIONES, key: "ranks.oficialDeposiciones", es: "Oficial de Deposiciones" },
  { id: RANK_IDS.SUBINSPECTOR_MOJON, key: "ranks.subinspectorMojon", es: "Subinspector del Mojón" },
  { id: RANK_IDS.INSPECTOR_TRUNOS, key: "ranks.inspectorTrunos", es: "Inspector de Truños" },
  { id: RANK_IDS.INSPECTOR_JEFE_MARRON, key: "ranks.inspectorJefeMarron", es: "Inspector Jefe del Marrón" },
  { id: RANK_IDS.COMISARIO_HECES_URBANAS, key: "ranks.comisarioHecesUrbanas", es: "Comisario de Heces Urbanas" },
  { id: RANK_IDS.COMISARIO_APOCALIPSIS_CANINO, key: "ranks.comisarioApocalipsisCanino", es: "Comisario Principal del Apocalipsis Canino" },
  { id: RANK_IDS.DIRECTOR_CAGADA_NACIONAL, key: "ranks.directorCagadaNacional", es: "Director General de la Cagada Nacional" },
];

export const RANK_ORDER = [
  RANK_IDS.DIRECTOR_CAGADA_NACIONAL,
  RANK_IDS.COMISARIO_APOCALIPSIS_CANINO,
  RANK_IDS.COMISARIO_HECES_URBANAS,
  RANK_IDS.INSPECTOR_JEFE_MARRON,
  RANK_IDS.INSPECTOR_TRUNOS,
  RANK_IDS.SUBINSPECTOR_MOJON,
  RANK_IDS.OFICIAL_DEPOSICIONES,
  RANK_IDS.POLICIA_CACA,
  RANK_IDS.AGENTE_EXCREMENTOS,
  RANK_IDS.ASPIRANTE_CAGON,
];

const RANK_BY_ID = Object.fromEntries(RANKS.map((rank) => [rank.id, rank]));
const RANK_ID_BY_SPANISH = Object.fromEntries(RANKS.map((rank) => [rank.es, rank.id]));

export function getRankId(rankOrId) {
  if (!rankOrId) return DEFAULT_RANK_ID;
  if (RANK_BY_ID[rankOrId]) return rankOrId;
  return RANK_ID_BY_SPANISH[rankOrId] || DEFAULT_RANK_ID;
}

export function getRankKey(rankOrId) {
  return RANK_BY_ID[getRankId(rankOrId)].key;
}

export function getRankLabel(rankOrId, t) {
  const key = getRankKey(rankOrId);
  const translated = t(key);
  if (translated && translated !== key) return translated;
  return RANK_BY_ID[getRankId(rankOrId)].es;
}

export function compareRanks(a, b) {
  const aIndex = RANK_ORDER.indexOf(getRankId(a));
  const bIndex = RANK_ORDER.indexOf(getRankId(b));
  return (aIndex === -1 ? RANK_ORDER.length : aIndex) - (bIndex === -1 ? RANK_ORDER.length : bIndex);
}

export function formatTranslation(t, key, values = {}) {
  return Object.entries(values).reduce(
    (message, [name, value]) => message.replaceAll(`{${name}}`, value ?? ""),
    t(key)
  );
}
