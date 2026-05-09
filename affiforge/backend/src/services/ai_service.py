"""
Advanced LLM service with LangChain for cluster generation and optimization.
Supports GPT-4o and Claude 3.5 Sonnet with cost tracking and safety limits.
"""

import json
import time
from typing import Optional

try:
    import openai
    from langchain.chains import LLMChain
    from langchain.chat_models import ChatOpenAI, ChatAnthropic
    from langchain.prompts import PromptTemplate
    from langchain.callbacks import get_openai_callback
except ImportError:
    pass

from ..config import settings


class CostExceededError(Exception):
    """Raised when LLM cost exceeds maximum allowed per task."""
    pass


class AIService:
    """LangChain-powered AI service for content generation and optimization."""
    
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.max_cost = float(settings.max_cost_per_task or 0.12)
        self.temperature = 0.7
        
        try:
            if model == "gpt-4o":
                self.llm = ChatOpenAI(
                    model_name="gpt-4o",
                    openai_api_key=settings.openai_api_key,
                    temperature=self.temperature,
                    max_tokens=4000,
                )
            elif model == "claude-3-5-sonnet":
                self.llm = ChatAnthropic(
                    model_name="claude-3-5-sonnet-20240620",
                    anthropic_api_key=settings.claude_api_key,
                    temperature=self.temperature,
                    max_tokens=4000,
                )
            else:
                raise ValueError(f"Unsupported model: {model}")
        except Exception:
            self.llm = None  # Fallback for dev environment
    
    def generate_cluster(
        self,
        reddit_data: dict,
        niche: str,
        audience: str,
    ) -> dict:
        """
        Generate a full SEO cluster (1 pillar + 8 supporting posts) from Reddit data.
        Cost capped at $0.12. Returns cluster structure with pillar + supporting posts.
        """
        if not self.llm:
            return self._fallback_cluster(reddit_data, niche, audience)
        
        start_time = time.time()
        cost = 0.0
        
        try:
            # Extract pain point
            pain_prompt = PromptTemplate(
                input_variables=["title", "text"],
                template="""Extract pain point from Reddit thread (1-2 sentences).
Title: {title}
Text: {text}
Return: {{"pain_point": "...", "score": 8.5}}"""
            )
            pain_chain = LLMChain(llm=self.llm, prompt=pain_prompt)
            
            with get_openai_callback() as cb:
                pain_result = pain_chain.run(
                    title=reddit_data.get("title", ""),
                    text=reddit_data.get("selftext", "")[:1000]
                )
                cost += cb.total_cost
            
            if cost > self.max_cost:
                raise CostExceededError(f"Cost ${cost:.4f} exceeds ${self.max_cost}")
            
            pain_data = json.loads(pain_result.strip())
            
            # Generate pillar outline
            pillar_prompt = PromptTemplate(
                input_variables=["pain", "niche", "audience"],
                template="""Create pillar post outline for {niche} addressing: {pain}
Audience: {audience}
Return JSON: {{"title": "...", "sections": ["s1", "s2", ...]}}"""
            )
            pillar_chain = LLMChain(llm=self.llm, prompt=pillar_prompt)
            
            with get_openai_callback() as cb:
                pillar_result = pillar_chain.run(
                    pain=pain_data.get("pain_point", ""),
                    niche=niche,
                    audience=audience
                )
                cost += cb.total_cost
            
            if cost > self.max_cost:
                raise CostExceededError(f"Cost ${cost:.4f} exceeds ${self.max_cost}")
            
            pillar_data = json.loads(pillar_result.strip())
            
            # Generate supporting posts
            supporting = []
            for i in range(1, 9):
                support_prompt = PromptTemplate(
                    input_variables=["pain", "num"],
                    template="""Generate supporting post {num}/8 for pain: {pain}
Return: {{"title": "...", "keyword": "..."}}"""
                )
                support_chain = LLMChain(llm=self.llm, prompt=support_prompt)
                
                with get_openai_callback() as cb:
                    support_result = support_chain.run(pain=pain_data.get("pain_point", ""), num=i)
                    cost += cb.total_cost
                
                if cost > self.max_cost:
                    raise CostExceededError(f"Cost ${cost:.4f} exceeds ${self.max_cost}")
                
                supporting.append(json.loads(support_result.strip()))
            
            duration = time.time() - start_time
            
            return {
                "status": "success",
                "cluster_id": f"reddit_{int(time.time())}",
                "cost": round(cost, 6),
                "duration_seconds": round(duration, 2),
                "pillar_post": {
                    "title": pillar_data.get("title", ""),
                    "sections": pillar_data.get("sections", []),
                    "word_count": 2500,
                },
                "supporting_posts": supporting,
            }
        
        except (CostExceededError, json.JSONDecodeError) as e:
            return {
                "status": "failed",
                "error": str(e),
                "cost": round(cost, 6),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "cost": round(cost, 6),
            }
    
    def optimize_post(self, post_title: str, conversion_rate: float = 2.5) -> dict:
        """Suggest ONE high-impact optimization for existing affiliate post."""
        if not self.llm:
            return self._fallback_optimization()
        
        try:
            prompt = PromptTemplate(
                input_variables=["title", "ctr"],
                template="""Optimize affiliate post "{title}" with CTR {ctr}%.
Suggest ONE change: video | table | urgency | internal-link | faq-schema | author-bio.
Return: {{"type": "...", "recommendation": "...", "estimated_lift": "25-30%"}}"""
            )
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            with get_openai_callback() as cb:
                result = chain.run(title=post_title, ctr=conversion_rate)
                cost = cb.total_cost
            
            if cost > self.max_cost:
                return {"status": "failed", "error": "Cost exceeded"}
            
            return {
                "status": "success",
                "optimization": json.loads(result.strip()),
                "cost": round(cost, 6),
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def _fallback_cluster(self, reddit_data: dict, niche: str, audience: str) -> dict:
        """Fallback cluster generation for dev/testing."""
        return {
            "status": "success",
            "cluster_id": f"dev_{int(time.time())}",
            "pillar_post": {"title": f"Best {niche} Guide", "sections": ["Intro", "Options", "Conclusion"]},
            "supporting_posts": [{"title": f"Post {i}", "keyword": f"long-tail-{i}"} for i in range(1, 9)],
        }
    
    def _fallback_optimization(self) -> dict:
        """Fallback optimization for dev/testing."""
        return {
            "status": "success",
            "optimization": {
                "type": "video_embed",
                "recommendation": "Add YouTube review videos above fold",
                "estimated_lift": "25-30%"
            }
        }
    
    # Legacy methods for backward compatibility
    def generate_article_outline(self, keyword: str) -> dict:
        return {"keyword": keyword, "sections": [f"What is {keyword}?", f"Best {keyword}"]}
    
    def generate_basic_post(self, keyword: str, pain_point: str) -> dict:
        return {
            "title": f"Best {keyword} for {pain_point}",
            "body": f"Solving {pain_point} with {keyword}..."
        }
    
    def generate_content_cluster(self, seed_keyword: str, audience: str, cluster_size: int) -> list:
        return [
            {
                "keyword": f"{seed_keyword} {i}",
                "title": f"Guide #{i} for {audience}",
                "search_intent": "commercial investigation",
                "brief": f"Cover practical buying guidance for {audience} evaluating {seed_keyword} options.",
            }
            for i in range(1, cluster_size + 1)
        ]
