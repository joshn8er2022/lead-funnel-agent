# Quick Start - Deploy in 10 Minutes

## Prerequisites Check

```bash
# Check git
git --version  # Should show git version

# If missing, install:
# Mac: xcode-select --install
```

## Option 1: Manual GitHub Setup (Recommended)

### 1. Create Repository on GitHub

1. Go to https://github.com/new
2. Name: `lead-funnel-agent`
3. Public or Private
4. **Don't** initialize with README
5. Click "Create repository"

### 2. Push Your Code

```bash
cd /Users/joshisrael/Projects/lead-funnel-agent

# Add your GitHub repo as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/lead-funnel-agent.git

# Push
git push -u origin main
```

### 3. Add Secrets

Go to: `https://github.com/YOUR_USERNAME/lead-funnel-agent/settings/secrets/actions`

Click "New repository secret" for each:

| Name | Value (you already have these) |
|------|-------------------------------|
| `TYPEFORM_TOKEN` | tfp_BioWCxqc... |
| `CLOSE_API_KEY` | api_6lNPtGIKn... |
| `CLOSE_CLIENT_ID` | oa2client_6bB... |
| `CLOSE_CLIENT_SECRET` | CcumUfit... |
| `CALENDLY_TOKEN` | eyJraWQi... |
| `SENDGRID_API_KEY` | SG.r7ItOHH... |
| `TWILIO_ACCOUNT_SID` | ACde6464... |
| `TWILIO_AUTH_TOKEN` | 604c675f... |
| `TWILIO_PHONE_NUMBER` | +12028399253 |

**You'll need to create:**

| Name | Where to get it |
|------|----------------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys |
| `SLACK_BOT_TOKEN` | https://api.slack.com/apps (create app) |
| `SLACK_SIGNING_SECRET` | https://api.slack.com/apps (same app) |

### 4. Set Up Slack Bot

1. Go to https://api.slack.com/apps
2. "Create New App" → "From scratch"
3. Name: "Lead Agent", select your workspace
4. **OAuth & Permissions** → Bot Token Scopes, add:
   - `chat:write`
   - `app_mentions:read`
   - `channels:history`
5. "Install to Workspace"
6. Copy "Bot User OAuth Token" → Add as `SLACK_BOT_TOKEN` secret
7. Copy "Signing Secret" from Basic Information → Add as `SLACK_SIGNING_SECRET`
8. In Slack #ai-test: `/invite @Lead Agent`

### 5. Configure Typeform Webhooks

See full instructions in `DEPLOYMENT_GUIDE.md` section 4.

**Quick version:**
- Typeform → Your Form → Connect → Webhooks
- URL: `https://api.github.com/repos/YOUR_USERNAME/lead-funnel-agent/dispatches`
- Need GitHub token with `repo` scope from https://github.com/settings/tokens

### 6. Test It!

```bash
# Go to GitHub repo → Actions tab → Lead Funnel Automation Agent
# Click "Run workflow" → Select "test_integrations" → Run
```

All tests should pass ✅

## Option 2: Quick Script

```bash
# From the project directory
cd /Users/joshisrael/Projects/lead-funnel-agent

# Set your GitHub username
export GITHUB_USER="your-username-here"

# Create repo and push (requires login)
git remote add origin https://github.com/$GITHUB_USER/lead-funnel-agent.git
git push -u origin main

echo "✅ Code pushed!"
echo "Now add secrets at: https://github.com/$GITHUB_USER/lead-funnel-agent/settings/secrets/actions"
```

## What Happens Next?

Once deployed:

1. **Typeform submissions** trigger the agent instantly
2. **Scheduled runs** happen at 9am & 5pm PT daily
3. **Slack notifications** go to #ai-test
4. **All leads** sync to Close CRM

## Monitoring

- **GitHub Actions** → See all runs and logs
- **Slack #ai-test** → Real-time notifications
- **Close CRM** → All lead data

## Commands in Slack

```
@Agent status              # System status
@Agent leads               # Recent leads
@Agent send email to ...   # Manual email
```

---

Need help? Check `DEPLOYMENT_GUIDE.md` for detailed troubleshooting.
