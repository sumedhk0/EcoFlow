/**
 * Client-side End-of-Life recalculation logic.
 * Mirrors the backend calculator's EOL formula so the What-If
 * feature can update the Sankey chart without a round-trip.
 */

// ---------------------------------------------------------------------------
// Types (matching backend response shape)
// ---------------------------------------------------------------------------

export interface SankeyNode {
  id: string;
  label: string;
  phase: string;
}

export interface SankeyLink {
  source: string;
  target: string;
  value: number;
}

export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
  summary: {
    total_co2e_kg: number;
    breakdown: {
      materials: number;
      manufacturing: number;
      transport: number;
      use: number;
      end_of_life: number;
    };
    weight_kg: number;
    category: string;
    eol_scenario: string;
  };
  per_material_weights: Record<string, number>;
  material_details: {
    name: string;
    fraction: number;
    weight_kg: number;
    impact_kg_co2e: number;
    factor: number;
  }[];
}

// ---------------------------------------------------------------------------
// EOL constants (must stay in sync with backend emission_factors.py)
// ---------------------------------------------------------------------------

export const EOL_METHOD_FACTORS: Record<string, number> = {
  landfill: 0.5,
  incineration: 1.0,
  recycling: -0.3,
};

export const EOL_SCENARIOS: Record<string, Record<string, number>> = {
  baseline: { landfill: 0.6, incineration: 0.2, recycling: 0.2 },
  best_case: { landfill: 0.1, incineration: 0.1, recycling: 0.8 },
  worst_case: { landfill: 0.8, incineration: 0.2, recycling: 0.0 },
};

export const SCENARIO_LABELS: Record<string, string> = {
  baseline: "Baseline",
  best_case: "Best Case (Recycling)",
  worst_case: "Worst Case (Landfill)",
};

// ---------------------------------------------------------------------------
// Recalculation function
// ---------------------------------------------------------------------------

/**
 * Recompute the EOL phase impact and update the Sankey data in-place (returns new object).
 *
 * Formula:
 *   blended_factor = Σ (scenario_fraction_m × method_factor_m)
 *   E_total = Σ_i (material_weight_i × blended_factor)
 *   new_total = materials + manufacturing + transport + use + E_total
 */
export function recalculateEOL(
  original: SankeyData,
  scenario: string
): SankeyData {
  const mix = EOL_SCENARIOS[scenario] ?? EOL_SCENARIOS.baseline;

  // Compute blended EOL factor for this scenario
  const blendedFactor = Object.entries(mix).reduce(
    (sum, [method, fraction]) => sum + fraction * (EOL_METHOD_FACTORS[method] ?? 0),
    0
  );

  // Compute new EOL total from per-material weights
  const newEol = Object.values(original.per_material_weights).reduce(
    (sum, weight) => sum + weight * blendedFactor,
    0
  );

  // Compute new total
  const b = original.summary.breakdown;
  const newTotal = b.materials + b.manufacturing + b.transport + b.use + newEol;

  // Clone and update links
  const newLinks = original.links.map((link) => {
    if (link.source === "eol" && link.target === "total") {
      return { ...link, value: Math.round(Math.abs(newEol) * 10000) / 10000 };
    }
    return { ...link };
  });

  // Clone and update summary
  const newSummary = {
    ...original.summary,
    total_co2e_kg: Math.round(newTotal * 10000) / 10000,
    eol_scenario: scenario,
    breakdown: {
      ...b,
      end_of_life: Math.round(newEol * 10000) / 10000,
    },
  };

  return {
    ...original,
    links: newLinks,
    summary: newSummary,
  };
}
