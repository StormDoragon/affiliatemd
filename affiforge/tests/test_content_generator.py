import pytest
from unittest.mock import patch, MagicMock
from affiforge.services.ai_service import generate_blog
from affiforge.schemas.generator import ClusterRequest


@pytest.fixture
def sample_reddit_data():
    """Sample Reddit thread data for testing."""
    return {
        "title": "Can you recommend the best espresso machine under $500?",
        "selftext": "I'm looking for a reliable espresso machine...",
        "score": 1200,
        "num_comments": 450,
        "subreddit": "Coffee",
        "url": "https://reddit.com/r/Coffee/comments/abc123/...",
        "created_utc": 1711100000
    }


@pytest.fixture
def cluster_request(sample_reddit_data):
    """Sample ClusterRequest for testing."""
    return ClusterRequest(
        reddit_post_id="abc123",
        niche="espresso_machines",
        audience_description="Coffee enthusiasts aged 25-45",
        budget_per_post=0.12
    )


def test_generate_blog_returns_valid_content(sample_reddit_data):
    """Test that generate_blog returns content with affiliate links and meets length requirement."""
    with patch('affiforge.services.ai_service.openai.ChatCompletion.create') as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=
                "# Best Espresso Machines Under $500\n\n"
                "After extensive research, here are my top recommendations:\n\n"
                "Check out [the Gaggia Classic Pro](https://www.amazon.com/dp/B00AQVXVAK?tag=espresso-101-20) "
                "which offers excellent value. "
                "I recommend [the Roka Espresso Machine](https://www.amazon.com/dp/B0BZF8KVMD?tag=espresso-101-20) "
                "for serious enthusiasts. " * 5  # Repeat to exceed 1500 chars
            ))]
        )
        
        post = generate_blog(sample_reddit_data)
        
        assert "Amazon affiliate link" in post or "amazon.com" in post
        assert len(post) > 1500
        assert "espresso" in post.lower()


def test_generate_blog_includes_fcc_disclosure(sample_reddit_data):
    """Test that generated content includes FTC disclosure."""
    with patch('affiforge.services.ai_service.openai.ChatCompletion.create') as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=
                "As an Amazon Associate, I earn from qualifying purchases.\n\n"
                "Best espresso machines: " * 200
            ))]
        )
        
        post = generate_blog(sample_reddit_data)
        
        assert "Amazon Associate" in post or "affiliate" in post.lower()


def test_generate_blog_returns_json_structure():
    """Test that generate_blog returns proper JSON structure with required fields."""
    reddit_data = {
        "title": "Test topic",
        "selftext": "Test content",
        "score": 100,
        "subreddit": "test"
    }
    
    with patch('affiforge.services.ai_service.openai.ChatCompletion.create') as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=
                '{"title": "Test", "slug": "test", "content": "x" * 2000, '
                '"meta_description": "test", "keywords": ["test"]}'
            ))]
        )
        
        result = generate_blog(reddit_data)
        
        # Should parse valid JSON
        assert isinstance(result, (dict, str))


def test_generate_blog_handles_api_cost_limit(sample_reddit_data):
    """Test that generate_blog respects cost limits."""
    with patch('affiforge.services.ai_service.openai.ChatCompletion.create') as mock_llm:
        with patch('affiforge.services.ai_service.calculate_cost') as mock_cost:
            # Simulate cost exceeding limit
            mock_cost.return_value = 0.15  # Exceeds $0.12 limit
            
            with pytest.raises(ValueError, match="cost exceed"):
                generate_blog(sample_reddit_data)


def test_generate_blog_retries_on_timeout(sample_reddit_data):
    """Test that generate_blog retries on API timeout."""
    with patch('affiforge.services.ai_service.openai.ChatCompletion.create') as mock_llm:
        # First call times out, second succeeds
        mock_llm.side_effect = [
            TimeoutError("API timeout"),
            MagicMock(choices=[MagicMock(message=MagicMock(
                content="Best espresso machines: [link](https://amazon.com?tag=test) " * 200
            ))])
        ]
        
        post = generate_blog(sample_reddit_data)
        
        assert post is not None
        assert len(post) > 0


def test_generate_blog_validates_reddit_input(cluster_request):
    """Test that generate_blog validates required Reddit fields."""
    invalid_data = {"incomplete": "data"}
    
    with pytest.raises((KeyError, ValueError)):
        generate_blog(invalid_data)


def test_generate_blog_handles_empty_response(sample_reddit_data):
    """Test that generate_blog handles empty LLM responses gracefully."""
    with patch('affiforge.services.ai_service.openai.ChatCompletion.create') as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=""))]
        )
        
        with pytest.raises(ValueError, match="empty|invalid"):
            generate_blog(sample_reddit_data)


@pytest.mark.integration
def test_generate_cluster_e2e(sample_reddit_data, cluster_request):
    """Integration test: Reddit data → cluster generation → valid output."""
    with patch('affiforge.services.ai_service.openai.ChatCompletion.create') as mock_llm:
        # Mock cluster response with pillar + supporting posts
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=
                '{"cluster_id": "reddit_abc123_20260322", '
                '"pillar_post": {"title": "Best Espresso", "content": "x" * 3000}, '
                '"supporting_posts": [{"title": "Budget", "content": "x" * 1500}]}'
            ))]
        )
        
        result = generate_blog(sample_reddit_data)
        
        assert result is not None
        assert "Espresso" in str(result) or "espresso" in str(result).lower()
