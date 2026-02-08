"""Article filtering and relevance scoring."""
from typing import List
import re
from datetime import datetime, timedelta

from src.models.article import Article
from src.config.settings import settings
from src.utils.logger import logger


class ArticleFilter:
    """Filters and ranks articles by relevance."""

    def __init__(self):
        """Initialize the filter."""
        self.include_keywords = [kw.lower() for kw in settings.include_keywords]
        self.exclude_keywords = [kw.lower() for kw in settings.exclude_keywords]
        self.max_articles = settings.max_articles
        self.min_score = settings.min_relevance_score

        # Source reputation scores (higher = more reputable)
        self.source_reputation = {
            'mit': 2.0,
            'ieee': 2.0,
            'arxiv': 1.5,
            'openai': 1.5,
            'deepmind': 1.5,
            'google ai': 1.5,
            'wired': 1.0,
            'techcrunch': 1.0,
            'venturebeat': 1.0,
        }

    def _calculate_keyword_score(self, text: str) -> float:
        """
        Calculate keyword match score for text.

        Args:
            text: Text to score (title or description)

        Returns:
            Score based on keyword matches
        """
        if not text:
            return 0.0

        text_lower = text.lower()
        score = 0.0

        # Check include keywords
        for keyword in self.include_keywords:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                score += 1.0

        return score

    def _get_source_reputation_score(self, source_name: str) -> float:
        """
        Get reputation score for a source.

        Args:
            source_name: Name of the source

        Returns:
            Reputation score (0-2)
        """
        source_lower = source_name.lower()

        for key, score in self.source_reputation.items():
            if key in source_lower:
                return score

        return 0.5  # Default score for unknown sources

    def _should_exclude(self, article: Article) -> bool:
        """
        Check if article should be excluded based on exclude keywords.

        Args:
            article: Article to check

        Returns:
            True if article should be excluded
        """
        text = f"{article.title} {article.description or ''}".lower()

        for keyword in self.exclude_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                logger.debug(f"Excluding article due to keyword '{keyword}': {article.title[:50]}...")
                return True

        return False

    def _get_recency_boost(self, article: Article) -> float:
        """
        Calculate recency boost based on article age.

        Args:
            article: Article to evaluate

        Returns:
            Boost multiplier (1.0 to recency_weight)
        """
        if not article.published_at:
            return 1.0

        now = datetime.now(article.published_at.tzinfo) if article.published_at.tzinfo else datetime.now()
        age_hours = (now - article.published_at).total_seconds() / 3600

        # Articles within 24 hours get full boost
        if age_hours <= 24:
            return settings.recency_weight
        # Articles within 48 hours get partial boost
        elif age_hours <= 48:
            return 1.0 + (settings.recency_weight - 1.0) * 0.5
        # Older articles get no boost
        else:
            return 1.0

    def calculate_relevance_score(self, article: Article) -> float:
        """
        Calculate relevance score for an article.

        Scoring:
        - Title keyword match: +3 points per keyword
        - Description keyword match: +1 point per keyword
        - Source reputation: +0-2 points
        - Recency boost: 1.0x to 2.0x multiplier

        Args:
            article: Article to score

        Returns:
            Relevance score
        """
        score = 0.0

        # Title keywords (weighted higher)
        title_score = self._calculate_keyword_score(article.title)
        score += title_score * 3.0

        # Description keywords
        description_score = self._calculate_keyword_score(article.description or "")
        score += description_score * 1.0

        # Source reputation bonus
        reputation_score = self._get_source_reputation_score(article.source)
        score += reputation_score

        # Apply recency boost
        recency_boost = self._get_recency_boost(article)
        score *= recency_boost

        return score

    def filter_and_rank(self, articles: List[Article]) -> List[Article]:
        """
        Filter articles by relevance and return top N ranked by score.

        Args:
            articles: List of articles to filter

        Returns:
            Filtered and ranked list of articles
        """
        logger.info(f"Filtering and ranking {len(articles)} articles...")

        # First pass: exclude articles with exclude keywords
        filtered = [a for a in articles if not self._should_exclude(a)]
        logger.info(f"After exclusion filter: {len(filtered)} articles")

        if not filtered:
            logger.warning("No articles passed exclusion filter")
            return []

        # Second pass: filter by article age (recency)
        max_age = timedelta(days=settings.max_age_days)
        now = datetime.now()
        recent_articles = []
        for article in filtered:
            if article.published_at:
                age = now - article.published_at.replace(tzinfo=None)
                if age <= max_age:
                    recent_articles.append(article)
            else:
                # Include articles without publish date
                recent_articles.append(article)

        logger.info(f"After recency filter ({settings.max_age_days} days): {len(recent_articles)} articles")

        if not recent_articles:
            logger.warning("No recent articles found")
            return []

        # Calculate relevance scores
        for article in recent_articles:
            article.relevance_score = self.calculate_relevance_score(article)

        # Filter by minimum score
        scored_articles = [a for a in recent_articles if a.relevance_score >= self.min_score]
        logger.info(f"After minimum score filter ({self.min_score}): {len(scored_articles)} articles")

        if not scored_articles:
            logger.warning("No articles passed minimum score threshold")
            return []

        # Sort by relevance score (descending)
        ranked_articles = sorted(scored_articles, key=lambda x: x.relevance_score, reverse=True)

        # Take top N articles
        top_articles = ranked_articles[:self.max_articles]

        logger.info(f"Returning top {len(top_articles)} articles")
        logger.info(f"Score range: {top_articles[0].relevance_score:.2f} - "
                   f"{top_articles[-1].relevance_score:.2f}")

        return top_articles

    def group_by_category(self, articles: List[Article]) -> dict:
        """
        Group articles by category.

        Args:
            articles: List of articles to group

        Returns:
            Dictionary with categories as keys and article lists as values
        """
        grouped = {
            'top': [],
            'ai': [],
            'robotics': [],
            'research': []
        }

        # Top stories (first 5 highest scoring)
        grouped['top'] = articles[:5]

        # Group by category
        for article in articles:
            if article.category in grouped:
                grouped[article.category].append(article)

        return grouped
