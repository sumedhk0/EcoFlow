"use client";

import React, { useState, useCallback } from "react";
import { Search, Loader2, AlertCircle, Leaf } from "lucide-react";
import SankeyChart from "@/components/SankeyChart";
import WhatIfSlider from "@/components/WhatIfSlider";
import SummaryCard from "@/components/SummaryCard";
import { recalculateEOL, type SankeyData } from "@/lib/eol-recalc";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [asin, setAsin] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [originalData, setOriginalData] = useState<SankeyData | null>(null);
  const [displayData, setDisplayData] = useState<SankeyData | null>(null);
  const [activeScenario, setActiveScenario] = useState("baseline");

  const handleAnalyze = useCallback(async () => {
    if (!asin.trim()) {
      setError("Please enter a product ASIN to get started.");
      return;
    }

    setLoading(true);
    setError(null);
    setOriginalData(null);
    setDisplayData(null);
    setActiveScenario("baseline");

    try {
      const params = new URLSearchParams({ eol_scenario: "baseline" });
      if (description.trim()) {
        params.set("description", description.trim());
      }
      const res = await fetch(`${API_URL}/analyze/${asin.trim()}?${params}`);

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Server error: ${res.status}`);
      }

      const data: SankeyData = await res.json();
      setOriginalData(data);
      setDisplayData(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, [asin, description]);

  const handleScenarioChange = useCallback(
    (scenario: string) => {
      if (!originalData) return;
      setActiveScenario(scenario);
      const updated = recalculateEOL(originalData, scenario);
      setDisplayData(updated);
    },
    [originalData]
  );

  return (
    <div className="min-h-screen bg-background">
      {/* ─── Header ─── */}
      <header className="border-b border-border/60">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-5">
          <div className="flex items-center gap-2">
            <Leaf className="h-[18px] w-[18px] text-primary" strokeWidth={2.2} />
            <span className="text-[15px] font-medium tracking-tight text-foreground">
              EcoFlow
            </span>
          </div>
          <span className="text-xs text-muted-foreground">
            Lifecycle Assessment
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5">
        {/* ─── Hero ─── */}
        <section className="pb-10 pt-16 sm:pt-20">
          <h1 className="font-serif text-3xl font-medium tracking-tight text-foreground sm:text-4xl">
            Understand your product&apos;s
            <br />
            environmental footprint
          </h1>
          <p className="mt-3 max-w-lg text-[15px] leading-relaxed text-muted-foreground">
            Enter an Amazon product ID to see a full lifecycle assessment —
            from raw material extraction through manufacturing, transport,
            use, and disposal.
          </p>
        </section>

        {/* ─── Search ─── */}
        <section className="pb-12">
          <div className="rounded-xl border border-border/80 bg-card p-5 shadow-sm">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:gap-4">
              <div className="sm:w-44">
                <label
                  htmlFor="asin-input"
                  className="mb-1.5 block text-xs font-medium text-muted-foreground"
                >
                  Product ASIN
                </label>
                <input
                  id="asin-input"
                  type="text"
                  value={asin}
                  onChange={(e) => setAsin(e.target.value)}
                  placeholder="B09V3KXJPB"
                  className="h-10 w-full rounded-lg border border-input bg-background px-3 font-mono text-sm text-foreground placeholder:text-muted-foreground/50 transition-colors duration-150 focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-ring/20"
                  onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                  aria-label="Amazon product ASIN"
                />
              </div>

              <div className="min-w-0 flex-1">
                <label
                  htmlFor="desc-input"
                  className="mb-1.5 block text-xs font-medium text-muted-foreground"
                >
                  Description{" "}
                  <span className="font-normal text-muted-foreground/60">
                    — leave empty to auto-fetch from Amazon
                  </span>
                </label>
                <input
                  id="desc-input"
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional: paste a product description instead"
                  className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground/50 transition-colors duration-150 focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-ring/20"
                  onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                  aria-label="Product description (optional)"
                />
              </div>

              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="inline-flex h-10 flex-shrink-0 items-center justify-center gap-2 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground shadow-sm transition-all duration-150 hover:bg-primary/90 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-ring/30 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none"
                aria-label="Analyze product"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                {loading ? "Analyzing" : "Analyze"}
              </button>
            </div>

            {/* Error */}
            {error && (
              <div
                className="mt-4 flex items-start gap-2.5 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive"
                role="alert"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>
        </section>

        {/* ─── Results ─── */}
        {displayData && (
          <section className="space-y-8 pb-20">
            {/* Product quick stats */}
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
              <h2 className="font-serif text-xl font-medium text-foreground">
                Assessment Results
              </h2>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>
                  <span className="font-mono font-medium text-foreground">
                    {displayData.summary.total_co2e_kg.toFixed(2)}
                  </span>{" "}
                  kg CO₂e total
                </span>
                <span className="text-border">|</span>
                <span>
                  <span className="font-mono font-medium text-foreground">
                    {displayData.summary.weight_kg.toFixed(2)}
                  </span>{" "}
                  kg product weight
                </span>
                <span className="text-border">|</span>
                <span className="capitalize">
                  {displayData.summary.category}
                </span>
              </div>
            </div>

            {/* Sankey diagram */}
            <div className="rounded-xl border border-border/80 bg-card p-5 shadow-sm">
              <div className="mb-4">
                <h3 className="font-serif text-lg font-medium text-foreground">
                  Lifecycle Flow
                </h3>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  How carbon emissions flow through each phase — hover any element for details
                </p>
              </div>
              <SankeyChart data={displayData} />
            </div>

            {/* What-If + Summary grid */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="lg:col-span-1">
                <WhatIfSlider
                  activeScenario={activeScenario}
                  onScenarioChange={handleScenarioChange}
                />
              </div>
              <div className="lg:col-span-2">
                <SummaryCard data={displayData} />
              </div>
            </div>
          </section>
        )}
      </main>

      {/* ─── Footer ─── */}
      <footer className="border-t border-border/40 py-8">
        <p className="text-center text-xs text-muted-foreground/70">
          EcoFlow — Open-source lifecycle assessment tool
        </p>
      </footer>
    </div>
  );
}
