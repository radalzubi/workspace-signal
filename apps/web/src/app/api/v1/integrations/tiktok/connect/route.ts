import { NextResponse } from "next/server";
import { authorizationUrl, createOAuthState, TIKTOK_COOKIE_PATH, TIKTOK_STATE_COOKIE } from "@/lib/tiktok";

export const runtime = "nodejs";

export async function GET() {
  try {
    const state = createOAuthState();
    const response = NextResponse.redirect(authorizationUrl(state));
    response.cookies.set(TIKTOK_STATE_COOKIE, state, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: TIKTOK_COOKIE_PATH,
      maxAge: 10 * 60,
    });
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    return NextResponse.redirect(new URL("/tiktok-connect?error=configuration", process.env.WEB_URL ?? "https://workspacesignal.com"));
  }
}
