"""Single source of truth for Caca Radar rank metadata."""

RANKS = [
    {
        "id": "aspiranteCagon",
        "threshold": 100,
        "name": "Aspirante Cagón",
    },
    {
        "id": "agenteExcrementos",
        "threshold": 75,
        "name": "Agente de Excrementos",
    },
    {
        "id": "policiaCaca",
        "threshold": 55,
        "name": "Policía de la Caca",
    },
    {
        "id": "oficialDeposiciones",
        "threshold": 40,
        "name": "Oficial de Deposiciones",
    },
    {
        "id": "subinspectorMojon",
        "threshold": 28,
        "name": "Subinspector del Mojón",
    },
    {
        "id": "inspectorTrunos",
        "threshold": 18,
        "name": "Inspector de Truños",
    },
    {
        "id": "inspectorJefeMarron",
        "threshold": 11,
        "name": "Inspector Jefe del Marrón",
    },
    {
        "id": "comisarioHecesUrbanas",
        "threshold": 6,
        "name": "Comisario de Heces Urbanas",
    },
    {
        "id": "comisarioApocalipsisCanino",
        "threshold": 3,
        "name": "Comisario Principal del Apocalipsis Canino",
    },
    {
        "id": "directorCagadaNacional",
        "threshold": 1,
        "name": "Director General de la Cagada Nacional",
    },
]

RANKS_BY_TOP_PERCENTILE = sorted(RANKS, key=lambda rank: rank["threshold"])
DEFAULT_RANK = RANKS[0]
DEFAULT_RANK_NAME = DEFAULT_RANK["name"]
RANK_ID_BY_NAME = {rank["name"]: rank["id"] for rank in RANKS}


def get_rank_for_percentile(percentile: float) -> str:
    inverse = 100 - percentile
    for rank in RANKS_BY_TOP_PERCENTILE:
        if inverse <= rank["threshold"]:
            return rank["name"]
    return DEFAULT_RANK_NAME


def get_rank_key(rank_name: str) -> str:
    return RANK_ID_BY_NAME.get(rank_name, DEFAULT_RANK["id"])
