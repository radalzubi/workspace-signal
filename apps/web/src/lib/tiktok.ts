import "server-only";

import { createCipheriv, createDecipheriv, createHash, randomBytes, timingSafeEqual } from "node:crypto";

export const TIKTOK_SESSION_COOKIE = "case_lantern_tiktok";
export const TIKTOK_STATE_COOKIE = "case_lantern_tiktok_state";
export const TIKTOK_COOKIE_PATH = "/api/v1/integrations/tiktok";
export const TIKTOK_MAX_VIDEO_BYTES = 50 * 1024 * 1024;

const AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/";
const TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/";
const REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/";
const UPLOAD_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/";
const STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/";

export type TikTokTokenBundle = {
  access_token: string;
  access_expires_at: number;
  expires_in: number;
  open_id: string;
  refresh_expires_in: number;
  refresh_token: string;
  scope: string;
  token_type: string;
};

type TikTokApiError = {
  error?: string | { code?: string; message?: string; log_id?: string };
  error_description?: string;
};

function required(name: "TIKTOK_CLIENT_KEY" | "TIKTOK_CLIENT_SECRET" | "TIKTOK_REDIRECT_URI"): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`${name} is not configured`);
  return value;
}

function encryptionKey(): Buffer {
  const source = process.env.TIKTOK_COOKIE_SECRET?.trim() || required("TIKTOK_CLIENT_SECRET");
  return createHash("sha256").update(source).digest();
}

function safeEqual(left: string, right: string): boolean {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

function assertTokenBundle(value: unknown): asserts value is TikTokTokenBundle {
  if (!value || typeof value !== "object") throw new Error("TikTok returned an invalid token response");
  const record = value as Record<string, unknown>;
  for (const field of ["access_token", "refresh_token", "open_id", "scope", "token_type"]) {
    if (typeof record[field] !== "string" || !record[field]) {
      throw new Error("TikTok returned an incomplete token response");
    }
  }
  for (const field of ["expires_in", "refresh_expires_in"]) {
    if (typeof record[field] !== "number" || record[field] <= 0) {
      throw new Error("TikTok returned an incomplete token response");
    }
  }
}

function providerError(payload: TikTokApiError, fallback: string): Error {
  if (typeof payload.error === "string") return new Error(`${fallback}: ${payload.error}`);
  const code = payload.error?.code;
  return new Error(code && code !== "ok" ? `${fallback}: ${code}` : fallback);
}

function apiErrorCode(payload: TikTokApiError): string | undefined {
  return typeof payload.error === "object" ? payload.error?.code : payload.error;
}

async function tokenRequest(body: URLSearchParams): Promise<TikTokTokenBundle> {
  const response = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache" },
    body,
    cache: "no-store",
    signal: AbortSignal.timeout(20_000),
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) throw providerError((payload ?? {}) as TikTokApiError, "TikTok token exchange failed");
  assertTokenBundle(payload);
  return { ...payload, access_expires_at: Date.now() + payload.expires_in * 1000 };
}

export function createOAuthState(): string {
  return randomBytes(32).toString("base64url");
}

export function verifyOAuthState(received: string | null, expected: string | undefined): boolean {
  return Boolean(received && expected && safeEqual(received, expected));
}

export function authorizationUrl(state: string): string {
  const params = new URLSearchParams({
    client_key: required("TIKTOK_CLIENT_KEY"),
    response_type: "code",
    scope: "user.info.basic,video.upload",
    redirect_uri: required("TIKTOK_REDIRECT_URI"),
    state,
  });
  return `${AUTHORIZE_URL}?${params.toString()}`;
}

export async function exchangeAuthorizationCode(code: string): Promise<TikTokTokenBundle> {
  return tokenRequest(new URLSearchParams({
    client_key: required("TIKTOK_CLIENT_KEY"),
    client_secret: required("TIKTOK_CLIENT_SECRET"),
    code,
    grant_type: "authorization_code",
    redirect_uri: required("TIKTOK_REDIRECT_URI"),
  }));
}

export async function refreshToken(bundle: TikTokTokenBundle): Promise<TikTokTokenBundle> {
  return tokenRequest(new URLSearchParams({
    client_key: required("TIKTOK_CLIENT_KEY"),
    client_secret: required("TIKTOK_CLIENT_SECRET"),
    grant_type: "refresh_token",
    refresh_token: bundle.refresh_token,
  }));
}

export async function currentToken(bundle: TikTokTokenBundle): Promise<{ bundle: TikTokTokenBundle; refreshed: boolean }> {
  if (bundle.access_expires_at > Date.now() + 5 * 60 * 1000) return { bundle, refreshed: false };
  return { bundle: await refreshToken(bundle), refreshed: true };
}

export function sealToken(bundle: TikTokTokenBundle): string {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", encryptionKey(), iv);
  const ciphertext = Buffer.concat([cipher.update(JSON.stringify(bundle), "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, ciphertext]).toString("base64url");
}

export function openToken(value: string | undefined): TikTokTokenBundle | null {
  if (!value) return null;
  try {
    const packed = Buffer.from(value, "base64url");
    if (packed.length < 29) return null;
    const decipher = createDecipheriv("aes-256-gcm", encryptionKey(), packed.subarray(0, 12));
    decipher.setAuthTag(packed.subarray(12, 28));
    const plaintext = Buffer.concat([decipher.update(packed.subarray(28)), decipher.final()]).toString("utf8");
    const parsed: unknown = JSON.parse(plaintext);
    assertTokenBundle(parsed);
    if (!Number.isFinite(parsed.access_expires_at)) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function tokenCookieMaxAge(bundle: TikTokTokenBundle): number {
  return Math.max(60, Math.min(bundle.refresh_expires_in, 365 * 24 * 60 * 60));
}

export async function revokeToken(bundle: TikTokTokenBundle): Promise<void> {
  const response = await fetch(REVOKE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache" },
    body: new URLSearchParams({
      client_key: required("TIKTOK_CLIENT_KEY"),
      client_secret: required("TIKTOK_CLIENT_SECRET"),
      token: bundle.access_token,
    }),
    cache: "no-store",
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) throw new Error("TikTok disconnect failed");
}

export async function initializeDraftUpload(accessToken: string, videoSize: number): Promise<{ publish_id: string; upload_url: string }> {
  if (!Number.isSafeInteger(videoSize) || videoSize <= 0 || videoSize > TIKTOK_MAX_VIDEO_BYTES) {
    throw new Error("Video must be between 1 byte and 50 MB");
  }
  const response = await fetch(UPLOAD_INIT_URL, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      source_info: { source: "FILE_UPLOAD", video_size: videoSize, chunk_size: videoSize, total_chunk_count: 1 },
    }),
    cache: "no-store",
    signal: AbortSignal.timeout(20_000),
  });
  const payload = await response.json().catch(() => ({})) as TikTokApiError & {
    data?: { publish_id?: string; upload_url?: string };
  };
  if (!response.ok || apiErrorCode(payload) !== "ok" || !payload.data?.publish_id || !payload.data.upload_url) {
    throw providerError(payload, "TikTok could not initialize the draft upload");
  }
  const upload = new URL(payload.data.upload_url);
  if (upload.protocol !== "https:" || !upload.hostname.endsWith("tiktokapis.com")) {
    throw new Error("TikTok returned an invalid upload destination");
  }
  return { publish_id: payload.data.publish_id, upload_url: payload.data.upload_url };
}

export async function fetchDraftStatus(accessToken: string, publishId: string): Promise<Record<string, unknown>> {
  if (!/^[A-Za-z0-9._~-]{1,200}$/.test(publishId)) throw new Error("Invalid TikTok publish ID");
  const response = await fetch(STATUS_URL, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json; charset=UTF-8" },
    body: JSON.stringify({ publish_id: publishId }),
    cache: "no-store",
    signal: AbortSignal.timeout(20_000),
  });
  const payload = await response.json().catch(() => ({})) as TikTokApiError & { data?: Record<string, unknown> };
  if (!response.ok || apiErrorCode(payload) !== "ok") throw providerError(payload, "TikTok draft status check failed");
  return payload.data ?? {};
}

export function publicConnection(bundle: TikTokTokenBundle | null): { connected: boolean; scope?: string; expires_at?: string } {
  if (!bundle) return { connected: false };
  return { connected: true, scope: bundle.scope, expires_at: new Date(bundle.access_expires_at).toISOString() };
}
