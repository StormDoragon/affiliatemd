export type Site = { id: number; wp_url: string; wp_username: string; amazon_tag: string };
export type Post = {
  id: number;
  title: string;
  slug: string;
  body: string;
  status: string;
  site_id: number | null;
  published_url: string | null;
};
export type DashboardPayload = {
  summary: { posts_count: number; revenue: number; earnings_count: number; epc: number };
  profit_share: { enabled: boolean; platform_share: number; user_share: number; ratio: number };
  programs: { network: string; revenue: number; events: number }[];
  posts: (Pick<Post, "id" | "title" | "status" | "published_url"> & { revenue: number; keyword: string | null })[];
  suggestions: string[];
};
export type Topic = { title: string; pain_point: string; thread_id: string; url: string };
export type ClusterItem = { title: string; keyword: string; search_intent: string; brief: string };
export type BillingStatus = {
  enabled: boolean;
  portal_available: boolean;
  prices: { id: string; name: string; amount: number; currency: string; interval: string; interval_count: number }[];
  subscriptions: { id: string; status: string }[];
};

export class ApiError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, body?: object, method = body ? "POST" : "GET"): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    method, cache: "no-store",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = Array.isArray(data?.detail)
      ? data.detail.map((item: { loc: string[]; msg: string }) => `${item.loc.at(-1)}: ${item.msg}`).join(". ")
      : data?.detail;
    throw new ApiError(response.status, message || "Something went wrong. Try again.");
  }
  if (data === null) throw new ApiError(502, "The server returned an invalid response.");
  return data;
}
