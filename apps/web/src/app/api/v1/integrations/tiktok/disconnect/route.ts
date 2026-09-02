import { NextRequest, NextResponse } from "next/server";
import { openToken, revokeToken, TIKTOK_COOKIE_PATH, TIKTOK_SESSION_COOKIE } from "@/lib/tiktok";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const bundle = openToken(request.cookies.get(TIKTOK_SESSION_COOKIE)?.value);
  if (bundle) await revokeToken(bundle).catch(() => undefined);
  const response = NextResponse.json({ connected: false }, { headers: { "Cache-Control": "no-store" } });
  response.cookies.delete({ name: TIKTOK_SESSION_COOKIE, path: TIKTOK_COOKIE_PATH });
  return response;
}
