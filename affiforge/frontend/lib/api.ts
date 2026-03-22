const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type DashboardPayload = {
  summary: {
    posts_count: number;
    revenue: number;
    earnings_count: number;
    epc: number;
  };
  profit_share: {
    enabled: boolean;
    total_revenue: number;
    platform_share: number;
    user_share: number;
    ratio: number;
  };
  programs: Array<{
    network: string;
    revenue: number;
    events: number;
  }>;
  posts: Array<{
    id: string;
    title: string;
    status: string;
    keyword: string;
    revenue: number;
  }>;
  attribution: Array<{
    utm_source: string;
    orders: number;
    revenue: number;
  }>;
};

const fallbackDashboardData: DashboardPayload = {
  summary: {
    posts_count: 4,
    revenue: 182.4,
    earnings_count: 9,
    epc: 45.6,
  },
  profit_share: {
    enabled: true,
    total_revenue: 182.4,
    platform_share: 21.89,
    user_share: 160.51,
    ratio: 0.12,
  },
  programs: [
    { network: "amazon", revenue: 121.8, events: 6 },
    { network: "impact", revenue: 42.6, events: 2 },
    { network: "clickbank", revenue: 18.0, events: 1 },
  ],
  posts: [
    {
      id: "post-1",
      title: "Best Espresso Machines Under $500",
      status: "published",
      keyword: "espresso machine under 500",
      revenue: 74.2,
    },
    {
      id: "post-2",
      title: "Gaggia Classic Pro vs Breville Barista Express",
      status: "published",
      keyword: "gaggia vs breville",
      revenue: 53.6,
    },
    {
      id: "post-3",
      title: "How to Clean an Espresso Machine",
      status: "draft",
      keyword: "clean espresso machine",
      revenue: 32.8,
    },
    {
      id: "post-4",
      title: "Best Burr Grinders for Beginners",
      status: "published",
      keyword: "best burr grinder beginner",
      revenue: 21.8,
    },
  ],
  attribution: [
    { utm_source: "cluster_espresso_post_1", orders: 4, revenue: 68.4 },
    { utm_source: "cluster_espresso_post_2", orders: 3, revenue: 57.0 },
    { utm_source: "cluster_grinder_post_1", orders: 2, revenue: 31.2 },
    { utm_source: "cluster_cleaning_post_1", orders: 1, revenue: 25.8 },
  ],
};

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/healthz`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to fetch API health");
  }
  return response.json() as Promise<{ status: string }>;
}

export async function getDashboardData(): Promise<DashboardPayload> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/earnings/dashboard`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return fallbackDashboardData;
    }

    const payload = (await response.json()) as Partial<DashboardPayload>;
    return {
      ...fallbackDashboardData,
      ...payload,
      summary: {
        ...fallbackDashboardData.summary,
        ...payload.summary,
      },
      profit_share: {
        ...fallbackDashboardData.profit_share,
        ...payload.profit_share,
      },
      programs: payload.programs ?? fallbackDashboardData.programs,
      posts: payload.posts ?? fallbackDashboardData.posts,
      attribution: payload.attribution ?? fallbackDashboardData.attribution,
    };
  } catch {
    return fallbackDashboardData;
  }
}
