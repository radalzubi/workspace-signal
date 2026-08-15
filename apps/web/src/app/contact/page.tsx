import type { Metadata } from "next";
import { PublicLayout } from "@/components/PublicSite";

export const metadata: Metadata = { title: "Contact", description: "Contact Workspace Signal about corrections, partnerships, or general questions.", alternates: { canonical: "/contact" } };

export default function ContactPage() {
  return <PublicLayout><section className="public-page-hero"><p className="public-kicker"><span /> Contact</p><h1>Send the right signal.</h1><p>Questions, corrections, partnership inquiries, and product-data updates are welcome.</p></section><section className="contact-grid"><div><span>General and editorial</span><h2>hello@workspacesignal.com</h2><p>For corrections, identify the page and include the reliable source supporting the change.</p><a className="public-primary" href="mailto:hello@workspacesignal.com">Open email <span>→</span></a></div><aside><b>Please do not send</b><ul><li>Passwords or access tokens</li><li>Payment-card or bank information</li><li>Tax identifiers or identity documents</li><li>Unlicensed product images</li></ul><p>Workspace Signal does not currently accept unsolicited guest posts or paid ranking requests.</p></aside></section></PublicLayout>;
}
