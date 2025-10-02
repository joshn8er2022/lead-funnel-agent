# Deployment Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `lead-funnel-agent`
3. Make it **Public** or **Private** (your choice)
4. Do NOT initialize with README (we already have one)
5. Click "Create repository"

## Step 2: Push Code to GitHub

From this directory, run:

```bash
cd /Users/joshisrael/Projects/lead-funnel-agent
git remote add origin https://github.com/YOUR_USERNAME/lead-funnel-agent.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 3: Add GitHub Secrets

Go to your repo: `Settings → Secrets and variables → Actions → New repository secret`

Add each of these:

```
Name: TYPEFORM_TOKEN
Value: [Your Typeform token - Josh has this]

Name: CLOSE_API_KEY
Value: [Your Close API key - Josh has this]

Name: CLOSE_CLIENT_ID
Value: [Your Close Client ID - Josh has this]

Name: CLOSE_CLIENT_SECRET
Value: [Your Close Client Secret - Josh has this]

Name: CALENDLY_TOKEN
Value: [Your Calendly token - Josh has this]

Name: SENDGRID_API_KEY
Value: [Your SendGrid API key - Josh has this]

Name: ANTHROPIC_API_KEY
Value: [Get from https://console.anthropic.com/settings/keys]

Name: TWILIO_ACCOUNT_SID
Value: [Your Twilio SID - Josh has this]

Name: TWILIO_AUTH_TOKEN
Value: [Your Twilio auth token - Josh has this]

Name: TWILIO_PHONE_NUMBER
Value: [Your Twilio phone number - Josh has this]
```

### For Slack (Need to create app first):

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "Lead Agent" and select your workspace
4. Go to "OAuth & Permissions"
5. Add these Bot Token Scopes:
   - `chat:write`
   - `app_mentions:read`
   - `channels:history`
   - `channels:read`
6. Click "Install to Workspace"
7. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
8. Add to GitHub Secrets:

```
Name: SLACK_BOT_TOKEN
Value: [Your Bot Token from step 7]

Name: SLACK_SIGNING_SECRET
Value: [From Slack App Settings → Basic Information → Signing Secret]
```

9. Invite bot to #ai-test channel:
   - In Slack, type: `/invite @Lead Agent` in #ai-test

## Step 4: Configure Typeform Webhooks

For **Hume Connect** form (F7whHyXK):

1. Open form in Typeform
2. Go to **Connect** → **Webhooks**
3. Add webhook URL:
   ```
   https://api.github.com/repos/YOUR_USERNAME/lead-funnel-agent/dispatches
   ```
4. In "Secret" add your GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Generate new token (classic)
   - Select scopes: `repo`, `workflow`
   - Copy token
5. In webhook headers, add:
   ```
   Accept: application/vnd.github.v3+json
   Authorization: Bearer YOUR_GITHUB_TOKEN
   ```
6. In the body, select "Send raw JSON" and use:
   ```json
   {
     "event_type": "typeform_submission",
     "client_payload": {
       "form_id": "F7whHyXK",
       "response_id": "{{hidden:response_id}}",
       "submitted_at": "{{submitted_at}}",
       "answers": {{answers}}
     }
   }
   ```
7. Test the webhook

Repeat for **Hume Hardware** form (wR9Ufu8Z).

## Step 5: Test the Agent

### Manual Test Run:

1. Go to your repo → **Actions** tab
2. Click "Lead Funnel Automation Agent"
3. Click "Run workflow"
4. Select `test_integrations`
5. Click "Run workflow"
6. Watch the logs - all tests should pass

### Test with Real Submission:

1. Submit a test form in Typeform
2. Check GitHub Actions - should trigger automatically
3. Check #ai-test Slack channel for notification
4. Check Close CRM for new lead

## Step 6: Monitor

The agent will now run automatically:
- **9am PT** (4pm UTC) - Morning run
- **5pm PT** (12am UTC) - Evening run

You can:
- View logs in **GitHub Actions**
- Get notifications in **#ai-test Slack**
- See all leads in **Close CRM**

## Troubleshooting

### GitHub Actions not running

Check:
- Actions are enabled: `Settings → Actions → General → Allow all actions`
- Secrets are set correctly (no spaces, correct names)

### Slack not posting

Check:
- Bot is invited to #ai-test
- Token starts with `xoxb-`
- Scopes are correct

### Emails not sending

Check:
- SendGrid domain authentication: `sendgrid.com → Settings → Sender Authentication`
- From email matches authenticated domain
- API key has "Full Access" permissions

### Close CRM errors

Check:
- API key is valid
- You have permission to create leads
- Status IDs match your org (see `close_sync.py` line 148)

## Need Help?

Message in #ai-test:
```
@Agent help
```

Or check logs in GitHub Actions tab.

---

🚀 Your autonomous lead agent is now live!
