import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DealForge — Affiliate operating system",
  description: "Profit-first deal discovery, content production and Pinterest operations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
