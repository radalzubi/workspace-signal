import { NextRequest, NextResponse } from "next/server";
import {
  currentToken,
  initializeDraftUpload,
  openToken,
  sealToken,
  TIKTOK_COOKIE_PATH,
  TIKTOK_SESSION_COOKIE,
  tokenCookieMaxAge,
} from "@/lib/tiktok";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const stored = openToken(request.cookies.get(TIKTOK_SESSION_COOKIE)?.value);
  if (!stored) return NextResponse.json({ detail: "Connect TikTok first" }, { status: 401 });
  try {
    const body = await request.json() as { video_size?: unknown; content_type?: unknown };
    if (body.content_type !== "video/mp4" && body.content_type !== "video/quicktime") {
      return NextResponse.json({ detail: "Choose an MP4 or MOV video" }, { status: 400 });
    }
    const { bundle, refreshed } = await currentToken(stored);
    const upload = await initializeDraftUpload(bundle.access_token, Number(body.video_size));
    const response = NextResponse.json(upload, { headers: { "Cache-Control": "no-store" } });
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
    return NextResponse.json({ detail: "TikTok could not initialize this draft" }, { status: 502 });
  }
}
