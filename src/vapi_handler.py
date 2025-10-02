"""
VAPI Voice AI Handler - Make and receive AI phone calls
Calls qualified leads automatically, handles objections, books meetings
"""
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from .close_sync import CloseClient
from .slack_bot import SlackBot

class VAPIHandler:
    def __init__(self):
        self.api_key = os.getenv("VAPI_PRIVATE_KEY", "6640389d-5c71-44f7-9053-00efee26a3d6")
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.close = CloseClient()
        self.slack = SlackBot()

    def make_outbound_call(self, lead_data: Dict[str, Any], call_reason: str = "follow_up") -> Dict[str, Any]:
        """
        Make an outbound AI call to a lead

        call_reason options:
        - "follow_up": General follow-up after no response
        - "demo_reminder": Remind about demo/call they showed interest in
        - "pricing_question": They asked about pricing
        - "objection_handling": They had concerns/objections
        """

        phone = lead_data.get("phone", "")

        if not phone:
            print(f"[VAPI] No phone number for lead")
            return {"status": "error", "message": "No phone number"}

        print(f"[VAPI] Making call to {lead_data['name']} at {phone} - Reason: {call_reason}")

        # Build the assistant configuration
        assistant_config = self._build_assistant_config(lead_data, call_reason)

        # Create the call
        payload = {
            "assistant": assistant_config,
            "phoneNumberId": None,  # Use default VAPI number
            "customer": {
                "number": phone,
                "name": lead_data.get("name", ""),
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/call/phone",
                headers=self.headers,
                json=payload
            )

            if response.status_code in [200, 201]:
                call_data = response.json()
                call_id = call_data.get("id", "")

                print(f"[VAPI] Call initiated: {call_id}")

                # Log to Close CRM
                self.close._log_activity(
                    lead_data.get("close_lead_id", ""),
                    f"AI Voice Call Initiated: {call_reason}",
                    {"call_id": call_id, "phone": phone}
                )

                # Notify Slack
                self.slack.send_notification(
                    f"📞 *AI Call Started*\n"
                    f"Reason: {call_reason.replace('_', ' ').title()}\n"
                    f"Call ID: {call_id}",
                    lead_data
                )

                return {"status": "success", "call_id": call_id, "data": call_data}

            else:
                error = response.text
                print(f"[VAPI] Call failed: {error}")

                self.slack.send_notification(
                    f"❌ *VAPI Call Failed*\n"
                    f"Error: {error[:200]}",
                    lead_data
                )

                return {"status": "error", "message": error}

        except Exception as e:
            print(f"[VAPI] Exception: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _build_assistant_config(self, lead_data: Dict[str, Any], call_reason: str) -> Dict[str, Any]:
        """Build the VAPI assistant configuration with custom system prompt"""

        # Base prompt
        base_prompt = f"""You are Josh Israel's AI sales assistant calling on behalf of Hume, a body composition tracking solution company.

LEAD INFO:
- Name: {lead_data.get('name', 'there')}
- Company: {lead_data.get('company', 'their company')}
- Industry: {lead_data.get('industry', 'their industry')}
- Lead Type: {lead_data.get('leadType', 'unknown')}
- Goals: {lead_data.get('goals', 'not specified')}

YOUR ROLE:
- You're calling to help, not to sell aggressively
- Be conversational and natural
- Listen more than you talk
- Handle objections gracefully
- Book a discovery call with Josh if appropriate
- Know when to end the call politely

CALL SCRIPT:

Opening:
"Hi {lead_data.get('name', 'there')}, this is the AI assistant from Hume. I'm following up on your interest in body composition tracking for {lead_data.get('company', 'your organization')}. Is now a good time for a quick 2-minute chat?"

If NO:
"No problem! When would be a better time? I can have Josh call you directly, or you can book a time that works: calendly.com/josh-myhumehealth"

If YES:
Continue with conversation based on call reason below.

"""

        # Add reason-specific script
        reason_scripts = {
            "follow_up": f"""
REASON: You filled out our form but haven't booked a call yet.

Questions to ask:
1. "What's prompting you to look at body composition tracking right now?"
2. "How many clients/patients would you be tracking?"
3. "What's your timeline for getting started?"

If interested:
"Great! I think Josh would be perfect to walk you through this. He has a few times open this week - would you like me to send you a booking link, or should I have him call you directly?"

If not ready:
"No worries! What would be helpful - should I send you some case studies from companies like yours, or would you prefer I check back in a few weeks?"
""",

            "demo_reminder": f"""
REASON: You showed interest in a demo but haven't booked yet.

Opening:
"I noticed you were interested in seeing how Hume works for {lead_data.get('industry', 'your industry')}. The demo only takes 15 minutes and Josh can customize it to your exact use case. Do you have time this week?"

If YES:
"Perfect! What day works best - Tuesday or Thursday? Morning or afternoon?"

If timing concerns:
"I totally get it. Even a quick 10-minute overview can be super valuable. Josh is pretty flexible - what's your schedule like?"
""",

            "pricing_question": f"""
REASON: You asked about pricing.

Opening:
"You asked about pricing for Hume. The honest answer is it depends on your volume and whether you need hardware, software, or both. Can I ask a few quick questions?"

Questions:
1. "Are you looking at this for a single location or multiple?"
2. "How many clients/patients per month?"
3. "Do you already have hardware, or would you need BodyPod units too?"

Then:
"Got it. Based on that, you're looking at roughly [range]. But Josh can put together a custom quote. Want to jump on a quick call with him to get exact numbers?"
""",

            "objection_handling": f"""
REASON: You had concerns we want to address.

Opening:
"I wanted to follow up on your questions about Hume. What was your main concern - was it pricing, implementation, or something else?"

Listen, then respond:

If pricing:
"I hear you. Can I ask - what's the cost of NOT having this data? Most clients see 30% better retention when they track objectively. That ROI usually pays for the system in 2-3 months."

If implementation:
"Implementation is actually easier than most systems. Average setup time is under a week, and we handle the integration. Want me to have Josh walk you through exactly how it would work for you?"

If "need to think":
"Totally fair. What specific piece are you thinking through? Maybe I can help clarify."
"""
        }

        system_prompt = base_prompt + reason_scripts.get(call_reason, reason_scripts["follow_up"])

        system_prompt += """

OBJECTION HANDLING:

"It's too expensive"
→ "I understand. Let me ask - what's the cost of losing clients because you can't show them objective progress? Most see 30% better retention with data tracking."

"Not sure it'll work for us"
→ "What specifically are you unsure about? Maybe I can address that, or Josh can show you examples from [their industry]."

"We're using something else"
→ "Oh interesting! What are you currently using? Is it giving you what you need, or are there gaps?"

"Need to talk to my partner/boss"
→ "Makes sense. What concerns do you think they'll have? That way when Josh talks to both of you, he can address those upfront."

END OF CALL:

If booking:
"Awesome! I'm sending you a calendar link right now to your email. Josh is looking forward to talking with you!"

If not ready:
"No problem at all! I'll send you some resources via email. Sound good?"

If objection you can't handle:
"You know what, this is a great question for Josh directly. Let me have him call you - does tomorrow work?"

TONE:
- Casual but professional
- No corporate jargon
- Use "you" and "your" a lot
- Ask questions, don't lecture
- If they're busy, get off the phone fast
- Never be pushy

CALENDLY LINK: calendly.com/josh-myhumehealth
"""

        # VAPI assistant configuration
        config = {
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7,
                "systemPrompt": system_prompt,
                "messages": []
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel - professional female voice
            },
            "firstMessage": f"Hi {lead_data.get('name', 'there')}, this is the AI assistant from Hume. I'm following up on your interest in body composition tracking. Is now a good time for a quick 2-minute chat?",
            "endCallFunctionEnabled": True,
            "recordingEnabled": True,
            "silenceTimeoutSeconds": 30,
            "maxDurationSeconds": 600  # 10 minute max
        }

        return config

    def handle_call_ended(self, vapi_webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle VAPI webhook when call ends

        Payload includes:
        - call_id
        - duration
        - transcript
        - outcome
        - recording_url
        """

        call_id = vapi_webhook_payload.get("id", "")
        transcript = vapi_webhook_payload.get("transcript", "")
        duration = vapi_webhook_payload.get("duration", 0)
        ended_reason = vapi_webhook_payload.get("endedReason", "")

        print(f"[VAPI] Call ended: {call_id}, Duration: {duration}s, Reason: {ended_reason}")

        # Extract phone number to find lead
        customer = vapi_webhook_payload.get("customer", {})
        phone = customer.get("number", "")

        if phone:
            # Find lead in Close
            lead = self._find_lead_by_phone(phone)

            if lead:
                lead_id = lead["id"]

                # Analyze transcript with AI to determine outcome
                outcome = self._analyze_call_outcome(transcript)

                # Log to Close
                self.close._log_activity(
                    lead_id,
                    f"AI Call Completed: {outcome['intent']}",
                    {
                        "duration": duration,
                        "outcome": outcome,
                        "transcript": transcript[:500],
                        "recording_url": vapi_webhook_payload.get("recordingUrl", "")
                    }
                )

                # Update lead state based on outcome
                if outcome.get("booked_call"):
                    self.close.update_lead_state(lead_id, "CALL_BOOKED", {"via": "vapi"})

                elif outcome.get("not_interested"):
                    self.close.update_lead_state(lead_id, "CLOSED_LOST", {"reason": "Not interested - voice call"})

                # Notify Slack
                self.slack.send_notification(
                    f"📞 *AI Call Completed*\n"
                    f"Duration: {duration}s\n"
                    f"Outcome: {outcome['summary']}\n"
                    f"Transcript: {transcript[:200]}...",
                    {}
                )

                return {"status": "processed", "outcome": outcome}

        return {"status": "no_lead_found"}

    def _analyze_call_outcome(self, transcript: str) -> Dict[str, Any]:
        """Analyze call transcript to determine outcome"""
        # Use Claude to analyze (simplified for now)
        if "calendar" in transcript.lower() or "book" in transcript.lower():
            return {
                "intent": "booking_interested",
                "booked_call": True,
                "not_interested": False,
                "summary": "Lead interested in booking a call"
            }
        elif "not interested" in transcript.lower() or "no thanks" in transcript.lower():
            return {
                "intent": "not_interested",
                "booked_call": False,
                "not_interested": True,
                "summary": "Lead not interested"
            }
        else:
            return {
                "intent": "needs_follow_up",
                "booked_call": False,
                "not_interested": False,
                "summary": "Lead needs more nurturing"
            }

    def _find_lead_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Find lead in Close CRM by phone number"""
        clean_phone = phone_number.replace("+1", "").replace("-", "").replace(" ", "")

        import requests
        response = requests.get(
            f"{self.close.base_url}/lead/",
            headers=self.close.headers,
            params={"_limit": 1, "query": f"phone:{clean_phone}"}
        )

        if response.status_code == 200:
            results = response.json().get("data", [])
            return results[0] if results else None

        return None
