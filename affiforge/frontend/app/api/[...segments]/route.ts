import { NextRequest, NextResponse } from "next/server";
import { backend, SESSION_COOKIE } from "../../../lib/backend";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const routes = {
  GET: /^(users\/registration|sites|content|content\/\d+|earnings\/dashboard|billing\/status)$/,
  POST: /^(users\/(register|token|logout)|sites|content|content\/\d+\/publish|generator\/(cluster|generate|reddit-scan)|earnings|billing\/(checkout-session|portal|profitshare\/toggle))$/,
  PATCH: /^content\/\d+$/,
  PUT: /^sites\/\d+$/,
};

const openRoutes = new Set(["users/registration", "users/register", "users/token", "users/logout"]);
const listRoutes = new Set(["sites", "content", "earnings"]);
const apiHeaders = { "Cache-Control": "no-store" };
const cookieOptions = {
  httpOnly: true,
  secure: process.env.ENVIRONMENT === "production",
  sameSite: "lax" as const,
  path: "/",
};

function error(detail: string, status: number) {
  return NextResponse.json({ detail }, { status, headers: apiHeaders });
}

async function api(
  request: NextRequest,
  context: { params: Promise<{ segments: string[] }> },
) {
  const path = (await context.params).segments.join("/");
  const method = request.method as keyof typeof routes;
  if (!routes[method]?.test(path)) return error("Endpoint not found", 404);

  if (method !== "GET") {
    const origin = process.env.APP_ORIGIN ?? "http://localhost:3000";
    if (request.headers.get("origin") !== origin) return error("Invalid request origin", 403);
  }

  if (path === "users/logout") {
    const response = NextResponse.json({ ok: true }, { headers: apiHeaders });
    response.cookies.set(SESSION_COOKIE, "", { ...cookieOptions, maxAge: 0 });
    return response;
  }

  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token && !openRoutes.has(path)) return error("Sign in to continue", 401);

  const headers = new Headers({ Accept: "application/json" });
  if (token && !openRoutes.has(path)) headers.set("Authorization", `Bearer ${token}`);
  let body: Uint8Array | undefined;
  if (method !== "GET") {
    if (request.headers.get("content-type")?.split(";")[0] !== "application/json") {
      return error("Send application/json", 415);
    }
    const reader = request.body?.getReader();
    body = new Uint8Array(262_144);
    let offset = 0;
    try {
      while (reader) {
        const chunk = await reader.read();
        if (chunk.done) break;
        if (offset + chunk.value.length > body.length) {
          await reader.cancel();
          return error("Request is too large", 413);
        }
        body.set(chunk.value, offset);
        offset += chunk.value.length;
      }
    } catch {
      return error("Could not read the request", 400);
    }
    body = body.slice(0, offset);
    headers.set("Content-Type", "application/json");
  }

  const query = method === "GET" && path === "content" ? request.nextUrl.search : "";
  try {
    const upstream = await backend(`/${path}${listRoutes.has(path) ? "/" : ""}${query}`, {
      method, headers, body,
    });
    if (path === "users/token" && upstream.ok) {
      const session = await upstream.json();
      const response = NextResponse.json({ ok: true }, { headers: apiHeaders });
      response.cookies.set(SESSION_COOKIE, session.access_token, {
        ...cookieOptions, maxAge: session.expires_in,
      });
      return response;
    }
    const responseHeaders = new Headers({ ...apiHeaders, "Content-Type": "application/json" });
    const retryAfter = upstream.headers.get("retry-after");
    if (retryAfter) responseHeaders.set("Retry-After", retryAfter);
    return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return error("The API is temporarily unavailable. Try again shortly.", 503);
  }
}

export { api as GET, api as POST, api as PATCH, api as PUT };
