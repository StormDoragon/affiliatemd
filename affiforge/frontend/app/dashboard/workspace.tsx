"use client";

import Link from "next/link";
import { FormEvent, ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, BillingStatus, ClusterItem, DashboardPayload, Post, Site, Topic } from "../../lib/api";

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const text = (form: FormData, key: string) => String(form.get(key) ?? "").trim();

function message(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    window.location.assign("/sign-in");
  }
  return error instanceof Error ? error.message : "The request failed.";
}

function Action({ children, run, label, disabled = false, clear = false }: {
  children?: ReactNode;
  run: (data: FormData) => Promise<string | void>;
  label: string;
  disabled?: boolean;
  clear?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const pending = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    pending.current = true;
    setError("");
    setResult("");
    setBusy(true);
    try {
      const outcome = await run(data);
      setResult(typeof outcome === "string" ? outcome : "");
      if (clear) form.reset();
    } catch (failure) {
      setError(message(failure));
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return <form onSubmit={submit} className="action-form">
    <fieldset className="fields" disabled={disabled || busy}>
      {children}
      <div><button className="button button-primary">{busy ? "Working…" : label}</button></div>
    </fieldset>
    {error && <p className="error" role="alert">{error}</p>}
    {result && <p className="success" role="status">{result}</p>}
  </form>;
}

function ConnectedSites({ sites, reload }: { sites: Site[]; reload: () => Promise<void> }) {
  const [selected, setSelected] = useState<Site | null>(null);
  return (
    <section id="sites" className="panel">
      <h2>WordPress sites</h2>
      <p>Use a WordPress application password for an account with publishing permission.</p>
      {!!sites.length && <ul className="site-list">{sites.map((site) =>
        <li key={site.id}><span>{site.wp_url}</span>
          <button className="link-button" onClick={() => setSelected(site)}>Update credentials</button></li>
      )}</ul>}
      <Action key={selected?.id ?? "new"} label={selected ? "Update connection" : "Connect site"} clear
        run={async (form) => {
          const payload = { wp_username: text(form, "username"), wp_app_password: text(form, "password"),
            amazon_tag: text(form, "tag") };
          if (selected) {
            await api(`sites/${selected.id}`, payload, "PUT");
          } else {
            await api("sites", { ...payload, wp_url: text(form, "url") });
          }
          await reload();
          return selected ? "Connection updated." : "Site connected.";
        }}>
        {selected
          ? <div className="row"><strong>{selected.wp_url}</strong><button type="button" className="link-button"
            onClick={() => setSelected(null)}>Connect another site</button></div>
          : <label>WordPress URL<input name="url" type="url" placeholder="https://example.com" maxLength={255} required /></label>}
        <div className="form-grid">
          <label>WordPress username<input name="username" defaultValue={selected?.wp_username} maxLength={255} required /></label>
          <label>Application password<input type="password" name="password" autoComplete="off" maxLength={255} required /></label>
          <label>Amazon Associates tag (optional)<input name="tag" defaultValue={selected?.amazon_tag} maxLength={64}
            pattern="[-A-Za-z0-9_]*" placeholder="yourtag-20" /></label>
        </div>
      </Action>
    </section>
  );
}

function Research({ pick }: { pick: (keyword: string, question: string, thread: string) => void }) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [cluster, setCluster] = useState<ClusterItem[]>([]);
  return (
    <section id="research" className="panel">
      <h2>Research ideas</h2>
      <div className="form-grid">
        <Action label="Search Reddit" run={async (form) => {
          setTopics([]);
          const result = await api<{ topics: Topic[] }>("generator/reddit-scan", {
            query: text(form, "query"), subreddit: text(form, "subreddit") || "all", limit: 8,
          });
          setTopics(result.topics);
          if (!result.topics.length) return "No matching discussions.";
        }}>
          <label>Search query<input name="query" minLength={2} maxLength={255} required /></label>
          <label>Subreddit<input name="subreddit" placeholder="all" maxLength={21} /></label>
        </Action>
        <Action label="Build a content plan" run={async (form) => {
          setCluster([]);
          const result = await api<{ items: ClusterItem[] }>("generator/cluster", {
            seed_keyword: text(form, "keyword"), audience: text(form, "audience"), cluster_size: 5,
          });
          setCluster(result.items);
        }}>
          <label>Seed keyword<input name="keyword" minLength={2} maxLength={255} required /></label>
          <label>Target audience<input name="audience" minLength={2} maxLength={255} required /></label>
        </Action>
      </div>
      {!!topics.length && <div className="results"><h3>Reddit discussions</h3><ul className="post-list">
        {topics.map((topic) => <li key={topic.thread_id} className="post-item">
          {topic.url ? <a href={topic.url} target="_blank" rel="noreferrer">{topic.title}</a> : <span>{topic.title}</span>}
          <button className="button button-secondary" onClick={() => pick(topic.title, topic.pain_point, topic.thread_id)}>Use in draft</button>
        </li>)}
      </ul></div>}
      {!!cluster.length && <div className="results"><h3>Content plan</h3><ul className="post-list">
        {cluster.map((item, index) => <li key={index} className="post-item">
          <div><h3>{item.title}</h3><p>{item.keyword} · {item.search_intent}</p><p>{item.brief}</p></div>
          <button className="button button-secondary" onClick={() => pick(item.keyword, item.brief, "")}>Use in draft</button>
        </li>)}
      </ul></div>}
    </section>
  );
}

function SiteSelect({ sites, current, onChange }: { sites: Site[]; current?: number | null; onChange?: (id: number) => void }) {
  return <label>WordPress site<select name="site" defaultValue={current ?? ""} onChange={(event) => onChange?.(Number(event.target.value))} required>
    <option value="">Select a site</option>
    {sites.map((site) => <option key={site.id} value={site.id}>{site.wp_url}</option>)}
  </select></label>;
}

function DraftEditor({ post, sites, reload }: { post: Post; sites: Site[]; reload: () => Promise<void> }) {
  const [title, setTitle] = useState(post.title);
  const [body, setBody] = useState(post.body);
  const [savedTitle, setSavedTitle] = useState(post.title);
  const [savedBody, setSavedBody] = useState(post.body);
  const [selectedSite, setSelectedSite] = useState(post.site_id ?? 0);
  const [published, setPublished] = useState(post.status === "published");
  const [publishedUrl, setPublishedUrl] = useState(post.published_url);
  const [confirm, setConfirm] = useState(false);
  const site = sites.find((candidate) => candidate.id === selectedSite);

  if (published) return <div className="results">
    <h3>{post.title}</h3><p>Status recorded as published.</p>
    {publishedUrl && <a href={publishedUrl} target="_blank" rel="noreferrer">View on WordPress</a>}
  </div>;

  return <div className="results editor">
    <Action label="Save draft" run={async () => {
      const saved = await api<Post>(`content/${post.id}`, { title, body }, "PATCH");
      setTitle(saved.title); setBody(saved.body); setSavedTitle(saved.title); setSavedBody(saved.body);
      await reload();
      return "Draft saved.";
    }}>
      <label>Draft title<input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} required /></label>
      <label>Draft body (Markdown)<textarea value={body} onChange={(event) => setBody(event.target.value)}
        rows={12} maxLength={40_000} required /></label>
    </Action>
    {site?.amazon_tag && <Action label="Insert Amazon link" clear run={async (form) => {
      const asin = text(form, "asin").toUpperCase();
      const label = text(form, "link_label").replaceAll("[", "").replaceAll("]", "");
      const disclosure = "As an Amazon Associate I earn from qualifying purchases.";
      const link = `[${label}](https://www.amazon.com/dp/${asin}?tag=${encodeURIComponent(site.amazon_tag)})`;
      const nextBody = `${body.includes(disclosure) ? "" : disclosure + "\n\n"}${body}\n\n${link}`;
      if (nextBody.length > 40_000) throw new Error("Shorten the draft before inserting this link.");
      setBody(nextBody);
      return "Link added. Save the draft before publishing.";
    }}>
      <div className="form-grid">
        <label>Amazon product ASIN<input name="asin" pattern="[A-Za-z0-9]{10}" minLength={10} maxLength={10} required /></label>
        <label>Link label<input name="link_label" maxLength={100} required /></label>
      </div>
    </Action>}
    <Action label="Publish to WordPress" disabled={title !== savedTitle || body !== savedBody || !sites.length}
      run={async (form) => {
        const result = await api<{ status: string; url: string | null }>(`content/${post.id}/publish`, {
          site_id: Number(form.get("site")),
        });
        if (result.status === "demo") {
          setConfirm(false);
          return "Demo complete. No WordPress post was created.";
        }
        setPublished(true);
        setPublishedUrl(result.url);
        await reload();
      }}>
      <SiteSelect sites={sites} current={selectedSite} onChange={(id) => { setSelectedSite(id); setConfirm(false); }} />
      <label className="checkbox"><input type="checkbox" checked={confirm} onChange={(event) => setConfirm(event.target.checked)} required />
        I reviewed the draft and want to make it public.</label>
      {(title !== savedTitle || body !== savedBody) && <span className="muted">Save your changes before publishing.</span>}
    </Action>
  </div>;
}

function Drafts({ sites, dashboard, reload, idea }: {
  sites: Site[]; dashboard: DashboardPayload | null; reload: () => Promise<void>;
  idea: { keyword: string; question: string; thread: string; version: number };
}) {
  const [openPost, setOpenPost] = useState<Post | null>(null);
  const [editorVersion, setEditorVersion] = useState(0);
  const [postError, setPostError] = useState("");
  const [loadingPost, setLoadingPost] = useState(false);
  const [page, setPage] = useState(0);
  const [older, setOlder] = useState<DashboardPayload["posts"]>([]);
  const total = dashboard?.summary.posts_count ?? 0;

  async function open(id: number) {
    const post = await api<Post>(`content/${id}`);
    setOpenPost(post);
    setEditorVersion((value) => value + 1);
    document.getElementById("draft-editor")?.scrollIntoView({ block: "start" });
  }

  async function changePage(next: number) {
    setPostError("");
    setLoadingPost(true);
    try {
      if (next) {
        const posts = await api<DashboardPayload["posts"]>(`content?offset=${next * 25}&limit=25`);
        setOlder(posts);
      }
      setPage(next);
    } catch (failure) {
      setPostError(message(failure));
    } finally {
      setLoadingPost(false);
    }
  }

  return <section id="drafts" className="panel">
    <h2>Draft and publish</h2>
    <div className="form-grid">
      <Action key={idea.version} label="Generate AI draft" disabled={!sites.length} run={async (form) => {
        const result = await api<{ post_id: number }>("generator/generate", {
          site_id: Number(form.get("site")), primary_keyword: text(form, "keyword"),
          pain_point: text(form, "question"), reddit_thread_id: idea.thread,
        });
        await reload();
        await open(result.post_id);
        return "Draft created.";
      }}>
        <SiteSelect sites={sites} />
        {!sites.length && <a href="#sites">Connect a site before generating an AI draft.</a>}
        <label>Primary keyword<input name="keyword" defaultValue={idea.keyword} minLength={2} maxLength={255} required /></label>
        <label>Audience question<textarea name="question" defaultValue={idea.question} minLength={2} maxLength={1000} required /></label>
      </Action>
      <Action label="Create manual draft" clear run={async (form) => {
        const title = text(form, "title");
        const prefix = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80).replace(/-$/, "");
        const result = await api<Post>("content", {
          title, slug: `${prefix || "post"}-${crypto.randomUUID().slice(0, 12)}`, body: text(form, "body"),
        });
        await reload();
        await open(result.id);
      }}>
        <label>Title<input name="title" maxLength={255} required /></label>
        <label>Body (Markdown)<textarea name="body" maxLength={40_000} required /></label>
      </Action>
    </div>
    <div id="draft-editor">
      {openPost && <DraftEditor key={editorVersion} post={openPost} sites={sites} reload={reload} />}
    </div>
    {!!total && <div className="results"><h3>Your posts</h3><ul className="post-list">
      {(page ? older : dashboard?.posts ?? []).map((post) =>
        <li key={post.id} className="post-item"><div><h3>{post.title}</h3>
          <p>Post ID {post.id} · {post.status}{typeof post.revenue === "number" ? ` · ${money.format(post.revenue)} reported` : ""}</p></div>
          <button className="button button-secondary" disabled={loadingPost} onClick={async () => {
            setLoadingPost(true); setPostError("");
            try { await open(post.id); } catch (failure) { setPostError(message(failure)); }
            finally { setLoadingPost(false); }
          }}>{post.status === "published" ? "View post" : "Review draft"}</button>
        </li>
      )}
    </ul>
    {total > 25 && <div className="row pagination">
      <button className="button button-secondary" disabled={!page || loadingPost} onClick={() => changePage(page - 1)}>Newer posts</button>
      <button className="button button-secondary" disabled={(page + 1) * 25 >= total || loadingPost} onClick={() => changePage(page + 1)}>Older posts</button>
    </div>}</div>}
    {postError && <p className="error" role="alert">{postError}</p>}
  </section>;
}

function Earnings({ dashboard, reload }: { dashboard: DashboardPayload; reload: () => Promise<void> }) {
  const draftKey = useRef("");
  return <section id="earnings" className="panel">
    <h2>Reported earnings</h2>
    <p>Record commissions in USD and link them to the post that earned them.</p>
    <Action label="Record commission" clear disabled={!dashboard.posts.length} run={async (form) => {
      draftKey.current ||= crypto.randomUUID();
      await api("earnings", { network: text(form, "network"), amount: text(form, "amount"),
        content_item_id: Number(form.get("post")), entry_key: draftKey.current });
      draftKey.current = "";
      await reload();
      return "Commission recorded.";
    }}>
      <div className="form-grid">
        <label>Post ID<input name="post" type="number" min={1} list="earning-posts" required /></label>
        <datalist id="earning-posts">{dashboard.posts.map((post) => <option key={post.id} value={post.id}>{post.title}</option>)}</datalist>
        <label>Affiliate network<input name="network" maxLength={120} required /></label>
        <label>Commission (USD)<input name="amount" type="number" min="0.01" max="99999999.99" step="0.01" required /></label>
      </div>
    </Action>
    {dashboard.programs.length ? <div className="results table-wrap"><table className="data-table">
      <thead><tr><th>Network</th><th>Entries</th><th>Commission</th></tr></thead>
      <tbody>{dashboard.programs.map((program) => <tr key={program.network}>
        <th scope="row">{program.network}</th><td>{program.events}</td><td>{money.format(program.revenue)}</td>
      </tr>)}</tbody>
    </table></div> : <p className="muted">No commissions recorded yet.</p>}
    <Action label={dashboard.profit_share.enabled ? "Hide projection" : "Show projection"} run={async () => {
      await api("billing/profitshare/toggle", { enabled: !dashboard.profit_share.enabled });
      await reload();
    }}>
      <h3>Revenue-share projection</h3>
      {dashboard.profit_share.enabled &&
        <p>Estimated platform share ({Math.round(dashboard.profit_share.ratio * 100)}%) {money.format(dashboard.profit_share.platform_share)} · Your share {money.format(dashboard.profit_share.user_share)}</p>}
    </Action>
  </section>;
}

function priceLabel(price: BillingStatus["prices"][number]): string {
  const formatter = new Intl.NumberFormat("en-US", { style: "currency", currency: price.currency });
  return formatter.format(price.amount / 10 ** (formatter.resolvedOptions().maximumFractionDigits ?? 2));
}

function Billing() {
  const [data, setData] = useState<BillingStatus | null>(null);
  return <section id="billing" className="panel">
    <h2>Subscriptions</h2>
    <Action label="Check subscription" run={async () => {
      setData(await api<BillingStatus>("billing/status"));
    }} />
    {data && !data.enabled && <p>Subscriptions are unavailable on this installation.</p>}
    {data?.enabled && <>
      {data.subscriptions.length ? <p>Status {data.subscriptions.map((item) => item.status.replaceAll("_", " ")).join(", ")}</p>
        : <p>No subscription found.</p>}
      {data.prices.map((price) => <Action key={price.id} label={`Subscribe to ${price.name}`} run={async () => {
        const result = await api<{ checkout_url: string }>("billing/checkout-session", { price_id: price.id });
        window.location.assign(result.checkout_url);
      }}>
        <p>{priceLabel(price)}{" "}per {price.interval_count > 1 ? `${price.interval_count} ${price.interval}s` : price.interval}</p>
      </Action>)}
      {data.portal_available && <Action label="Manage subscription" run={async () => {
        const result = await api<{ url: string }>("billing/portal", {});
        window.location.assign(result.url);
      }} />}
    </>}
  </section>;
}

export default function Workspace({ name, demo }: { name: string; demo: boolean }) {
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [loadError, setLoadError] = useState("");
  const [idea, setIdea] = useState({ keyword: "", question: "", thread: "", version: 0 });

  const reload = useCallback(async () => {
    setLoadError("");
    try {
      const [overview, connections] = await Promise.all([
        api<DashboardPayload>("earnings/dashboard"), api<Site[]>("sites"),
      ]);
      setDashboard(overview);
      setSites(connections);
    } catch (failure) {
      setLoadError(message(failure));
    }
  }, []);

  useEffect(() => { void reload(); }, [reload]);

  return <main className="dashboard-page">
    <header className="dashboard-head">
      <div className="row"><Link className="eyebrow" href="/">AffiForge</Link>
        <Action label="Sign out" run={async () => {
          await api("users/logout", {});
          window.location.assign("/sign-in");
        }} />
      </div>
      <h1>{name}&rsquo;s workspace</h1>
      <nav className="workspace-nav" aria-label="Workspace">
        <a href="#sites">Sites</a><a href="#research">Research</a><a href="#drafts">Drafts</a>
        <a href="#earnings">Earnings</a><a href="#billing">Subscriptions</a>
      </nav>
    </header>
    {demo && <p className="demo-banner" role="status">Demo mode. Research results are examples, and publishing is simulated.</p>}
    {loadError && <div className="panel" role="alert"><p className="error">{loadError}</p>
      <button className="button button-secondary" onClick={reload}>Retry loading workspace</button></div>}
    {!dashboard && !loadError && <p role="status">Loading your workspace…</p>}
    {dashboard && <>
      <section className="stats-grid" aria-label="Earnings overview">
        <article className="stat-card"><h2>Reported revenue</h2><strong>{money.format(dashboard.summary.revenue)}</strong></article>
        <article className="stat-card"><h2>Posts</h2><strong>{dashboard.summary.posts_count}</strong></article>
        <article className="stat-card"><h2>Commission entries</h2><strong>{dashboard.summary.earnings_count}</strong></article>
        <article className="stat-card"><h2>Revenue per post</h2><strong>{money.format(dashboard.summary.epc)}</strong></article>
      </section>
      <ConnectedSites sites={sites} reload={reload} />
      <Research pick={(keyword, question, thread) => {
        setIdea((previous) => ({ keyword: keyword.slice(0, 255), question: question.slice(0, 1000),
          thread, version: previous.version + 1 }));
        document.getElementById("drafts")?.scrollIntoView();
      }} />
      <Drafts sites={sites} dashboard={dashboard} reload={reload} idea={idea} />
      <Earnings dashboard={dashboard} reload={reload} />
      <Billing />
    </>}
  </main>;
}
