import { getDashboardData } from "../../lib/api";
import { cookies } from "next/headers";

function formatMoney(value: number): string {
  return `$${value.toFixed(2)}`;
}

export default async function DashboardPage() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("access_token")?.value;
  const data = await getDashboardData(accessToken);
  const nextAction =
    data.summary.posts_count < 3
      ? "Create 2 more posts this week to improve visibility."
      : "Update your top performing post with a fresh product comparison table.";
  const topPrograms = data.programs.slice(0, 3);
  const recentPosts = data.posts.slice(0, 3);

  return (
    <main className="dashboard-page">
      <section className="dashboard-head">
        <p className="eyebrow">Dashboard</p>
        <h1>Your Affiliate Snapshot</h1>
        <p>See what happened, then take the next best action.</p>
      </section>

      <section className="panel action-panel">
        <div className="panel-head">
          <h2>Next Best Action</h2>
          <p>{nextAction}</p>
        </div>
      </section>

      <section className="stats-grid">
        <article className="stat-card">
          <h2>Total Revenue</h2>
          <strong>{formatMoney(data.summary.revenue)}</strong>
        </article>
        <article className="stat-card">
          <h2>Posts Created</h2>
          <strong>{data.summary.posts_count}</strong>
        </article>
        <article className="stat-card">
          <h2>Sales</h2>
          <strong>{data.summary.earnings_count}</strong>
        </article>
        <article className="stat-card">
          <h2>Avg Revenue per Post</h2>
          <strong>{formatMoney(data.summary.epc)}</strong>
        </article>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Top Revenue Channels</h2>
          <p>Your 3 strongest affiliate programs right now.</p>
        </div>
        <ul className="simple-list">
          {topPrograms.map((program) => (
            <li key={program.network} className="simple-item">
              <div>
                <h3>{program.network}</h3>
                <p>{program.events} sales</p>
              </div>
              <strong>{formatMoney(program.revenue)}</strong>
            </li>
          ))}
        </ul>

        <details className="details-block">
          <summary>Show detailed channel table</summary>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Network</th>
                  <th>Events</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {data.programs.map((program) => (
                  <tr key={program.network}>
                    <td>{program.network}</td>
                    <td>{program.events}</td>
                    <td>{formatMoney(program.revenue)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td>Total</td>
                  <td>{data.summary.earnings_count}</td>
                  <td>{formatMoney(data.summary.revenue)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </details>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Recent Posts</h2>
          <p>Focus on improving these first.</p>
        </div>
        <ul className="post-list">
          {recentPosts.map((post) => (
            <li key={post.id} className="post-item">
              <div>
                <h3>{post.title}</h3>
                <p>
                  Status: <strong>{post.status}</strong>
                </p>
              </div>
              <div className="post-money">{formatMoney(post.revenue)}</div>
            </li>
          ))}
        </ul>

        <details className="details-block">
          <summary>Show all posts and keywords</summary>
          <ul className="post-list post-list-detailed">
            {data.posts.map((post) => (
              <li key={post.id} className="post-item">
                <div>
                  <h3>{post.title}</h3>
                  <p>
                    Status: <strong>{post.status}</strong> · Keyword: {post.keyword}
                  </p>
                </div>
                <div className="post-money">{formatMoney(post.revenue)}</div>
              </li>
            ))}
          </ul>
        </details>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Profit Share</h2>
          <p>How this month&apos;s revenue is split.</p>
        </div>
        <div className="split-inline">
          <span>
            Platform ({(data.profit_share.ratio * 100).toFixed(0)}%): {formatMoney(data.profit_share.platform_share)}
          </span>
          <span>User: {formatMoney(data.profit_share.user_share)}</span>
        </div>

        <details className="details-block">
          <summary>Show attribution details</summary>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>UTM Source</th>
                  <th>Orders</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {data.attribution.map((row) => (
                  <tr key={row.utm_source}>
                    <td>{row.utm_source}</td>
                    <td>{row.orders}</td>
                    <td>{formatMoney(row.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>
    </main>
  );
}
