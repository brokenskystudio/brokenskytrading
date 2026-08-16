import type { Metadata } from "next";

import "./styles.css";

export const metadata: Metadata = {
  title: "Trading Research",
  description: "Local portfolio research workspace",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
