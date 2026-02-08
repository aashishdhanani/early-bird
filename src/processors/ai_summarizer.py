"""AI-powered article summarization."""
import os
from typing import List, Optional
import requests

from src.models.article import Article
from src.config.settings import settings
from src.utils.logger import logger


class AISummarizer:
    """Generates intelligent summaries using AI."""

    def __init__(self):
        """Initialize AI summarizer."""
        self.enabled = settings.ai_summaries_enabled
        self.provider = settings.ai_provider
        self.model = settings.ai_model
        self.api_key = os.getenv('OPENAI_API_KEY')

        if self.enabled and not self.api_key:
            logger.warning("AI summaries enabled but OPENAI_API_KEY not found in .env")
            self.enabled = False

    def summarize_article(self, article: Article) -> Optional[str]:
        """
        Generate an AI summary for an article.

        Args:
            article: Article to summarize

        Returns:
            Enhanced summary or None if generation fails
        """
        if not self.enabled:
            return article.description

        try:
            prompt = self._build_prompt(article)
            summary = self._call_openai(prompt)

            if summary:
                logger.info(f"Generated AI summary for: {article.title[:50]}...")
                return summary
            else:
                return article.description

        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return article.description

    def _build_prompt(self, article: Article) -> str:
        """Build prompt for AI summarization."""
        return f"""You are an AI/Robotics news analyst. Summarize this article in 2-3 concise sentences.

Focus on:
1. What happened or was announced
2. Why it matters for AI/robotics
3. Key implications or impact

Article Title: {article.title}
Article Description: {article.description or 'No description available'}
Source: {article.source}

Provide a clear, insightful summary that helps readers understand the significance without reading the full article. Be specific and avoid generic statements."""

    def _call_openai(self, prompt: str) -> Optional[str]:
        """
        Call OpenAI API to generate summary.

        Args:
            prompt: Prompt text

        Returns:
            Generated summary or None
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a technical news analyst specializing in AI and robotics. Provide clear, insightful summaries that highlight key developments and their implications.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 200
            }

            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                summary = result['choices'][0]['message']['content'].strip()
                return summary
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None

    def batch_summarize(self, articles: List[Article]) -> List[Article]:
        """
        Generate summaries for multiple articles.

        Args:
            articles: List of articles to summarize

        Returns:
            Articles with enhanced descriptions
        """
        if not self.enabled:
            logger.info("AI summaries disabled, using original descriptions")
            return articles

        logger.info(f"Generating AI summaries for {len(articles)} articles...")

        for i, article in enumerate(articles, 1):
            logger.info(f"Summarizing article {i}/{len(articles)}")
            enhanced_summary = self.summarize_article(article)
            if enhanced_summary:
                article.description = enhanced_summary

        logger.info("AI summarization complete")
        return articles
