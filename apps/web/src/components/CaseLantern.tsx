"use client";

import { useState } from "react";

type StorySource = {
  id: string;
  title: string;
  publisher: string;
  url: string;
  source_type: string;
  verified: boolean;
};

type StoryClaim = {
  id: string;
  claim_text: string;
  source_ids: string[];
  status: string;
};

type QualityReport = {
  passed?: boolean;
  errors?: string[];
  warnings?: string[];
  word_count?: number;
  source_count?: number;
  verified_source_count?: number;
  supported_claim_ratio?: number;
  human_approval_required?: boolean;
  public_auto_post_allowed?: boolean;
};

export type StoryProject = {
  id: string;
  title: string;
  slug: string;
  status: string;
  story_type: string;
  hook: string;
  synopsis: string;
  script: string;
  caption: string;
  duration_seconds: number;
  risk_level: string;
  factual_confidence: number;
  quality_report: QualityReport;
  visual_plan: Array<{ seconds: string; asset: string; text: string }>;
  export_uri: string | null;
  approved_at: string | null;
  sources: StorySource[];
  claims: StoryClaim[];
};

type ActionResult = {
  detail?: string;
  story_id?: string;
  status?: string;
  export_uri?: string | null;
  approved_at?: string | null;
};

export function CaseLantern({ initial, settings }: { initial: StoryProject[]; settings: Record<string, unknown> }) {
  const [stories, setStories] = useState(initial);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    const response = await fetch("/api/proxy/case-lantern/stories", { cache: "no-store" });
    if (response.ok) setStories(await response.json() as StoryProject[]);
  }

  async function createPilot() {
    setBusy("pilot");
    setMessage(null);
    const response = await fetch("/api/proxy/case-lantern/pilot", { method: "POST" });
    const result = await response.json() as ActionResult;
    if (!response.ok) setMessage(result.detail ?? "Pilot creation failed.");
    else {
      await refresh();
      setMessage("Sourced pilot created and queued for human review.");
    }
    setBusy(null);
  }

  async function act(story: StoryProject, action: "approve" | "reject" | "regenerate" | "export") {
    let reason: string | null = null;
    if (action === "reject") {
      reason = window.prompt("Why should this story be rejected?", "Needs factual or editorial changes.");
      if (reason === null) return;
    }
    setBusy(`${story.id}:${action}`);
    setMessage(null);
    const response = await fetch(`/api/proxy/case-lantern/stories/${story.id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action, reason }),
    });
    const result = await response.json() as ActionResult;
    if (!response.ok) setMessage(result.detail ?? "Action failed.");
    else {
      setStories((current) => current.map((item) => item.id === story.id ? {
        ...item,
        status: result.status ?? item.status,
        export_uri: result.export_uri ?? item.export_uri,
        approved_at: result.approved_at ?? item.approved_at,
      } : item));
      const label = action === "export" ? "Draft package created. Final upload still requires review." : `Story ${action}d.`;
      setMessage(label);
    }
    setBusy(null);
  }

  const enabled = Boolean(settings.case_lantern_enabled);
  const approved = stories.filter((story) => Boolean(story.approved_at)).length;
  const ready = stories.filter((story) => story.status === "render_ready").length;

  return <div className="case-lantern-page">
    <div className="section-intro case-lantern-hero">
      <div>
        <p className="eyebrow">SOURCED TRUE-CRIME PRODUCTION</p>
        <h2>Case Lantern control room</h2>
        <p>Research, validate, approve, and export original TikTok stories without unsafe public auto-posting.</p>
      </div>
      <button onClick={createPilot} disabled={busy === "pilot" || stories.length > 0}>{stories.length ? "Pilot created" : "Create sourced pilot"}</button>
    </div>

    <div className="case-metrics">
      <article><small>Automation</small><strong>{enabled ? "ACTIVE" : "SAFE OFF"}</strong></article>
      <article><small>Stories in pipeline</small><strong>{stories.length}</strong></article>
      <article><small>Human approved</small><strong>{approved}</strong></article>
      <article><small>Draft packages ready</small><strong>{ready}</strong></article>
      <article><small>Publishing mode</small><strong>{String(settings.tiktok_posting_mode ?? "draft").toUpperCase()}</strong></article>
    </div>

    <div className="case-lock">🔒 Public auto-post is locked. Every story requires factual validation, your approval, and final TikTok review.</div>
    {message && <div className="case-message" role="status">{message}</div>}

    {stories.length === 0 ? <section className="panel case-empty"><h3>No story projects yet</h3><p>Create the D.B. Cooper pilot to test the complete sourced workflow.</p></section> : stories.map((story) => {
      const report = story.quality_report ?? {};
      const locked = busy?.startsWith(story.id) ?? false;
      return <article className="panel case-story" key={story.id}>
        <div className="panel-head">
          <div><p className="eyebrow">{story.story_type.replaceAll("_", " ")} • {story.duration_seconds}s</p><h2>{story.title}</h2><p className="case-hook">{story.hook}</p></div>
          <div className="case-badges"><span className={`state ${story.status}`}>{story.status.replaceAll("_", " ")}</span><span className="pill">Confidence {story.factual_confidence}%</span><span className="pill">Risk {story.risk_level}</span></div>
        </div>

        <div className="case-quality">
          <span className={report.passed ? "pass" : "fail"}>{report.passed ? "✓ Validation passed" : "⚠ Validation blocked"}</span>
          <span>{report.word_count ?? 0} words</span><span>{report.verified_source_count ?? 0}/{report.source_count ?? 0} verified sources</span><span>{Math.round((report.supported_claim_ratio ?? 0) * 100)}% claims supported</span>
        </div>
        {(report.errors ?? []).map((error) => <p className="case-error" key={error}>{error}</p>)}

        <div className="case-columns">
          <section><h3>Narration script</h3><p className="case-script">{story.script}</p><h3>Caption</h3><p className="case-caption">{story.caption}</p></section>
          <aside><h3>Verified sources</h3>{story.sources.map((source) => <a className="case-source" href={source.url} target="_blank" rel="noreferrer" key={source.id}><b>{source.title}</b><small>{source.publisher} • {source.verified ? "Verified" : "Unverified"}</small></a>)}
            <h3>Structured claims</h3>{story.claims.map((claim) => <div className="case-claim" key={claim.id}><span>{claim.status === "supported" ? "✓" : "!"}</span><p>{claim.claim_text}</p></div>)}
          </aside>
        </div>

        <h3>Original visual plan</h3>
        <div className="case-visuals">{story.visual_plan.map((beat) => <div key={`${beat.seconds}-${beat.text}`}><b>{beat.seconds}</b><span>{beat.asset}</span><small>{beat.text}</small></div>)}</div>
        {story.export_uri && <p className="case-export"><b>Draft package:</b> {story.export_uri}</p>}
        <div className="actions case-actions">
          <button onClick={() => act(story, "approve")} disabled={locked || !report.passed || Boolean(story.approved_at)}>Approve</button>
          <button onClick={() => act(story, "export")} disabled={locked || !story.approved_at}>Export TikTok draft</button>
          <button className="ghost" onClick={() => act(story, "regenerate")} disabled={locked}>Request rewrite</button>
          <button className="ghost" onClick={() => act(story, "reject")} disabled={locked}>Reject</button>
        </div>
      </article>;
    })}
  </div>;
}
