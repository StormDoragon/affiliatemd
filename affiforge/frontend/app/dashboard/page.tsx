type DashboardPayload = {
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
  suggestions: string[];
};

const fallbackData: DashboardPayload = {
  summary: {
    posts_count: 4,
    revenue: 182.4,
    earnings_count: 9,
    epc: 45.6,
  },
  profit_share: {
    enabled: true,
    total_revenue: 182.4,
    platform_share: 54.72,
    user_share: 127.68,
    ratio: 0.3,
  },
  suggestions: [
    "Publish at least 3 comparison posts to diversify affiliate entry points.",
    "Improve product-intent CTAs near comparison tables to lift EPC.",
  ],
};

function formatMoney(value: number): string {
  return `$${value.toFixed(2)}`;
}

export default function DashboardPage() {
  const data = fallbackData;

  return (
    <main className="dashboard-page">
      <section className="dashboard-head">
        <p className="eyebrow">Revenue Share</p>
        <h1>Affiliate Earnings Dashboard</h1>
        <p>Track money, split logic, and optimization actions in one place.</p>
      </section>

      <section className="stats-grid">
        <article className="stat-card">
          <h2>Total Revenue</h2>
          <strong>{formatMoney(data.summary.revenue)}</strong>
        </article>
        <article className="stat-card">
          <h2>Posts</h2>
          <strong>{data.summary.posts_count}</strong>
        </article>
        <article className="stat-card">
          <h2>Earnings Events</h2>
          <strong>{data.summary.earnings_count}</strong>
        </article>
        <article className="stat-card">
          <h2>EPC</h2>
          <strong>{formatMoney(data.summary.epc)}</strong>
        </article>
      </section>

      <section className="split-panel">
        <h2>ProfitShare Breakdown</h2>
        <p>
          Split ratio: {(data.profit_share.ratio * 100).toFixed(0)}% platform /{" "}
          {(100 - data.profit_share.ratio * 100).toFixed(0)}% user
        </p>
        <div className="split-row">
          <span>Platform Share</span>
          <strong>{formatMoney(data.profit_share.platform_share)}</strong>
        </div>
        <div className="split-row">
          <span>User Share</span>
          <strong>{formatMoney(data.profit_share.user_share)}</strong>
        </div>
      </section>

      <section className="suggestions-panel">
        <h2>Optimization Suggestions</h2>
        <ul>
          {data.suggestions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
