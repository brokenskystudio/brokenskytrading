"use client";

import { useEffect, useState } from "react";
import SiteHeader from "../../components/site-header";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
type Security = { id: number; symbol: string; name: string; exchange: string; asset_type: string };
type Compared = { security: Security; quote: { price: string } | null; historical: { performance: Record<string, string>; annualized_volatility: string } | null; fundamentals: Record<string, string | number> | null };
type Portfolio = { id: number; name: string; risk_profile: string };
type Fit = { symbol: string; already_held: boolean; current_quantity: string; current_allocation_percent: string; asset_type: string; portfolio_asset_type_overlap: boolean; context: string[] };

async function request<T>(path: string): Promise<T> { const response = await fetch(`${apiBaseUrl}${path}`, { cache: "no-store" }); if (!response.ok) throw new Error("Could not load comparison data."); return response.json(); }

export default function ComparePage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Security[]>([]);
  const [selected, setSelected] = useState<Security[]>([]);
  const [comparison, setComparison] = useState<Compared[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [portfolioId, setPortfolioId] = useState("");
  const [fits, setFits] = useState<Record<string, Fit>>({});

  useEffect(() => { if (query.trim().length < 2) { setResults([]); return; } const timer = window.setTimeout(() => request<Security[]>(`/market-data/search?q=${encodeURIComponent(query)}`).then(setResults).catch(() => setResults([])), 250); return () => window.clearTimeout(timer); }, [query]);
  useEffect(() => { request<Portfolio[]>("/portfolios").then(setPortfolios).catch(() => setPortfolios([])); }, []);
  useEffect(() => { if (selected.length < 2) { setComparison([]); return; } setLoading(true); request<Compared[]>(`/market-data/compare?symbols=${selected.map((security) => security.symbol).join(",")}`).then(setComparison).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load comparison data.")).finally(() => setLoading(false)); }, [selected]);
  useEffect(() => { if (!portfolioId || selected.length === 0) { setFits({}); return; } Promise.all(selected.map((security) => request<Fit>(`/portfolios/${portfolioId}/security-fit/${security.symbol}`))).then((items) => setFits(Object.fromEntries(items.map((item) => [item.symbol, item])))).catch(() => setFits({})); }, [portfolioId, selected]);

  function addSecurity(security: Security) { if (!selected.some((item) => item.symbol === security.symbol) && selected.length < 4) setSelected([...selected, security]); setQuery(""); setResults([]); }
  function removeSecurity(symbol: string) { setSelected(selected.filter((security) => security.symbol !== symbol)); }
  function value(item: Compared, key: string) { const fundamental = item.fundamentals?.[key]; return fundamental === undefined ? "-" : typeof fundamental === "number" ? fundamental.toLocaleString() : fundamental; }

  return <main className="shell compare-page" style={{ "--page-background": "#F3E9D8", "--surface": "#E5D4BA", "--line": "#B99B78", "--ink": "#241A14", "--muted": "#634D3B", "--accent": "#854719", "--danger": "#963B2F", "--button-ink": "#FFF8ED", "--input-background": "#FFFDF8", "--input-ink": "#241A14" } as React.CSSProperties}>
    <SiteHeader />
    <header className="compare-hero"><p className="eyebrow">MARKET RESEARCH / COMPARISON</p><h1>Put the facts<br />side by side.</h1><p>Compare a small set of securities using the same market context and descriptive metrics. This view does not rank or recommend them.</p></header>
    <section className="compare-section"><div className="section-heading"><span>SELECT SECURITIES</span><span>{selected.length} / 4</span></div><div className="compare-search"><input placeholder="Search a symbol or company" value={query} onChange={(event) => setQuery(event.target.value)} />{results.length > 0 && <div className="market-results">{results.map((security) => <button key={security.id} onClick={() => addSecurity(security)}><strong>{security.symbol}</strong><span>{security.name} · {security.exchange}</span></button>)}</div>}</div><div className="selected-securities">{selected.map((security) => <button key={security.symbol} onClick={() => removeSecurity(security.symbol)}>{security.symbol} <span>×</span></button>)}</div><div className="compare-portfolio"><label>Portfolio context<select value={portfolioId} onChange={(event) => setPortfolioId(event.target.value)}><option value="">No portfolio selected</option>{portfolios.map((portfolio) => <option value={portfolio.id} key={portfolio.id}>{portfolio.name} · {portfolio.risk_profile}</option>)}</select></label></div></section>
    {selected.length < 2 ? <div className="compare-empty"><p className="eyebrow">COMPARE</p><h2>Select at least two securities.</h2><p>Use the search field to build a focused research comparison.</p></div> : <section className="compare-section"><div className="section-heading"><span>COMPARISON</span><span>{loading ? "LOADING" : "CACHED CONTEXT"}</span></div><div className="comparison-table"><div className="comparison-row comparison-header"><span>METRIC</span>{comparison.map((item) => <strong key={item.security.symbol}>{item.security.symbol}</strong>)}</div>{[["Name", (item: Compared) => item.security.name], ["Asset type", (item: Compared) => item.security.asset_type], ["Exchange", (item: Compared) => item.security.exchange], ["Latest price", (item: Compared) => item.quote ? `$${Number(item.quote.price).toFixed(2)}` : "Unavailable"], ["1 month", (item: Compared) => item.historical ? `${Number(item.historical.performance["1_month"]).toFixed(2)}%` : "Unavailable"], ["6 months", (item: Compared) => item.historical ? `${Number(item.historical.performance["6_months"]).toFixed(2)}%` : "Unavailable"], ["1 year", (item: Compared) => item.historical ? `${Number(item.historical.performance["1_year"]).toFixed(2)}%` : "Unavailable"], ["Volatility", (item: Compared) => item.historical ? `${Number(item.historical.annualized_volatility).toFixed(2)}%` : "Unavailable"], ["Sector", (item: Compared) => value(item, "sector")], ["Market cap", (item: Compared) => value(item, "market_cap")], ["Trailing P/E", (item: Compared) => value(item, "trailing_pe")]].map(([label, getter]) => <div className="comparison-row" key={label as string}><span>{label as string}</span>{comparison.map((item) => <strong key={item.security.symbol}>{(getter as (item: Compared) => string)(item)}</strong>)}</div>)}{portfolioId && <><div className="comparison-row comparison-subhead"><span>PORTFOLIO FIT</span>{comparison.map((item) => <strong key={item.security.symbol}>{fits[item.security.symbol]?.already_held ? "HELD" : "NOT HELD"}</strong>)}</div><div className="comparison-row"><span>Current allocation</span>{comparison.map((item) => <strong key={item.security.symbol}>{fits[item.security.symbol] ? `${Number(fits[item.security.symbol].current_allocation_percent).toFixed(2)}%` : "-"}</strong>)}</div><div className="comparison-row"><span>Asset overlap</span>{comparison.map((item) => <strong key={item.security.symbol}>{fits[item.security.symbol]?.portfolio_asset_type_overlap ? "Yes" : "No"}</strong>)}</div></>}</div></section>}
    <footer className="footer"><div><strong>Trading Research</strong><span>A Broken Sky Studio app by Alejandro Restrepo.</span></div><nav><a href="/market">Market</a><a href="/workspace">Workspace</a><a href="/">Home</a></nav></footer>
  </main>;
}
