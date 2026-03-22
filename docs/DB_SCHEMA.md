# AffiForge Database Schema (v1.2)

## Monetization Tiers (Live as of March 22, 2026)

| Tier | Price | Features | Revenue Share |
|------|-------|----------|----------------|
| **Starter** | $19/mo | 5 sites, 50 posts/month, basic analytics | — |
| **Pro** | $49/mo | 20 sites, 500 posts/month, cluster generator, A/B testing | — |
| **Elite** | $99/mo | Unlimited sites, unlimited posts, auto-optimization, priority support | **12% revenue share** |

### Refund Policy
- If account earns $0 in first 30 days: full refund
- Prorated refunds after 30 days (if churning due to service issues)

### Payment Integration
- **Processor**: Stripe (PCI-DSS compliant)
- **Dashboard**: Custom earnings CSV parsing from Amazon reports
- **Billing Cycle**: Monthly, auto-renewal (daily webhook reconciliation)
- **Timezone**: UTC (all timestamps stored as UTC, converted in dashboard per user timezone)

---

## Core Tables

### `users`
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  tier VARCHAR(50) DEFAULT 'starter', -- starter | pro | elite
  stripe_customer_id VARCHAR(255) UNIQUE,
  stripe_subscription_id VARCHAR(255),
  subscription_status VARCHAR(50), -- active | past_due | canceled | trialing
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  email_verified_at TIMESTAMP,
  last_login_at TIMESTAMP,
  timezone VARCHAR(50) DEFAULT 'UTC',
  api_key_hash VARCHAR(255), -- hashed for security
  INDEX idx_email (email),
  INDEX idx_stripe_customer_id (stripe_customer_id)
);

-- Revenue tracking for Elite tier
CREATE TABLE user_revenue_share (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  billing_period_start DATE,
  billing_period_end DATE,
  total_revenue NUMERIC(10, 2), -- sum of all earning_events
  revenue_share_amount NUMERIC(10, 2), -- total_revenue * 0.12
  payout_status VARCHAR(50) DEFAULT 'pending', -- pending | processed | failed
  payout_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, billing_period_start),
  INDEX idx_user_id (user_id),
  INDEX idx_payout_status (payout_status)
);
```

### `sites`
```sql
CREATE TABLE sites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  domain VARCHAR(255) UNIQUE NOT NULL,
  niche VARCHAR(255), -- e.g., "espresso_machines", "fitness_supplements"
  wordpress_url VARCHAR(255),
  wordpress_username_encrypted BYTEA, -- AES-256 encrypted
  wordpress_password_encrypted BYTEA,
  amazon_associate_id VARCHAR(255),
  stripe_key_encrypted BYTEA,
  monthly_traffic BIGINT DEFAULT 0,
  monthly_revenue NUMERIC(10, 2) DEFAULT 0.0,
  status VARCHAR(50) DEFAULT 'active', -- active | paused | deleted
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_user_id (user_id),
  INDEX idx_domain (domain)
);
```

### `scans` (Reddit + Serper low-competition validator)
```sql
CREATE TABLE scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  reddit_post_id VARCHAR(255),
  reddit_title VARCHAR(500),
  reddit_subreddit VARCHAR(100),
  reddit_score BIGINT,
  reddit_url VARCHAR(500),
  pain_point TEXT, -- extracted from Reddit thread
  search_volume BIGINT, -- from Serper
  competition_level VARCHAR(50), -- low | medium | high
  opportunity_score NUMERIC(5, 2), -- 0-10 scale
  serper_data JSONB, -- raw SERP results
  status VARCHAR(50) DEFAULT 'pending', -- pending | approved | rejected | published
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days',
  INDEX idx_site_id (site_id),
  INDEX idx_status (status),
  INDEX idx_opportunity_score (opportunity_score DESC)
);
```

### `clusters` (NEW: Pillar + supporting posts)
```sql
CREATE TABLE clusters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id VARCHAR(255) UNIQUE NOT NULL, -- reddit_{reddit_post_id}_{timestamp}
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  scan_id UUID REFERENCES scans(id) ON DELETE SET NULL,
  niche VARCHAR(255),
  pillar_post_id UUID,
  pillar_slug VARCHAR(255),
  pillar_title VARCHAR(500),
  pillar_word_count BIGINT,
  pillar_projected_revenue NUMERIC(10, 2),
  supporting_post_count INT DEFAULT 0, -- 0-8
  total_word_count BIGINT,
  estimated_monthly_traffic BIGINT,
  estimated_monthly_revenue NUMERIC(10, 2),
  status VARCHAR(50) DEFAULT 'draft', -- draft | generated | published | archived
  created_at TIMESTAMP DEFAULT NOW(),
  published_at TIMESTAMP,
  INDEX idx_site_id (site_id),
  INDEX idx_status (status),
  INDEX idx_cluster_id (cluster_id)
);
```

### `content_items` (Individual blog posts)
```sql
CREATE TABLE content_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id UUID REFERENCES clusters(id) ON DELETE CASCADE,
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  title VARCHAR(500) NOT NULL,
  slug VARCHAR(255) UNIQUE NOT NULL,
  content TEXT,
  word_count BIGINT,
  primary_keyword VARCHAR(255),
  keywords_json JSONB, -- array of LSI keywords
  search_volume BIGINT,
  competition VARCHAR(50),
  meta_description VARCHAR(160),
  internal_links JSONB, -- array of {anchor_text, target_slug}
  amazon_products JSONB, -- array of {asin, anchor_text, utm_source}
  schema_markup JSON, -- FAQPage, BreadcrumbList, ProductSchema
  wordpress_post_id BIGINT,
  wordpress_url VARCHAR(500),
  status VARCHAR(50) DEFAULT 'draft', -- draft | ready_to_publish | published | archived
  projected_monthly_revenue NUMERIC(10, 2),
  actual_monthly_revenue NUMERIC(10, 2) DEFAULT 0.0,
  created_at TIMESTAMP DEFAULT NOW(),
  published_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_site_id (site_id),
  INDEX idx_cluster_id (cluster_id),
  INDEX idx_slug (slug),
  INDEX idx_status (status)
);

-- Audit trail for content changes
CREATE TABLE content_revisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  revision_number INT,
  title VARCHAR(500),
  content TEXT,
  change_summary VARCHAR(500),
  changed_by VARCHAR(255), -- user email
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_content_id (content_id),
  INDEX idx_created_at (created_at)
);
```

### `earning_events` (Revenue attribution with sub-tag tracking)
```sql
CREATE TABLE earning_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  content_id UUID REFERENCES content_items(id),
  cluster_id UUID REFERENCES clusters(id),
  order_id VARCHAR(255), -- Amazon order ID
  asin VARCHAR(255),
  product_title VARCHAR(500),
  earning_amount NUMERIC(10, 2),
  commission_rate NUMERIC(5, 2), -- 3% - 10%
  utm_source VARCHAR(255), -- cluster_{cluster_id}_post_{post_number}
  utm_medium VARCHAR(255) DEFAULT 'affiliate_link',
  utm_campaign VARCHAR(255),
  referral_date TIMESTAMP,
  order_date TIMESTAMP,
  order_amount NUMERIC(10, 2),
  status VARCHAR(50) DEFAULT 'confirmed', -- confirmed | pending | canceled
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_site_id (site_id),
  INDEX idx_content_id (content_id),
  INDEX idx_cluster_id (cluster_id),
  INDEX idx_utm_source (utm_source),
  INDEX idx_order_date (order_date),
  INDEX idx_status (status)
);

-- Monthly revenue summary (for dashboard caching)
CREATE TABLE monthly_revenue_summary (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  month_year DATE, -- first day of month
  total_earnings NUMERIC(10, 2),
  total_orders BIGINT,
  avg_revenue_per_post NUMERIC(10, 2),
  top_product_asin VARCHAR(255),
  top_product_earnings NUMERIC(10, 2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(site_id, month_year),
  INDEX idx_site_id (site_id),
  INDEX idx_month_year (month_year)
);
```

### `llm_tasks` (Cost tracking & audit)
```sql
CREATE TABLE llm_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id VARCHAR(255) UNIQUE,
  user_id UUID NOT NULL REFERENCES users(id),
  site_id UUID REFERENCES sites(id),
  cluster_id UUID REFERENCES clusters(id),
  task_type VARCHAR(100), -- generate_cluster | optimize_post | refresh_content
  model VARCHAR(100), -- gpt-4o | claude-3-5-sonnet
  input_tokens BIGINT,
  output_tokens BIGINT,
  total_tokens BIGINT,
  cost_usd NUMERIC(8, 6),
  status VARCHAR(50), -- pending | success | failed | cost_exceeded
  error_message TEXT,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  duration_seconds BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_user_id (user_id),
  INDEX idx_task_id (task_id),
  INDEX idx_status (status),
  INDEX idx_created_at (created_at)
);
```

### `api_keys` (For programmatic access)
```sql
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255),
  key_hash VARCHAR(255) UNIQUE NOT NULL, -- SHA-256 hash (key never stored plain)
  last_used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  revoked_at TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_key_hash (key_hash)
);
```

---

## Key Relationships

```
users
├─ user_revenue_share (1 user → N revenue periods)
├─ sites (1 user → N sites)
│  ├─ scans (1 site → N Reddit scans)
│  ├─ clusters (1 site → N content clusters)
│  │  ├─ content_items (1 cluster → 1 pillar + 8 supporting posts)
│  │  │  └─ content_revisions (1 post → N revisions)
│  │  └─ earning_events (1 cluster → N earning events)
│  └─ monthly_revenue_summary (1 site → N months)
├─ llm_tasks (1 user → N tasks)
└─ api_keys (1 user → N keys)
```

---

## Indexes & Performance

| Table | Critical Indexes | Average Query | Purpose |
|-------|------------------|----------------|---------|
| `users` | email, stripe_customer_id | Auth lookup | <10ms |
| `sites` | user_id, domain | Get user sites | <5ms |
| `scans` | site_id, status, opportunity_score | Rank opportunities | <100ms |
| `content_items` | site_id, status, published_at | Dashboard listing | <50ms |
| `earning_events` | site_id, cluster_id, order_date | Revenue dashboard | <200ms (aggregated) |
| `llm_tasks` | user_id, status, created_at | Audit trail | <50ms |

### Materialized Views (for fast dashboards)

```sql
-- User revenue snapshot (refreshed nightly)
CREATE MATERIALIZED VIEW user_dashboard AS
  SELECT 
    u.id, u.email, u.tier, u.stripe_subscription_id,
    COUNT(DISTINCT s.id) as site_count,
    COUNT(DISTINCT ci.id) as post_count,
    SUM(ee.earning_amount) as total_earnings_all_time,
    SUM(CASE WHEN ee.order_date >= NOW() - INTERVAL '30 days' 
           THEN ee.earning_amount ELSE 0 END) as monthly_earning_last_30d,
    SUM(CASE WHEN ee.order_date >= NOW() - INTERVAL '30 days' 
           THEN 1 ELSE 0 END) as order_count_last_30d
  FROM users u
  LEFT JOIN sites s ON u.id = s.user_id
  LEFT JOIN content_items ci ON s.id = ci.site_id
  LEFT JOIN earning_events ee ON s.id = ee.site_id
  GROUP BY u.id;

CREATE INDEX idx_user_dashboard_user_id ON user_dashboard(id);
REFRESH MATERIALIZED VIEW CONCURRENTLY user_dashboard;
```

---

## Security Measures

1. **Encryption at Rest**
   - WordPress credentials (XML-RPC): AES-256
   - API keys: SHA-256 hash (never stored plain)
   - User passwords: bcrypt (min. cost 12)

2. **Row-Level Security (RLS)**
   - Users can only access their own sites, content, and earnings
   - Policy: `WHERE user_id = current_user_id`

3. **Audit Trail**
   - All content changes tracked in `content_revisions`
   - LLM costs logged in `llm_tasks`
   - Stripe webhook events logged separately

---

## Migration History

| Version | Date | Migration | Purpose |
|---------|------|-----------|---------|
| v1 | 2026-03-01 | `20260301_000001_init_schema.py` | Initial schema (users, sites, content) |
| v1.1 | 2026-03-15 | `20260315_000002_add_clusters.py` | Add cluster tables + revenue-share tracking |
| v1.2 | 2026-03-22 | `20260322_000003_add_monetization.py` | Add user_revenue_share, subscription tracking |

---

## Cost & Growth Estimates

### Storage
- 1,000 users × 10 sites × 100 posts = 1M content rows ≈ 500 GB (with revisions)
- 1M earning events ≈ 100 GB
- **Total**: ~1 TB for 1,000 users (acceptable for PostgreSQL)

### Query Optimization
- **Monthly earnings dashboard**: Materialized view (refreshed nightly)
- **Real-time updates**: Direct queries on earning_events (indexed by order_date)
- **Cache layer**: Redis for user tier/subscription (TTL: 1 hour)

---

## Notes

- All timestamps are stored in **UTC** (convert to user.timezone in application layer)
- Revenue-share payouts calculated monthly (Elite tier only, automatic via Stripe Connect)
- Arkansas Stripe account used for US affiliate compliance (Schedule C tax reporting ready)
