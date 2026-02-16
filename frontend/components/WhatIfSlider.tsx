"use client";

import React from "react";
import { Recycle, Trash2, Flame, FlaskConical } from "lucide-react";
import {
  SCENARIO_LABELS,
  EOL_SCENARIOS,
  EOL_METHOD_FACTORS,
} from "@/lib/eol-recalc";

interface WhatIfSliderProps {
  activeScenario: string;
  onScenarioChange: (scenario: string) => void;
}

const SCENARIO_ICONS: Record<string, React.ReactNode> = {
  baseline: <FlaskConical className="h-3.5 w-3.5" />,
  best_case: <Recycle className="h-3.5 w-3.5" />,
  worst_case: <Trash2 className="h-3.5 w-3.5" />,
};

const METHOD_ICONS: Record<string, React.ReactNode> = {
  landfill: <Trash2 className="h-3 w-3" />,
  incineration: <Flame className="h-3 w-3" />,
  recycling: <Recycle className="h-3 w-3" />,
};

const METHOD_COLORS: Record<string, string> = {
  landfill: "#c2524a",
  incineration: "#c4a882",
  recycling: "#5c7c6b",
};

export default function WhatIfSlider({
  activeScenario,
  onScenarioChange,
}: WhatIfSliderProps) {
  const scenarios = Object.entries(SCENARIO_LABELS);
  const currentMix = EOL_SCENARIOS[activeScenario] ?? EOL_SCENARIOS.baseline;

  return (
    <div className="h-full rounded-xl border border-border/80 bg-card shadow-sm">
      <div className="p-5 pb-0">
        <h3 className="font-serif text-base font-medium text-foreground">
          What-If Analysis
        </h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Explore different disposal scenarios
        </p>
      </div>

      <div className="space-y-5 p-5">
        {/* Scenario buttons */}
        <div className="flex flex-col gap-1.5">
          {scenarios.map(([key, label]) => {
            const isActive = activeScenario === key;
            return (
              <button
                key={key}
                onClick={() => onScenarioChange(key)}
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors duration-150 ${
                  isActive
                    ? "bg-primary/10 font-medium text-primary"
                    : "text-foreground/70 hover:bg-muted/50"
                }`}
                aria-pressed={isActive}
                aria-label={`Select ${label} scenario`}
              >
                {SCENARIO_ICONS[key]}
                {label}
              </button>
            );
          })}
        </div>

        {/* Disposal mix breakdown */}
        <div className="space-y-3">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Disposal Mix
          </p>
          {Object.entries(currentMix).map(([method, fraction]) => {
            const pct = fraction * 100;
            const factor = EOL_METHOD_FACTORS[method] ?? 0;
            return (
              <div key={method} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 capitalize text-foreground/75">
                    {METHOD_ICONS[method]}
                    {method}
                  </span>
                  <span className="font-mono text-muted-foreground">
                    {pct.toFixed(0)}%
                  </span>
                </div>
                <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full transition-all duration-400 ease-out"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: METHOD_COLORS[method],
                      opacity: 0.7,
                    }}
                  />
                </div>
                <p className="text-[10px] text-muted-foreground/70">
                  {factor > 0 ? "+" : ""}
                  {factor} kg CO₂e per kg
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
