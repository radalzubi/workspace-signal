import type { Metadata } from "next";
import "./globals.css";
import "./public.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://workspacesignal.com"),
  title: { default: "Workspace Signal", template: "%s — Workspace Signal" },
  description: "Independent workspace guides, practical comparisons, and verified deal context for home offices.",
  openGraph: { siteName: "Workspace Signal", type: "website", locale: "en_US" },
  verification: {
    other: {
      "p:domain_verify": "00981787995b3c3d63ef630304f3819c",
    },
  },
};

const impactVerificationMeta = {
  name: "impact-site-verification",
  value: "4152e211-aa50-48d8-a061-f38bc85aeb7d",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <meta {...impactVerificationMeta} />
      </head>
      <body>{children}</body>
    </html>
  );
}
