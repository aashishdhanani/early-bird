"""Deduplication of articles."""
import json
from datetime import datetime, timedelta
from typing import List, Set
from pathlib import Path
from Levenshtein import ratio

from src.models.article import Article
from src.config.settings import settings
from src.utils.logger import logger


class Deduplicator:
    """Removes duplicate and near-duplicate articles."""

    def __init__(self):
        """Initialize deduplicator."""
        self.cache_file = settings.deduplication_cache_file
        self.similarity_threshold = settings.similarity_threshold
        self.lookback_days = settings.lookback_days
        self.seen_hashes: Set[str] = set()
        self._load_cache()

    def _load_cache(self):
        """Load previously seen article hashes from cache file."""
        if not self.cache_file.exists():
            logger.info("No deduplication cache found, starting fresh")
            return

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            # Remove entries older than lookback_days
            cutoff_date = datetime.now() - timedelta(days=self.lookback_days)

            for hash_value, timestamp_str in cache_data.items():
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp >= cutoff_date:
                        self.seen_hashes.add(hash_value)
                except Exception as e:
                    logger.warning(f"Error parsing cache timestamp: {e}")
                    continue

            logger.info(f"Loaded {len(self.seen_hashes)} cached article hashes")

        except json.JSONDecodeError as e:
            logger.error(f"Error reading cache file: {e}")
            self.seen_hashes = set()
        except Exception as e:
            logger.error(f"Unexpected error loading cache: {e}")
            self.seen_hashes = set()

    def _save_cache(self, articles: List[Article]):
        """Save article hashes to cache file."""
        try:
            # Load existing cache
            cache_data = {}
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, 'r') as f:
                        cache_data = json.load(f)
                except:
                    cache_data = {}

            # Add new articles to cache
            now = datetime.now().isoformat()
            for article in articles:
                cache_data[article.hash] = now

            # Remove old entries
            cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
            cache_data = {
                hash_val: timestamp
                for hash_val, timestamp in cache_data.items()
                if datetime.fromisoformat(timestamp) >= cutoff_date
            }

            # Save to file
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"Saved {len(cache_data)} hashes to cache")

        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _is_similar(self, title1: str, title2: str) -> bool:
        """
        Check if two titles are similar using Levenshtein distance.

        Args:
            title1: First title
            title2: Second title

        Returns:
            True if titles are similar above threshold
        """
        # Normalize titles
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        # Calculate similarity ratio (0.0 to 1.0)
        similarity = ratio(t1, t2)

        return similarity >= self.similarity_threshold

    def deduplicate(self, articles: List[Article]) -> List[Article]:
        """
        Remove exact duplicates and near-duplicates from articles.

        Args:
            articles: List of articles to deduplicate

        Returns:
            Deduplicated list of articles
        """
        if not settings.deduplication_enabled:
            logger.info("Deduplication disabled, skipping")
            return articles

        logger.info(f"Deduplicating {len(articles)} articles...")

        unique_articles = []
        current_hashes = set()
        seen_titles = []

        for article in articles:
            # Check for exact duplicate (by hash)
            if article.hash in self.seen_hashes or article.hash in current_hashes:
                logger.debug(f"Exact duplicate found: {article.title[:50]}...")
                continue

            # Check for near-duplicate (by title similarity)
            is_duplicate = False
            for seen_title in seen_titles:
                if self._is_similar(article.title, seen_title):
                    logger.debug(f"Near-duplicate found: {article.title[:50]}...")
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_articles.append(article)
                current_hashes.add(article.hash)
                seen_titles.append(article.title)

        logger.info(f"Removed {len(articles) - len(unique_articles)} duplicates, "
                   f"{len(unique_articles)} unique articles remain")

        # Save new hashes to cache
        self._save_cache(unique_articles)

        return unique_articles
