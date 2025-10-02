"""
Email Reply Handler - Processes inbound email replies from leads
Uses SendGrid Inbound Parse webhook
"""
import os
import json
from typing import Dict, Any, Optional
from email.parser import Parser
from datetime import datetime

from .conversation_intelligence import ConversationIntelligence
from .close_sync import CloseClient
from .email_engine import EmailEngine
from .slack_bot import SlackBot

class EmailReplyHandler:
    def __init__(self):
        self.conversation_ai = ConversationIntelligence()
        self.close = CloseClient()
        self.email_engine = EmailEngine()
        self.slack = SlackBot()

    def handle_inbound_email(self, sendgrid_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an inbound email from SendGrid Inbound Parse webhook

        Payload structure:
        {
            "from": "lead@example.com",
            "to": "josh@humeprograms.com",
            "subject": "Re: Welcome to Hume",
            "text": "email body text",
            "html": "<html>email body</html>",
            "headers": "...",
            "attachments": []
        }
        """

        from_email = sendgrid_payload.get("from", "").lower()
        subject = sendgrid_payload.get("subject", "")
        body = sendgrid_payload.get("text", "") or sendgrid_payload.get("html", "")

        # Extract clean email address
        if "<" in from_email:
            from_email = from_email.split("<")[1].split(">")[0]

        print(f"[EmailReply] Received reply from: {from_email}")

        # Find lead in Close CRM
        lead = self.close.get_lead_by_email(from_email)

        if not lead:
            print(f"[EmailReply] No lead found for {from_email}, escalating to Josh")
            self.slack.send_notification(
                f"📧 *Email from Unknown Lead*\nFrom: {from_email}\nSubject: {subject}\n\nReply manually at josh@humeprograms.com",
                {}
            )
            return {"status": "escalated", "reason": "unknown_lead"}

        # Get lead data
        lead_data = self._extract_lead_data(lead)

        # Get conversation history from Close activities
        conversation_history = self._get_conversation_history(lead["id"])

        # Analyze the reply with AI
        analysis = self.conversation_ai.analyze_message(
            message=body,
            lead_context=lead_data,
            conversation_history=conversation_history
        )

        print(f"[EmailReply] Analysis: {analysis['intent']}, Sentiment: {analysis['sentiment']}")

        # Log the inbound message to Close
        self.close._log_activity(
            lead["id"],
            f"Inbound Email Reply: {subject}",
            {"body": body[:500], "sentiment": analysis["sentiment"]}
        )

        # Update lead state to ENGAGED
        if lead_data.get("custom", {}).get("agent_state") == "NURTURING":
            self.close.update_lead_state(lead["id"], "ENGAGED", {"via": "email_reply"})

        # Handle based on analysis
        result = self._handle_based_on_analysis(lead, lead_data, analysis, conversation_history)

        return result

    def _handle_based_on_analysis(self, lead: Dict[str, Any], lead_data: Dict[str, Any], analysis: Dict[str, Any], history: list) -> Dict[str, Any]:
        """Handle the reply based on AI analysis"""

        lead_id = lead["id"]
        action = analysis["next_action"]

        # Always notify Slack of replies
        self.slack.send_notification(
            f"📧 *Email Reply: {analysis['intent'].replace('_', ' ').title()}*\n"
            f"Sentiment: {analysis['sentiment']}\n"
            f"Action: {action}",
            lead_data
        )

        if analysis["should_escalate"]:
            # Escalate to Josh
            print(f"[EmailReply] Escalating to Josh: {analysis['escalation_reason']}")

            self.slack.send_notification(
                f"⚠️ *ESCALATION NEEDED*\n"
                f"Reason: {analysis['escalation_reason']}\n\n"
                f"Lead's Message:\n{analysis.get('key_concerns', [])}",
                lead_data
            )

            self.close._log_activity(lead_id, "Escalated to Josh", analysis)

            # Send holding response
            self.email_engine._send_email(
                to_email=lead_data["email"],
                to_name=lead_data["name"],
                subject="Re: " + analysis.get("subject", "Your inquiry"),
                html_content=f"""
                <p>Hi {lead_data['name']},</p>
                <p>Thanks for your message! I want to make sure you get the best answer for your specific situation.</p>
                <p>Josh will reach out to you directly within the next few hours to discuss this personally.</p>
                <p>Talk soon!</p>
                """
            )

            return {"status": "escalated", "reason": analysis["escalation_reason"]}

        elif action == "book_call":
            # Send booking link
            print(f"[EmailReply] Sending booking link")

            response = f"""
            <p>Hi {lead_data['name']},</p>
            <p>{analysis['suggested_response']}</p>
            <p><strong>Let's schedule a quick call:</strong><br>
            <a href="https://calendly.com/josh-myhumehealth" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Book a Time</a></p>
            <p>Looking forward to speaking with you!</p>
            """

            self.email_engine._send_email(
                to_email=lead_data["email"],
                to_name=lead_data["name"],
                subject="Re: Let's schedule a call",
                html_content=response
            )

            self.close._log_activity(lead_id, "Sent booking link via email reply")

            return {"status": "booking_sent"}

        elif action == "send_response":
            # Send AI-generated response
            print(f"[EmailReply] Sending AI response")

            response = f"""
            <p>Hi {lead_data['name']},</p>
            {self._format_for_email(analysis['suggested_response'])}
            <p>Let me know if you have any other questions!</p>
            """

            self.email_engine._send_email(
                to_email=lead_data["email"],
                to_name=lead_data["name"],
                subject="Re: Your question",
                html_content=response
            )

            self.close._log_activity(
                lead_id,
                f"AI Response Sent: {analysis['intent']}",
                {"response": analysis['suggested_response'][:200]}
            )

            # Add to conversation history
            self._save_to_history(lead_id, "Agent", analysis['suggested_response'])

            return {"status": "response_sent", "response": analysis['suggested_response']}

        elif action == "end_conversation":
            # Lead unsubscribed or not interested
            print(f"[EmailReply] Ending conversation")

            self.close.update_lead_state(lead_id, "CLOSED_LOST", {"reason": "Not interested"})

            self.slack.send_notification(
                f"❌ *Lead Not Interested*\nMarked as closed-lost",
                lead_data
            )

            return {"status": "closed"}

        else:
            # Default: send resources
            return {"status": "handled", "action": action}

    def _extract_lead_data(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Extract lead data into standard format"""
        contacts = lead.get("contacts", [])
        contact = contacts[0] if contacts else {}

        return {
            "leadType": lead.get("custom", {}).get("lead_type", "unknown"),
            "name": contact.get("name", "Unknown"),
            "email": self._get_lead_email(lead) or "",
            "phone": contact.get("phones", [{}])[0].get("phone", ""),
            "company": lead.get("name", "Unknown"),
            "industry": lead.get("custom", {}).get("industry", ""),
            "goals": lead.get("custom", {}).get("goals", ""),
            "priority": lead.get("custom", {}).get("priority", "medium"),
            "custom": lead.get("custom", {})
        }

    def _get_lead_email(self, lead: Dict[str, Any]) -> Optional[str]:
        """Extract email from lead object"""
        contacts = lead.get("contacts", [])
        if contacts and contacts[0].get("emails"):
            return contacts[0]["emails"][0]["email"]
        return None

    def _get_conversation_history(self, lead_id: str) -> list:
        """Get conversation history from Close CRM activities"""
        # This would query Close API for activity history
        # Simplified for now
        return []

    def _save_to_history(self, lead_id: str, sender: str, message: str):
        """Save message to conversation history in Close"""
        self.close._log_activity(
            lead_id,
            f"Conversation: {sender}",
            {"message": message, "timestamp": datetime.utcnow().isoformat()}
        )

    def _format_for_email(self, text: str) -> str:
        """Format AI response for HTML email"""
        # Convert line breaks to paragraphs
        paragraphs = text.split("\n")
        html = "".join([f"<p>{p}</p>" for p in paragraphs if p.strip()])
        return html
