"""
Main agent orchestrator - autonomous lead management
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from anthropic import Anthropic

from .classifier import LeadClassifier
from .close_sync import CloseClient
from .calendly_check import CalendlyChecker
from .email_engine import EmailEngine
from .slack_bot import SlackBot
from .report_generator import ReportGenerator

class LeadAgent:
    """
    Autonomous agent that manages the complete lead lifecycle
    """

    def __init__(self):
        self.classifier = LeadClassifier()
        self.close = CloseClient()
        self.calendly = CalendlyChecker()
        self.email_engine = EmailEngine()
        self.slack = SlackBot()
        self.report_gen = ReportGenerator()
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def process_typeform_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for new Typeform submissions
        """
        print(f"[Agent] Processing new Typeform submission")

        # 1. Classify the lead
        classified_lead = self.classifier.classify(payload)
        print(f"[Agent] Classified as: {classified_lead['leadType']}")

        # 2. Sync to Close CRM
        typeform_id = payload.get("response_id", payload.get("event_id", "unknown"))
        close_lead = self.close.upsert_lead(classified_lead, typeform_id)
        lead_id = close_lead["id"]
        print(f"[Agent] Synced to Close: {lead_id}")

        # 3. Check for Calendly booking
        email = classified_lead.get("email", "")
        calendly_booking = None

        if email:
            calendly_booking = self.calendly.check_booking(email)

        # 4. Route based on booking status
        if calendly_booking:
            print(f"[Agent] Booking detected! Entering BOOKED path")
            return self._handle_booked_lead(lead_id, classified_lead, calendly_booking)
        else:
            print(f"[Agent] No booking detected. Entering NURTURE path")
            return self._handle_unbooked_lead(lead_id, classified_lead)

    def _handle_booked_lead(self, lead_id: str, lead_data: Dict[str, Any], calendly_event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle leads who already booked a call"""

        # Mark as booked in Close
        self.close.mark_as_booked(lead_id, calendly_event)
        self.close.update_lead_state(lead_id, "BOOKED")

        # Send asset pack
        email_sent = self.email_engine.send_booked_asset_pack(lead_data, calendly_event)

        if email_sent:
            self.close.update_email_tracking(lead_id, 0, "Booked: Asset pack sent")

        # Notify Slack
        self.slack.send_notification(
            f"🎉 *New Booked Lead!*\nCall scheduled for {calendly_event['start_time']}",
            lead_data
        )

        return {
            "status": "success",
            "path": "booked",
            "lead_id": lead_id,
            "email_sent": email_sent
        }

    def _handle_unbooked_lead(self, lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle leads who haven't booked - start nurture sequence"""

        # Update state to NURTURING
        self.close.update_lead_state(lead_id, "NURTURING")

        # Send first nurture email immediately
        email_sent = self.email_engine.send_nurture_email(lead_data, step=1)

        if email_sent:
            self.close.update_email_tracking(lead_id, 1, "Nurture: Welcome email")

        # Notify Slack
        self.slack.send_notification(
            f"📥 *New Lead Entered Nurture*\nStarting 8-email sequence",
            lead_data
        )

        return {
            "status": "success",
            "path": "nurture",
            "lead_id": lead_id,
            "email_sent": email_sent
        }

    def run_scheduled_tasks(self) -> Dict[str, Any]:
        """
        Run scheduled tasks - called twice daily by GitHub Actions
        """
        print(f"[Agent] Running scheduled tasks at {datetime.utcnow().isoformat()}")

        results = {
            "emails_sent": 0,
            "bookings_detected": 0,
            "escalations": 0,
            "leads_processed": 0
        }

        # Get all leads in NURTURING state
        nurturing_leads = self._get_nurturing_leads()

        for lead in nurturing_leads:
            try:
                result = self._process_nurturing_lead(lead)
                results["leads_processed"] += 1

                if result.get("email_sent"):
                    results["emails_sent"] += 1
                if result.get("booking_detected"):
                    results["bookings_detected"] += 1
                if result.get("escalated"):
                    results["escalations"] += 1

            except Exception as e:
                print(f"[Agent] Error processing lead {lead.get('id')}: {str(e)}")
                self.slack.send_notification(f"❌ Error processing lead: {str(e)}")

        # Send summary to Slack
        self.slack.send_notification(
            f"""📊 *Scheduled Run Complete*
Leads Processed: {results['leads_processed']}
Emails Sent: {results['emails_sent']}
New Bookings: {results['bookings_detected']}
Escalations: {results['escalations']}"""
        )

        return results

    def _process_nurturing_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single lead in nurture sequence"""

        lead_id = lead["id"]
        email = self._get_lead_email(lead)
        current_step = int(lead.get("custom", {}).get("email_sequence_step", "0"))

        result = {
            "email_sent": False,
            "booking_detected": False,
            "escalated": False
        }

        # Check if they booked in the meantime
        if email:
            booking = self.calendly.check_booking(email)
            if booking:
                print(f"[Agent] Booking detected for lead {lead_id}!")
                self._convert_to_booked(lead, booking)
                result["booking_detected"] = True
                return result

        # Check if it's time to send next email
        next_step = current_step + 1

        if next_step > 8:
            # Sequence complete - notify via Slack
            print(f"[Agent] Lead {lead_id} completed sequence")
            lead_data = self._extract_lead_data(lead)
            self.slack.send_notification(
                f"⚠️ *Lead Completed Sequence*\nNo reply after 8 emails - review for closure",
                lead_data
            )
            self.close.update_lead_state(lead_id, "SEQUENCE_COMPLETE")
            result["escalated"] = True
            return result

        # Check if enough time has passed for next email
        lead_data = self._extract_lead_data(lead)

        if self.email_engine.should_send_email(lead_data, next_step):
            print(f"[Agent] Sending email step {next_step} to lead {lead_id}")

            # Generate custom report for steps 3, 5, 7
            custom_report = None
            if next_step in [3, 5, 7]:
                custom_report = self.report_gen.generate_report(lead_data, next_step)

            # Send email
            email_sent = self.email_engine.send_nurture_email(lead_data, next_step, custom_report)

            if email_sent:
                self.close.update_email_tracking(lead_id, next_step, f"Nurture step {next_step}")
                result["email_sent"] = True

                # Notify on key milestones
                if next_step == 4:
                    self.slack.send_notification(
                        f"📧 Milestone: Lead reached email 4 with no reply",
                        lead_data
                    )

        return result

    def _convert_to_booked(self, lead: Dict[str, Any], booking: Dict[str, Any]) -> None:
        """Convert a nurturing lead to booked status"""

        lead_id = lead["id"]
        lead_data = self._extract_lead_data(lead)

        # Mark as booked
        self.close.mark_as_booked(lead_id, booking)
        self.close.update_lead_state(lead_id, "BOOKED")

        # Send asset pack
        self.email_engine.send_booked_asset_pack(lead_data, booking)

        # Notify
        self.slack.send_notification(
            f"🎉 *Lead Converted to Booked!*\nWas in nurture, now scheduled call",
            lead_data
        )

    def _get_nurturing_leads(self) -> List[Dict[str, Any]]:
        """Get all leads currently in nurture sequence"""
        # This would query Close CRM for leads with agent_state = NURTURING
        # Placeholder implementation
        return []

    def _get_lead_email(self, lead: Dict[str, Any]) -> Optional[str]:
        """Extract email from lead object"""
        contacts = lead.get("contacts", [])
        if contacts and contacts[0].get("emails"):
            return contacts[0]["emails"][0]["email"]
        return None

    def _extract_lead_data(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Extract lead data into standard format"""
        contact = lead.get("contacts", [{}])[0]

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
