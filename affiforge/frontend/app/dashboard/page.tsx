import { getDashboardData } from "../../lib/api";

function formatMoney(value: number): string {
  return `$${value.toFixed(2)}`;
}

export default async function DashboardPage() {
  const data = await getDashboardData();

  return (
    <main className="dashboard-page">
      <section className="dashboard-head">
        <p className="eyebrow">MVP Dashboard</p>
        <h1>Revenue, Posts, and Attribution</h1>
        <p>A compact proof-of-value view for affiliate operators and early testers.</p>
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

      <section className="panel">
        <div className="panel-head">
          <h2>Revenue Table</h2>
          <p>Channel-level earnings and event counts</p>
        </div>
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
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Post List</h2>
          <p>Latest generated and published posts</p>
        </div>
        <ul className="post-list">
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
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Attribution View</h2>
          <p>UTM performance and profit-share split</p>
        </div>
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
        <div className="split-inline">
          <span>
            Platform ({(data.profit_share.ratio * 100).toFixed(0)}%): {formatMoney(data.profit_share.platform_share)}
          </span>
          <span>User: {formatMoney(data.profit_share.user_share)}</span>
        </div>
      </section>
    </main>
  );
}
