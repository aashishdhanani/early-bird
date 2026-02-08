# Gmail API Setup Guide

This guide will help you set up Gmail API for Early Bird so you can send emails **without needing an app-specific password**.

## Why Gmail API?

- ✅ **No app password needed** - Uses OAuth2 instead
- ✅ **More secure** - You authorize the app once
- ✅ **More reliable** - Better deliverability than SMTP
- ✅ **Free forever** - No limits for personal use

## Setup Steps (10 minutes)

### Step 1: Enable Gmail API in Google Cloud Console

1. **Go to Google Cloud Console**:
   - Visit: https://console.cloud.google.com/

2. **Create a new project** (or use existing):
   - Click the project dropdown at the top
   - Click "New Project"
   - Name it: "Early Bird"
   - Click "Create"

3. **Enable Gmail API**:
   - Make sure your "Early Bird" project is selected
   - Go to: https://console.cloud.google.com/apis/library
   - Search for "Gmail API"
   - Click on "Gmail API"
   - Click "Enable"

### Step 2: Create OAuth Credentials

1. **Configure OAuth Consent Screen**:
   - Go to: https://console.cloud.google.com/apis/credentials/consent
   - Select "External" user type
   - Click "Create"
   - Fill in required fields:
     - App name: "Early Bird News Aggregator"
     - User support email: your_email@gmail.com
     - Developer contact: your_email@gmail.com
   - Click "Save and Continue"
   - Skip "Scopes" (click "Save and Continue")
   - Add yourself as a test user:
     - Click "Add Users"
     - Enter: aashishd2004@gmail.com
     - Click "Add"
   - Click "Save and Continue"
   - Click "Back to Dashboard"

2. **Create OAuth Client ID**:
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Early Bird Desktop"
   - Click "Create"
   - **Download the JSON file** - This is important!
   - Click "Download JSON" or the download icon

3. **Save credentials file**:
   - Rename the downloaded file to `credentials.json`
   - Move it to your Early Bird project folder:
     ```bash
     mv ~/Downloads/client_secret_*.json /Users/aashishd/Desktop/early-bird/credentials.json
     ```

### Step 3: Configure Early Bird

Your `.env` file is already configured to use Gmail API:

```bash
EMAIL_METHOD=gmail_api
EMAIL_RECIPIENT=aashishd2004@gmail.com
```

### Step 4: Run First-Time Authentication

1. **Run the test email command**:
   ```bash
   cd /Users/aashishd/Desktop/early-bird
   source .venv/bin/activate
   python main.py --test-email
   ```

2. **Browser will open automatically**:
   - You'll see: "Google hasn't verified this app"
   - Click "Advanced"
   - Click "Go to Early Bird News Aggregator (unsafe)"
   - This is safe - it's your own app!

3. **Grant permissions**:
   - Sign in with: aashishd2004@gmail.com
   - Click "Continue" to grant Gmail send permissions
   - You should see "The authentication flow has completed"

4. **Check your inbox**:
   - You should receive a test email from yourself
   - Subject: "Early Bird - Gmail API Test"

### Step 5: You're Done! 🎉

The app is now authenticated and will remember your credentials in `token.pickle`. You won't need to authenticate again unless:
- You delete `token.pickle`
- The token expires (rare, only after long inactivity)
- You revoke access in your Google account

## Testing

Run a full test:
```bash
python main.py --run-now
```

This will:
1. Collect articles from RSS feeds
2. Filter and rank them
3. Send you a digest email

## Troubleshooting

### "credentials.json not found"
- Make sure you downloaded the OAuth client credentials
- Rename it to `credentials.json`
- Place it in the project root directory

### "Access blocked: Early Bird has not completed verification"
- You need to add yourself as a test user in OAuth consent screen
- Go to: https://console.cloud.google.com/apis/credentials/consent
- Under "Test users", add your email

### "Token has been expired or revoked"
- Delete `token.pickle`
- Run `python main.py --test-email` again to re-authenticate

### Browser doesn't open automatically
- The console will show a URL
- Copy and paste it into your browser manually

## Security Notes

- `credentials.json` contains your OAuth client ID (not sensitive, but don't share)
- `token.pickle` contains your access token (keep private!)
- Both files are excluded from git via `.gitignore`
- You can revoke access anytime at: https://myaccount.google.com/permissions

## Switching Back to SMTP

If you want to use SendGrid or Gmail SMTP instead:

1. Edit `.env`:
   ```bash
   EMAIL_METHOD=smtp
   ```

2. Configure SMTP credentials (see README.md)

## Support

If you encounter issues:
1. Check the logs: `tail -f logs/earlybird.log`
2. Verify credentials.json is in the right place
3. Make sure Gmail API is enabled in Google Cloud Console
4. Confirm you're added as a test user in OAuth consent screen
