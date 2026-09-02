import type { Metadata } from "next";
import "./globals.css";
import "./public.css";
import "./case-lantern.css";
import "./tiktok.css";

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
  value: "e25a1cc9-4aee-4766-a206-5e3c4a48d1c9",
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
