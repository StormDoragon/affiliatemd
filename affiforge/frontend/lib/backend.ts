export const SESSION_COOKIE = "affiforge_session";

export function backend(path: string, init?: RequestInit) {
  const origin = process.env.INTERNAL_API_URL ?? "http://127.0.0.1:8000";
  return fetch(new URL(path, origin), {
    ...init,
    cache: "no-store",
    redirect: "error",
    signal: AbortSignal.timeout(75_000),
  });
}
