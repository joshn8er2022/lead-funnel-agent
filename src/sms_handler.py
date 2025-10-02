"""
SMS Conversation Handler - Two-way SMS via Twilio
Handles inbound texts and responds intelligently
"""
import os
from typing import Dict, Any
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from .conversation_intelligence import ConversationIntelligence
from .close_sync import CloseClient
from .slack_bot import SlackBot

class SMSHandler:
    def __init__(self):
        self.twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.conversation_ai = ConversationIntelligence()
        self.close = CloseClient()
        self.slack = SlackBot()

    def handle_inbound_sms(self, twilio_payload: Dict[str, Any]) -> str:
        """
        Handle inbound SMS from Twilio webhook

        Payload structure:
        {
            "From": "+15551234567",
            "To": "+12028399253",
            "Body": "Yes, I'm interested in pricing",
            "MessageSid": "SM...",
            "FromCity": "San Francisco",
            "FromState": "CA"
        }
        """

        from_number = twilio_payload.get("From", "")
        message_body = twilio_payload.get("Body", "")
        from_city = twilio_payload.get("FromCity", "")
        from_state = twilio_payload.get("FromState", "")

        print(f"[SMS] Received from {from_number}: {message_body}")

        # Find lead by phone number in Close
        lead = self._find_lead_by_phone(from_number)

        if not lead:
            # Unknown number - create lead or escalate
            print(f"[SMS] Unknown number: {from_number}")

            self.slack.send_notification(
                f"📱 *SMS from Unknown Number*\n"
                f"From: {from_number} ({from_city}, {from_state})\n"
                f"Message: {message_body}",
                {}
            )

            # Send helpful response
            response = self._create_twiml_response(
                "Hi! Thanks for texting Hume. I don't have you in our system yet. "
                "Could you share your name and company? Or book a call: https://calendly.com/josh-myhumehealth"
            )

            return response

        # Extract lead data
        lead_data = self._extract_lead_data(lead)
        lead_id = lead["id"]

        # Get conversation history
        conversation_history = self._get_sms_history(lead_id)

        # Analyze message with AI
        analysis = self.conversation_ai.analyze_message(
            message=message_body,
            lead_context=lead_data,
            conversation_history=conversation_history
        )

        print(f"[SMS] Analysis: {analysis['intent']}, Action: {analysis['next_action']}")

        # Log to Close CRM
        self.close._log_activity(
            lead_id,
            f"Inbound SMS: {message_body}",
            {"from": from_number, "sentiment": analysis["sentiment"]}
        )

        # Update state to ENGAGED if nurturing
        if lead_data.get("custom", {}).get("agent_state") == "NURTURING":
            self.close.update_lead_state(lead_id, "ENGAGED", {"via": "sms"})

        # Handle based on analysis
        response_text = self._handle_sms_analysis(lead, lead_data, analysis, conversation_history)

        # Send SMS response
        self._send_sms(from_number, response_text)

        # Log outbound SMS
        self.close._log_activity(
            lead_id,
            f"Outbound SMS: {response_text}",
            {"to": from_number}
        )

        # Notify Slack
        self.slack.send_notification(
            f"📱 *SMS Conversation*\n"
            f"Lead: {lead_data['name']}\n"
            f"Intent: {analysis['intent']}\n"
            f"Response sent: {response_text[:100]}...",
            lead_data
        )

        # Return TwiML for webhook (empty since we already sent)
        return self._create_twiml_response("")

    def _handle_sms_analysis(self, lead: Dict[str, Any], lead_data: Dict[str, Any], analysis: Dict[str, Any], history: list) -> str:
        """Generate SMS response based on analysis"""

        lead_id = lead["id"]

        if analysis["should_escalate"]:
            # Escalate but send helpful holding response
            self.slack.send_notification(
                f"⚠️ *SMS ESCALATION*\n"
                f"Reason: {analysis['escalation_reason']}",
                lead_data
            )

            return f"Hi {lead_data['name']}, great question! Josh will text you back within the hour to discuss this personally."

        elif analysis["next_action"] == "book_call":
            # Booking link via SMS
            return f"{analysis['suggested_response']}\n\nBook here: https://calendly.com/josh-myhumehealth"

        elif analysis["next_action"] == "send_response":
            # AI-generated response (keep under 160 chars if possible)
            response = analysis['suggested_response']

            # Shorten for SMS
            if len(response) > 300:
                response = response[:297] + "..."

            return response

        else:
            # Default helpful response
            return f"Thanks for reaching out! I'm Josh's AI assistant. How can I help? (Or book a call: https://calendly.com/josh-myhumehealth)"

    def send_proactive_sms(self, to_number: str, message: str, lead_id: Optional[str] = None):
        """Send a proactive SMS to a lead"""

        print(f"[SMS] Sending proactive SMS to {to_number}")

        try:
            self.twilio_client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=message
            )

            if lead_id:
                self.close._log_activity(
                    lead_id,
                    f"Proactive SMS sent: {message}",
                    {"to": to_number}
                )

            return True
        except Exception as e:
            print(f"[SMS] Error sending: {str(e)}")
            return False

    def _send_sms(self, to_number: str, message: str) -> bool:
        """Send an SMS via Twilio"""
        try:
            self.twilio_client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=message
            )
            return True
        except Exception as e:
            print(f"[SMS] Failed to send: {str(e)}")
            return False

    def _create_twiml_response(self, message: str) -> str:
        """Create TwiML response for Twilio webhook"""
        resp = MessagingResponse()
        if message:
            resp.message(message)
        return str(resp)

    def _find_lead_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Find lead in Close CRM by phone number"""
        # Clean phone number (remove +1, spaces, dashes)
        clean_phone = phone_number.replace("+1", "").replace("-", "").replace(" ", "")

        # Query Close CRM
        import requests
        response = requests.get(
            f"{self.close.base_url}/lead/",
            headers=self.close.headers,
            params={
                "_limit": 1,
                "query": f"phone:{clean_phone}"
            }
        )

        if response.status_code == 200:
            results = response.json().get("data", [])
            return results[0] if results else None

        return None

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

    def _get_sms_history(self, lead_id: str) -> list:
        """Get SMS conversation history from Close activities"""
        # Simplified - would query Close activities filtered by SMS
        return []
