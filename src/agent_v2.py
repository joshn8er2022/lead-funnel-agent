"""
Extended agent methods for Phase 2 - Full conversational AI
Adds to agent.py
"""

def make_proactive_calls(self) -> Dict[str, Any]:
    """
    Make proactive VAPI calls to qualified leads who haven't booked
    Called during scheduled runs
    """
    print("[Agent] Checking for leads who need calls")

    # Get leads that should be called
    leads_to_call = self._get_leads_for_calling()

    results = {
        "calls_made": 0,
        "errors": 0
    }

    for lead in leads_to_call:
        try:
            lead_data = self._extract_lead_data(lead)
            lead_data["close_lead_id"] = lead["id"]

            # Determine call reason
            reason = self._determine_call_reason(lead_data)

            # Make the call
            result = self.vapi_handler.make_outbound_call(lead_data, reason)

            if result["status"] == "success":
                results["calls_made"] += 1
                # Update state
                self.close.update_lead_state(lead["id"], "CALLING", {"call_id": result["call_id"]})
            else:
                results["errors"] += 1

        except Exception as e:
            print(f"[Agent] Error calling lead: {str(e)}")
            results["errors"] += 1

    return results

def _get_leads_for_calling(self) -> List[Dict[str, Any]]:
    """Get leads that should receive voice calls"""
    # Query Close for leads meeting call criteria
    # - High priority wholesale leads after 2 emails
    # - Any lead after 4 emails with no response
    # - Leads who asked about demos/pricing but didn't book
    return []  # Placeholder

def _determine_call_reason(self, lead_data: Dict[str, Any]) -> str:
    """Determine why we're calling this lead"""
    email_count = int(lead_data.get("custom", {}).get("email_sequence_step", "0"))

    if email_count >= 4:
        return "follow_up"
    elif lead_data.get("leadType") == "wholesale":
        return "pricing_question"
    else:
        return "demo_reminder"

def process_sms_reply(self, phone: str, message: str) -> Dict[str, Any]:
    """
    Process incoming SMS
    Called by webhook handler
    """
    return self.sms_handler.handle_inbound_sms({
        "From": phone,
        "Body": message
    })

def process_email_reply(self, from_email: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Process incoming email reply
    Called by SendGrid webhook
    """
    return self.email_handler.handle_inbound_email({
        "from": from_email,
        "subject": subject,
        "text": body
    })

def send_proactive_sms(self, lead_id: str, message: str) -> bool:
    """Send a proactive SMS to a lead"""
    lead = self.close._get_lead_by_id(lead_id)

    if not lead:
        return False

    lead_data = self._extract_lead_data(lead)
    phone = lead_data.get("phone", "")

    if not phone:
        return False

    return self.sms_handler.send_proactive_sms(phone, message, lead_id)
