# Earnings Attribution & Revenue Tracking (v1.2)

## Overview

AffiForge tracks affiliate earnings with **post-level granularity**, enabling Elite tier users to earn **12% revenue share** on their platform-generated content. Attribution uses `utm_source` tags embedded in Amazon links, capturing which cluster and post drove each click.

---

## Revenue Attribution Model

### Layered Attribution Chain

```
Reddit Opportunity
    ↓
Scan & Manual Approval
    ↓
Cluster Generated (cluster_id = reddit_{post_id}_{timestamp})
    ↓
Pillar Post (utm_source = cluster_{cluster_id}_pillar)
    ↓
8x Supporting Posts (utm_source = cluster_{cluster_id}_post_{1-8})
    ↓
Amazon Link Click (Amazon Associates tracks utm_source)
    ↓
Order Placed (purchase recorded in Amazon reports)
    ↓
Revenue Earned & Attributed Back to Post
```

### UTM Tracking Structure

```
Amazon Affiliate Link Format:
https://www.amazon.com/dp/{ASIN}?tag={amazon_associate_id}&linkCode=as2&camp={campaign_id}&creative={creative_id}&creativeASIN={ASIN}&utm_source=cluster_{cluster_id}_post_{post_num}&utm_medium=affiliate_link&utm_campaign={site_id}_{niche}

Example (Real):
https://www.amazon.com/dp/B0BZF8KVMD?tag=espresso-101-20&linkCode=as2&camp=1789&creative=9325&creativeASIN=B0BZF8KVMD&utm_source=cluster_reddit_abc123_20260322_post_2&utm_medium=affiliate_link&utm_campaign=espresso-puro_machines

Breaking Down:
- cluster_id: reddit_abc123_20260322
- post_number: 2 (from 8 supporting posts)
- utm_source: cluster_reddit_abc123_20260322_post_2
- utm_campaign: {site_id}_{niche}
```

### Attribution Window

- **Click-to-Order**: 24-hour window (Amazon Associates standard)
- **Order-to-Reporting**: 2-7 days (Amazon payment reporting lag)
- **Dashboard Refresh**: Nightly (02:00 UTC via Celery beat)
- **Revenue Recognition**: On order confirmation (conservative approach, no refund prediction)

---

## Revenue Share Calculation (Elite Tier)

### Monthly Payout Flow

```
Step 1: Aggregate All Earning Events
  SELECT SUM(earning_amount) as monthly_total
  FROM earning_events
  WHERE site_id IN (user's sites)
    AND order_date >= DATE_TRUNC('month', NOW()) - INTERVAL '1 month'
    AND order_date < DATE_TRUNC('month', NOW())

Step 2: Calculate Platform Share (12%)
  revenue_share = monthly_total * 0.12

Step 3: Process Payment via Stripe Connect
  - Stripe ACH transfer to user's bank account
  - Deducted from next month's subscription charge
  - OR sent directly if user opts into Stripe Connect payout

Step 4: Log Transaction
  INSERT INTO user_revenue_share (user_id, billing_period, revenue, payout_status)
  VALUES (user_id, billing_period, revenue_share, 'processed')
```

### Example Calculation

```
User: alice@example.com (Elite tier, $99/mo)
Subscription Fee: -$99.00
Period: March 1-31, 2026

Earning Events (March):
- Post 1 (pillar): $47.50
- Post 2: $28.75
- Post 3: $12.30
- Post 4: $9.50
- Post 5: $2.95
- Total Earnings: $101.00

Revenue Share Calculation:
  $101.00 * 0.12 = $12.12 ✓ (user's share on top of $99 subscription)

Total Charge (April 1):
  Subscription: $99.00
  Less Revenue Share: -$12.12
  Net Due: $86.88

Payout Log:
  billing_period_start: 2026-03-01
  billing_period_end: 2026-03-31
  total_revenue: $101.00
  revenue_share_amount: $12.12
  payout_status: processed
  payout_date: 2026-04-01
```

---

## Amazon Earnings Parsing & Import

### Automated CSV Ingestion

Users upload Amazon Associates monthly reports (CSV or Excel) to their dashboard:

```
File Format Expected:
Date,Order ID,Item Title,Item ASIN,Quantity,Advertised Cost,Amount,Status

2026-03-15,123-4567890-1234567,Espresso Machine WX-100,B0BZF8KVMD,1,899.99,26.99,Confirmed
2026-03-16,123-4567890-1234568,Coffee Grinder PRO,B07VD5QD2X,1,149.99,9.50,Confirmed
2026-03-18,123-4567890-1234569,Frother DELUXE,B09NRL7FQX,1,79.99,4.80,Confirmed
```

### Matching Logic

```python
# Pseudo-code for matching Amazon CSV → earning_events
def ingest_amazon_report(user_id, file_bytes):
    rows = parse_csv(file_bytes)
    
    for row in rows:
        order_id = row['Order ID']
        asin = row['Item ASIN']
        earning_amount = float(row['Amount'])
        order_date = parse_date(row['Date'])
        
        # Find matching content_item by ASIN
        content_item = db.query(ContentItem).filter_by(
            site_id=user_site_ids,
            amazon_products.asin=asin  # JSONB search
        ).first()
        
        if content_item:
            cluster_id = content_item.cluster_id
            post_num = extract_post_num(content_item.utm_source)
            
            # Create earning_event
            earning_event = EarningEvent(
                site_id=content_item.site_id,
                content_id=content_item.id,
                cluster_id=cluster_id,
                order_id=order_id,
                asin=asin,
                earning_amount=earning_amount,
                utm_source=f"cluster_{cluster_id}_post_{post_num}",
                order_date=order_date,
                status='confirmed'
            )
            db.add(earning_event)
    
    db.commit()
    return {"rows_imported": len(rows), "status": "success"}
```

### Fallback: Manual Linking

If Amazon CSV doesn't contain utm_source data:
1. User manually uploads mapping file: `order_id → utm_source → content_id`
2. System cross-references and creates earning_events
3. Dashboard highlights "unlinked" earnings (no attribution possible)

---

## Multi-Touch Attribution (Future Enhancement)

Current model: **Last-click attribution** (simplest, most transparent)

Future: **Time-decay model** (supporting posts get credit if pillar linked to them)

```
Example (Future):
User clicks supporting_post_2.utm_source → reads → clicks pillar.utm_source → buys

Attribution:
- Pillar: 70% of earnings (last click)
- Supporting post 2: 30% of earnings (assist credit, 7-day window)

Implementation: Add touch_attribution table, adjust revenue_share calculations
```

---

## Dashboard Reporting

### User-Facing Metrics

**Earnings Summary**
```
Period: March 1-31, 2026
Total Earnings: $1,245.67
Revenue Share: $149.48
Payout Status: Pending (next payout April 1)

Top Posts (by earnings):
1. "Best Espresso Machines 2026" (pillar): $847.50 (68%)
2. "Budget Espresso Grinder Guide" (post_1): $215.30 (17%)
3. "Espresso Tamper Technique" (post_5): $182.87 (15%)
```

**Cluster Performance**
```
Cluster ID: reddit_abc123_20260315
Generated: March 15, 2026
Posts: 1 pillar + 8 supporting
Status: ✓ All published
Total Earnings (YTD): $2,145.67
Avg. Revenue/Post: $238.41
Traffic (estimated): 3,450 visits
Click-Through Rate: 4.2%
```

**Hourly Earnings Feed** (real-time from Amazon API)
```
[Example Webhook from Amazon/Stripe]
timestamp: 2026-03-22T14:35:00Z
event: order_confirmed
order_id: 123-4567890-1234567
asin: B0BZF8KVMD
utm_source: cluster_reddit_abc123_20260322_post_2
earning_amount: $26.99
```

---

## Revenue Assurance & Fraud Prevention

### Risk Mitigation

| Risk | Mitigation | Monitoring |
|------|-----------|-----------|
| **Click Fraud** | Amazon Associates ToS violations → account suspension; AWS WAF rate-limiting on referral traffic | Anomaly detection: >500 clicks/min from same IP |
| **Product Misrepresentation** | FTC compliance checks; manual review of top 10 best-sellers per cluster | Quarterly audit of product claims |
| **Link Manipulation** | utm_source locked in DB; cannot be edited post-generation | Integrity check: utm_source matches post_id |
| **Duplicate Orders** | One order_id = one earning_event; Amazon deduplicates server-side | Manual review if same order appears twice |
| **Refund/Cancellation** | Amazon reports "Cancelled" status; system reverses earning & recalculates revenue-share | Task: nightly refresh of order statuses |

### Refund & Chargeback Policy

**Starter/Pro Tiers:**
- If earnings < $1 in first 30 days: 100% refund (no revenue share involved)
- After 30 days: no refunds (flat subscription model)

**Elite Tier:**
- If earnings < $1 in first 30 days: 100% refund
- Revenue-share is **deducted from next month's charge** (conservative: only payout on confirmed orders, 60+ days old)
- If user disputes earnings: manual reconciliation with Amazon Associates account

---

## Compliance & Transparency

### Earnings Audit Trail

All earning_events are immutable (append-only):
```
earning_event.id: uuid
earning_event.created_at: timestamp (not editable)
earning_event.updated_at: timestamp (for status changes only)
earning_event.status: confirmed | pending | canceled (only status can change)
```

### User Export & Reconciliation

Users can download:
1. **CSV Export**: All earning_events with utm_source, asin, amount, order_id, date
2. **Revenue Share Report**: Monthly calculation breakdown
3. **Raw Amazon Data**: Original CSV they uploaded (for cross-check)

```bash
# Example endpoint
GET /api/v1/earnings/export?format=csv&start_date=2026-03-01&end_date=2026-03-31
Response: CSV with columns:
  order_id, order_date, asin, product_title, utm_source, content_id, 
  earning_amount, commission_rate, status, import_date
```

### Webhook Transparency

Elite users can subscribe to real-time earnings webhooks:
```
POST user_webhook_url {
  "event": "earning_event_created",
  "data": {
    "order_id": "123-...",
    "earning_amount": 26.99,
    "utm_source": "cluster_...",
    "timestamp": "2026-03-22T14:35:00Z"
  }
}
```

---

## Integration with Payment Systems

### Stripe + Amazon Data Flow

```
Amazon Associates CSV Upload
    ↓ (nightly at 02:00 UTC)
Parse CSV → Create earning_events in PostGres
    ↓
Sum monthly earnings per site
    ↓
Calculate Elite revenue-share (12% for qualifying accounts)
    ↓
Update user_revenue_share table
    ↓
Queue Stripe invoice for next billing cycle
    ↓
Stripe webhook: invoice.paid → confirm payout processed
    ↓
User dashboard reflects new balance
```

### Payment Timing

```
Timeline for Elite User:
March 1-31: Earnings accumulate in earning_events table
April 1, 00:00 UTC: Celery beat job runs → calculates revenue-share
April 1, 00:15 UTC: Stripe invoice generated (revenue-share amount deducted from $99 subscription)
April 1-3: User receives ACH payout via Stripe Connect (or credit applied to account)
```

---

## References

- [Amazon Associates Operating Agreement](https://affiliate-program.amazon.com/help/operating/agreement) — Revenue share, attribution windows
- [16 CFR Part 255 - FTC Endorsements & Testimonials](https://www.ftc.gov/legal-library/browse/rules/part-255-guides-use-endorsements-testimonials-advertising) — Disclosure requirements
- [Stripe Connect Documentation](https://stripe.com/docs/connect) — Payout processing, ACH transfers
