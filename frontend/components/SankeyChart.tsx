"use client";

import React, { useRef, useEffect, useState, useCallback } from "react";
import {
  sankey as d3Sankey,
  sankeyLinkHorizontal,
  sankeyLeft,
} from "d3-sankey";
import type { SankeyData } from "@/lib/eol-recalc";

/* Muted earth-tone palette for each lifecycle phase */
const PHASE_COLORS: Record<string, string> = {
  material: "#7a9e8e",   // sage
  extraction: "#c4a882", // sand
  manufacturing: "#b8806a", // clay
  transport: "#8a8580",  // stone
  use: "#5c7c6b",        // deep sage
  eol: "#c2524a",        // muted red
  total: "#6b5c4a",      // dark earth
};

/* eslint-disable @typescript-eslint/no-explicit-any */

interface SankeyChartProps {
  data: SankeyData;
}

export default function SankeyChart({ data }: SankeyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });

  const updateDimensions = useCallback(() => {
    if (containerRef.current) {
      const w = containerRef.current.offsetWidth;
      setDimensions({ width: w, height: Math.max(300, Math.min(w * 0.45, 460)) });
    }
  }, []);

  useEffect(() => {
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, [updateDimensions]);

  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    text: string;
    sub?: string;
  } | null>(null);

  const { width, height } = dimensions;
  const MARGIN = { top: 20, right: 130, bottom: 20, left: 16 };

  const nodeMap = new Map<string, number>();
  const nodes = data.nodes.map((n, i) => {
    nodeMap.set(n.id, i);
    return { ...n, nodeIndex: i };
  });

  const links = data.links
    .filter((l) => l.value > 0.001)
    .map((l) => ({
      source: nodeMap.get(l.source) ?? 0,
      target: nodeMap.get(l.target) ?? 0,
      value: l.value,
    }));

  const sankeyGenerator = (d3Sankey as any)()
    .nodeWidth(12)
    .nodePadding(14)
    .nodeAlign(sankeyLeft)
    .extent([
      [MARGIN.left, MARGIN.top],
      [width - MARGIN.right, height - MARGIN.bottom],
    ]);

  let layoutNodes: any[] = [];
  let layoutLinks: any[] = [];

  try {
    const result = sankeyGenerator({
      nodes: nodes.map((n) => ({ ...n })),
      links: links.map((l) => ({ ...l })),
    });
    layoutNodes = result.nodes;
    layoutLinks = result.links;
  } catch {
    return (
      <div className="rounded-lg border border-border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
        Unable to render diagram. The data may not contain enough material flows.
      </div>
    );
  }

  const linkPathGen = sankeyLinkHorizontal();

  return (
    <div ref={containerRef} className="relative w-full">
      <svg
        width={width}
        height={height}
        className="overflow-visible"
        role="img"
        aria-label="Sankey diagram showing carbon emissions flow through lifecycle phases"
      >
        <defs>
          {layoutLinks.map((_: any, i: number) => {
            const sourcePhase = layoutLinks[i]?.source?.phase ?? "material";
            const targetPhase = layoutLinks[i]?.target?.phase ?? "total";
            return (
              <linearGradient
                key={`grad-${i}`}
                id={`link-grad-${i}`}
                gradientUnits="userSpaceOnUse"
                x1={layoutLinks[i]?.source?.x1 ?? 0}
                x2={layoutLinks[i]?.target?.x0 ?? 0}
              >
                <stop
                  offset="0%"
                  stopColor={PHASE_COLORS[sourcePhase] ?? "#8a8580"}
                  stopOpacity={0.35}
                />
                <stop
                  offset="100%"
                  stopColor={PHASE_COLORS[targetPhase] ?? "#8a8580"}
                  stopOpacity={0.15}
                />
              </linearGradient>
            );
          })}
        </defs>

        {/* Links */}
        <g>
          {layoutLinks.map((link: any, i: number) => {
            const path = (linkPathGen as any)(link);
            return (
              <path
                key={`link-${i}`}
                d={path ?? ""}
                fill="none"
                stroke={`url(#link-grad-${i})`}
                strokeWidth={Math.max(2, link.width ?? 1)}
                className="transition-opacity duration-150 hover:opacity-80"
                style={{ cursor: "pointer" }}
                onMouseEnter={(e) => {
                  setTooltip({
                    x: e.clientX,
                    y: e.clientY,
                    text: `${link.source?.label ?? "?"} → ${link.target?.label ?? "?"}`,
                    sub: `${link.value.toFixed(3)} kg CO₂e`,
                  });
                }}
                onMouseLeave={() => setTooltip(null)}
              />
            );
          })}
        </g>

        {/* Nodes */}
        <g>
          {layoutNodes.map((node: any, i: number) => {
            const x0: number = node.x0 ?? 0;
            const x1: number = node.x1 ?? 0;
            const y0: number = node.y0 ?? 0;
            const y1: number = node.y1 ?? 0;
            const phase: string = node.phase ?? "material";
            const label: string = node.label ?? "";
            const nodeHeight = y1 - y0;
            const color = PHASE_COLORS[phase] ?? "#8a8580";

            return (
              <g key={`node-${i}`}>
                <rect
                  x={x0}
                  y={y0}
                  width={x1 - x0}
                  height={nodeHeight}
                  fill={color}
                  rx={2}
                  className="transition-opacity duration-150"
                  style={{ opacity: 0.85, cursor: "pointer" }}
                  onMouseEnter={(e) => {
                    setTooltip({
                      x: e.clientX,
                      y: e.clientY,
                      text: label,
                      sub: `${(node.value ?? 0).toFixed(3)} kg CO₂e`,
                    });
                  }}
                  onMouseLeave={() => setTooltip(null)}
                />
                {nodeHeight > 10 && (
                  <text
                    x={x1 + 6}
                    y={(y0 + y1) / 2}
                    dy="0.35em"
                    textAnchor="start"
                    className="pointer-events-none select-none"
                    style={{
                      fontSize: "11px",
                      fontWeight: 450,
                      fill: "#787572",
                    }}
                  >
                    {label}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="pointer-events-none fixed z-50 rounded-lg border border-border bg-card px-3 py-2 shadow-md"
          style={{ left: tooltip.x + 12, top: tooltip.y - 10 }}
        >
          <div className="text-xs font-medium text-card-foreground">
            {tooltip.text}
          </div>
          {tooltip.sub && (
            <div className="mt-0.5 font-mono text-[11px] text-muted-foreground">
              {tooltip.sub}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
