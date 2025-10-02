"""
Conversation Intelligence - Claude-powered sales conversation handler
Understands intent, qualifies leads, handles objections, books meetings
"""
import os
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
from datetime import datetime

class ConversationIntelligence:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines agent's sales personality"""
        return """You are Josh Israel's AI sales assistant for Hume, a body composition tracking solution company.

YOUR ROLE:
- Help leads understand Hume's value proposition
- Answer questions about pricing, features, implementation
- Handle objections professionally
- Qualify leads (budget, timeline, decision-making authority)
- Book discovery calls when appropriate
- Escalate complex questions to Josh

YOUR PRODUCTS:

1. **Hume Connect** (Patient Monitoring for Healthcare)
   - Remote body composition tracking
   - HIPAA-compliant
   - Integrates with existing EMR systems
   - Ideal for: Clinics, telehealth providers, wellness centers
   - Pricing: Contact for quote (based on patient volume)

2. **Hume Hardware** (Wholesale BodyPod Sales)
   - Bulk BodyPod units for gyms, franchises, corporate wellness
   - Hardware + Software bundles available
   - Implementation support included
   - Ideal for: Gym chains, corporate wellness, resellers
   - Pricing: Tiered based on volume (10+ units get bulk discount)

3. **Affiliate Program**
   - Partner with Hume to resell or refer
   - Commission-based structure
   - Marketing materials provided
   - Ideal for: Consultants, wellness coaches, tech resellers

YOUR PERSONALITY:
- Professional but friendly
- Consultative, not pushy
- Lead with value, not features
- Ask good qualifying questions
- Know when to book a call vs. continue nurturing

COMMON OBJECTIONS & RESPONSES:

**"This seems expensive"**
→ I understand. Let me ask - what's the cost of NOT having objective body composition data? Most of our clients see 30% better client retention when they use data-driven tracking. That ROI typically pays for the system in the first 2-3 months.

**"I need to think about it"**
→ Absolutely, this is an important decision. What specific concerns do you have that I can help address? Is it budget, implementation, or something else?

**"Can I get a discount?"**
→ We don't typically discount, but we do have volume pricing for 10+ units. How many locations/clients are you planning to serve?

**"How does this integrate with [X system]?"**
→ Great question! We have API integrations and can work with most systems. What's your current tech stack? I can have Josh walk you through the integration on a quick call.

**"I'm just researching right now"**
→ Perfect! I'm here to help. What's driving your research? Are you solving a specific problem or exploring options?

QUALIFICATION QUESTIONS TO ASK:
1. What's prompting you to look at body composition tracking now?
2. How many clients/patients would you be tracking?
3. What's your timeline for implementation?
4. Who else is involved in this decision?
5. What's your budget range?

WHEN TO BOOK A CALL:
- Lead asks detailed technical questions
- Lead asks about pricing for their specific use case
- Lead mentions timeline ("we need this by X")
- Lead has budget authority
- Lead asks "what's next?"

WHEN TO ESCALATE TO JOSH:
- Enterprise deals (100+ units)
- Complex custom integrations
- Legal/compliance questions beyond standard HIPAA
- Angry or dissatisfied leads
- Anything you're unsure about

CALENDLY LINK: https://calendly.com/josh-myhumehealth

TONE:
- Keep responses under 3-4 sentences unless explaining something complex
- Use line breaks for readability
- Always end with a question or clear next step
- Be human, not robotic
- Use "I" and "we" naturally
"""

    def analyze_message(self, message: str, lead_context: Dict[str, Any], conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Analyze an incoming message and determine:
        - Intent (question, objection, booking, info-request, etc.)
        - Sentiment (interested, hesitant, ready-to-buy, cold)
        - Qualification level (qualified, needs-qualification, unqualified)
        - Suggested response
        - Should escalate to human?
        """

        # Build context
        context = f"""
LEAD INFO:
- Name: {lead_context.get('name', 'Unknown')}
- Company: {lead_context.get('company', 'Unknown')}
- Industry: {lead_context.get('industry', 'Unknown')}
- Lead Type: {lead_context.get('leadType', 'Unknown')}
- Goals: {lead_context.get('goals', 'Not specified')}

CONVERSATION HISTORY:
{self._format_history(conversation_history or [])}

LATEST MESSAGE FROM LEAD:
"{message}"

ANALYZE THIS MESSAGE AND RESPOND IN JSON:
{{
  "intent": "question | objection | booking_request | info_request | pricing_question | ready_to_buy | unsubscribe | other",
  "sentiment": "very_interested | interested | neutral | hesitant | not_interested | frustrated",
  "qualification_level": "qualified | partially_qualified | unqualified | unknown",
  "key_concerns": ["list of concerns or questions they have"],
  "should_escalate": true/false,
  "escalation_reason": "why to escalate (or null)",
  "suggested_response": "your response to the lead",
  "should_book_call": true/false,
  "next_action": "send_response | book_call | escalate | send_resources | end_conversation"
}}
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": context}]
        )

        import json
        try:
            analysis = json.loads(response.content[0].text)
            return analysis
        except:
            # Fallback if JSON parsing fails
            return {
                "intent": "unknown",
                "sentiment": "neutral",
                "qualification_level": "unknown",
                "key_concerns": [],
                "should_escalate": True,
                "escalation_reason": "Failed to parse response - needs human review",
                "suggested_response": "Thanks for reaching out! I want to make sure I give you the best answer. Let me connect you with Josh directly: https://calendly.com/josh-myhumehealth",
                "should_book_call": True,
                "next_action": "escalate"
            }

    def generate_response(self, message: str, lead_context: Dict[str, Any], conversation_history: List[Dict[str, str]] = None, custom_instructions: Optional[str] = None) -> str:
        """
        Generate a conversational response to a lead's message
        """

        context = f"""
LEAD INFO:
- Name: {lead_context.get('name', 'Unknown')}
- Company: {lead_context.get('company', 'Unknown')}
- Industry: {lead_context.get('industry', 'Unknown')}
- Lead Type: {lead_context.get('leadType', 'Unknown')}
- Goals: {lead_context.get('goals', 'Not specified')}

CONVERSATION HISTORY:
{self._format_history(conversation_history or [])}

LATEST MESSAGE FROM LEAD:
"{message}"

{f"SPECIAL INSTRUCTIONS: {custom_instructions}" if custom_instructions else ""}

Generate a natural, helpful response that moves the conversation forward.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=self.system_prompt,
            messages=[{"role": "user", "content": context}]
        )

        return response.content[0].text

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for context"""
        if not history:
            return "No previous conversation"

        formatted = []
        for msg in history[-10:]:  # Last 10 messages only
            sender = msg.get("sender", "unknown")
            text = msg.get("text", "")
            timestamp = msg.get("timestamp", "")
            formatted.append(f"[{timestamp}] {sender}: {text}")

        return "\n".join(formatted)

    def should_make_call(self, lead_context: Dict[str, Any], conversation_history: List[Dict[str, str]]) -> bool:
        """
        Determine if agent should make a voice call via VAPI
        """

        # Criteria for making a call:
        # 1. High-value lead (wholesale, high priority)
        # 2. Multiple emails sent but no response
        # 3. Engaged in conversation but hasn't booked
        # 4. Asked about demos/pricing

        email_count = int(lead_context.get("custom", {}).get("email_sequence_step", "0"))
        lead_type = lead_context.get("leadType", "")
        priority = lead_context.get("priority", "")

        # High priority wholesale leads who haven't booked after 2 emails
        if lead_type == "wholesale" and priority == "high" and email_count >= 2:
            return True

        # Any lead with 4+ emails and no booking
        if email_count >= 4 and lead_context.get("custom", {}).get("booked", "") != "yes":
            return True

        # Lead asked about demos or pricing in conversation
        for msg in conversation_history[-5:]:
            text = msg.get("text", "").lower()
            if any(keyword in text for keyword in ["demo", "pricing", "price", "cost", "how much"]):
                return True

        return False
