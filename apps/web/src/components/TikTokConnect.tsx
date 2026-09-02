"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Connection = { connected: boolean; scope?: string; expires_at?: string };
type UploadInit = { publish_id: string; upload_url: string; detail?: string };

const MAX_BYTES = 50 * 1024 * 1024;

export function TikTokConnect() {
  const [connection, setConnection] = useState<Connection | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("Checking connection…");
  const [busy, setBusy] = useState(false);

  async function refreshConnection() {
    const response = await fetch("/api/v1/integrations/tiktok/session", { cache: "no-store" });
    const result = await response.json() as Connection;
    setConnection(result);
    setMessage(result.connected ? "TikTok is connected for draft uploads." : "Connect the target TikTok account to continue.");
  }

  useEffect(() => {
    let active = true;
    void fetch("/api/v1/integrations/tiktok/session", { cache: "no-store" })
      .then((response) => response.json() as Promise<Connection>)
      .then((result) => {
        if (!active) return;
        setConnection(result);
        setMessage(result.connected ? "TikTok is connected for draft uploads." : "Connect the target TikTok account to continue.");
      });
    return () => { active = false; };
  }, []);

  async function uploadDraft() {
    if (!file || busy) return;
    if (file.size <= 0 || file.size > MAX_BYTES) {
      setMessage("Choose an MP4 or MOV file no larger than 50 MB.");
      return;
    }
    setBusy(true);
    setMessage("Opening a secure TikTok upload…");
    try {
      const initResponse = await fetch("/api/v1/integrations/tiktok/drafts/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_size: file.size, content_type: file.type || "video/mp4" }),
      });
      const init = await initResponse.json() as UploadInit;
      if (!initResponse.ok) throw new Error(init.detail || "Draft initialization failed");
      setMessage("Uploading the original video directly to TikTok…");
      const uploadResponse = await fetch(init.upload_url, {
        method: "PUT",
        headers: {
          "Content-Type": file.type || "video/mp4",
          "Content-Range": `bytes 0-${file.size - 1}/${file.size}`,
        },
        body: file,
      });
      if (!uploadResponse.ok) throw new Error(`TikTok upload returned ${uploadResponse.status}`);
      setMessage(`Draft accepted (${init.publish_id}). Open TikTok → Inbox to review, edit, and post it.`);
      window.setTimeout(async () => {
        const statusResponse = await fetch(`/api/v1/integrations/tiktok/drafts/status?publish_id=${encodeURIComponent(init.publish_id)}`);
        if (statusResponse.ok) {
          const status = await statusResponse.json() as Record<string, unknown>;
          const state = String(status.status ?? status.publish_status ?? "processing");
          setMessage(`TikTok draft status: ${state}. Open TikTok → Inbox to finish the post.`);
        }
      }, 5000);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The draft upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    setBusy(true);
    await fetch("/api/v1/integrations/tiktok/disconnect", { method: "POST" });
    await refreshConnection();
    setBusy(false);
  }

  return <section className="tiktok-card">
    <div className="tiktok-card-head">
      <div><span>CASE LANTERN</span><h2>TikTok draft connection</h2></div>
      <b className={connection?.connected ? "connected" : "disconnected"}>{connection?.connected ? "Connected" : "Not connected"}</b>
    </div>
    <p className="tiktok-explainer">This tool sends an original Case Lantern MP4 to your TikTok Draft inbox. It never publishes publicly. You must review and complete every post inside TikTok.</p>
    {!connection?.connected ? <Link className="tiktok-button" href="/api/v1/integrations/tiktok/connect" prefetch={false}>Continue with TikTok</Link> : <>
      <label className="tiktok-file">Choose approved MP4 or MOV
        <input accept="video/mp4,video/quicktime,.mp4,.mov" type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <small>{file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MB` : "Maximum 50 MB · H.264/AAC recommended"}</small>
      </label>
      <div className="tiktok-actions">
        <button className="tiktok-button" disabled={!file || busy} onClick={() => void uploadDraft()} type="button">{busy ? "Working…" : "Send to TikTok Drafts"}</button>
        <button className="tiktok-link" disabled={busy} onClick={() => void disconnect()} type="button">Disconnect</button>
      </div>
    </>}
    <p className="tiktok-message" aria-live="polite">{message}</p>
    <div className="tiktok-safety"><b>Safety lock</b><span>Draft-only API</span><span>Original media only</span><span>Human post required</span></div>
  </section>;
}
