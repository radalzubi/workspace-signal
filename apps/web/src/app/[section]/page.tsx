import { notFound } from "next/navigation";
import { Economics } from "@/components/Economics";
import { Onboarding } from "@/components/Onboarding";
import { Overview, type OverviewData } from "@/components/Overview";
import { Queue, type QueueItem } from "@/components/Queue";
import { sectionKeys, Shell } from "@/components/Shell";
import { apiGet, money } from "@/lib/api";

type Params = Promise<{ section: string }>;

export default async function SectionPage({ params }: { params: Params }) {
  const { section } = await params;
  if (!sectionKeys.includes(section as never)) notFound();
  const settings = await apiGet<Record<string, unknown>>("/settings");
  let body: React.ReactNode;
  if (section === "overview") {
    const [overview, deals, health] = await Promise.all([
      apiGet<OverviewData>("/overview"),
      apiGet<Array<Record<string, unknown>>>("/deals"),
      apiGet<Record<string, unknown>>("/system-health"),
    ]);
    body = <Overview data={overview} deals={deals} health={health} />;
  } else if (section === "content-queue" || section === "content") {
    const items = await apiGet<QueueItem[]>("/content");
    body = <><div className="section-intro"><div><p className="eyebrow">HUMAN-IN-THE-LOOP</p><h2>{section === "content-queue" ? "Approve the work worth publishing" : "Generated content library"}</h2></div><span className="pill">AUTO_PUBLISH: {settings.auto_publish ? "ON" : "OFF"}</span></div><Queue initial={items} /></>;
  } else if (section === "analytics" || section === "revenue") {
    const data = await apiGet<OverviewData>("/overview");
    body = <><Overview data={data} deals={[]} health={{}} /><Economics /></>;
  } else if (section === "settings") {
    body = <><Onboarding /><Economics /></>;
  } else {
    body = <GenericSection section={section} />;
  }
  return <Shell section={section} demo={Boolean(settings.demo_mode)}>{body}</Shell>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function textValue(...values: unknown[]): string {
  const value = values.find((item) => typeof item === "string" || typeof item === "number");
  return value === undefined ? "" : String(value);
}

function metricValue(row: Record<string, unknown>): string {
  if (typeof row.current_price === "string" || typeof row.current_price === "number") {
    return money(row.current_price);
  }
  if (typeof row.deal_score === "string" || typeof row.deal_score === "number") {
    return String(row.deal_score);
  }
  if (typeof row.amount === "string" || typeof row.amount === "number") {
    return money(row.amount);
  }
  return "Active";
}

async function GenericSection({ section }: { section: string }) {
  const routes: Record<string, string> = {
    products: "/products", deals: "/deals", published: "/publications",
    experiments: "/experiments", costs: "/costs", "system-health": "/system-health",
    campaigns: "/experiments",
  };
  const data = await apiGet<unknown>(routes[section] ?? "/overview");
  const rows = Array.isArray(data) ? data.filter(isRecord) : isRecord(data) ? [data] : [];
  return <section className="panel"><div className="panel-head"><div><p className="eyebrow">LIVE OPERATING DATA</p><h2>{section.replaceAll("-", " ")}</h2></div><span className="pill">{rows.length} records</span></div><div className="generic-list">{rows.map((row, index) => <article key={textValue(row.id, index)}><div><b>{textValue(row.product_name, row.name, row.summary, row.platform, "System snapshot")}</b><small>{textValue(row.category, row.hypothesis, row.status, "Current data")}</small></div><div><strong>{metricValue(row)}</strong><small>{row.discount_percent ? `${textValue(row.discount_percent)}% listed discount` : textValue(row.currency)}</small></div></article>)}</div></section>;
}
