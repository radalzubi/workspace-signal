import { timingSafeEqual } from "node:crypto";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

function sameValue(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  return leftBuffer.length === rightBuffer.length && timingSafeEqual(leftBuffer, rightBuffer);
}

export function proxy(request: NextRequest) {
  if (process.env.NODE_ENV !== "production") return NextResponse.next();

  const user = process.env.DASHBOARD_USER;
  const password = process.env.DASHBOARD_PASSWORD;
  if (!user || !password) {
    return new NextResponse("DealForge dashboard is unavailable until private access is configured.", {
      status: 503,
      headers: { "Cache-Control": "no-store" },
    });
  }

  const supplied = request.headers.get("authorization") ?? "";
  const expected = `Basic ${Buffer.from(`${user}:${password}`).toString("base64")}`;
  if (!sameValue(supplied, expected)) {
    return new NextResponse("Authentication required", {
      status: 401,
      headers: {
        "Cache-Control": "no-store",
        "WWW-Authenticate": 'Basic realm="DealForge Operations", charset="UTF-8"',
      },
    });
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/overview/:path*", "/products/:path*", "/deals/:path*", "/opportunities/:path*",
    "/seo/:path*", "/affiliate-programs/:path*", "/content/:path*", "/content-queue/:path*",
    "/published/:path*", "/analytics/:path*", "/revenue/:path*", "/experiments/:path*",
    "/campaigns/:path*", "/costs/:path*", "/settings/:path*", "/strategy-report/:path*",
    "/watchlists/:path*", "/system-health/:path*", "/api/proxy/:path*",
  ],
};
