import { NextRequest, NextResponse } from "next/server";
import { API_INTERNAL_URL } from "@/lib/api";

const MAX_BODY_BYTES = 5 * 1024 * 1024;
const PLACEHOLDER_KEYS = new Set(["", "demo-admin-change-me", "replace-with-at-least-32-random-characters"]);

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!path.length || path.some((segment) => !/^[A-Za-z0-9._~-]+$/.test(segment))) {
    return NextResponse.json({ detail: "Invalid API path" }, { status: 400 });
  }
  const adminKey = process.env.ADMIN_API_KEY ?? "";
  if (PLACEHOLDER_KEYS.has(adminKey) || adminKey.length < 32) {
    return NextResponse.json(
      { detail: "Private API proxy is not configured" },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (!Number.isFinite(contentLength) || contentLength > MAX_BODY_BYTES) {
    return NextResponse.json({ detail: "Request body is too large" }, { status: 413 });
  }
  const safePath = path.map(encodeURIComponent).join("/");
  const url = `${API_INTERNAL_URL}/api/v1/${safePath}${request.nextUrl.search}`;
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${adminKey}`);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer();
  if (body && body.byteLength > MAX_BODY_BYTES) {
    return NextResponse.json({ detail: "Request body is too large" }, { status: 413 });
  }
  try {
    const response = await fetch(url, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(15_000),
    });
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "X-Robots-Tag": "noindex, nofollow, noarchive",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Private API service is unavailable" },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
