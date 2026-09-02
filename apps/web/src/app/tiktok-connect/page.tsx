import type { Metadata } from "next";
import Link from "next/link";
import { TikTokConnect } from "@/components/TikTokConnect";

export const metadata: Metadata = { title: "TikTok Draft Connection", robots: { index: false, follow: false } };

export default function TikTokConnectPage() {
  return <main className="tiktok-page"><div className="tiktok-shell">
    <Link className="tiktok-brand" href="/"><i><span /><span /><span /></i> Workspace Signal</Link>
    <TikTokConnect />
    <p className="tiktok-footnote">Private operator tool · Tokens are encrypted and stored in an HTTP-only browser session.</p>
  </div></main>;
}
