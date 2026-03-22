from datetime import UTC, datetime


def generate() -> dict[str, str]:
	return {
		"title": "Test Affiliate Article",
		"slug": "test-affiliate-article",
		"generated_at": datetime.now(UTC).isoformat(),
	}


if __name__ == "__main__":
	print(generate())
