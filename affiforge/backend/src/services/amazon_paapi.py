import logging
from decimal import Decimal
from typing import Optional

# Amazon PA-API v5 requires signature v4 signing (boto3 can help, but paapi5-python-sdk is simpler)
try:
	from paapi5_python_sdk.api.default_api import DefaultApi
	from paapi5_python_sdk.models.partner_type import PartnerType
	from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
	from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
except ImportError:  # pragma: no cover
	DefaultApi = None


logger = logging.getLogger(__name__)


class AmazonPAAPIService:
	"""
	Amazon Product Advertising API v5 service for fetching product recommendations.
	
	Requires paapi5-python-sdk + AWS credentials for PA-API.
	Falls back to local demo data if credentials missing or SDK unavailable.
	"""
	
	def __init__(self, access_key: str = "", secret_key: str = "", partner_tag: str = ""):
		self.access_key = access_key
		self.secret_key = secret_key
		self.partner_tag = partner_tag
		self.region = "us-east-1"
		self.host = "webservices.amazon.com"
		self._api = None
		
		if self.access_key and self.secret_key and self.partner_tag and DefaultApi:
			try:
				self._api = DefaultApi(
					access_key=self.access_key,
					secret_key=self.secret_key,
					host=self.host,
					region=self.region
				)
			except Exception as e:
				logger.warning(f"Failed to initialize PA-API client: {e}, using fallback")
	
	def fetch_products(
		self,
		keyword: str,
		max_items: int = 10,
		min_price: Optional[int] = None,
		max_price: Optional[int] = None,
		rating_min: float = 4.0,  # Only 4.0★+ to avoid low-quality products
	) -> dict[str, object]:
		"""
		Fetch Amazon products matching keyword with optional filters.
		
		Args:
			keyword: Search keyword (e.g. 'espresso machine')
			max_items: Number of results to return (max 10 per Amazon API)
			min_price: Minimum product price in USD
			max_price: Maximum product price in USD
			rating_min: Minimum customer rating (0-5 stars)
		
		Returns:
			{
				"keyword": str,
				"results_count": int,
				"products": [
					{
						"asin": str,
						"title": str,
						"url": str,  # Affiliate link with partner_tag
						"price": str,
						"rating": float,
						"review_count": int,
						"image_url": str
					}
				],
				"affiliate_disclaimer": str
			}
		"""
		if not self._api:
			return self._fallback(keyword, max_items)
		
		try:
			request = SearchItemsRequest()
			request.partner_tag = self.partner_tag
			request.search_index = "All"
			request.keywords = keyword
			request.item_count = min(max_items, 10)  # PA-API max is 10
			
			# Request specific product attributes for recommendations
			request.resources = [
				SearchItemsResource.IMAGES_PRIMARY_LARGE,
				SearchItemsResource.ITEM_INFO_TITLE,
				SearchItemsResource.OFFERS_LISTINGS_PRICE,
				SearchItemsResource.CUSTOMER_REVIEWS_COUNT,
				SearchItemsResource.CUSTOMER_REVIEWS_STAR_RATING,
			]
			
			response = self._api.search_items(request)
			
			if not response.search_result or not response.search_result.items:
				return self._fallback(keyword, max_items)
			
			products = []
			for item in response.search_result.items:
				# Extract product info from PA-API response
				asin = item.asin
				title = item.item_info.title.display_value if item.item_info.title else ""
				price_str = ""
				
				if item.offers and item.offers.listings:
					price_str = item.offers.listings[0].price.display_value
				
				rating = float(item.customer_reviews.star_rating.raw_value) if item.customer_reviews and item.customer_reviews.star_rating else 0.0
				review_count = int(item.customer_reviews.count.raw_value) if item.customer_reviews and item.customer_reviews.count else 0
				
				# Skip low-rated products (Amazon policy check)
				if rating < rating_min:
					continue
				
				# Build affiliate URL with partner tag
				affiliate_url = f"https://www.amazon.com/dp/{asin}?tag={self.partner_tag}"
				
				image_url = ""
				if item.images and item.images.primary:
					image_url = item.images.primary.large.url
				
				products.append({
					"asin": asin,
					"title": title,
					"url": affiliate_url,
					"price": price_str,
					"rating": rating,
					"review_count": review_count,
					"image_url": image_url
				})
			
			return {
				"keyword": keyword,
				"results_count": len(products),
				"products": products,
				"affiliate_disclaimer": "All product links are affiliate links. We may earn a commission when you purchase through these links."
			}
		
		except Exception as e:
			logger.error(f"PA-API error fetching products for '{keyword}': {e}")
			return self._fallback(keyword, max_items)
	
	def _fallback(self, keyword: str, max_items: int) -> dict[str, object]:
		"""
		Fallback demo data when PA-API is unavailable.
		Used for local development and testing.
		"""
		demo_products = {
			"espresso machine": [
				{"asin": "B00AQVXVAK", "title": "Gaggia Classic Pro Espresso Machine", "price": "$199.99", "rating": 4.5, "review_count": 2341},
				{"asin": "B0BZF8KVMD", "title": "Breville Barista Express Espresso Machine", "price": "$449.95", "rating": 4.6, "review_count": 4521},
				{"asin": "B08XZL6X2H", "title": "DeLonghi Dedica Espresso Machine", "price": "$289.99", "rating": 4.3, "review_count": 1852},
			],
			"burr grinder": [
				{"asin": "B00IBDQZ4I", "title": "Baratza Encore Conical Burr Grinder", "price": "$139.95", "rating": 4.7, "review_count": 5234},
				{"asin": "B000JQRTBY", "title": "Baratza Virtuoso BurGrinder", "price": "$39.95", "rating": 4.4, "review_count": 3421},
			],
			"coffee": [
				{"asin": "B00EPQFE48", "title": "Lavazza Super Crema Whole Beans", "price": "$16.99", "rating": 4.5, "review_count": 892},
			],
		}
		
		products_for_keyword = demo_products.get(keyword.lower(), [])
		selected = products_for_keyword[:max_items]
		
		for product in selected:
			product["url"] = f"https://www.amazon.com/dp/{product['asin']}?tag={self.partner_tag or 'affiforge-affiliate-20'}"
			product.pop("asin")
		
		return {
			"keyword": keyword,
			"results_count": len(selected),
			"products": selected,
			"affiliate_disclaimer": "All product links are affiliate links. Demo data only."
		}
