import { NextRequest, NextResponse } from "next/server";
import {
  currentToken,
  fetchDraftStatus,
  openToken,
  sealToken,
  TIKTOK_COOKIE_PATH,
  TIKTOK_SESSION_COOKIE,
  tokenCookieMaxAge,
} from "@/lib/tiktok";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const stored = openToken(request.cookies.get(TIKTOK_SESSION_COOKIE)?.value);
  if (!stored) return NextResponse.json({ detail: "Connect TikTok first" }, { status: 401 });
  try {
    const publishId = request.nextUrl.searchParams.get("publish_id") ?? "";
    const { bundle, refreshed } = await currentToken(stored);
    const status = await fetchDraftStatus(bundle.access_token, publishId);
    const response = NextResponse.json({ publish_id: publishId, ...status }, { headers: { "Cache-Control": "no-store" } });
    if (refreshed) {
      response.cookies.set(TIKTOK_SESSION_COOKIE, sealToken(bundle), {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: TIKTOK_COOKIE_PATH,
        maxAge: tokenCookieMaxAge(bundle),
      });
    }
    return response;
  } catch {
    return NextResponse.json({ detail: "TikTok draft status is not available yet" }, { status: 502 });
  }
}
