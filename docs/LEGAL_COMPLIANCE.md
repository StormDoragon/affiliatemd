# Legal Compliance & Risk Mitigation (v1.2)

## Regulatory Framework

AffiForge operates in multiple compliance domains. This document outlines statutory requirements and our implementation strategy.

---

## 1. FTC Endorsement & Affiliate Disclosure

### Applicable Regulation

**16 CFR Part 255** — Guides Concerning the Use of Endorsements and Testimonials in Advertising

#### Key Requirements

1. **Disclosure of Material Connections**
   - When publisher has financial incentive (affiliate commission), must disclose clearly and conspicuously
   - Disclosure placement: "As an Amazon Associate, I earn from qualifying purchases" (header or intro)
   - Timing: Must appear **before** user scrolls past fold (above first Amazon link)

2. **Prohibited: Deceptive Endorsements**
   - Cannot recommend products **solely** for commission without genuine use/belief
   - Must be truthful representation of genuine experience or research
   - Cannot use fake user reviews or testimonials

3. **Clear & Conspicuous Standard**
   - Text size must be readable (same as surrounding copy, min. 10pt)
   - Proximity: Disclosure adjacent to claim, not hidden in footer
   - "AD" or "#ad" hashtag accepted for social media

### AffiForge Implementation

#### Automatic Disclosure Injection

```yaml
# In content_item.py model
class ContentItem:
  schema_markup: JSON # includes disclosure in schema
  content: TEXT # includes FTC paragraph
  
# Celery task: publish_to_wordpress
def inject_ftc_disclosure(post_content: str, site_id: uuid) -> str:
  """
  Prepend FTC disclosure to all posts with Amazon links.
  Runs before WordPress XML-RPC publish.
  """
  affiliate_network = site.amazon_associate_id
  disclosure = f"""
## Disclosure: Affiliate Links & Commissions
As an Amazon Associate, I earn from qualifying purchases. 
I may also earn from other affiliate programs listed on this site.

All product recommendations in this post are genuine and fact-checked.
I only recommend products I would personally use. Product links open in new window.
"""
  return disclosure + "\n\n" + post_content

# Template for pillar posts
PILLAR_POST_INTRO = """
## About This Guide
This comprehensive guide is based on {months} months of research into {niche}. 
I've tested {X} of the top products and consulted {Y} user reviews to identify the best options.

**Affiliate Disclosure**: As an Amazon Associate and {other_networks}, I earn from qualifying purchases 
made through the links in this guide. I only recommend products I genuinely believe in.
"""
```

#### Implementation Checklist

- [x] All WordPress posts include disclosure in first paragraph
- [x] Amazon links marked with `<a href="..." rel="sponsored">`
- [x] FAQ schema includes disclaimer: `"Did this post recommend a product I should buy?": "This post contains affiliate links to products I recommend."`
- [x] Email newsletters include: "This newsletter contains affiliate links"
- [x] Social media posts use `#ad` or `#sponsored` if post is paid sponsorship
- [ ] Reddit posts: Manual disclosure required (automated bots violate Reddit ToS)

#### Quarterly Compliance Audit

```
Process:
1. Sample 50 random posts from platform per user
2. Check: Disclosure present in first 300px, readable font, adjacent to first Amazon link
3. Check: Product claims fact-checked (ratings, specs match Amazon/reviews)
4. Flag: Posts recommending products user has not tested
5. Email user: "Compliance score: 98%" or "Issues found: 2 posts, corrective action needed"
```

---

## 2. Privacy & Data Protection

### GDPR (EU Users)

**Applicability**: If user base includes EU residents or if collecting EU user data (analytics, surveys)

#### Compliance Measures

| Element | Implementation |
|---------|-----------------|
| **Consent** | Cookie banner (OneTrust or Termly) requiring explicit opt-in for non-essential cookies |
| **Data Processing** | Data Processing Agreement (DPA) with Supabase, Stripe, Plausible Analytics |
| **User Rights** | Endpoint: `GET /api/v1/gdpr/personal-data` (exports all user data in JSON) |
| **Deletion** | Endpoint: `DELETE /api/v1/gdpr/account` (soft-delete user, anonymize in 30 days) |
| **Subcontractors** | List of all vendors in Privacy Policy + links to their privacy statements |

#### Supabase DPA
- Supabase signs DPA addendum (available in their docs)
- Data residency: Ireland (eu-west-1) for EU accounts

### CCPA (California Users)

**Applicability**: If user base includes California residents

#### Compliance Measures

- **Right to Know**: User can request all data collected about them
- **Right to Delete**: User can request permanent deletion (opt-out)
- **Right to Opt-Out**: User can opt-out of "sale" of personal data (we don't "sell" — no third-party sharing without consent)
- **Non-Discrimination**: Cannot charge more for opting out

#### Implementation

```python
# In dependencies.py
async def gdpr_data_export(user_id: UUID) -> dict:
  """
  Export all personal data for GDPR/CCPA requests.
  """
  user = db.query(User).filter_by(id=user_id).first()
  
  return {
    "user": {
      "email": user.email,
      "created_at": user.created_at,
      "subscription_tier": user.tier,
    },
    "sites": [
      {
        "id": s.id,
        "domain": s.domain,
        "posts": s.content_items.count(),
        "total_earnings": sum(e.earning_amount for e in s.earning_events)
      } for s in user.sites
    ],
    "earnings": [
      {
        "order_id": e.order_id,
        "asin": e.asin,
        "amount": e.earning_amount,
        "date": e.order_date
      } for e in user.earning_events
    ],
    "api_keys": [{"name": k.name, "created_at": k.created_at} for k in user.api_keys]
  }
```

### TCPA (Telemarketing - US)

**Applicability**: If sending SMS/phone calls to users (we don't)

**Status**: Not applicable; we only use email

---

## 3. Copyright & Content Ownership

### User-Generated Content

AffiForge **does not claim ownership** of user-generated content (blog posts). Users retain 100% copyright.

#### Licensing Terms

```
User grants AffiForge a non-exclusive, worldwide, royalty-free license to:
1. Store the content on our servers
2. Display content in user's dashboard
3. Use anonymized snippets for aggregate metrics (e.g., "avg. blog length: 1,200 words")
4. NOT: Republish, sell, or use for advertising without explicit consent
```

**Legal basis**: Included in ToS §3, accepted at signup.

### LLM Training Data

**Policy**: User content is NOT used to train our LLMs (GPT-4o, Claude).

```
Exception: Users can opt-in to contribute anonymized content to improve prompts.
Opt-in is explicit (checkbox at signup) and can be revoked anytime.
```

### Third-Party IP in Generated Content

LangChain prompts generate content that may reference:
- Amazon product images, names, specs (Amazon ToS permits in affiliate posts)
- Public Reddit data (Reddit ToS §2: permitted use)
- Public SERP results (Google permits for SEO/research purposes)

**Risk**: User is responsible for ensuring generated content doesn't violate third-party copyright.

**Mitigation**: 
- Prompt includes instruction: "Only recommend products with 3+ reviews and 4.0+ rating"
- Content audit: Detect plagiarism using Copyscape API (via task: `audit_content_plagiarism`)

---

## 4. Tax Compliance & Affiliate Reporting

### US Tax Obligations (IRS)

#### Income Reporting

- **Affiliate earnings** are self-employment income (Schedule C, form 1040)
- **Revenue-share earnings** from Elite tier are also self-employment income
- **AffiForge subscription expense** is deductible (business expense)
- **LLM API costs** are deductible (Content Production expense)

#### Compliance Requirements

1. **Form 1099-NEC** (if user entity earns >$600/year from AffiForge revenue-share)
   - AffiForge must issue 1099-NEC to Elite users who earn $600+ annually
   - Due date: January 31, 2027 (for 2026 earnings)
   - Requires: User's SSN/EIN + W-9 form

2. **Form 1099-K** (issued by Stripe for affiliate earnings affiliate)
   - Stripe issues 1099-K if user receives >$20,000 and 200+ transactions
   - AffiForge does NOT issue (we're not the payor)

#### Implementation

```python
# In billing_service.py
def generate_1099_nec(user_id: UUID, tax_year: int):
  """
  Generate 1099-NEC form for Elite users earning $600+.
  Requires: user.w9_form_signed = True
  """
  total_revenue_share = db.query(UserRevenueShare).filter(
    UserRevenueShare.user_id == user_id,
    extract(year, UserRevenueShare.billing_period_start) == tax_year
  ).sum(UserRevenueShare.revenue_share_amount)
  
  if total_revenue_share >= 600:
    form_1099_nec = generate_pdf(
      recipient_name=user.name,
      recipient_ssn=user.ssn_encrypted,  # AES-256 decrypted for tax form
      payer_name="AffiForge Inc.",
      payer_ein="XX-XXXXXXX",
      box_1a=total_revenue_share,  # NEC non-employee compensation
      tax_year=tax_year
    )
    return form_1099_nec
```

#### W-9 Requirement

Users must complete **Form W-9** (Request for Taxpayer Identification Number) to receive 1099-NEC:
- Collected at signup if user selects Elite tier
- Stored encrypted in `users.w9_form_signed` + SSN/EIN in encrypted field
- Validated with IRS PTIN verification (optional, recommended)

### International Tax Treaties

**UK/EU Users**: 
- Earnings are subject to local income tax authorities of their country
- AffiForge provides earnings data for tax reporting; user is responsible for compliance
- No VAT charged (digital services may be exempt in some jurisdictions; not applicable)

**Canada**: 
- Affiliate earnings reported on T1 General (Schedule 8, Business Income)
- GST/HST may apply if user is registered GST collector (not applicable for AffiForge subscription)

---

## 5. Amazon Associates Compliance

### Program Agreement Violations (Risk: Account Suspension)

**Prohibited Activities**:

| Activity | Why Prohibited | Enforcement |
|----------|----------------|------------|
| **Keyword Stuffing** | Manipulates search rankings; violates Google EEAT | Google SEO penalty + Amazon may suspend account |
| **Private Label Products (PLPs)** | Amazon prohibits promoting self-owned products via affiliate links | Immediate account suspension |
| **Discount Code Gaming** | Promoting discount codes to artificially inflate orders | Amazon refunds commission + suspension |
| **Click Fraud** | Bot clicks, incentivized clicks, URL shortener redirects | Immediate suspension, earnings forfeited |
| **Misleading Ad Copy** | FTC violation; claims not supported by product | Amazon + FTC takedown of site |
| **Expired/Broken Links** | Low user experience; violates quality standard | Earnings credited to affiliate only if approved |
| **Scraping Amazon Data** | API abuse; copyright violation | IP ban + legal action |
| **Promoting Counterfeit** | Illegal; Amazon policy violation | Account suspension + report to law enforcement |

#### AffiForge Guardrails

```python
# In optimization_service.py
def compliance_check_before_publish(content_item: ContentItem) -> bool:
  """
  Validate content against Amazon Associates agreement before publishing.
  """
  checks = {
    "fcc_disclosure": "As an Amazon Associate" in content_item.content[:500],
    "affiliate_link_format": all(
      "tag=" in link for link in extract_amazon_links(content_item.content)
    ),
    "product_rating": all(
      get_amazon_product(asin)["rating"] >= 4.0 
      for asin in content_item.amazon_product_asins
    ),
    "keyword_density": calculate_keyword_density(content_item) < 3.0,  # avoid stuffing
    "unique_content": plagiarism_score(content_item.content) > 95,  # 95% unique
  }
  
  failed = [k for k, v in checks.items() if not v]
  if failed:
    raise ComplianceError(f"Content violates Amazon policy: {failed}")
  return True
```

### Amazon's Attribution Window

- **Click-to-Order**: 24 hours (must click Amazon link → complete purchase within 24h)
- **Multi-Session**: If user clicks link, leaves, returns later: 24-hour window resets
- **Platform Requirement**: Link must use user's assigned Associate ID (tag parameter)

**Implementation in AffiForge**: 
- All links include user's `amazon_associate_id` in `tag=` parameter
- Validated before publishing (prevent misconfigured links)

---

## 6. WordPress XML-RPC Security

### Risk: Account Compromise via XML-RPC Brute Force

**Vulnerability**: WordPress XML-RPC API allows unlimited login attempts without rate-limiting

**Mitigation in AffiForge**:

```python
# In wordpress_service.py
class WordPressPublisher:
  def __init__(self, site: Site):
    # Store credentials encrypted in Supabase
    self.wp_url = site.wordpress_url
    self.username = decrypt(site.wordpress_username_encrypted)
    self.password = decrypt(site.wordpress_password_encrypted)
    
  def publish_post(self, content_item: ContentItem) -> bool:
    """
    Publish to WordPress with security measures.
    """
    # Use application password (WordPress 5.6+), not main password
    # If available, prompt user to create application-specific password
    
    xml_rpc_client = xmlrpc.client.ServerProxy(f"{self.wp_url}/xmlrpc.php")
    
    try:
      post_id = xml_rpc_client.wp.newPost(
        1,  # blog_id
        self.username,
        self.password,  # Sent over HTTPS only
        {
          "post_title": content_item.title,
          "post_content": content_item.content,
          "post_status": "publish",
          "post_type": "post",
          "terms_names": {"category": [content_item.primary_keyword]}
        }
      )
      
      content_item.wordpress_post_id = post_id
      content_item.wordpress_url = f"{self.wp_url}/?p={post_id}"
      db.commit()
      
      return True
    except Exception as e:
      log_error(f"XML-RPC publish failed: {e}", user_id=site.user_id)
      raise
```

#### User Recommendations

- Disable XML-RPC if not needed: Add to `wp-config.php`: `define('XMLRPC_REQUEST_TIMEOUT', 1);`
- Use application-specific passwords, not main account password
- Use IP whitelist on WordPress firewall (Wordfence, Sucuri)
- Enable two-factor authentication on WordPress admin account

---

## 7. Stripe Payment Compliance

### PCI-DSS (Payment Card Industry Data Security Standard)

**Requirement**: Handle credit card data securely

**Implementation**:
- **Payment Processing**: Delegated entirely to Stripe (Stripe handles PCI compliance)
- **Card Data Storage**: NOT stored on AffiForge servers (Stripe stores, we store stripe_customer_id only)
- **HTTPS**: All endpoints use TLS 1.2+
- **Sensitive Data Logging**: Never log card numbers, CVV, or expiration dates

### Stripe Webhook Security

```python
# In routers/billing.py
@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, raw_body: bytes):
  """
  Verify Stripe webhook signature before processing.
  """
  sig_header = request.headers.get("stripe-signature")
  
  try:
    event = stripe.Webhook.construct_event(
      raw_body, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid signature")
  except stripe.error.SignatureVerificationError:
    raise HTTPException(status_code=403, detail="Signature verification failed")
  
  # Process event only if signature is valid
  if event["type"] == "invoice.payment_succeeded":
    handle_payment_success(event["data"]["object"])
  
  return {"status": "success"}
```

---

## 8. Liability & Disclaimers

### Limitation of Liability (Terms of Service §8)

```markdown
## 8. Limitation of Liability

**Disclaimer**: AffiForge provides tools for content generation and affiliate marketing. 
We do not guarantee earnings, traffic, or SEO rankings.

### EARNINGS DISCLAIMER
- Affiliate earnings are not guaranteed and depend on user's audience, content quality, and market conditions
- Most users earn $0-100/month; earnings >$1,000/mo are rare and require significant traffic
- Historical performance does not indicate future results
- Revenue-share is only available to Elite tier and is subject to terms change

### NO LIABILITY FOR USER CONTENT
- Users are solely responsible for content accuracy, copyright compliance, and legality
- AffiForge disclaims liability for defamatory, infringing, or illegal content posted by users
- Users indemnify AffiForge against claims arising from their content

### THIRD-PARTY SERVICE FAILURES
- If WordPress, WordPress, Stripe, or Amazon APIs are unavailable, AffiForge is not liable for lost earnings
- Users are responsible for maintaining backups of their content

### LIABILITY CAP
- AffiForge's total liability is limited to 100% of fees paid in the last 12 months
- In no event shall AffiForge be liable for consequential, indirect, or punitive damages
```

### Earnings Expectations Disclaimer

Every user sees this on signup:

```
⚠️ **EARNINGS DISCLAIMER**

Most new affiliate marketers earn $0-500 in their first year. 
Earning $1,000+/month requires:
- High-traffic niche site (10,000+ monthly visitors)
- 6-12 months of consistent content production
- Strong SEO fundamentals & backlink profile
- Audience trust & email list building

AffiForge tools accelerate content creation but cannot guarantee earnings.
If you don't earn $1 in 30 days, you're eligible for a full refund.
```

---

## 9. Cyber Security & Data Breach Response

### Notification Requirements (US State Laws)

If data breach affects >500 users in any state, must notify:
1. Users (email within 60 days)
2. State Attorney General
3. Consumer reporting agencies (for large breaches)

**Response Plan**:
```
Day 0: Breach discovered → Isolate affected systems → Notify Incident Response Team
Day 1: Forensic analysis → Identify compromised data & extent
Day 3: Legal review → Determine notification obligations
Day 7: Notify affected users → Email with breach details, credit monitoring offer
Day 30: Notify regulators → Send required notifications to state AGs
Day 60: Post-incident review → Implement fixes, update security policies
```

### Encryption & Key Management

- **At Rest**: AES-256 for sensitive data (passwords, API keys, SSN)
- **In Transit**: TLS 1.2+ for all HTTPS connections
- **Key Storage**: Use Supabase Vault (KMS provider) or AWS Secrets Manager
- **Key Rotation**: Quarterly rotation of encryption keys

---

## 10. Compliance Calendar

| Date | Task | Owner | Status |
|------|------|-------|--------|
| Q1 2026 (by March 31) | Audit FTC disclosures across 100 sample posts | Legal | ⏳ In Progress |
| Q2 2026 (by June 30) | GDPR & CCPA compliance audit | Legal + DevOps | 🔄 Planned |
| Q3 2026 (by Sept 30) | Penetration test & security audit | Security | 🔄 Planned |
| Q4 2026 (by Dec 31) | 1099-NEC generation & validation for 2026 tax year | Finance | 🔄 Planned |
| Ongoing | Real-time monitoring of Amazon Associates policy updates | Legal | 🟢 Active |

---

## 11. Contact & Support

### Legal Inquiries
- **Email**: legal@affiforge.com
- **Response Time**: 48 hours for urgent compliance questions

### Data Privacy Requests (GDPR/CCPA)
- **Portal**: https://affiforge.com/privacy/data-request
- **Response Time**: 30 days (legal deadline)

### Report a Violation
- **Form**: https://affiforge.com/report-violation
- **Anonymous**: Yes
- **Investigation**: Within 7 days

---

## References

- [16 CFR Part 255 - FTC Endorsement Guides](https://www.ftc.gov/legal-library/browse/rules/part-255-guides-use-endorsements-testimonials-advertising)
- [Amazon Associates Operating Agreement](https://affiliate-program.amazon.com/help/operating/agreement)
- [Amazon Associates Prohibited Activities](https://affiliate-program.amazon.com/help/operating/policies)
- [GDPR / CCPA Compliance Checklist (IAPP)](https://iapp.org)
- [Stripe PCI Compliance](https://stripe.com/us/resources/more/blog/pci-dss-compliance-for-stripe-merchants)
- [IRS Form 1099-NEC Instructions](https://www.irs.gov/pub/irs-pdf/i1099nic.pdf)
- [FCC Telephone Consumer Protection Act (TCPA)](https://www.fcc.gov/document/0-fcc-91-360) (not applicable)
