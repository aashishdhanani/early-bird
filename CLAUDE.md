# CLAUDE.md - Early Bird Architecture & Development Guide

This document provides a comprehensive overview of the Early Bird codebase architecture, key components, and development workflows.

## Architecture Overview

Early Bird follows a **modular monolith** architecture for simplicity and maintainability. The application is organized into distinct modules with clear responsibilities:

```
Pipeline Flow:
Collect → Deduplicate → Filter → Compose → Send
```

### Core Modules

#### 1. **Collectors** (`src/collectors/`)
Responsible for fetching articles from RSS feeds.

- `rss_collector.py`:
  - `RSSCollector` class fetches from 15+ RSS sources
  - Uses `feedparser` library with 5-second timeout
  - Handles network errors gracefully
  - Extracts: title, description, URL, published date, images
  - Cleans HTML from descriptions using BeautifulSoup

**Key Methods:**
- `collect_from_source(feed_url, source_name, category)` - Fetch from single source
- `collect_all()` - Fetch from all enabled sources in config

#### 2. **Processors** (`src/processors/`)
Handles deduplication and relevance filtering.

- `deduplicator.py`:
  - Removes exact duplicates using MD5 hash (title + URL)
  - Fuzzy matching for near-duplicates (85% Levenshtein similarity)
  - Maintains cache of seen articles (7-day lookback)
  - Cache stored in `cache/seen_articles.json`

- `filter.py`:
  - Keyword-based relevance scoring
  - Scoring formula:
    - Title keyword match: +3 points per keyword
    - Description keyword match: +1 point per keyword
    - Source reputation bonus: +0.5 to +2 points
  - Filters by minimum score threshold
  - Returns top N articles (default: 20)
  - Groups articles by category (top/ai/robotics/research)

**Source Reputation Scores:**
- MIT, IEEE, ArXiv: 2.0 points
- OpenAI, DeepMind, Google AI: 1.5 points
- TechCrunch, Wired, VentureBeat: 1.0 points
- Unknown sources: 0.5 points

#### 3. **Composers** (`src/composers/`)
Generates HTML and plain text email content.

- `html_builder.py`:
  - Uses Jinja2 templating engine
  - Renders `templates/newsletter.html`
  - Groups articles by category
  - Formats timestamps as relative ("2 hours ago")
  - Generates both HTML and plain text versions
  - Saves preview.html for testing

- `templates/newsletter.html`:
  - Responsive design with inline CSS
  - Sections: Top Stories, AI News, Robotics News, Research Papers
  - Mobile-friendly (media queries for <600px)
  - Email client compatible (Gmail, Outlook, Apple Mail tested)

#### 4. **Senders** (`src/senders/`)
Handles email delivery via Gmail SMTP.

- `email_sender.py`:
  - Gmail SMTP configuration (smtp.gmail.com:587)
  - TLS encryption enabled
  - Retry logic: 3 attempts with 5-second delays
  - Sends multipart emails (HTML + plain text fallback)
  - Proper email headers (From, To, Subject, Date)

**Methods:**
- `send_email(recipient, subject, html_content, plain_text_content)` - Generic send
- `send_digest(html, plain_text, article_count, date)` - Send daily digest
- `send_test_email()` - Configuration verification

#### 5. **Scheduler** (`src/scheduler/`)
Daily execution scheduling.

- `job_scheduler.py`:
  - Uses APScheduler with CronTrigger
  - Runs at configured time and timezone
  - Graceful shutdown on SIGINT/SIGTERM
  - Blocking scheduler (runs indefinitely)

**Methods:**
- `schedule_daily()` - Set up daily cron job
- `start()` - Start scheduler (blocking)
- `stop()` - Graceful shutdown
- `run_immediately()` - Execute pipeline once

#### 6. **Models** (`src/models/`)
Data structures using Pydantic.

- `article.py`:
  - `Article` class with validation
  - Fields: title, description, url, published_at, source, category, image_url, hash, relevance_score
  - Methods:
    - `generate_hash()` - MD5 hash for deduplication
    - `get_clean_title()` - Sanitized title
    - `get_time_ago()` - Relative timestamp

#### 7. **Config** (`src/config/`)
Configuration management.

- `settings.py`:
  - Loads `config.yaml` and `.env`
  - Global `settings` singleton
  - Properties for all configuration values
  - Validates required settings at startup
  - Provides helper methods (e.g., `get_feeds_by_category()`)

#### 8. **Utils** (`src/utils/`)
Shared utilities.

- `logger.py`:
  - Configured logger with dual output (console + file)
  - Rotating file handler (10MB, 5 backups)
  - Log file: `logs/earlybird.log`
  - Format: `YYYY-MM-DD HH:MM:SS - name - LEVEL - message`

## Configuration Files

### `config.yaml`
Main configuration file containing:
- Email settings (SMTP configuration)
- Schedule settings (time, timezone)
- RSS feed sources (15+ feeds with enable/disable flags)
- Filtering rules (include/exclude keywords, thresholds)
- Collection settings (timeouts, limits)

### `.env`
Environment variables (secrets):
- `EMAIL_RECIPIENT` - Where to send digests
- `EMAIL_PASSWORD` - Gmail app-specific password
- `EMAIL_SENDER` - Gmail address to send from

## Entry Point

### `main.py`
CLI application with three modes:

1. **`--run-now`**: Execute pipeline immediately (for testing)
2. **`--schedule`**: Start scheduler (production mode)
3. **`--test-email`**: Verify email configuration

**Pipeline Function** (`run_pipeline()`):
```python
1. Collect articles (RSSCollector)
2. Deduplicate (Deduplicator)
3. Filter & rank (ArticleFilter)
4. Compose email (HTMLBuilder)
5. Send email (EmailSender)
```

## Key Files & Their Purposes

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `main.py` | Entry point, CLI, pipeline orchestration | `run_pipeline()`, `main()` |
| `src/collectors/rss_collector.py` | RSS feed fetching | `RSSCollector` |
| `src/processors/deduplicator.py` | Duplicate removal | `Deduplicator` |
| `src/processors/filter.py` | Relevance scoring | `ArticleFilter` |
| `src/composers/html_builder.py` | Email generation | `HTMLBuilder` |
| `src/senders/email_sender.py` | Email delivery | `EmailSender` |
| `src/scheduler/job_scheduler.py` | Scheduling | `JobScheduler` |
| `src/models/article.py` | Data models | `Article` |
| `src/config/settings.py` | Configuration | `Settings` |
| `src/utils/logger.py` | Logging | `setup_logger()` |

## Development Commands

### Testing
```bash
# Run full pipeline immediately
python main.py --run-now

# Send test email
python main.py --test-email

# View generated HTML
open preview.html

# Watch logs
tail -f logs/earlybird.log

# Check for errors in logs
grep ERROR logs/earlybird.log
```

### Adding a New RSS Source

1. Find RSS feed URL (usually `/feed`, `/rss`, or `/feed.xml`)
2. Add to `config.yaml`:
```yaml
sources:
  rss_feeds:
    - name: "Source Name"
      url: "https://example.com/feed"
      category: "ai"  # or "robotics" or "research"
      enabled: true
```
3. Test: `python main.py --run-now`
4. Check logs for errors: `tail logs/earlybird.log`

### Customizing Filters

Edit `config.yaml`:
```yaml
filtering:
  keywords:
    include:
      - "new keyword"
    exclude:
      - "spam keyword"
  max_articles: 25  # Change max articles
  min_relevance_score: 1.0  # Increase threshold
```

### Modifying Email Template

1. Edit `src/composers/templates/newsletter.html`
2. Test with: `python main.py --run-now`
3. Preview: `open preview.html`
4. Verify in Gmail (desktop + mobile)

## Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| feedparser | RSS feed parsing | 6.0.10+ |
| apscheduler | Job scheduling | 3.10.4+ |
| jinja2 | Template rendering | 3.1.2+ |
| pyyaml | YAML config parsing | 6.0.1+ |
| python-dotenv | Environment variables | 1.0.0+ |
| pydantic | Data validation | 2.5.0+ |
| beautifulsoup4 | HTML cleaning | 4.12.2+ |
| lxml | XML parsing | 4.9.3+ |
| requests | HTTP requests | 2.31.0+ |
| python-dateutil | Date parsing | 2.8.2+ |
| python-Levenshtein | Fuzzy string matching | 0.23.0+ |

## Error Handling

### Network Errors
- RSS collection has 5-second timeout per feed
- Failed feeds don't block pipeline (logged as errors)
- Email sender retries 3 times with exponential backoff

### Configuration Errors
- Settings validates required keys on startup
- Missing `.env` values raise clear error messages
- Invalid RSS feeds logged but don't crash pipeline

### Empty Results
- Pipeline handles gracefully if no articles collected
- Won't send empty emails
- Logs warnings at each stage

## Logging Strategy

**Log Levels:**
- `INFO`: Normal operation (collection progress, article counts)
- `WARNING`: Recoverable issues (bad feed, no articles)
- `ERROR`: Failures (network errors, email send failure)
- `DEBUG`: Detailed info (duplicate detection, scoring)

**Key Log Messages:**
- "Collected N articles from [source]"
- "Removed N duplicates, N unique articles remain"
- "Returning top N articles"
- "Email sent successfully to [recipient]"

## Testing Checklist

Before deploying:
- [ ] Test email delivery: `python main.py --test-email`
- [ ] Run full pipeline: `python main.py --run-now`
- [ ] Check preview.html renders correctly
- [ ] Verify all RSS feeds accessible (check logs)
- [ ] Confirm deduplication working (run twice, check cache)
- [ ] Test email in Gmail (desktop + mobile)
- [ ] Verify scheduler timing: `python main.py --schedule` (check logs for next run time)

## Performance Considerations

### Collection Phase
- Parallel RSS fetching could be added (currently sequential)
- 5-second timeout prevents slow feeds from blocking
- Typical collection time: 30-60 seconds for 15 feeds

### Deduplication
- Cache file grows ~1KB per 100 articles
- Old entries pruned after 7 days automatically
- In-memory fuzzy matching O(n²) but fast for n < 200

### Filtering
- Keyword matching uses regex with word boundaries
- Sorting by score is O(n log n) - negligible for n < 200

### Email Generation
- Jinja2 rendering < 1 second for typical digest
- Preview HTML saved to disk for debugging

## Future Enhancements

Potential improvements (not yet implemented):
1. **Images**: Add article thumbnails to email
2. **AI Summaries**: Use OpenAI API for article summaries
3. **Twitter Integration**: Fetch from Twitter/X API
4. **Web UI**: Configuration dashboard
5. **Multi-user**: Support multiple recipients with preferences
6. **Analytics**: Track clicks and engagement
7. **Weekly Digest**: Optional weekly roundup
8. **Read Later**: Integration with Pocket/Instapaper
9. **Async Collection**: Parallel RSS fetching with asyncio
10. **Database**: Store articles for historical search

## Troubleshooting Tips

### "No module named src"
- Make sure you're running from project root
- Activate virtual environment: `source .venv/bin/activate`

### "EMAIL_PASSWORD not configured"
- Check `.env` file exists and has correct values
- Ensure using app-specific password, not regular Gmail password

### "SMTP authentication failed"
- Enable 2FA on Gmail account
- Generate new app-specific password
- Check email/password in `.env` are correct

### Scheduler not running at expected time
- Verify timezone in `config.yaml` matches your location
- Check time format is "HH:MM" (24-hour)
- Look for "Next run" in logs when starting scheduler

### Articles seem irrelevant
- Lower `min_relevance_score` in `config.yaml`
- Add more specific keywords to `include` list
- Check logs for relevance scores of filtered articles

## Code Style

- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Docstrings for all classes and public methods
- Keep functions focused (single responsibility)
- Log important actions and errors
- Handle exceptions gracefully

## Contact

For questions about the codebase, create an issue on GitHub with the "question" label.

---

Last updated: 2026-02-08
