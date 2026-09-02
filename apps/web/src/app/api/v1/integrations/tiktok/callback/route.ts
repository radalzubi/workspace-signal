import { NextRequest, NextResponse } from "next/server";
import {
  exchangeAuthorizationCode,
  sealToken,
  TIKTOK_COOKIE_PATH,
  TIKTOK_SESSION_COOKIE,
  TIKTOK_STATE_COOKIE,
  tokenCookieMaxAge,
  verifyOAuthState,
} from "@/lib/tiktok";

export const runtime = "nodejs";

function destination(request: NextRequest, result: string): URL {
  return new URL(`/tiktok-connect?${result}`, request.nextUrl.origin);
}

export async function GET(request: NextRequest) {
  const state = request.nextUrl.searchParams.get("state");
  const code = request.nextUrl.searchParams.get("code");
  const providerError = request.nextUrl.searchParams.get("error");
  if (providerError) return NextResponse.redirect(destination(request, "error=authorization_denied"));
  if (!code || !verifyOAuthState(state, request.cookies.get(TIKTOK_STATE_COOKIE)?.value)) {
    return NextResponse.redirect(destination(request, "error=invalid_state"));
  }
  try {
    const bundle = await exchangeAuthorizationCode(code);
    const scopes = new Set(bundle.scope.split(",").map((scope) => scope.trim()));
    if (!scopes.has("video.upload")) return NextResponse.redirect(destination(request, "error=missing_video_scope"));
    const response = NextResponse.redirect(destination(request, "connected=1"));
    response.cookies.set(TIKTOK_SESSION_COOKIE, sealToken(bundle), {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: TIKTOK_COOKIE_PATH,
      maxAge: tokenCookieMaxAge(bundle),
    });
    response.cookies.delete({ name: TIKTOK_STATE_COOKIE, path: TIKTOK_COOKIE_PATH });
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    return NextResponse.redirect(destination(request, "error=token_exchange"));
  }
}
