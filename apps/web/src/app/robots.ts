import type { MetadataRoute } from "next";
import { site } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return { rules: [{ userAgent: "*", allow: "/", disallow: ["/api/", "/overview", "/products", "/deals", "/opportunities", "/seo", "/affiliate-programs", "/content", "/content-queue", "/published", "/analytics", "/revenue", "/experiments", "/campaigns", "/costs", "/settings", "/strategy-report", "/watchlists", "/system-health"] }], sitemap: `${site.url}/sitemap.xml` };
}
