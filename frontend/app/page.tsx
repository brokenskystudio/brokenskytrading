"use client";

import { useEffect, useState } from "react";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const brandPalette = { background: "#140A0D", surface: "#261116", line: "#4D242A", ink: "#FFF4E8", muted: "#BCA49A", accent: "#F6C453", danger: "#FB7185" };

type Portfolio = {
  id: number;
  name: string;
  risk_profile: "conservative" | "balanced" | "aggressive";
  cash_balance: string;
  holdings: { id: number }[];
};

async function loadPortfolios(): Promise<Portfolio[]> {
  const response = await fetch(`${apiBaseUrl}/portfolios`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load portfolios.");
  return response.json();
}

export default function Home() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadPortfolios()
      .then(setPortfolios)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load portfolios."))
      .finally(() => setLoading(false));
  }, []);

  const totalCash = portfolios.reduce((total, portfolio) => total + Number(portfolio.cash_balance), 0);
  const totalHoldings = portfolios.reduce((total, portfolio) => total + portfolio.holdings.length, 0);

  return (
    <main className="shell dashboard-shell" style={{ "--page-background": brandPalette.background, "--surface": brandPalette.surface, "--line": brandPalette.line, "--ink": brandPalette.ink, "--muted": brandPalette.muted, "--accent": brandPalette.accent, "--danger": brandPalette.danger } as React.CSSProperties}>
      <div className="studio-bar">
        <a className="brand" href="https://brokensky.studio" target="_blank" rel="noreferrer" aria-label="Broken Sky Studio website">
          <span className="brand-mark">BSS</span>
          <span><strong>BROKEN SKY</strong><small>STUDIO / PRODUCT 01</small></span>
        </a>
        <span className="studio-owner">ALEJANDRO RESTREPO</span>
      </div>
      <header className="dashboard-hero">
        <div><p className="eyebrow">BROKEN SKY STUDIO / OVERVIEW</p><h1>Your research<br />workspace.</h1></div>
        <p className="hero-copy">A quiet place to keep track of your investment portfolios and the questions worth researching next.</p>
      </header>
      <div className="dashboard-stats"><div><span>PORTFOLIOS</span><strong>{loading ? "—" : portfolios.length}</strong></div><div><span>RECORDED POSITIONS</span><strong>{loading ? "—" : totalHoldings}</strong></div><div><span>CASH ON RECORD</span><strong>{loading ? "—" : `$${totalCash.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}</strong></div></div>
      {error && <div className="error" role="alert">{error} Is the backend running on port 8000?</div>}
      <section className="dashboard-section"><div className="section-heading"><span>YOUR PORTFOLIOS</span><a className="workspace-link" href="/workspace">OPEN WORKSPACE ↗</a></div>{loading ? <p className="muted">Loading your portfolios...</p> : portfolios.length === 0 ? <div className="dashboard-empty"><h2>Your research starts here.</h2><p>Create a portfolio to record holdings, cash, and risk preferences.</p><a className="primary link-button" href="/workspace">Create your first portfolio</a></div> : <div className="dashboard-grid">{portfolios.map((portfolio) => <a className="summary-card" href="/workspace" key={portfolio.id}><div className="summary-card-top"><span className="card-index">{portfolio.id.toString().padStart(2, "0")}</span><span className="risk-pill">{portfolio.risk_profile}</span></div><h2>{portfolio.name}</h2><div className="summary-card-bottom"><span>{portfolio.holdings.length} {portfolio.holdings.length === 1 ? "position" : "positions"}</span><span>${Number(portfolio.cash_balance).toLocaleString("en-US", { minimumFractionDigits: 2 })} cash</span></div></a>)}</div>}</section>
      <footer className="footer"><div><strong>Trading Research</strong><span>A Broken Sky Studio app by Alejandro Restrepo.</span></div><nav aria-label="Studio links"><a href="https://www.linkedin.com/in/your-linkedin-handle" target="_blank" rel="noreferrer">LinkedIn placeholder</a><a href="https://brokensky.studio" target="_blank" rel="noreferrer">brokensky.studio</a></nav></footer>
    </main>
  );
}
