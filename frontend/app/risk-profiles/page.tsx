import Link from "next/link";
import SiteHeader from "../components/site-header";

const profiles = [
  {
    name: "Conservative",
    code: "01 / PRESERVE",
    description: "Prioritizes lower concentration and a larger cash reserve. It is designed for users who prefer a more defensive starting policy.",
    accent: "defensive",
    rules: [["Maximum single holding", "10%"], ["Minimum cash target", "10%"], ["Preferred holdings", "8+"], ["Volatility preference", "Lower"]],
  },
  {
    name: "Balanced",
    code: "02 / COMPOSE",
    description: "A middle-ground policy that balances diversification, cash reserves, and exposure to growth assets.",
    accent: "balanced",
    rules: [["Maximum single holding", "15%"], ["Minimum cash target", "5%"], ["Preferred holdings", "6+"], ["Volatility preference", "Moderate"]],
  },
  {
    name: "Aggressive",
    code: "03 / EXPLORE",
    description: "Allows larger positions and less cash for users who accept higher concentration and volatility in pursuit of growth.",
    accent: "growth",
    rules: [["Maximum single holding", "25%"], ["Minimum cash target", "0%"], ["Preferred holdings", "4+"], ["Volatility preference", "Higher tolerated"]],
  },
];

export default function RiskProfilesPage() {
  return (
    <main className="shell risk-page" style={{ "--page-background": "#F3E9D8", "--surface": "#E5D4BA", "--line": "#B99B78", "--ink": "#241A14", "--muted": "#634D3B", "--accent": "#854719", "--danger": "#963B2F", "--button-ink": "#FFF8ED" } as React.CSSProperties}>
      <SiteHeader />
      <header className="risk-hero"><p className="eyebrow">TRADING RESEARCH / POLICY GUIDE</p><h1>Choose a policy<br />for your research.</h1><p>Risk profiles are portfolio-analysis settings. They describe the rules the app will use to identify concentration, cash, and diversification alerts.</p></header>
      <section className="risk-grid">{profiles.map((profile) => <article className={`risk-card ${profile.accent}`} key={profile.name}><div className="risk-card-top"><span>{profile.code}</span><span>PROFILE</span></div><h2>{profile.name}</h2><p>{profile.description}</p><div className="risk-rules">{profile.rules.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div></article>)}</section>
      <section className="risk-notes"><div><p className="eyebrow">HOW TO READ THIS</p><h2>Rules create signals,<br />not instructions.</h2></div><p>These are product defaults, not universal financial rules or a regulated suitability assessment. A breach means that a configured portfolio policy may need review. The app does not execute trades or guarantee outcomes.</p></section>
      <footer className="footer"><div><strong>Trading Research</strong><span>A Broken Sky Studio app by Alejandro Restrepo.</span></div><nav aria-label="Page links"><Link href="/workspace">Workspace</Link><a href="https://www.linkedin.com/in/your-linkedin-handle" target="_blank" rel="noreferrer">LinkedIn placeholder</a><a href="https://brokensky.studio" target="_blank" rel="noreferrer">brokensky.studio</a></nav></footer>
    </main>
  );
}
