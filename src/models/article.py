"""Data models for articles."""
from datetime import datetime
from typing import Optional
import hashlib
from pydantic import BaseModel, Field, field_validator


class Article(BaseModel):
    """Represents a news article from an RSS feed."""

    title: str = Field(..., description="Article title")
    description: Optional[str] = Field(None, description="Article description/summary")
    url: str = Field(..., description="Article URL")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    source: str = Field(..., description="Source name (e.g., 'MIT Tech Review AI')")
    category: str = Field(..., description="Category: ai, robotics, or research")
    image_url: Optional[str] = Field(None, description="Article thumbnail image URL")
    hash: str = Field(default="", description="Hash for deduplication")
    relevance_score: float = Field(default=0.0, description="Relevance score from filtering")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL starts with http(s)."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v

    def generate_hash(self) -> str:
        """Generate a hash for deduplication based on title and URL."""
        content = f"{self.title.lower().strip()}{self.url}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def model_post_init(self, __context) -> None:
        """Generate hash after model initialization if not provided."""
        if not self.hash:
            self.hash = self.generate_hash()

    def get_clean_title(self) -> str:
        """Get cleaned title for display."""
        return self.title.strip()

    def get_time_ago(self) -> str:
        """Get relative time string (e.g., '2 hours ago')."""
        if not self.published_at:
            return "Recently"

        now = datetime.now(self.published_at.tzinfo)
        delta = now - self.published_at

        if delta.days > 0:
            if delta.days == 1:
                return "1 day ago"
            return f"{delta.days} days ago"

        hours = delta.seconds // 3600
        if hours > 0:
            if hours == 1:
                return "1 hour ago"
            return f"{hours} hours ago"

        minutes = delta.seconds // 60
        if minutes > 0:
            if minutes == 1:
                return "1 minute ago"
            return f"{minutes} minutes ago"

        return "Just now"

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
