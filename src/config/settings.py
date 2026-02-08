"""Configuration management for Early Bird."""
import os
from pathlib import Path
from typing import Any, Dict, List
import yaml
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from config.yaml and .env"""

    def __init__(self, config_path: str = None):
        """Initialize settings from config file."""
        if config_path is None:
            # Default to config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yaml"

        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _validate_config(self):
        """Validate required configuration keys exist."""
        required_keys = ['email', 'schedule', 'sources', 'filtering']
        for key in required_keys:
            if key not in self._config:
                raise ValueError(f"Missing required config key: {key}")

    # Email settings
    @property
    def email_sender(self) -> str:
        """Get sender email from environment or config."""
        return os.getenv('EMAIL_SENDER', self._config['email']['sender'])

    @property
    def email_recipient(self) -> str:
        """Get recipient email from environment."""
        recipient = os.getenv('EMAIL_RECIPIENT')
        if not recipient or recipient == 'your_email@example.com':
            raise ValueError("EMAIL_RECIPIENT not configured in .env file")
        return recipient

    @property
    def email_password(self) -> str:
        """Get email password/API key from environment (supports both Gmail and SendGrid)."""
        # Try SendGrid API key first
        api_key = os.getenv('SENDGRID_API_KEY')
        if api_key and api_key != 'your_sendgrid_api_key_here':
            return api_key

        # Fall back to EMAIL_PASSWORD for Gmail
        password = os.getenv('EMAIL_PASSWORD')
        if password and password != 'your_app_specific_password_here':
            return password

        raise ValueError("Neither SENDGRID_API_KEY nor EMAIL_PASSWORD configured in .env file")

    @property
    def is_sendgrid(self) -> bool:
        """Check if using SendGrid (vs Gmail)."""
        return 'sendgrid' in self.smtp_host.lower()

    @property
    def smtp_host(self) -> str:
        return self._config['email']['smtp']['host']

    @property
    def smtp_port(self) -> int:
        return self._config['email']['smtp']['port']

    @property
    def smtp_use_tls(self) -> bool:
        return self._config['email']['smtp']['use_tls']

    @property
    def email_subject_prefix(self) -> str:
        return self._config['email']['subject_prefix']

    # Schedule settings
    @property
    def schedule_time(self) -> str:
        """Get scheduled time (HH:MM format)."""
        return self._config['schedule']['time']

    @property
    def schedule_timezone(self) -> str:
        """Get timezone (e.g., 'America/Chicago')."""
        return self._config['schedule']['timezone']

    @property
    def schedule_enabled(self) -> bool:
        """Check if scheduling is enabled."""
        return self._config['schedule']['enabled']

    # RSS sources
    @property
    def rss_feeds(self) -> List[Dict[str, Any]]:
        """Get list of enabled RSS feeds."""
        all_feeds = self._config['sources']['rss_feeds']
        return [feed for feed in all_feeds if feed.get('enabled', True)]

    def get_feeds_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get RSS feeds filtered by category."""
        return [feed for feed in self.rss_feeds if feed.get('category') == category]

    # Filtering settings
    @property
    def include_keywords(self) -> List[str]:
        """Get keywords to include in filtering."""
        return self._config['filtering']['keywords']['include']

    @property
    def exclude_keywords(self) -> List[str]:
        """Get keywords to exclude in filtering."""
        return self._config['filtering']['keywords']['exclude']

    @property
    def max_articles(self) -> int:
        """Get maximum number of articles to include in digest."""
        return self._config['filtering']['max_articles']

    @property
    def min_relevance_score(self) -> float:
        """Get minimum relevance score threshold."""
        return self._config['filtering']['min_relevance_score']

    @property
    def recency_weight(self) -> float:
        """Get recency weight multiplier for scoring."""
        return self._config['filtering'].get('recency_weight', 1.0)

    @property
    def max_age_days(self) -> int:
        """Get maximum article age in days."""
        return self._config['filtering'].get('max_age_days', 7)

    @property
    def deduplication_enabled(self) -> bool:
        """Check if deduplication is enabled."""
        return self._config['filtering']['deduplication']['enabled']

    @property
    def similarity_threshold(self) -> float:
        """Get similarity threshold for fuzzy deduplication."""
        return self._config['filtering']['deduplication']['similarity_threshold']

    @property
    def lookback_days(self) -> int:
        """Get number of days to look back for deduplication."""
        return self._config['filtering']['deduplication']['lookback_days']

    # Collection settings
    @property
    def collection_timeout(self) -> int:
        """Get timeout in seconds for RSS collection."""
        return self._config['collection']['timeout_seconds']

    @property
    def max_articles_per_source(self) -> int:
        """Get maximum articles to collect per source."""
        return self._config['collection']['max_articles_per_source']

    # Paths
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @property
    def cache_dir(self) -> Path:
        """Get cache directory path."""
        cache = self.project_root / "cache"
        cache.mkdir(exist_ok=True)
        return cache

    @property
    def logs_dir(self) -> Path:
        """Get logs directory path."""
        logs = self.project_root / "logs"
        logs.mkdir(exist_ok=True)
        return logs

    @property
    def deduplication_cache_file(self) -> Path:
        """Get deduplication cache file path."""
        return self.cache_dir / "seen_articles.json"

    # AI Summary settings
    @property
    def ai_summaries_enabled(self) -> bool:
        """Check if AI summaries are enabled."""
        return self._config.get('ai_summaries', {}).get('enabled', False)

    @property
    def ai_provider(self) -> str:
        """Get AI provider (openai or anthropic)."""
        return self._config.get('ai_summaries', {}).get('provider', 'openai')

    @property
    def ai_model(self) -> str:
        """Get AI model to use."""
        return self._config.get('ai_summaries', {}).get('model', 'gpt-4o-mini')


# Global settings instance
settings = Settings()
