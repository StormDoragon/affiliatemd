class WordpressService:
	def publish_post(self, title: str, content: str) -> dict[str, str]:
		return {
			"status": "queued",
			"title": title,
			"content_preview": content[:100],
		}
