"use client";

import { useEffect, useState } from "react";
import SiteHeader from "../components/site-header";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
type Quote = { symbol: string; price: string; previous_close: string | null; data_as_of: string; provider: string; delayed: boolean };
type Security = { id: number; symbol: string; name: string; exchange: string; asset_type: string };
type Overview = { benchmarks: Quote[]; limitations: string[] };
type Research = { security: Security; quote: Quote | null; signals: string[]; change_percent: string | null; historical: { performance: Record<string, string>; recent_high: string; recent_low: string; annualized_volatility: string } | null; fundamentals: Record<string, string | number> | null; limitations: string[] };
type ChartData = { symbol: string; range: string; interval: string; points: { date: string; close: string }[]; provider: string };
type Portfolio = { id: number; name: string; risk_profile: string };
type PortfolioFit = { symbol: string; already_held: boolean; current_quantity: string; current_allocation_percent: string; asset_type: string; sector: string | null; portfolio_asset_type_overlap: boolean; context: string[] };

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error("Market data is unavailable.");
  return response.json();
}

function PriceChart({ chart }: { chart: ChartData }) {
  if (chart.points.length < 2) return <p className="muted">Not enough price history for this range.</p>;
  const width = 760;
  const height = 338;
  const pad = 28;
  const values = chart.points.map((point) => Number(point.close));
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const precision = rawMax > 10 ? 0 : rawMax >= 1 ? 1 : 2;
  const unit = 10 ** -precision;
  const axisMin = Math.floor(rawMin / unit) * unit;
  const initialMax = Math.ceil(rawMax / unit) * unit;
  const intervalUnits = Math.max(1, Math.ceil((initialMax - axisMin) / unit / 5));
  const interval = intervalUnits * unit;
  const expandedMin = axisMin - interval >= 0 ? axisMin - interval : axisMin;
  const axisMax = axisMin + interval * 5;
  const spread = axisMax - expandedMin || unit;
  const points = chart.points.map((point, index) => `${pad + (index / (chart.points.length - 1)) * (width - pad * 2)},${height - pad - ((Number(point.close) - expandedMin) / spread) * (height - pad * 2)}`).join(" ");
  const tickCount = expandedMin < axisMin ? 7 : 6;
  const yTicks = Array.from({ length: tickCount }, (_, index) => expandedMin + interval * index);
  const xTickCount = chart.interval === "1d" ? 6 : 5;
  const xTicks = Array.from({ length: xTickCount }, (_, index) => Math.round((index / (xTickCount - 1)) * (chart.points.length - 1)));
  return <div className="chart-wrap"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${chart.symbol} price history`}>
    {yTicks.map((value, index) => { const y = height - pad - (index / (tickCount - 1)) * (height - pad * 2); return <g key={`y-${value}`}><line className="chart-grid" x1={pad} x2={width - pad} y1={y} y2={y} /><text className="chart-label" x={2} y={y + 4}>${value.toFixed(precision)}</text></g>; })}
    {xTicks.map((pointIndex) => { const x = pad + (pointIndex / (chart.points.length - 1)) * (width - pad * 2); return <g key={`x-${pointIndex}`}><line className="chart-grid vertical" x1={x} x2={x} y1={pad} y2={height - pad} /><text className="chart-label" x={x} y={height - 7} textAnchor="middle">{new Date(chart.points[pointIndex].date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</text></g>; })}
    <polyline className="chart-line" points={points} fill="none" />
  </svg><p className="chart-interval">Each point represents one {chart.interval === "1d" ? "trading day" : chart.interval === "1wk" ? "week" : "month"}.</p></div>;
}

export default function MarketPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Security[]>([]);
  const [research, setResearch] = useState<Research | null>(null);
  const [error, setError] = useState("");
  const [chartRange, setChartRange] = useState<"1m" | "6m" | "1y" | "2y">("1m");
  const [chart, setChart] = useState<ChartData | null>(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState("");
  const [portfolioFit, setPortfolioFit] = useState<PortfolioFit | null>(null);

  useEffect(() => { request<Overview>("/market-data/overview").then(setOverview).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Market data is unavailable.")); }, []);
  useEffect(() => { request<Portfolio[]>("/portfolios").then(setPortfolios).catch(() => setPortfolios([])); }, []);
  useEffect(() => {
    if (query.trim().length < 2) { setResults([]); return; }
    const timer = window.setTimeout(() => { request<Security[]>(`/market-data/search?q=${encodeURIComponent(query)}`).then(setResults).catch(() => setResults([])); }, 250);
    return () => window.clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    if (!research) return;
    setChartLoading(true);
    request<ChartData>(`/market-data/securities/${research.security.symbol}/chart?range=${chartRange}`).then(setChart).catch(() => setChart(null)).finally(() => setChartLoading(false));
  }, [research, chartRange]);
  useEffect(() => {
    if (!research || !selectedPortfolioId) { setPortfolioFit(null); return; }
    request<PortfolioFit>(`/portfolios/${selectedPortfolioId}/security-fit/${research.security.symbol}`).then(setPortfolioFit).catch(() => setPortfolioFit(null));
  }, [research, selectedPortfolioId]);

  return <main className="shell market-page" style={{ "--page-background": "#F3E9D8", "--surface": "#E5D4BA", "--line": "#B99B78", "--ink": "#241A14", "--muted": "#634D3B", "--accent": "#854719", "--danger": "#963B2F", "--button-ink": "#FFF8ED", "--input-background": "#FFFDF8", "--input-ink": "#241A14" } as React.CSSProperties}>
    <SiteHeader />
    <header className="market-hero"><p className="eyebrow">TRADING RESEARCH / MARKET CONTEXT</p><h1>Look closer<br />before deciding.</h1><p>Explore recent market information and neutral evidence signals. The app presents context, not instructions.</p></header>
    {error && <div className="error">{error}</div>}
    <section className="market-section"><div className="section-heading"><span>MARKET PULSE</span><span>BENCHMARKS</span></div><div className="benchmark-grid">{overview?.benchmarks.map((quote) => <div className="benchmark-card" key={quote.symbol}><span>{quote.symbol}</span><strong>${Number(quote.price).toFixed(2)}</strong><small>{quote.previous_close ? `${Number(((Number(quote.price) - Number(quote.previous_close)) / Number(quote.previous_close)) * 100).toFixed(2)}% from previous close` : "No comparison"}</small></div>) ?? <p className="muted">Loading market benchmarks...</p>}</div><p className="data-note">Quotes may be delayed. This market pulse is informational context, not a recommendation.</p></section>
     <section className="market-section"><div className="section-heading"><span>SECURITY RESEARCH</span><span>LOCAL CATALOG</span></div><div className="portfolio-context"><label>View portfolio context<select value={selectedPortfolioId} onChange={(event) => setSelectedPortfolioId(event.target.value)}><option value="">No portfolio selected</option>{portfolios.map((portfolio) => <option key={portfolio.id} value={portfolio.id}>{portfolio.name} · {portfolio.risk_profile}</option>)}</select></label></div><div className="market-search"><input placeholder="Search a symbol or company" value={query} onChange={(event) => setQuery(event.target.value)} />{results.length > 0 && <div className="market-results">{results.map((security) => <button key={security.id} onClick={() => { setQuery(""); setResults([]); request<Research>(`/market-data/securities/${security.symbol}`).then(setResearch).catch(() => setError("Could not load security research.")); }}><strong>{security.symbol}</strong><span>{security.name} · {security.exchange}</span></button>)}</div>}</div>{research && <article className="research-card"><div className="section-heading"><span>{research.security.exchange} / {research.security.asset_type}</span><span>{research.security.symbol}</span></div><h2>{research.security.name}</h2><p className="research-symbol">{research.security.symbol}</p>{portfolioFit && <div className="portfolio-fit"><div className="section-heading"><span>PORTFOLIO CONTEXT</span><span>{portfolioFit.already_held ? "HELD" : "NOT HELD"}</span></div><div className="fit-stats"><div><span>CURRENT QUANTITY</span><strong>{portfolioFit.current_quantity}</strong></div><div><span>ALLOCATION</span><strong>{Number(portfolioFit.current_allocation_percent).toFixed(2)}%</strong></div><div><span>ASSET TYPE</span><strong>{portfolioFit.asset_type}</strong></div></div>{portfolioFit.context.map((item) => <p key={item}>{item}</p>)}</div>}<div className="research-stats"><div><span>LATEST PRICE</span><strong>{research.quote ? `$${Number(research.quote.price).toFixed(2)}` : "Unavailable"}</strong></div><div><span>PREVIOUS CLOSE CHANGE</span><strong>{research.change_percent === null ? "Unavailable" : `${Number(research.change_percent).toFixed(2)}%`}</strong></div></div>{research.fundamentals && <div className="fundamentals"><div className="section-heading"><span>DESCRIPTIVE FUNDAMENTALS</span><span>FACTS</span></div><div className="fundamental-grid">{Object.entries(research.fundamentals).map(([key, value]) => <div key={key}><span>{key.replaceAll("_", " ")}</span><strong>{typeof value === "number" ? value.toLocaleString() : value}</strong></div>)}</div></div>}<div className="chart-panel"><div className="section-heading"><span>PRICE HISTORY</span><div className="chart-tabs">{(["1m", "6m", "1y", "2y"] as const).map((range) => <button className={chartRange === range ? "active" : ""} key={range} onClick={() => setChartRange(range)}>{range === "1m" ? "1 month / daily" : range === "6m" ? "6 months / weekly" : range === "1y" ? "1 year / monthly" : "2 years / monthly"}</button>)}</div></div>{chartLoading ? <p className="muted">Loading price history...</p> : chart ? <PriceChart chart={chart} /> : <p className="muted">Price history unavailable.</p>}</div>{research.historical && <div className="historical-context"><div className="section-heading"><span>HISTORICAL CONTEXT</span><span>1 YEAR</span></div><div className="history-grid">{Object.entries(research.historical.performance).map(([period, value]) => <div key={period}><span>{period.replace("_", " ")}</span><strong className={Number(value) >= 0 ? "positive" : "negative"}>{Number(value).toFixed(2)}%</strong></div>)}<div><span>VOLATILITY</span><strong>{Number(research.historical.annualized_volatility).toFixed(2)}%</strong></div><div><span>RECENT RANGE</span><strong>${Number(research.historical.recent_low).toFixed(2)} - ${Number(research.historical.recent_high).toFixed(2)}</strong></div></div></div>}<div className="signal-list">{research.signals.map((signal) => <p key={signal}>{signal}</p>)}</div><p className="data-note">{research.limitations[0]}</p></article>}</section>
    <footer className="footer"><div><strong>Trading Research</strong><span>A Broken Sky Studio app by Alejandro Restrepo.</span></div><nav><a href="/">Home</a><a href="/market/compare">Compare</a><a href="/workspace">Workspace</a><a href="https://brokensky.studio">brokensky.studio</a></nav></footer>
  </main>;
}
