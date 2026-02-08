"""HTML email composer using Jinja2 templates."""
from datetime import datetime
from pathlib import Path
from typing import List
from jinja2 import Environment, FileSystemLoader, select_autoescape
from bs4 import BeautifulSoup

from src.models.article import Article
from src.processors.filter import ArticleFilter
from src.utils.logger import logger


class HTMLBuilder:
    """Builds HTML email content from articles."""

    def __init__(self):
        """Initialize the HTML builder."""
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.filter = ArticleFilter()

    def build_html(self, articles: List[Article]) -> str:
        """
        Build HTML email from articles.

        Args:
            articles: List of filtered and ranked articles

        Returns:
            HTML string
        """
        logger.info(f"Building HTML email with {len(articles)} articles...")

        # Group articles by category
        grouped_articles = self.filter.group_by_category(articles)

        # Prepare context for template
        context = {
            'date': datetime.now().strftime("%B %d, %Y"),
            'article_count': len(articles),
            'grouped_articles': grouped_articles,
        }

        # Render template
        template = self.env.get_template('newsletter.html')
        html = template.render(**context)

        logger.info("HTML email built successfully")
        return html

    def build_plain_text(self, articles: List[Article]) -> str:
        """
        Build plain text version of the email.

        Args:
            articles: List of filtered and ranked articles

        Returns:
            Plain text string
        """
        logger.info(f"Building plain text email with {len(articles)} articles...")

        lines = []
        lines.append("=" * 70)
        lines.append("EARLY BIRD - Your Daily AI & Robotics Digest")
        lines.append("=" * 70)
        lines.append("")
        lines.append(datetime.now().strftime("%B %d, %Y"))
        lines.append(f"{len(articles)} articles curated for you")
        lines.append("")

        # Group articles
        grouped_articles = self.filter.group_by_category(articles)

        # Top Stories
        if grouped_articles['top']:
            lines.append("-" * 70)
            lines.append("TOP STORIES")
            lines.append("-" * 70)
            lines.append("")
            for article in grouped_articles['top']:
                lines.extend(self._format_article_plain(article))

        # AI News
        ai_articles = [a for a in grouped_articles['ai'] if a not in grouped_articles['top']]
        if ai_articles:
            lines.append("-" * 70)
            lines.append("AI NEWS")
            lines.append("-" * 70)
            lines.append("")
            for article in ai_articles:
                lines.extend(self._format_article_plain(article))

        # Robotics News
        robotics_articles = [a for a in grouped_articles['robotics'] if a not in grouped_articles['top']]
        if robotics_articles:
            lines.append("-" * 70)
            lines.append("ROBOTICS NEWS")
            lines.append("-" * 70)
            lines.append("")
            for article in robotics_articles:
                lines.extend(self._format_article_plain(article))

        # Research Papers
        research_articles = [a for a in grouped_articles['research'] if a not in grouped_articles['top']]
        if research_articles:
            lines.append("-" * 70)
            lines.append("RESEARCH PAPERS")
            lines.append("-" * 70)
            lines.append("")
            for article in research_articles:
                lines.extend(self._format_article_plain(article))

        # Footer
        lines.append("=" * 70)
        lines.append("Early Bird - Your daily AI & robotics news aggregator")
        lines.append(f"Delivered on {datetime.now().strftime('%B %d, %Y')}")
        lines.append("=" * 70)

        plain_text = "\n".join(lines)
        logger.info("Plain text email built successfully")
        return plain_text

    def _format_article_plain(self, article: Article) -> List[str]:
        """
        Format a single article for plain text.

        Args:
            article: Article to format

        Returns:
            List of formatted lines
        """
        lines = []

        # Title
        lines.append(f"[{article.source}] {article.get_clean_title()}")

        # Meta info
        meta_parts = [
            article.category.upper(),
            article.get_time_ago()
        ]
        if article.relevance_score > 0:
            meta_parts.append(f"Score: {article.relevance_score:.1f}")
        lines.append(" | ".join(meta_parts))

        # Description
        if article.description:
            lines.append("")
            lines.append(article.description)

        # URL
        lines.append("")
        lines.append(f"Read more: {article.url}")
        lines.append("")

        return lines

    def preview_html(self, html: str, output_path: Path = None):
        """
        Save HTML to file for preview.

        Args:
            html: HTML string
            output_path: Optional output path (defaults to preview.html in project root)
        """
        if output_path is None:
            output_path = Path(__file__).parent.parent.parent / "preview.html"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"HTML preview saved to {output_path}")
