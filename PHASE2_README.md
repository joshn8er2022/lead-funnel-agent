# Phase 2: Full Conversational AI Sales Agent

## What's New in Phase 2

Your agent is now a **complete sales rep replacement** that:

✅ **Responds to email replies** intelligently
✅ **Handles SMS conversations** back-and-forth
✅ **Makes AI voice calls** via VAPI when needed
✅ **Qualifies leads** through natural conversation
✅ **Handles objections** professionally
✅ **Books meetings** automatically
✅ **Escalates to you** only when necessary

---

## New Capabilities

### 1. Email Reply Intelligence (`email_reply_handler.py`)

**What it does:**
- Receives email replies from leads via SendGrid
- Analyzes intent using Claude AI
- Responds intelligently to questions/objections
- Books calls when appropriate
- Escalates complex issues to you

**Example Flow:**
```
Lead replies: "What's your pricing for 10 BodyPods?"

Agent analyzes → Sees pricing question for wholesale
Agent responds: "Great question! For 10 units, you're looking at..."
Agent: "Want to hop on a quick call to get exact numbers?"
Lead: "Sure"
Agent: Sends Calendly link
```

### 2. SMS Conversations (`sms_handler.py`)

**What it does:**
- Two-way SMS via Twilio
- Natural conversation handling
- Qualification questions
- Objection responses
- Booking links via text

**Example Flow:**
```
Lead texts: "Is this really AI?"

Agent: "Yep! I'm Josh's AI assistant. But I can answer most questions.
What are you looking to learn about Hume?"

Lead: "Pricing for my gym"

Agent: "How many locations? That helps me give you accurate pricing"

Lead: "3 locations"

Agent: "Perfect! For 3 gyms you'd need about 6-9 units. That's $X-Y range.
Want to book a call to get exact numbers? calendly.com/josh-myhumehealth"
```

### 3. AI Voice Calls (`vapi_handler.py`)

**When agent makes calls:**
- High-priority wholesale leads after 2 emails (no response)
- Any lead after 4 emails (no response)
- Leads who asked about demos/pricing but didn't book

**What happens on the call:**
- Natural AI voice (sounds human)
- Follows custom scripts based on lead type
- Asks qualifying questions
- Handles objections
- Books discovery calls
- Records and transcribes everything

**Example Call Script:**
```
Agent: "Hi Sarah, this is the AI assistant from Hume. I'm following up on
your interest in body composition tracking for Peak Fitness. Is now a good
time for a quick 2-minute chat?"

Lead: "Sure, but I'm concerned about the price"

Agent: "I understand. Let me ask - what's the cost of losing clients because
you can't show them objective progress? Most gyms see 30% better retention
with data tracking. That ROI typically pays for the system in 2-3 months.
Want me to have Josh walk you through exact numbers?"

Lead: "Yeah, that would be helpful"

Agent: "Perfect! I'm sending you a calendar link right now..."
```

### 4. Conversation Intelligence (`conversation_intelligence.py`)

**The Brain Behind It All:**
- Analyzes every message (email/SMS/voice)
- Determines intent, sentiment, qualification level
- Generates contextual responses
- Knows when to escalate
- Personalizes based on lead history

---

## Setup Guide

### Step 1: Add New GitHub Secrets

Go to: `https://github.com/YOUR_USERNAME/lead-funnel-agent/settings/secrets/actions`

Add:
```
VAPI_PRIVATE_KEY = 6640389d-5c71-44f7-9053-00efee26a3d6
VAPI_PUBLIC_KEY = 4bc2d7c2-7b32-4cad-925c-90e40f9588c3
```

### Step 2: Deploy Webhook Server

**Option A: Railway (Recommended)**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy from your repo
cd /Users/joshisrael/Projects/lead-funnel-agent
railway init
railway up
```

**Option B: Heroku**
```bash
# Create Procfile
echo "web: python src/webhook_server.py" > Procfile

# Deploy
heroku create lead-funnel-agent
git push heroku main
```

**Option C: Vercel Serverless**
- Push to GitHub
- Connect to Vercel
- Deploy automatically

### Step 3: Configure SendGrid Inbound Parse

1. Go to https://app.sendgrid.com/settings/parse
2. Add hostname: `reply.humeprograms.com` (or use SendGrid subdomain)
3. Set URL to: `https://YOUR_WEBHOOK_URL/webhook/email`
4. Update DNS: Add MX record pointing to SendGrid

**MX Record:**
```
Host: reply.humeprograms.com
Type: MX
Priority: 10
Value: mx.sendgrid.net
```

### Step 4: Configure Twilio SMS Webhook

1. Go to https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click your phone number: `+12028399253`
3. Under "Messaging":
   - Webhook URL: `https://YOUR_WEBHOOK_URL/webhook/sms`
   - HTTP POST
4. Save

### Step 5: Configure VAPI Webhooks

1. Go to https://dashboard.vapi.ai/webhooks
2. Add webhook URL: `https://YOUR_WEBHOOK_URL/webhook/vapi`
3. Select events: `call.ended`, `call.started`
4. Save

---

## How It Works Now

### Scenario 1: Lead Submits Typeform

```
1. Lead fills Typeform → GitHub Actions triggered
2. Agent classifies lead
3. Syncs to Close CRM
4. Checks Calendly for booking
5. If not booked → Sends Email #1 + logs phone for SMS
6. Lead data stored with full context
```

### Scenario 2: Lead Replies to Email

```
1. Lead replies to nurture email
2. SendGrid forwards to /webhook/email
3. Agent analyzes with Claude:
   - Intent: pricing_question
   - Sentiment: interested
   - Action: send_response
4. Agent responds with pricing info + booking link
5. Logs conversation to Close CRM
6. Notifies you in Slack
```

### Scenario 3: Lead Texts Your Number

```
1. Lead texts +12028399253
2. Twilio posts to /webhook/sms
3. Agent finds lead in Close by phone
4. Analyzes message with Claude
5. Generates contextual response
6. Sends SMS back
7. Logs to Close + notifies Slack
8. Continues conversation until booking or escalation
```

### Scenario 4: Agent Makes Proactive Call

```
1. Scheduled run detects: "High-priority lead, 4 emails sent, no response"
2. Agent decides to call via VAPI
3. VAPI dials lead's phone
4. AI voice has conversation (following script)
5. Handles objections, books call, or escalates
6. Call ends → VAPI posts transcript to /webhook/vapi
7. Agent analyzes outcome
8. Updates Close CRM
9. Notifies you with full transcript
```

---

## Architecture

```
┌─────────────────┐
│  Typeform       │
│  Submission     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐     ┌──────────────────┐
│ GitHub Actions  │────→│  Claude AI       │
│ (Scheduled)     │     │  Classification  │
└────────┬────────┘     └──────────────────┘
         │
         ↓
┌─────────────────────────────────────────────┐
│           LEAD AGENT (Brain)                │
│  ┌──────────────────────────────────────┐  │
│  │  Conversation Intelligence (Claude)  │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌───────┐  ┌───────┐  ┌───────┐          │
│  │ Email │  │  SMS  │  │ Voice │          │
│  │Handler│  │Handler│  │(VAPI) │          │
│  └───┬───┘  └───┬───┘  └───┬───┘          │
└──────┼──────────┼──────────┼──────────────┘
       │          │          │
       ↓          ↓          ↓
┌─────────────────────────────────┐
│      Webhook Server (Flask)      │
│  /webhook/email  (SendGrid)     │
│  /webhook/sms    (Twilio)       │
│  /webhook/vapi   (VAPI)         │
└──────────┬──────────────────────┘
           │
           ↓
    ┌──────────────┐
    │  Close CRM   │
    │  (All Data)  │
    └──────┬───────┘
           │
           ↓
    ┌──────────────┐
    │    Slack     │
    │ (#ai-test)   │
    └──────────────┘
```

---

## Conversation Flow Examples

### Objection: "Too Expensive"

**Email:**
```
Lead: "This seems really expensive for what it is."

Agent (Claude analyzes) →
Intent: objection
Concern: pricing
Qualification: partially_qualified

Agent responds:
"I totally understand. Let me ask - what's the cost of NOT having this data?

Most of our clients in [industry] see 30% better client retention when they
use objective body composition tracking. For a gym your size, that's typically
10-15 extra members per month.

At $50/month per member, that's $500-750/month in retained revenue. Our system
pays for itself in the first 2-3 months.

Want to hop on a quick call so Josh can show you the exact ROI for [company]?"
```

**SMS:**
```
Lead: "Too pricey"

Agent: "I hear you! Quick question - how much revenue do you lose when clients
quit because they don't see progress? Most gyms see 30% better retention with
our data. That ROI > the cost. Want the math? Or just book a call: [link]"
```

**Voice:**
```
Lead: "I'm not sure we can afford this right now"

Agent: "I completely understand budget concerns. Can I ask - how many clients
do you lose per month currently? ... Ok, 5-10. And if you could keep just 3
of those by showing them real data-driven progress, how much would that be
worth? ... $150/month each, so $450/month. Our system is less than that and
typically prevents way more churn. Worth a 15-minute call to see the numbers?"
```

---

## Escalation Rules

Agent escalates to you when:

✅ Enterprise deals (100+ units)
✅ Complex custom integrations
✅ Legal/compliance questions (beyond standard HIPAA)
✅ Angry/frustrated leads
✅ Requests the agent doesn't understand
✅ Lead specifically asks to talk to a human

**Escalation Flow:**
1. Agent detects escalation condition
2. Sends holding response: "Great question! Josh will reach out within the hour"
3. Posts to Slack: "⚠️ ESCALATION: [reason]"
4. Logs full conversation to Close
5. You take over manually

---

## Testing

### Test Email Reply:
```bash
# Send test email to reply@humeprograms.com (after SendGrid setup)
# Or use curl:
curl -X POST https://YOUR_WEBHOOK_URL/webhook/email \
  -d "from=test@example.com" \
  -d "subject=Re: Welcome" \
  -d "text=What's your pricing?"
```

### Test SMS:
```bash
# Text your Twilio number: +12028399253
# Or use curl:
curl -X POST https://YOUR_WEBHOOK_URL/webhook/sms \
  -d "From=+15551234567" \
  -d "Body=I'm interested in pricing"
```

### Test Voice Call:
```python
# Run from your repo
python -c "
from src.vapi_handler import VAPIHandler
vapi = VAPIHandler()
result = vapi.make_outbound_call({
    'name': 'Test Lead',
    'phone': '+YOUR_PHONE',
    'company': 'Test Company',
    'leadType': 'hume_connect',
    'goals': 'Testing the system'
}, 'follow_up')
print(result)
"
```

---

## Monitoring

**Slack Notifications:**
- 📧 Email reply received
- 📱 SMS conversation
- 📞 Voice call started/ended
- ⚠️ Escalations
- 🎉 Bookings

**Close CRM:**
- Every interaction logged as activity
- Full conversation history
- Call recordings attached
- Transcripts saved

---

## Cost Estimate (Phase 2)

| Service | Monthly Cost |
|---------|-------------|
| Claude API | ~$50-100 (2x usage) |
| VAPI Voice Calls | ~$0.10/min (~$30-50) |
| Twilio SMS | ~$0.01/msg (~$10-20) |
| Webhook Hosting (Railway) | $5-10 |
| **Total Phase 2 Addition** | **~$95-180/month** |

**Combined Total (Phase 1 + 2):** ~$130-245/month

**ROI:** If agent closes just 1 extra deal/month → 20-40x ROI

---

## What You Can Do Now

### Via Email:
Lead replies → Agent responds → Books calls automatically

### Via SMS:
Leads text → Agent qualifies → Sends booking links

### Via Voice:
Agent calls qualified leads → Handles objections → Books meetings

### Via Slack:
```
@Agent call +15551234567
@Agent send sms to lead@example.com "Custom message"
@Agent what's the status of Sarah from Peak Fitness?
```

---

## Next Steps

1. **Deploy webhook server** (Railway/Heroku/Vercel)
2. **Configure webhooks** (SendGrid, Twilio, VAPI)
3. **Test each channel** (email, SMS, voice)
4. **Monitor Slack** for agent activity
5. **Let it run** for 1 week and watch deals close

---

**Your agent is now a full sales team.** 🚀

Questions? Ask in Slack: `@Agent help`
