import { NextRequest, NextResponse } from "next/server";
import { openToken, publicConnection, TIKTOK_SESSION_COOKIE } from "@/lib/tiktok";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const bundle = openToken(request.cookies.get(TIKTOK_SESSION_COOKIE)?.value);
  return NextResponse.json(publicConnection(bundle), { headers: { "Cache-Control": "no-store" } });
}
