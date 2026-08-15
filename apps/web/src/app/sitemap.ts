import type { MetadataRoute } from "next";
import { guides, site } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const pages = ["", "/guides", "/picks", "/about", "/methodology", "/affiliate-disclosure", "/privacy", "/terms", "/contact"];
  return [...pages.map((path) => ({ url: `${site.url}${path}`, lastModified: new Date("2026-08-15"), changeFrequency: path === "" ? "weekly" as const : "monthly" as const, priority: path === "" ? 1 : path === "/guides" ? 0.9 : 0.5 })), ...guides.map((guide) => ({ url: `${site.url}/guides/${guide.slug}`, lastModified: new Date("2026-08-15"), changeFrequency: "monthly" as const, priority: 0.8 }))];
}
