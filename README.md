# 🐦 Early Bird - AI & Robotics News Aggregator

A production-ready daily news aggregator that collects AI and robotics news from 15+ premium RSS sources, filters for relevance, and delivers a beautifully formatted HTML email every day at 8:00 AM CT.

## Features

- **15+ Premium Sources**: Curates from MIT Tech Review, IEEE Spectrum, ArXiv, OpenAI, DeepMind, and more
- **Smart Filtering**: Keyword-based relevance scoring with source reputation weighting
- **Deduplication**: Removes exact and near-duplicate articles using fuzzy matching
- **Beautiful Emails**: Responsive HTML design that looks great on desktop and mobile
- **Daily Delivery**: Automated scheduling with APScheduler
- **Easy Configuration**: Simple YAML config and environment variables

## Quick Start

### Prerequisites

- Python 3.9+
- Gmail account with 2-factor authentication enabled
- App-specific password for Gmail (see setup below)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd early-bird
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

1. **Email Setup**: Edit `.env` file with your credentials:
```bash
# Your email address to receive the daily digest
EMAIL_RECIPIENT=your_email@example.com

# Gmail app-specific password
EMAIL_PASSWORD=your_app_specific_password_here

# Gmail address to send from
EMAIL_SENDER=your_gmail@gmail.com
```

**Getting a Gmail App-Specific Password:**
- Go to https://myaccount.google.com/apppasswords
- Sign in to your Google account
- Select "Mail" and your device
- Click "Generate"
- Copy the 16-character password to `.env`

2. **RSS Sources**: Edit `config.yaml` to customize:
- RSS feed sources (enable/disable feeds)
- Filtering keywords
- Schedule time and timezone
- Maximum articles per digest

### Usage

#### Test Email Configuration
```bash
python main.py --test-email
```

#### Run Immediately (for testing)
```bash
python main.py --run-now
```

#### Start Scheduler (production)
```bash
python main.py --schedule
```

### Viewing Email Preview

After running the pipeline, open `preview.html` in your browser to see how the email will look.

## Configuration Options

### RSS Sources (`config.yaml`)

The default configuration includes 15+ sources across categories:
- **AI News**: MIT Tech Review, VentureBeat, TechCrunch, AI News, The Gradient, Wired
- **Robotics**: IEEE Spectrum, The Robot Report, Robotics Business Review
- **Research**: ArXiv CS.AI, ArXiv CS.RO
- **Company Blogs**: OpenAI, DeepMind, Google AI

To add a new source:
```yaml
sources:
  rss_feeds:
    - name: "New Source"
      url: "https://example.com/feed.xml"
      category: "ai"  # or "robotics" or "research"
      enabled: true
```

### Filtering Keywords

Customize relevance scoring by editing `config.yaml`:
```yaml
filtering:
  keywords:
    include:
      - "AI"
      - "machine learning"
      - "robotics"
      # Add more keywords
    exclude:
      - "crypto"
      - "bitcoin"
      # Add keywords to exclude
  max_articles: 20
  min_relevance_score: 0.5
```

### Schedule Configuration

Change delivery time:
```yaml
schedule:
  time: "08:00"  # HH:MM format (24-hour)
  timezone: "America/Chicago"
  enabled: true
```

Available timezones: Use any IANA timezone (e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`)

## Project Structure

```
early-bird/
├── src/
│   ├── collectors/
│   │   └── rss_collector.py        # RSS feed collection
│   ├── processors/
│   │   ├── deduplicator.py         # Duplicate removal
│   │   └── filter.py               # Relevance scoring
│   ├── composers/
│   │   ├── html_builder.py         # Email generation
│   │   └── templates/
│   │       └── newsletter.html     # Email template
│   ├── senders/
│   │   └── email_sender.py         # Gmail SMTP delivery
│   ├── scheduler/
│   │   └── job_scheduler.py        # Daily scheduling
│   ├── models/
│   │   └── article.py              # Data models
│   ├── config/
│   │   └── settings.py             # Configuration loader
│   └── utils/
│       └── logger.py               # Logging
├── main.py                          # Entry point
├── config.yaml                      # Configuration
├── .env                            # Secrets
├── requirements.txt
└── logs/                           # Log files
```

## Deployment

### Running as a Background Service

#### macOS (launchd)

1. Create `~/Library/LaunchAgents/com.earlybird.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.earlybird</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/early-bird/.venv/bin/python</string>
        <string>/path/to/early-bird/main.py</string>
        <string>--schedule</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/early-bird/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/early-bird/logs/stderr.log</string>
</dict>
</plist>
```

2. Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.earlybird.plist
```

#### Linux (systemd)

1. Create `/etc/systemd/system/earlybird.service`:
```ini
[Unit]
Description=Early Bird News Aggregator
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/early-bird
ExecStart=/path/to/early-bird/.venv/bin/python /path/to/early-bird/main.py --schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable earlybird
sudo systemctl start earlybird
sudo systemctl status earlybird
```

#### Alternative: tmux/screen

```bash
# Start in tmux
tmux new -s earlybird
source .venv/bin/activate
python main.py --schedule

# Detach: Ctrl+B, then D
# Re-attach: tmux attach -t earlybird
```

## Logging

Logs are written to:
- Console (stdout)
- `logs/earlybird.log` (with rotation, max 10MB, 5 backups)

View logs:
```bash
tail -f logs/earlybird.log
```

## Troubleshooting

### Email Not Sending

1. **Check credentials**: Verify `.env` has correct email and password
2. **App-specific password**: Make sure you're using an app password, not your regular Gmail password
3. **2FA enabled**: Gmail requires 2-factor authentication for app passwords
4. **Test connection**: Run `python main.py --test-email`

### No Articles in Digest

1. **Check RSS feeds**: Some sources may be down or slow
2. **Lower minimum score**: Edit `config.yaml` and reduce `min_relevance_score`
3. **Check logs**: Look for errors in `logs/earlybird.log`
4. **Test collection**: Run `python main.py --run-now` and check `preview.html`

### Scheduler Not Running

1. **Check timezone**: Verify `schedule.timezone` in `config.yaml`
2. **Check time format**: Must be "HH:MM" in 24-hour format
3. **Enable scheduling**: Set `schedule.enabled: true` in `config.yaml`

## Development

### Running Tests

```bash
# Run immediate pipeline
python main.py --run-now

# Check preview
open preview.html

# Verify logs
tail logs/earlybird.log
```

### Adding New RSS Sources

1. Find the RSS feed URL
2. Add to `config.yaml` under `sources.rss_feeds`
3. Test: `python main.py --run-now`
4. Check logs for any errors

### Customizing Email Template

Edit `src/composers/templates/newsletter.html` to change:
- Colors and styling
- Layout and sections
- Header/footer content

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

Made with ❤️ for staying updated on AI & Robotics
