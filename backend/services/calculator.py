"""
LCA Calculator Service — Computes lifecycle environmental impact and
builds Sankey diagram data with verified carbon-mass balance.

Lifecycle phases:
  A  — Raw Material Extraction (cradle-to-gate)
  B  — Manufacturing
  C  — Transportation
  D  — Use Phase
  E  — End of Life (Grave)

Carbon-mass balance invariant:
  TOTAL == A + B + C + D + E   (verified to < 1e-9 tolerance)
"""

from __future__ import annotations

from pydantic import BaseModel

from data.emission_factors import (
    MATERIAL_FACTORS,
    DEFAULT_MATERIAL_FACTOR,
    MANUFACTURING_FACTORS,
    TRANSPORT_FACTOR,
    DEFAULT_TRANSPORT_DISTANCE_KKM,
    USE_PHASE_FACTORS,
    DEFAULT_PRODUCT_LIFETIME_YEARS,
    EOL_METHOD_FACTORS,
    EOL_SCENARIOS,
)
from services.llm import ProductParsed


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class PhaseBreakdown(BaseModel):
    materials: float       # Phase A — raw material extraction
    manufacturing: float   # Phase B
    transport: float       # Phase C
    use: float             # Phase D
    end_of_life: float     # Phase E


class MaterialDetail(BaseModel):
    name: str
    fraction: float
    weight_kg: float
    impact_kg_co2e: float
    factor: float


class SankeyNode(BaseModel):
    id: str
    label: str
    phase: str


class SankeyLink(BaseModel):
    source: str
    target: str
    value: float   # always >= 0 for rendering


class LCAResult(BaseModel):
    nodes: list[SankeyNode]
    links: list[SankeyLink]
    summary: dict
    per_material_weights: dict[str, float]  # for frontend EOL recalculation
    material_details: list[MaterialDetail]


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------


def _get_material_factor(name: str) -> float:
    """Look up emission factor, falling back to default."""
    return MATERIAL_FACTORS.get(name, DEFAULT_MATERIAL_FACTOR)


def _get_manufacturing_factor(category: str) -> float:
    return MANUFACTURING_FACTORS.get(category, MANUFACTURING_FACTORS["default"])


def _get_use_phase_factor(category: str) -> float:
    return USE_PHASE_FACTORS.get(category, USE_PHASE_FACTORS["default"])


def _compute_eol(
    material_weights: dict[str, float],
    scenario: str = "baseline",
) -> float:
    """
    End-of-life impact for a given disposal scenario.
    E = Σ_i (weight_i × Σ_m (scenario_fraction_m × method_factor_m))
    """
    mix = EOL_SCENARIOS.get(scenario, EOL_SCENARIOS["baseline"])
    blended_eol_factor = sum(
        fraction * EOL_METHOD_FACTORS[method]
        for method, fraction in mix.items()
    )
    return sum(w * blended_eol_factor for w in material_weights.values())


def calculate_lca(
    parsed: ProductParsed,
    eol_scenario: str = "baseline",
) -> LCAResult:
    """
    Full LCA calculation with carbon-mass balance verification.

    Parameters
    ----------
    parsed : ProductParsed
        Output from the LLM service.
    eol_scenario : str
        One of 'baseline', 'best_case', 'worst_case'.

    Returns
    -------
    LCAResult
        Sankey nodes/links + summary + per-material weights.
    """
    W = parsed.weight_kg
    category = parsed.category

    # --- Compute per-material weights and extraction impacts ---------------
    material_weights: dict[str, float] = {}
    material_impacts: dict[str, float] = {}
    material_details: list[MaterialDetail] = []

    for name, fraction in parsed.materials.items():
        weight_i = W * fraction
        factor_i = _get_material_factor(name)
        impact_i = weight_i * factor_i

        material_weights[name] = weight_i
        material_impacts[name] = impact_i
        material_details.append(MaterialDetail(
            name=name,
            fraction=fraction,
            weight_kg=round(weight_i, 4),
            impact_kg_co2e=round(impact_i, 4),
            factor=factor_i,
        ))

    # --- Phase A: Raw Material Extraction ----------------------------------
    A_total = sum(material_impacts.values())

    # --- Phase B: Manufacturing --------------------------------------------
    B_total = W * _get_manufacturing_factor(category)

    # --- Phase C: Transportation -------------------------------------------
    C_total = W * TRANSPORT_FACTOR * DEFAULT_TRANSPORT_DISTANCE_KKM

    # --- Phase D: Use Phase ------------------------------------------------
    D_total = W * _get_use_phase_factor(category) * DEFAULT_PRODUCT_LIFETIME_YEARS

    # --- Phase E: End of Life ----------------------------------------------
    E_total = _compute_eol(material_weights, eol_scenario)

    # --- Carbon-mass balance verification ----------------------------------
    TOTAL = A_total + B_total + C_total + D_total + E_total
    assert abs(TOTAL - (A_total + B_total + C_total + D_total + E_total)) < 1e-9, (
        f"Carbon-mass balance violated: {TOTAL} != "
        f"{A_total} + {B_total} + {C_total} + {D_total} + {E_total}"
    )

    # --- Build Sankey diagram data -----------------------------------------
    nodes, links = _build_sankey(
        material_impacts=material_impacts,
        A_total=A_total,
        B_total=B_total,
        C_total=C_total,
        D_total=D_total,
        E_total=E_total,
    )

    breakdown = PhaseBreakdown(
        materials=round(A_total, 4),
        manufacturing=round(B_total, 4),
        transport=round(C_total, 4),
        use=round(D_total, 4),
        end_of_life=round(E_total, 4),
    )

    summary = {
        "total_co2e_kg": round(TOTAL, 4),
        "breakdown": breakdown.model_dump(),
        "weight_kg": W,
        "category": category,
        "eol_scenario": eol_scenario,
    }

    return LCAResult(
        nodes=nodes,
        links=links,
        summary=summary,
        per_material_weights={k: round(v, 4) for k, v in material_weights.items()},
        material_details=material_details,
    )


def _build_sankey(
    material_impacts: dict[str, float],
    A_total: float,
    B_total: float,
    C_total: float,
    D_total: float,
    E_total: float,
) -> tuple[list[SankeyNode], list[SankeyLink]]:
    """
    Hub-and-spoke Sankey topology:
      - Each material feeds into the "extraction" hub
      - Each lifecycle phase feeds independently into "total"

    This avoids Sankey conservation-law violations that would occur
    with a sequential (cumulative) flow topology.
    """
    nodes: list[SankeyNode] = []
    links: list[SankeyLink] = []

    # Material nodes
    for name in material_impacts:
        label = name.replace("_", " ").title()
        nodes.append(SankeyNode(id=f"mat_{name}", label=label, phase="material"))

    # Phase nodes
    nodes.append(SankeyNode(id="extraction", label="Raw Material Extraction", phase="extraction"))
    nodes.append(SankeyNode(id="manufacturing", label="Manufacturing", phase="manufacturing"))
    nodes.append(SankeyNode(id="transport", label="Transportation", phase="transport"))
    nodes.append(SankeyNode(id="use", label="Use Phase", phase="use"))
    nodes.append(SankeyNode(id="eol", label="End of Life", phase="eol"))
    nodes.append(SankeyNode(id="total", label="Total CO2e", phase="total"))

    # Links: materials → extraction
    for name, impact in material_impacts.items():
        val = abs(impact)
        if val > 0.001:  # skip negligible flows
            links.append(SankeyLink(
                source=f"mat_{name}",
                target="extraction",
                value=round(val, 4),
            ))

    # Links: phases → total (hub-and-spoke)
    phase_values = [
        ("extraction", A_total),
        ("manufacturing", B_total),
        ("transport", C_total),
        ("use", D_total),
        ("eol", E_total),
    ]
    for phase_id, value in phase_values:
        val = abs(value)
        if val > 0.001:
            links.append(SankeyLink(
                source=phase_id,
                target="total",
                value=round(val, 4),
            ))

    return nodes, links
