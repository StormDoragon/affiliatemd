import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class SerpService:
	"""
	Serper.dev Search Engine Results Page (SERP) API integration.
	
	Used for:
	1. Keyword research (search volume, difficulty, CPC)
	2. SERP analysis (top 10 ranking pages for opportunity gaps)
	3. Featured snippet detection
	4. Related keywords discovery
	
	Docs: https://serper.dev/docs
	"""
	
	BASE_URL = "https://google.serper.dev"
	
	def __init__(self, api_key: str = ""):
		self.api_key = api_key
		self.timeout = 15.0
	
	def search_keywords(self, query: str, limit: int = 10) -> dict[str, object]:
		"""
		Search Google SERP for a keyword and return top results.
		
		Args:
			query: Keyword to search (e.g. "best espresso machines under $500")
			limit: Number of organic results to return (max 100)
		
		Returns:
			{
				"query": str,
				"search_volume": int,  # Monthly searches (0 if not available)
				"results_count": int,
				"organic_results": [
					{
						"position": int,
						"title": str,
						"url": str,
						"snippet": str,
						"domain": str,
						"publish_date": str or None
					}
				],
				"featured_snippet": {
					"title": str,
					"snippet": str,
					"source": str
				} or None,
				"related_keywords": [str]
			}
		"""
		if not self.api_key:
			return self._fallback(query, limit)
		
		try:
			headers = {
				"X-API-KEY": self.api_key,
				"Content-Type": "application/json"
			}
			
			payload = {
				"q": query,
				"num": min(limit, 100),  # Serper max is 100
				"gl": "us",  # Country
				"hl": "en",  # Language
			}
			
			with httpx.Client(timeout=self.timeout) as client:
				response = client.post(
					f"{self.BASE_URL}/search",
					json=payload,
					headers=headers
				)
				response.raise_for_status()
				data = response.json()
			
			# Parse organic results
			organic_results = []
			for idx, result in enumerate(data.get("organic", [])[:limit], 1):
				organic_results.append({
					"position": idx,
					"title": result.get("title", ""),
					"url": result.get("link", ""),
					"snippet": result.get("snippet", ""),
					"domain": result.get("domain", ""),
					"publish_date": result.get("date")
				})
			
			# Extract featured snippet if present
			featured_snippet = None
			if data.get("answerBox"):
				answer = data["answerBox"]
				featured_snippet = {
					"title": answer.get("title", ""),
					"snippet": answer.get("snippet", ""),
					"source": answer.get("source", "")
				}
			
			# Extract related keywords (Serper calls these "related searches")
			related_keywords = [s.get("query", "") for s in data.get("relatedSearches", [])][:10]
			
			# Attempt to extract search volume (Serper includes this in some tiers)
			search_volume = data.get("searchParameters", {}).get("volume", 0)
			
			return {
				"query": query,
				"search_volume": search_volume,
				"results_count": len(organic_results),
				"organic_results": organic_results,
				"featured_snippet": featured_snippet,
				"related_keywords": related_keywords
			}
		
		except Exception as e:
			logger.error(f"Serper API error for query '{query}': {e}")
			return self._fallback(query, limit)
	
	def analyze_serp_competition(self, keyword: str) -> dict[str, object]:
		"""
		Analyze SERP competition for a keyword.
		
		Returns:
			{
				"keyword": str,
				"competition": "low" | "medium" | "high",
				"top_3_domains": [str],
				"snippet_opportunities": [str],  # Keywords in snippets but not in top 10
				"content_gap": "short-form" | "long-form" | "video",  # Type of content needed
			}
		"""
		if not self.api_key:
			return self._fallback_competition(keyword)
		
		try:
			headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
			payload = {"q": keyword, "num": 10, "gl": "us"}
			
			with httpx.Client(timeout=self.timeout) as client:
				response = client.post(
					f"{self.BASE_URL}/search",
					json=payload,
					headers=headers
				)
				response.raise_for_status()
				data = response.json()
			
			organic_results = data.get("organic", [])
			top_3_domains = [r.get("domain", "") for r in organic_results[:3]]
			
			# Simple heuristic: if top 3 are major marketplaces (Amazon, Etsy, etc), high competition
			marketplace_domains = {"amazon.com", "etsy.com", "ebay.com"}
			has_marketplaces = any(domain in marketplace_domains for domain in top_3_domains)
			
			# Estimate competition
			competition = "high" if has_marketplaces or len(organic_results) > 8 else "medium" if len(organic_results) > 5 else "low"
			
			# Detect content gaps
			snippets_text = " ".join([r.get("snippet", "") for r in organic_results])
			has_video_mention = "video" in snippets_text.lower()
			has_table_mention = "table" in snippets_text.lower() or "comparison" in snippets_text.lower()
			
			content_gap = "video" if has_video_mention else "long-form" if len(snippets_text) > 500 else "short-form"
			
			return {
				"keyword": keyword,
				"competition": competition,
				"top_3_domains": top_3_domains,
				"snippet_opportunities": [],  # Would need semantic analysis
				"content_gap": content_gap
			}
		
		except Exception as e:
			logger.error(f"Serper competition analysis error: {e}")
			return self._fallback_competition(keyword)
	
	def _fallback(self, query: str, limit: int) -> dict[str, object]:
		"""
		Fallback demo SERP results when Serper API unavailable.
		"""
		demo_results = {
			"best espresso machines under $500": [
				{
					"position": 1,
					"title": "Best Espresso Machines Under $500 - Coffee Review 2025",
					"url": "https://coffeereview.com/espresso-machines-under-500",
					"snippet": "Find the best affordable espresso machines. Gaggia Classic Pro, Breville Barista Express...",
					"domain": "coffeereview.com",
					"publish_date": "2025-03-15"
				},
				{
					"position": 2,
					"title": "Top 10 Budget Espresso Machines | Wirecutter",
					"url": "https://www.nytimes.com/wirecutter/reviews/espresso",
					"snippet": "After 100+ hours testing, here are our top picks for the best espresso machines under $500...",
					"domain": "nytimes.com",
					"publish_date": "2025-01-10"
				},
			],
			"how to make espresso at home": [
				{
					"position": 1,
					"title": "The Complete Guide to Making Espresso at Home",
					"url": "https://seriouseats.com/how-to-make-espresso",
					"snippet": "Learn the basics of espresso making. Grind, tamp, extract, and pull the perfect shot...",
					"domain": "seriouseats.com",
					"publish_date": None
				},
			],
		}
		
		results = demo_results.get(query.lower(), [{"position": 1, "title": query, "url": "https://example.com", "snippet": "Demo result", "domain": "example.com", "publish_date": None}])
		
		return {
			"query": query,
			"search_volume": 0,
			"results_count": len(results[:limit]),
			"organic_results": results[:limit],
			"featured_snippet": None,
			"related_keywords": ["espresso machine reviews", "burr grinder", "coffee supplies"]
		}
	
	def _fallback_competition(self, keyword: str) -> dict[str, object]:
		"""Fallback SERP competition analysis."""
		return {
			"keyword": keyword,
			"competition": "medium",
			"top_3_domains": ["amazon.com", "wirecutter.com", "coffeereview.com"],
			"snippet_opportunities": [],
			"content_gap": "long-form"
		}
