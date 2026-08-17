"use client";

import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  ["Home", "/"],
  ["Market", "/market"],
  ["Workspace", "/workspace"],
  ["Risk guide", "/risk-profiles"],
] as const;

export default function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  function isActive(path: string) {
    return path === "/" ? pathname === path : pathname.startsWith(path);
  }

  return (
    <header className="site-header">
      <a className="brand" href="/" aria-label="Broken Sky Studio home">
        <span className="brand-mark">BSS</span>
        <span><strong>BROKEN SKY</strong><small>STUDIO / PRODUCT 01</small></span>
      </a>
      <button className="mobile-nav-toggle" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="site-navigation">{open ? "Close" : "Menu"}</button>
      <nav id="site-navigation" className={`site-nav ${open ? "open" : ""}`} aria-label="Primary navigation">
        {links.map(([label, href]) => <a className={isActive(href) ? "active" : ""} aria-current={isActive(href) ? "page" : undefined} href={href} key={href} onClick={() => setOpen(false)}>{label}</a>)}
      </nav>
      <span className="studio-owner">ALEJANDRO RESTREPO</span>
    </header>
  );
}
