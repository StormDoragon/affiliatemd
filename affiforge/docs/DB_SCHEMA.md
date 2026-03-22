# DB Schema

```python
class User(Base):
	id, email, stripe_customer_id, profitshare_enabled: bool


class Site(Base):  # User's WordPress sites
	user_id, wp_url, wp_username, wp_app_password, amazon_tag


class GeneratedPost(Base):
	site_id, reddit_thread_id, keyword, title, slug, status (draft/published), revenue_attributed: Decimal


class EarningsLog(Base):
	post_id, amazon_order_id, commission_amount, date
```
