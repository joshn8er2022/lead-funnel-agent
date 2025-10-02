# Lead Funnel Automation Agent

Autonomous AI agent that manages your entire lead funnel from Typeform submission to booking calls. Runs 24/7 on GitHub Actions.

## Features

- **Automatic Lead Classification**: Classifies leads as Hume Connect, Wholesale, or Affiliate using rules + LLM
- **CRM Sync**: Automatically creates and updates leads in Close CRM
- **Booking Detection**: Checks Calendly for call bookings and adjusts workflow
- **Email Sequences**: Sends personalized 8-email nurture sequences via SendGrid
- **Custom Reports**: Generates 8 types of personalized HTML reports using Claude
- **Slack Integration**: Receive notifications and send commands via #ai-test channel
- **Fully Autonomous**: Runs twice daily on GitHub Actions with no human intervention

## Architecture

```
Typeform Submission
    ↓
Lead Classification (Rules + Claude)
    ↓
Close CRM Sync
    ↓
Calendly Check
    ↓
    ├─→ Booked? → Send Asset Pack → Notify
    └─→ Not Booked? → Start Nurture Sequence
            ↓
        8-Email Sequence
        - Day 0: Welcome
        - Day 3: Case Study
        - Day 7: Custom Report #1
        - Day 10: Social Proof
        - Day 14: Custom Report #2
        - Day 17: Problem-Solution
        - Day 21: Custom Report #3
        - Day 28: Break-up Email
```

## Setup

### 1. Install GitHub App

Run this in your terminal (with Claude Code):
```bash
/install-github-app
```

This installs the Claude Code GitHub app into this repository.

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

```
TYPEFORM_TOKEN=tfp_BioWCxqc...
CLOSE_API_KEY=api_6lNPtGIKn...
CLOSE_CLIENT_ID=oa2client_6bB...
CLOSE_CLIENT_SECRET=CcumUfit...
CALENDLY_TOKEN=eyJraWQi...
SENDGRID_API_KEY=SG.r7ItOHH...
ANTHROPIC_API_KEY=sk-ant-...
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
TWILIO_ACCOUNT_SID=ACde6464...
TWILIO_AUTH_TOKEN=604c675f...
TWILIO_PHONE_NUMBER=+12028399253
```

### 3. Configure Typeform Webhooks

For each form (Hume Connect and Hume Hardware):

1. Go to Typeform → Your Form → Connect → Webhooks
2. Add webhook URL:
   ```
   https://api.github.com/repos/joshisrael/lead-funnel-agent/dispatches
   ```
3. Set up authentication with your GitHub token
4. Send `typeform_submission` event type

### 4. Deploy

```bash
git add .
git commit -m "Initial agent setup"
git push origin main
```

The agent will now run automatically twice daily at 9am and 5pm PT.

## Usage

### Manual Triggers

Run the agent manually from GitHub Actions:

1. Go to **Actions** tab
2. Select "Lead Funnel Automation Agent"
3. Click "Run workflow"
4. Choose action: `scheduled_run`, `process_submission`, or `test_integrations`

### Slack Commands

In #ai-test channel:

```
@Agent status                          # Check system status
@Agent leads                           # List recent leads
@Agent send email to josh@example.com step 3   # Manual email
@Agent update lead josh@example.com state BOOKED
```

Or just ask questions:
```
@Agent How many leads came in today?
@Agent Show me all wholesale leads from this week
@Agent Send a custom email to the latest lead
```

### Testing

```bash
# Test integrations
python src/test_integrations.py

# Process a test submission
python src/process_typeform.py test_payload.json

# Run scheduled tasks locally
python src/run_scheduled.py
```

## Monitoring

- **Slack**: All notifications go to #ai-test
- **GitHub Actions**: View logs in the Actions tab
- **Close CRM**: All activities logged as notes

## Customization

### Email Templates

Edit templates in `templates/emails/`:
- `booked_assets.html` - Sent when call is booked
- `nurture_1_welcome.html` through `nurture_8_breakup.html` - Sequence emails

### Report Templates

Edit templates in `templates/reports/` to customize the 8 HTML reports.

### Classification Rules

Edit `src/classifier.py` to adjust lead classification logic.

### Email Timing

Edit `src/email_engine.py` → `get_next_email_date()` to change schedule:
```python
schedule = {
    1: 0,   # Immediate
    2: 3,   # Day 3
    # ... customize here
}
```

## Architecture Files

```
lead-funnel-agent/
├── .github/workflows/
│   └── lead-agent.yml           # GitHub Actions workflow
├── src/
│   ├── agent.py                 # Main orchestrator
│   ├── classifier.py            # Lead classification
│   ├── close_sync.py            # Close CRM integration
│   ├── calendly_check.py        # Booking detection
│   ├── email_engine.py          # SendGrid emails
│   ├── report_generator.py      # Custom HTML reports
│   ├── slack_bot.py             # Slack integration
│   ├── run_scheduled.py         # Scheduled runner
│   └── process_typeform.py      # Typeform processor
├── templates/
│   ├── emails/                  # Email templates
│   └── reports/                 # Report templates
├── requirements.txt
└── README.md
```

## Troubleshooting

### Agent not running on schedule

- Check GitHub Actions is enabled for the repo
- Verify secrets are set correctly
- Look at Actions tab for error logs

### Emails not sending

- Verify SendGrid domain authentication
- Check SendGrid API key permissions
- Review SendGrid activity feed

### Calendly not detecting bookings

- Confirm Calendly token has correct scopes
- Verify organization slug is correct
- Check that lead email matches Calendly invitee email exactly

### Slack not responding

- Verify Slack app has correct OAuth scopes:
  - `chat:write`
  - `app_mentions:read`
  - `channels:history`
- Check bot is invited to #ai-test channel
- Verify tokens in GitHub Secrets

## Security

- **Never** commit API keys to the repository
- All secrets stored in GitHub Secrets (encrypted)
- Use environment variables only
- Logs never contain API keys or PII
- Rotate keys after testing

## Support

Questions? Message in #ai-test:
```
@Agent help
```

Or reach out to josh@myhumehealth.com

---

**Built with**: Claude Sonnet 4.5, GitHub Actions, Close CRM, SendGrid, Calendly, Slack
