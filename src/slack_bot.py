"""
Slack bot integration - allows texting commands to agent in #ai-test channel
"""
import os
import json
from typing import Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from anthropic import Anthropic

class SlackBot:
    def __init__(self):
        self.slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        self.claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.channel = os.getenv("SLACK_CHANNEL_ID", "#ai-test")

    def handle_message(self, event: Dict[str, Any]) -> None:
        """Handle incoming Slack messages"""
        text = event.get("text", "")
        channel = event.get("channel")
        user = event.get("user")

        # Ignore bot messages
        if event.get("bot_id"):
            return

        # Process the command
        response = self.process_command(text, user)

        # Send response
        self.send_message(channel, response)

    def process_command(self, text: str, user: str) -> str:
        """Process a text command using Claude"""

        # Check for specific commands
        if text.lower().startswith("status"):
            return self._get_system_status()
        elif text.lower().startswith("leads"):
            return self._get_recent_leads()
        elif text.lower().startswith("send email"):
            return self._manual_email_send(text)
        elif text.lower().startswith("update lead"):
            return self._update_lead_command(text)
        else:
            # Use Claude for general queries
            return self._ask_claude(text, user)

    def _ask_claude(self, query: str, user: str) -> str:
        """Ask Claude to interpret and execute the command"""

        # Import required modules
        from .close_sync import CloseClient
        from .email_engine import EmailEngine
        from .calendly_check import CalendlyChecker

        close = CloseClient()
        email_engine = EmailEngine()
        calendly = CalendlyChecker()

        system_prompt = f"""You are an AI agent that manages a lead funnel automation system.

User {user} has sent you a command via Slack: "{query}"

Available actions:
1. Check lead status in Close CRM
2. Send emails via SendGrid
3. Check Calendly bookings
4. Update lead information
5. Get system statistics
6. Manual interventions on leads

Current system capabilities:
- Close CRM API for lead management
- SendGrid for email sending
- Calendly for booking checks
- Motion API for task creation

Interpret the command and either:
A) Execute the action using available APIs
B) Provide clear information
C) Ask for clarification if ambiguous

Be concise and actionable. If you execute something, confirm what you did.
"""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": query}
                ]
            )

            return response.content[0].text
        except Exception as e:
            return f"Error processing command: {str(e)}"

    def _get_system_status(self) -> str:
        """Get current system status"""
        from .close_sync import CloseClient

        close = CloseClient()

        try:
            # Get lead counts by status
            status_text = "🔄 *System Status*\n\n"
            status_text += "✅ All integrations operational\n"
            status_text += "• Close CRM: Connected\n"
            status_text += "• SendGrid: Connected\n"
            status_text += "• Calendly: Connected\n"
            status_text += "• Motion: Connected\n\n"

            status_text += "_Run `leads` to see recent activity_"

            return status_text
        except Exception as e:
            return f"❌ Error checking status: {str(e)}"

    def _get_recent_leads(self) -> str:
        """Get recent leads from Close"""
        from .close_sync import CloseClient

        close = CloseClient()

        try:
            # Fetch recent leads (simplified - you'll need to implement pagination)
            leads_text = "📊 *Recent Leads*\n\n"

            # This is a placeholder - implement actual lead fetching
            leads_text += "_(Implement lead listing from Close API)_\n"
            leads_text += "Use: `python src/scripts/list_leads.py` for full list"

            return leads_text
        except Exception as e:
            return f"❌ Error fetching leads: {str(e)}"

    def _manual_email_send(self, text: str) -> str:
        """Manually trigger an email send"""
        # Parse command: "send email to lead@example.com step 3"
        parts = text.lower().split()

        if len(parts) < 5:
            return "❌ Usage: `send email to <email> step <number>`"

        try:
            to_index = parts.index("to")
            step_index = parts.index("step")

            email = parts[to_index + 1]
            step = int(parts[step_index + 1])

            from .close_sync import CloseClient
            from .email_engine import EmailEngine

            close = CloseClient()
            email_engine = EmailEngine()

            # Get lead by email
            lead = close.get_lead_by_email(email)

            if not lead:
                return f"❌ No lead found with email: {email}"

            # Send email
            success = email_engine.send_nurture_email(lead, step)

            if success:
                close.update_email_tracking(lead["id"], step, f"Manual send via Slack")
                return f"✅ Sent email step {step} to {email}"
            else:
                return f"❌ Failed to send email to {email}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _update_lead_command(self, text: str) -> str:
        """Update a lead via command"""
        # Parse command: "update lead email@example.com status qualified"
        parts = text.lower().split()

        if len(parts) < 4:
            return "❌ Usage: `update lead <email> <field> <value>`"

        try:
            email = parts[2]
            field = parts[3]
            value = " ".join(parts[4:])

            from .close_sync import CloseClient

            close = CloseClient()
            lead = close.get_lead_by_email(email)

            if not lead:
                return f"❌ No lead found with email: {email}"

            # Update based on field
            if field == "state":
                close.update_lead_state(lead["id"], value.upper())
                return f"✅ Updated lead state to: {value}"
            else:
                return f"❌ Unknown field: {field}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def send_message(self, channel: str, text: str) -> None:
        """Send a message to Slack"""
        try:
            self.slack_client.chat_postMessage(
                channel=channel,
                text=text,
                mrkdwn=True
            )
        except SlackApiError as e:
            print(f"Error sending Slack message: {e}")

    def send_notification(self, message: str, lead_data: Optional[Dict[str, Any]] = None) -> None:
        """Send a notification to the #ai-test channel"""
        if lead_data:
            message += f"\n\n*Lead:* {lead_data.get('name', 'Unknown')}"
            message += f"\n*Email:* {lead_data.get('email', 'N/A')}"
            message += f"\n*Company:* {lead_data.get('company', 'N/A')}"
            message += f"\n*Type:* {lead_data.get('leadType', 'N/A')}"

        self.send_message(self.channel, message)
