"use client";

import React from "react";
import {
  Mountain,
  Factory,
  Truck,
  Plug,
  Trash2,
} from "lucide-react";
import type { SankeyData } from "@/lib/eol-recalc";

interface SummaryCardProps {
  data: SankeyData;
}

const PHASE_META: Record<
  string,
  { label: string; color: string; icon: React.ReactNode }
> = {
  materials: {
    label: "Raw Materials",
    color: "#c4a882",
    icon: <Mountain className="h-3.5 w-3.5" />,
  },
  manufacturing: {
    label: "Manufacturing",
    color: "#b8806a",
    icon: <Factory className="h-3.5 w-3.5" />,
  },
  transport: {
    label: "Transport",
    color: "#8a8580",
    icon: <Truck className="h-3.5 w-3.5" />,
  },
  use: {
    label: "Use Phase",
    color: "#5c7c6b",
    icon: <Plug className="h-3.5 w-3.5" />,
  },
  end_of_life: {
    label: "End of Life",
    color: "#c2524a",
    icon: <Trash2 className="h-3.5 w-3.5" />,
  },
};

export default function SummaryCard({ data }: SummaryCardProps) {
  const { summary, material_details } = data;
  const breakdown = summary.breakdown;
  const total = summary.total_co2e_kg;

  const phases = Object.entries(breakdown).sort(
    ([, a], [, b]) => Math.abs(b) - Math.abs(a)
  );
  const maxPhaseValue = Math.max(...phases.map(([, v]) => Math.abs(v)), 0.01);

  return (
    <div className="h-full rounded-xl border border-border/80 bg-card shadow-sm">
      <div className="p-5 pb-0">
        <h3 className="font-serif text-base font-medium text-foreground">
          Impact Breakdown
        </h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          CO₂ equivalent by lifecycle phase
        </p>
      </div>

      <div className="space-y-6 p-5">
        {/* Phase bars */}
        <div className="space-y-3">
          {phases.map(([phase, value]) => {
            const meta = PHASE_META[phase];
            const absValue = Math.abs(value);
            const pct = (absValue / maxPhaseValue) * 100;
            const isNegative = value < 0;

            return (
              <div key={phase} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-medium text-foreground/80">
                    {meta?.icon}
                    {meta?.label ?? phase}
                  </span>
                  <span className="font-mono text-muted-foreground">
                    {isNegative ? "" : "+"}
                    {value.toFixed(3)} kg
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full transition-all duration-500 ease-out"
                    style={{
                      width: `${Math.max(pct, 2)}%`,
                      backgroundColor: meta?.color ?? "#8a8580",
                      opacity: isNegative ? 0.45 : 0.75,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Total */}
        <div className="flex items-baseline justify-between rounded-lg bg-secondary/60 px-4 py-3">
          <span className="text-sm font-medium text-foreground">
            Total Impact
          </span>
          <span className="font-mono text-lg font-semibold text-primary">
            {total.toFixed(2)}{" "}
            <span className="text-xs font-normal text-muted-foreground">
              kg CO₂e
            </span>
          </span>
        </div>

        {/* Divider */}
        <div className="border-t border-border/60" />

        {/* Material details */}
        <div>
          <h4 className="mb-2.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Materials
          </h4>
          <div className="space-y-0.5">
            {material_details
              .sort(
                (a, b) => Math.abs(b.impact_kg_co2e) - Math.abs(a.impact_kg_co2e)
              )
              .map((m) => (
                <div
                  key={m.name}
                  className="flex items-center justify-between rounded-md px-2 py-1.5 text-xs transition-colors duration-150 hover:bg-muted/40"
                >
                  <span className="capitalize text-foreground/75">
                    {m.name.replace(/_/g, " ")}
                  </span>
                  <div className="flex items-center gap-3 font-mono text-muted-foreground">
                    <span className="w-8 text-right">
                      {(m.fraction * 100).toFixed(0)}%
                    </span>
                    <span className="w-14 text-right">
                      {m.weight_kg.toFixed(3)} kg
                    </span>
                    <span className="w-20 text-right font-medium text-foreground/65">
                      {m.impact_kg_co2e.toFixed(3)} CO₂e
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
