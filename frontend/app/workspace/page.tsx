"use client";

import { FormEvent, useEffect, useState } from "react";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RiskProfile = "conservative" | "balanced" | "aggressive";

type Holding = {
  id: number;
  symbol: string;
  quantity: string;
  average_cost: string;
  notes: string | null;
};

type Purchase = { id: number; quantity: string; price: string; notes: string | null; purchased_at: string };
type HoldingDetail = Holding & { purchases: Purchase[] };

type Quote = {
  symbol: string;
  price: string;
  previous_close: string | null;
  data_as_of: string;
  provider: string;
  delayed: boolean;
};

type SecuritySuggestion = {
  id: number;
  symbol: string;
  name: string;
  exchange: string;
  asset_type: string;
};
type Analysis = { total_value: string; cash_value: string; cash_percent: string; invested_value: string; total_gain_loss: string; positions: { symbol: string; allocation_percent: string; gain_loss: string }[]; alerts: { severity: string; message: string }[]; missing_symbols: string[]; summary: string; recommendations: { action: string; symbol: string | null; reason: string; risks: string[]; confidence: string }[] };
type AnalysisHistoryEntry = { id: number; created_at: string; data_as_of: string; market_provider: string; metrics: Analysis };

type Portfolio = {
  id: number;
  name: string;
  risk_profile: RiskProfile;
  cash_balance: string;
  holdings: Holding[];
};

type Palette = {
  name: string;
  background: string;
  surface: string;
  line: string;
  ink: string;
  muted: string;
  accent: string;
  danger: string;
  buttonInk: string;
  inputBackground: string;
  inputInk: string;
};

const palettes: Palette[] = [
  { name: "Coffee Cream", background: "#F3E9D8", surface: "#E5D4BA", line: "#B99B78", ink: "#241A14", muted: "#634D3B", accent: "#854719", danger: "#963B2F", buttonInk: "#FFF8ED", inputBackground: "#FFFDF8", inputInk: "#241A14" },
  { name: "Coffee + Slate", background: "#10151A", surface: "#1E252B", line: "#3B4A52", ink: "#EEF2F0", muted: "#A4B0AE", accent: "#D7A56D", danger: "#E98578", buttonInk: "#241A14", inputBackground: "#0B1014", inputInk: "#EEF2F0" },
];

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "The request could not be completed.");
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export default function Home() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [newPortfolioName, setNewPortfolioName] = useState("");
  const [portfolioForm, setPortfolioForm] = useState({ name: "", cash_balance: "0", risk_profile: "balanced" as RiskProfile });
  const [holdingForm, setHoldingForm] = useState({ symbol: "", quantity: "", average_cost: "", notes: "" });
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [quotesLoading, setQuotesLoading] = useState(false);
  const [quotesError, setQuotesError] = useState("");
  const [suggestions, setSuggestions] = useState<SecuritySuggestion[]>([]);
  const [detailHolding, setDetailHolding] = useState<HoldingDetail | null>(null);
  const [averageCost, setAverageCost] = useState("");
  const [buyForm, setBuyForm] = useState({ quantity: "", price: "", notes: "" });
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryEntry[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<number | null>(null);
  const [themeMode, setThemeMode] = useState<"light" | "dark">("light");
  const selectedPalette = palettes[themeMode === "light" ? 0 : 1];

  const selectedPortfolio = portfolios.find((portfolio) => portfolio.id === selectedId) ?? null;
  const holdingsMarketValue = selectedPortfolio?.holdings.reduce((total, holding) => {
    const quote = quotes[holding.symbol];
    return total + (quote ? Number(holding.quantity) * Number(quote.price) : 0);
  }, 0) ?? 0;
  const currentPortfolioValue = (Number(selectedPortfolio?.cash_balance ?? 0) + holdingsMarketValue).toFixed(2);

  async function loadPortfolios(selectFirst = false) {
    try {
      setError("");
      const result = await request<Portfolio[]>("/portfolios");
      setPortfolios(result);
      if (selectFirst && result[0]) {
        setSelectedId(result[0].id);
        setPortfolioForm({ name: result[0].name, cash_balance: result[0].cash_balance, risk_profile: result[0].risk_profile });
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load portfolios.");
    } finally {
      setLoading(false);
    }
  }

  async function loadQuotes(portfolioId: number) {
    setQuotesLoading(true);
    setQuotesError("");
    try {
      const result = await request<{ quotes: Quote[]; missing_symbols: string[] }>(`/portfolios/${portfolioId}/quotes`);
      setQuotes(Object.fromEntries(result.quotes.map((quote) => [quote.symbol, quote])));
    } catch (reason) {
      setQuotesError(reason instanceof Error ? reason.message : "Market data is unavailable.");
    } finally {
      setQuotesLoading(false);
    }
  }

  useEffect(() => {
    void loadPortfolios(true);
  }, []);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem("trading-research-theme");
    if (savedTheme === "dark") setThemeMode("dark");
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    void loadQuotes(selectedId);
    request<AnalysisHistoryEntry[]>(`/portfolios/${selectedId}/analyses`).then(setAnalysisHistory).catch(() => setAnalysisHistory([]));
  }, [selectedId]);

  useEffect(() => {
    const query = holdingForm.symbol.trim();
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = window.setTimeout(() => {
      request<SecuritySuggestion[]>(`/market-data/search?q=${encodeURIComponent(query)}`)
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [holdingForm.symbol]);

  function selectPortfolio(portfolio: Portfolio) {
    setSelectedId(portfolio.id);
    setPortfolioForm({ name: portfolio.name, cash_balance: portfolio.cash_balance, risk_profile: portfolio.risk_profile });
  }

  async function createPortfolio(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newPortfolioName.trim()) return;
    setSaving(true);
    try {
      const portfolio = await request<Portfolio>("/portfolios", { method: "POST", body: JSON.stringify({ name: newPortfolioName.trim(), cash_balance: "0", risk_profile: "balanced" }) });
      setPortfolios((current) => [portfolio, ...current]);
      selectPortfolio(portfolio);
      setNewPortfolioName("");
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create portfolio.");
    } finally {
      setSaving(false);
    }
  }

  async function updatePortfolio(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPortfolio) return;
    setSaving(true);
    try {
      const updated = await request<Portfolio>(`/portfolios/${selectedPortfolio.id}`, { method: "PUT", body: JSON.stringify(portfolioForm) });
      setPortfolios((current) => current.map((portfolio) => portfolio.id === updated.id ? updated : portfolio));
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update portfolio.");
    } finally {
      setSaving(false);
    }
  }

  async function addHolding(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPortfolio) return;
    setSaving(true);
    try {
      const holding = await request<Holding>(`/portfolios/${selectedPortfolio.id}/holdings`, { method: "POST", body: JSON.stringify(holdingForm) });
      setPortfolios((current) => current.map((portfolio) => portfolio.id === selectedPortfolio.id ? { ...portfolio, holdings: [...portfolio.holdings, holding] } : portfolio));
      setHoldingForm({ symbol: "", quantity: "", average_cost: "", notes: "" });
      await loadQuotes(selectedPortfolio.id);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not add holding.");
    } finally {
      setSaving(false);
    }
  }

  async function removeHolding(holdingId: number) {
    if (!selectedPortfolio) return;
    try {
      await request<void>(`/holdings/${holdingId}`, { method: "DELETE" });
      setPortfolios((current) => current.map((portfolio) => portfolio.id === selectedPortfolio.id ? { ...portfolio, holdings: portfolio.holdings.filter((holding) => holding.id !== holdingId) } : portfolio));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not remove holding.");
    }
  }

  async function openHoldingDetails(holdingId: number) {
    try {
      const detail = await request<HoldingDetail>(`/holdings/${holdingId}`);
      setDetailHolding(detail);
      setAverageCost(detail.average_cost);
      setBuyForm({ quantity: "", price: "", notes: "" });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load holding details.");
    }
  }

  async function refreshPortfolio() {
    if (!selectedPortfolio) return;
    const updated = await request<Portfolio>(`/portfolios/${selectedPortfolio.id}`);
    setPortfolios((current) => current.map((portfolio) => portfolio.id === updated.id ? updated : portfolio));
  }

  async function saveAverageCost(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detailHolding) return;
    setSaving(true);
    try {
      await request<Holding>(`/holdings/${detailHolding.id}`, { method: "PUT", body: JSON.stringify({ symbol: detailHolding.symbol, quantity: detailHolding.quantity, average_cost: averageCost, notes: detailHolding.notes }) });
      await refreshPortfolio();
      await openHoldingDetails(detailHolding.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update average cost.");
    } finally {
      setSaving(false);
    }
  }

  async function addBuy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detailHolding) return;
    setSaving(true);
    try {
      await request<Purchase>(`/holdings/${detailHolding.id}/purchases`, { method: "POST", body: JSON.stringify(buyForm) });
      await refreshPortfolio();
      await openHoldingDetails(detailHolding.id);
      await loadQuotes(selectedPortfolio?.id ?? 0);
      setBuyForm({ quantity: "", price: "", notes: "" });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not add purchase.");
    } finally {
      setSaving(false);
    }
  }

  async function analyzePortfolio() {
    if (!selectedPortfolio) return;
    setAnalysisLoading(true);
    try {
      const result = await request<{ id: number; metrics: Analysis }>(`/portfolios/${selectedPortfolio.id}/analyze`, { method: "POST" });
      setAnalysis(result.metrics);
      setSelectedAnalysisId(result.id);
      const history = await request<AnalysisHistoryEntry[]>(`/portfolios/${selectedPortfolio.id}/analyses`);
      setAnalysisHistory(history);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not analyze portfolio.");
    } finally {
      setAnalysisLoading(false);
    }
  }

  function toggleTheme() {
    const nextTheme = themeMode === "light" ? "dark" : "light";
    setThemeMode(nextTheme);
    window.localStorage.setItem("trading-research-theme", nextTheme);
  }

  async function removePortfolio() {
    if (!selectedPortfolio || !window.confirm(`Delete ${selectedPortfolio.name}?`)) return;
    try {
      await request<void>(`/portfolios/${selectedPortfolio.id}`, { method: "DELETE" });
      const remaining = portfolios.filter((portfolio) => portfolio.id !== selectedPortfolio.id);
      setPortfolios(remaining);
      setSelectedId(remaining[0]?.id ?? null);
      setPortfolioForm({ name: "", cash_balance: "0", risk_profile: "balanced" });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not delete portfolio.");
    }
  }

  return (
    <main className="shell" style={{ "--page-background": selectedPalette.background, "--surface": selectedPalette.surface, "--line": selectedPalette.line, "--ink": selectedPalette.ink, "--muted": selectedPalette.muted, "--accent": selectedPalette.accent, "--danger": selectedPalette.danger, "--button-ink": selectedPalette.buttonInk, "--input-background": selectedPalette.inputBackground, "--input-ink": selectedPalette.inputInk } as React.CSSProperties}>
      <div className="studio-bar">
        <a className="brand" href="/" aria-label="Go to Trading Research home">
          <span className="brand-mark">BSS</span>
          <span><strong>BROKEN SKY</strong><small>STUDIO / PRODUCT 01</small></span>
        </a>
        <span className="studio-owner">ALEJANDRO RESTREPO</span>
      </div>
      <header className="topbar">
        <div>
          <p className="eyebrow">BROKEN SKY STUDIO / LOCAL RESEARCH WORKSPACE</p>
          <h1>Trading Research</h1>
        </div>
        <div className="header-tools"><div className="theme-controls"><button className="theme-toggle" onClick={toggleTheme} aria-label={themeMode === "light" ? "Switch to dark theme" : "Switch to light theme"} title={themeMode === "light" ? "Switch to dark theme" : "Switch to light theme"}>{themeMode === "light" ? <svg className="theme-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 15.2A8.5 8.5 0 0 1 8.8 3.5 8.5 8.5 0 1 0 20.5 15.2Z" /></svg> : <svg className="theme-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3.5" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></svg>}</button><div className="theme-previews" aria-label="Moon icon previews"><span title="Classic crescent"><svg viewBox="0 0 24 24"><path d="M20.5 15.2A8.5 8.5 0 0 1 8.8 3.5 8.5 8.5 0 1 0 20.5 15.2Z" /></svg></span><span title="Outlined crescent"><svg viewBox="0 0 24 24"><path d="M18.5 16.2A7.5 7.5 0 0 1 8.2 5.5 7.5 7.5 0 1 0 18.5 16.2Z" /></svg></span><span title="Moon and star"><svg viewBox="0 0 24 24"><path d="M19.5 15.5A7.5 7.5 0 0 1 8.5 5 7.5 7.5 0 1 0 19.5 15.5Z" /><path d="m17.5 4 .4 1.1L19 5.5l-1.1.4-.4 1.1-.4-1.1-1.1-.4 1.1-.4.4-1.1Z" /></svg></span><span title="Eclipse"><svg viewBox="0 0 24 24"><circle cx="10" cy="12" r="6" /><circle cx="14" cy="10" r="6" /></svg></span><span title="Horizon moon"><svg viewBox="0 0 24 24"><path d="M5 15a7 7 0 0 0 14 0" /><path d="M3 18h18" /></svg></span></div></div><p className="disclaimer">Informational research only.<br />No trade execution.</p></div>
      </header>

      {error && <div className="error" role="alert">{error}</div>}
      <div className="workspace">
        <aside className="sidebar">
          <div className="section-heading"><span>PORTFOLIOS</span><span>{portfolios.length}</span></div>
          {loading && <p className="muted">Loading portfolios...</p>}
          {!loading && portfolios.length === 0 && <p className="muted">No portfolios yet. Create your first research workspace.</p>}
          <div className="portfolio-list">
            {portfolios.map((portfolio) => (
              <button className={`portfolio-card ${portfolio.id === selectedId ? "active" : ""}`} key={portfolio.id} onClick={() => selectPortfolio(portfolio)}>
                <strong>{portfolio.name}</strong>
                <span>{portfolio.risk_profile} · {portfolio.holdings.length} holdings</span>
              </button>
            ))}
          </div>
          <form className="new-form" onSubmit={createPortfolio}>
            <p className="form-label">NEW PORTFOLIO</p>
            <input required placeholder="Portfolio name" value={newPortfolioName} onChange={(event) => setNewPortfolioName(event.target.value)} />
            <button className="primary" disabled={saving}>Create portfolio</button>
          </form>
        </aside>

        <section className="content">
          {!selectedPortfolio ? (
            <div className="empty-state"><p className="eyebrow">START HERE</p><h2>Create a portfolio to begin.</h2><p>Record your cash and holdings, then review the research signals in a later phase.</p></div>
          ) : (
            <>
              <div className="content-header"><div><p className="eyebrow">PORTFOLIO / {selectedPortfolio.id.toString().padStart(3, "0")}</p><h2>{selectedPortfolio.name}</h2></div><div className="header-actions"><button className="primary small" onClick={analyzePortfolio} disabled={analysisLoading}>{analysisLoading ? "Analyzing..." : "Analyze portfolio"}</button><button className="quiet danger" onClick={removePortfolio}>Delete portfolio</button></div></div>
              <div className="value-summary"><div><span>CURRENT VALUE</span><strong>${Number(currentPortfolioValue).toLocaleString("en-US", { minimumFractionDigits: 2 })}</strong></div><div><span>POSITIONS VALUE</span><strong>${holdingsMarketValue.toLocaleString("en-US", { minimumFractionDigits: 2 })}</strong></div><div><span>CASH</span><strong>${Number(selectedPortfolio.cash_balance).toLocaleString("en-US", { minimumFractionDigits: 2 })}</strong></div></div>
              {analysis && <section className="analysis-panel"><div className="section-heading"><span>DETERMINISTIC ANALYSIS</span><span>{selectedAnalysisId === analysisHistory[0]?.id ? "LATEST" : "SAVED"}</span></div><p className="analysis-summary-text">{analysis.summary}</p><div className="analysis-summary"><div><span>TOTAL GAIN / LOSS</span><strong className={Number(analysis.total_gain_loss) >= 0 ? "positive" : "negative"}>${Number(analysis.total_gain_loss).toFixed(2)}</strong></div><div><span>CASH ALLOCATION</span><strong>{Number(analysis.cash_percent).toFixed(2)}%</strong></div><div><span>ALERTS</span><strong>{analysis.alerts.length}</strong></div></div>{analysis.alerts.length > 0 && <div className="alerts">{analysis.alerts.map((alert, index) => <p className={`alert ${alert.severity}`} key={`${alert.message}-${index}`}>{alert.message}</p>)}</div>}{analysis.recommendations.length > 0 && <div className="recommendations"><div className="section-heading"><span>RESEARCH CANDIDATES</span><span>RULE-BASED</span></div>{analysis.recommendations.map((recommendation, index) => <div className="recommendation" key={`${recommendation.symbol}-${index}`}><div><strong>{recommendation.action} {recommendation.symbol ?? ""}</strong><span>{recommendation.reason}</span></div><small>{recommendation.confidence} confidence</small></div>)}</div>}{analysis.missing_symbols.length > 0 && <p className="muted">Missing market data: {analysis.missing_symbols.join(", ")}</p>}<div className="allocation-list">{analysis.positions.map((position) => <div key={position.symbol}><strong>{position.symbol}</strong><span>{Number(position.allocation_percent).toFixed(2)}% allocation · ${Number(position.gain_loss).toFixed(2)} gain/loss</span></div>)}</div><div className="analysis-history"><div className="section-heading"><span>ANALYSIS HISTORY</span><span>{analysisHistory.length} RUNS</span></div>{analysisHistory.slice(0, 5).map((entry) => <button className={`history-entry ${entry.id === selectedAnalysisId ? "active" : ""}`} key={entry.id} onClick={() => { setSelectedAnalysisId(entry.id); setAnalysis(entry.metrics); }}><strong>{entry.id === analysisHistory[0]?.id ? "Latest run" : `Run ${entry.id}`}</strong><span>{new Date(entry.created_at).toLocaleString()} · {entry.market_provider}</span></button>)}</div></section>}
              <form className="panel portfolio-form" onSubmit={updatePortfolio}>
                <div className="section-heading"><span>PROFILE SETTINGS</span><a className="workspace-link" href="/risk-profiles">WHAT DOES THIS MEAN? ↗</a></div>
                <div className="field-grid"><label>Name<input required value={portfolioForm.name} onChange={(event) => setPortfolioForm({ ...portfolioForm, name: event.target.value })} /></label><label>Cash balance<input required min="0" step="0.01" type="number" value={portfolioForm.cash_balance} onChange={(event) => setPortfolioForm({ ...portfolioForm, cash_balance: event.target.value })} /></label><label>Risk profile<select value={portfolioForm.risk_profile} onChange={(event) => setPortfolioForm({ ...portfolioForm, risk_profile: event.target.value as RiskProfile })}><option value="conservative">Conservative</option><option value="balanced">Balanced</option><option value="aggressive">Aggressive</option></select></label></div>
                <button className="primary small" disabled={saving}>Save settings</button>
              </form>
              <div className="panel"><div className="section-heading"><span>HOLDINGS</span><span>{selectedPortfolio.holdings.length} POSITIONS</span></div>{quotesLoading && <p className="muted">Loading market data from yfinance...</p>}{quotesError && <p className="muted">{quotesError}</p>}{selectedPortfolio.holdings.length === 0 ? <p className="muted">No holdings recorded. Add a position below.</p> : <div className="holdings"><div className="holding-row table-head"><span>SYMBOL</span><span>QUANTITY</span><span>AVERAGE COST</span><span>LATEST PRICE</span><span>MARKET VALUE</span><span></span></div>{selectedPortfolio.holdings.map((holding) => { const quote = quotes[holding.symbol]; const marketValue = quote ? Number(holding.quantity) * Number(quote.price) : null; return <div className="holding-row" key={holding.id}><button className="holding-symbol" onClick={() => openHoldingDetails(holding.id)}><strong>{holding.symbol}</strong><small>View details</small></button><span>{holding.quantity}</span><span>${holding.average_cost}</span><span>{quote ? `$${Number(quote.price).toFixed(2)}` : "—"}</span><span>{marketValue === null ? "—" : `$${marketValue.toFixed(2)}`}</span><button className="remove" onClick={() => removeHolding(holding.id)}>Remove</button></div>; })}</div>}{Object.keys(quotes).length > 0 && <p className="data-note">Prices supplied by {Object.values(quotes)[0].provider}. Data may be delayed and is for research only.</p>}</div>
              {detailHolding && <section className="panel detail-panel"><div className="section-heading"><span>{detailHolding.symbol} / DETAILS</span><button className="quiet" type="button" onClick={() => setDetailHolding(null)}>Close</button></div><h3>{detailHolding.symbol}</h3><p className="muted">Basic position information and purchase history.</p><form className="detail-form" onSubmit={saveAverageCost}><label>Total quantity<input value={detailHolding.quantity} readOnly /></label><label>Average cost<input required min="0.01" step="0.01" type="number" value={averageCost} onChange={(event) => setAverageCost(event.target.value)} /></label><button className="primary small" disabled={saving}>Save average cost</button></form><div className="purchase-history"><div className="section-heading"><span>BUY HISTORY</span><span>{detailHolding.purchases.length} ENTRIES</span></div>{detailHolding.purchases.length === 0 ? <p className="muted">No purchase history recorded for this position.</p> : detailHolding.purchases.map((purchase) => <div className="purchase-row" key={purchase.id}><span>{new Date(purchase.purchased_at).toLocaleDateString()}</span><span>{purchase.quantity} units</span><strong>${purchase.price}</strong></div>)}</div><form className="buy-form" onSubmit={addBuy}><p className="form-label">ADD NEW BUY</p><div className="field-grid"><label>Quantity<input required min="0.00000001" step="any" type="number" value={buyForm.quantity} onChange={(event) => setBuyForm({ ...buyForm, quantity: event.target.value })} /></label><label>Buy price<input required min="0.01" step="0.01" type="number" value={buyForm.price} onChange={(event) => setBuyForm({ ...buyForm, price: event.target.value })} /></label><label>Notes<input value={buyForm.notes} onChange={(event) => setBuyForm({ ...buyForm, notes: event.target.value })} /></label></div><button className="primary small" disabled={saving}>Record buy</button></form></section>}
              <form className="panel add-form" onSubmit={addHolding}><div className="section-heading"><span>ADD POSITION</span><span>LOCAL CATALOG</span></div><div className="field-grid"><label className="symbol-field">Symbol<input required maxLength={12} placeholder="VOO" value={holdingForm.symbol} onChange={(event) => setHoldingForm({ ...holdingForm, symbol: event.target.value })} />{suggestions.length > 0 && <div className="suggestions">{suggestions.map((suggestion) => <button type="button" className="suggestion" key={suggestion.id} onClick={() => { setHoldingForm({ ...holdingForm, symbol: suggestion.symbol }); setSuggestions([]); }}><strong>{suggestion.symbol}</strong><span>{suggestion.name} · {suggestion.exchange}</span></button>)}</div>}</label><label>Quantity<input required min="0.00000001" step="any" type="number" placeholder="0" value={holdingForm.quantity} onChange={(event) => setHoldingForm({ ...holdingForm, quantity: event.target.value })} /></label><label>Average cost<input required min="0.01" step="0.01" type="number" placeholder="0.00" value={holdingForm.average_cost} onChange={(event) => setHoldingForm({ ...holdingForm, average_cost: event.target.value })} /></label></div><label>Notes <input placeholder="Optional context" value={holdingForm.notes} onChange={(event) => setHoldingForm({ ...holdingForm, notes: event.target.value })} /></label><button className="primary small" disabled={saving}>Add holding</button></form>
            </>
          )}
        </section>
      </div>
      <footer className="footer">
        <div><strong>Trading Research</strong><span>A Broken Sky Studio app by Alejandro Restrepo.</span></div>
        <nav aria-label="Studio links"><a href="https://www.linkedin.com/in/your-linkedin-handle" target="_blank" rel="noreferrer">LinkedIn placeholder</a><a href="https://brokensky.studio" target="_blank" rel="noreferrer">brokensky.studio</a></nav>
      </footer>
    </main>
  );
}
