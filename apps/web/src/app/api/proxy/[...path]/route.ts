import { NextRequest, NextResponse } from "next/server";
import { API_INTERNAL_URL } from "@/lib/api";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const url = `${API_INTERNAL_URL}/api/v1/${path.join("/")}${request.nextUrl.search}`;
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${process.env.ADMIN_API_KEY ?? "demo-admin-change-me"}`);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer();
  const response = await fetch(url, { method: request.method, headers, body, cache: "no-store" });
  return new NextResponse(response.body, { status: response.status, headers: { "content-type": response.headers.get("content-type") ?? "application/json" } });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
