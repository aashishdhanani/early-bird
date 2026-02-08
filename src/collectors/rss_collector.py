"""RSS feed collector for gathering news articles."""
from datetime import datetime
from typing import List, Optional
import feedparser
import requests
from dateutil import parser as date_parser

from src.models.article import Article
from src.config.settings import settings
from src.utils.logger import logger


class RSSCollector:
    """Collects articles from RSS feeds."""

    def __init__(self):
        """Initialize the RSS collector."""
        self.timeout = settings.collection_timeout
        self.max_articles_per_source = settings.max_articles_per_source

    def collect_from_source(self, feed_url: str, source_name: str, category: str) -> List[Article]:
        """
        Collect articles from a single RSS source.

        Args:
            feed_url: URL of the RSS feed
            source_name: Name of the source (e.g., "MIT Tech Review AI")
            category: Category of the source (ai, robotics, research)

        Returns:
            List of Article objects
        """
        articles = []

        try:
            logger.info(f"Fetching from {source_name}: {feed_url}")

            # Set timeout for feed parsing
            feed = feedparser.parse(
                feed_url,
                request_headers={'User-Agent': 'Early-Bird-News-Aggregator/1.0'}
            )

            # Check for errors
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {source_name}: {feed.bozo_exception}")

            if not feed.entries:
                logger.warning(f"No entries found in {source_name}")
                return articles

            # Process entries
            for entry in feed.entries[:self.max_articles_per_source]:
                try:
                    article = self._parse_entry(entry, source_name, category)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing entry from {source_name}: {e}")
                    continue

            logger.info(f"Collected {len(articles)} articles from {source_name}")

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {source_name}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {source_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {source_name}: {e}")

        return articles

    def _parse_entry(self, entry: dict, source_name: str, category: str) -> Optional[Article]:
        """
        Parse a single RSS entry into an Article object.

        Args:
            entry: RSS entry dictionary
            source_name: Name of the source
            category: Category of the article

        Returns:
            Article object or None if parsing fails
        """
        # Extract title (required)
        title = entry.get('title', '').strip()
        if not title:
            logger.warning(f"Entry from {source_name} missing title")
            return None

        # Extract URL (required)
        url = entry.get('link', '').strip()
        if not url:
            logger.warning(f"Entry from {source_name} missing URL")
            return None

        # Extract description/summary
        description = None
        if 'summary' in entry:
            description = entry.summary
        elif 'description' in entry:
            description = entry.description
        elif 'content' in entry and entry.content:
            description = entry.content[0].get('value', '')

        # Clean HTML tags from description
        if description:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(description, 'html.parser')
            description = soup.get_text(separator=' ', strip=True)
            # Limit description length
            if len(description) > 500:
                description = description[:497] + "..."

        # Extract published date
        published_at = None
        date_fields = ['published', 'pubDate', 'updated', 'created']
        for field in date_fields:
            if field in entry:
                try:
                    published_at = date_parser.parse(entry[field])
                    break
                except Exception as e:
                    logger.debug(f"Error parsing date from {field}: {e}")

        # If no date found, use current time
        if not published_at:
            published_at = datetime.now()

        # Extract image URL if available
        image_url = None
        if 'media_thumbnail' in entry and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get('url')
        elif 'media_content' in entry and entry.media_content:
            image_url = entry.media_content[0].get('url')
        elif 'image' in entry:
            if isinstance(entry.image, dict):
                image_url = entry.image.get('href')
            else:
                image_url = entry.image

        # Create Article object
        try:
            article = Article(
                title=title,
                description=description,
                url=url,
                published_at=published_at,
                source=source_name,
                category=category,
                image_url=image_url
            )
            return article
        except Exception as e:
            logger.error(f"Error creating Article object: {e}")
            return None

    def collect_all(self) -> List[Article]:
        """
        Collect articles from all enabled RSS feeds.

        Returns:
            List of all collected Article objects
        """
        all_articles = []

        feeds = settings.rss_feeds
        logger.info(f"Collecting from {len(feeds)} RSS feeds...")

        for feed_config in feeds:
            try:
                articles = self.collect_from_source(
                    feed_url=feed_config['url'],
                    source_name=feed_config['name'],
                    category=feed_config['category']
                )
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error collecting from {feed_config.get('name', 'unknown')}: {e}")
                continue

        logger.info(f"Total articles collected: {len(all_articles)}")
        return all_articles
