"use client";

import { useState } from "react";
import Image from "next/image";
import { API_PUBLIC_URL } from "@/lib/api";

export type QueueItem = { id: string; template_key: string; caption: string; media_uri: string | null; status: string; quality_report: { passed?: boolean; errors?: string[] }; winner_state: string };

export function Queue({ initial }: { initial: QueueItem[] }) {
  const [items, setItems] = useState(initial);
  const [busy, setBusy] = useState<string | null>(null);
  async function act(id: string, action: "approve" | "reject" | "publish") {
    setBusy(id + action);
    const response = await fetch(`/api/proxy/content/${id}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ action }) });
    const result = await response.json();
    if (!response.ok) alert(result.detail ?? "Action failed");
    else setItems(current => current.map(item => item.id === id ? { ...item, status: result.status } : item));
    setBusy(null);
  }
  return <div className="queue-grid">{items.map(item => <article className="content-card" key={item.id}>
    <div className="preview">{item.media_uri ? <Image src={`${API_PUBLIC_URL}${item.media_uri}`} alt="Generated affiliate Pin preview" width={1000} height={1500} unoptimized /> : <div className="empty">Render pending</div>}<span className={`state ${item.status}`}>{item.status.replaceAll("_", " ")}</span></div>
    <div className="content-card-body"><p className="eyebrow">{item.template_key.replaceAll("_", " ")} • PINTEREST</p><p className="caption">{item.caption}</p><div className="quality">{item.quality_report?.passed ? "✓ Quality checks passed" : `⚠ ${(item.quality_report?.errors ?? []).join(", ")}`}</div>
      <div className="actions"><button onClick={() => act(item.id,"approve")} disabled={!!busy}>Approve</button><button onClick={() => act(item.id,"publish")} disabled={!!busy}>Publish</button><button className="ghost" onClick={() => act(item.id,"reject")} disabled={!!busy}>Reject</button></div>
    </div>
  </article>)}</div>;
}
