"""
Close CRM integration - create/update leads, contacts, activities
"""
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime

class CloseClient:
    def __init__(self):
        self.api_key = os.getenv("CLOSE_API_KEY")
        self.base_url = "https://api.close.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def upsert_lead(self, lead_data: Dict[str, Any], typeform_id: str) -> Dict[str, Any]:
        """
        Create or update a lead in Close CRM
        Uses external_id to prevent duplicates
        """
        external_id = f"typeform_{typeform_id}"

        # Check if lead exists
        existing_lead = self._find_lead_by_external_id(external_id)

        if existing_lead:
            # Update existing lead
            lead_id = existing_lead["id"]
            return self._update_lead(lead_id, lead_data)
        else:
            # Create new lead
            return self._create_lead(lead_data, external_id)

    def _find_lead_by_external_id(self, external_id: str) -> Optional[Dict[str, Any]]:
        """Find lead by external_id"""
        params = {
            "_limit": 1,
            "query": f'custom.external_id:"{external_id}"'
        }

        response = requests.get(
            f"{self.base_url}/lead/",
            headers=self.headers,
            params=params
        )

        if response.status_code == 200:
            results = response.json().get("data", [])
            return results[0] if results else None
        return None

    def _create_lead(self, lead_data: Dict[str, Any], external_id: str) -> Dict[str, Any]:
        """Create a new lead in Close"""
        payload = {
            "name": lead_data.get("company", f"{lead_data.get('name', 'Unknown')} Lead"),
            "custom.external_id": external_id,
            "custom.lead_type": lead_data.get("leadType"),
            "custom.priority": lead_data.get("priority"),
            "custom.agent_state": "NEW",
            "custom.industry": lead_data.get("industry"),
            "custom.goals": lead_data.get("goals"),
            "status_id": self._get_status_id("New Lead")
        }

        # Add custom fields for tracking
        payload["custom.source"] = "typeform"
        payload["custom.form_id"] = lead_data.get("form_id", "")
        payload["custom.booked"] = "no"
        payload["custom.last_email_sent"] = ""
        payload["custom.email_sequence_step"] = "0"

        response = requests.post(
            f"{self.base_url}/lead/",
            headers=self.headers,
            json=payload
        )

        if response.status_code == 200:
            lead = response.json()
            # Create contact for this lead
            self._create_contact(lead["id"], lead_data)
            # Log activity
            self._log_activity(lead["id"], "Lead created from Typeform submission", lead_data)
            return lead
        else:
            raise Exception(f"Failed to create lead: {response.text}")

    def _update_lead(self, lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing lead"""
        payload = {
            "custom.priority": lead_data.get("priority"),
            "custom.goals": lead_data.get("goals"),
        }

        response = requests.put(
            f"{self.base_url}/lead/{lead_id}/",
            headers=self.headers,
            json=payload
        )

        if response.status_code == 200:
            # Log update activity
            self._log_activity(lead_id, "Lead updated from new Typeform submission", lead_data)
            return response.json()
        else:
            raise Exception(f"Failed to update lead: {response.text}")

    def _create_contact(self, lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update contact for a lead"""
        payload = {
            "lead_id": lead_id,
            "name": lead_data.get("name", "Unknown"),
            "emails": [{"email": lead_data.get("email")}] if lead_data.get("email") else [],
            "phones": [{"phone": lead_data.get("phone")}] if lead_data.get("phone") else []
        }

        # Check if contact already exists
        response = requests.get(
            f"{self.base_url}/contact/",
            headers=self.headers,
            params={"lead_id": lead_id}
        )

        if response.status_code == 200:
            contacts = response.json().get("data", [])
            if contacts:
                # Update existing contact
                contact_id = contacts[0]["id"]
                response = requests.put(
                    f"{self.base_url}/contact/{contact_id}/",
                    headers=self.headers,
                    json=payload
                )
                return response.json()

        # Create new contact
        response = requests.post(
            f"{self.base_url}/contact/",
            headers=self.headers,
            json=payload
        )

        return response.json() if response.status_code == 200 else {}

    def _log_activity(self, lead_id: str, note: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an activity note to a lead"""
        timestamp = datetime.utcnow().isoformat()

        note_content = f"{note}\n\nTimestamp: {timestamp}"
        if metadata:
            note_content += f"\n\nMetadata:\n{self._format_metadata(metadata)}"

        payload = {
            "lead_id": lead_id,
            "note": note_content
        }

        response = requests.post(
            f"{self.base_url}/activity/note/",
            headers=self.headers,
            json=payload
        )

        return response.json() if response.status_code == 200 else {}

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for activity note"""
        lines = []
        for key, value in metadata.items():
            if value and key not in ["email", "phone"]:  # Skip PII in notes
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _get_status_id(self, status_name: str) -> str:
        """Get status ID by name (you'll need to configure this for your Close org)"""
        # For now, return a placeholder - you'll need to fetch your actual status IDs
        # from Close and map them here
        status_map = {
            "New Lead": "stat_new",  # Replace with actual status ID
            "Contacted": "stat_contacted",
            "Qualified": "stat_qualified",
            "Closed Won": "stat_won",
            "Closed Lost": "stat_lost"
        }
        return status_map.get(status_name, "stat_new")

    def update_lead_state(self, lead_id: str, new_state: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update the agent state for a lead"""
        payload = {
            "custom.agent_state": new_state,
            "custom.state_updated_at": datetime.utcnow().isoformat()
        }

        response = requests.put(
            f"{self.base_url}/lead/{lead_id}/",
            headers=self.headers,
            json=payload
        )

        if response.status_code == 200:
            self._log_activity(lead_id, f"Agent state changed to: {new_state}", metadata)
            return response.json()
        else:
            raise Exception(f"Failed to update lead state: {response.text}")

    def mark_as_booked(self, lead_id: str, calendly_event: Dict[str, Any]):
        """Mark a lead as having booked a call"""
        payload = {
            "custom.booked": "yes",
            "custom.calendly_event_uri": calendly_event.get("uri", ""),
            "custom.call_scheduled_at": calendly_event.get("start_time", ""),
            "status_id": self._get_status_id("Qualified")
        }

        response = requests.put(
            f"{self.base_url}/lead/{lead_id}/",
            headers=self.headers,
            json=payload
        )

        if response.status_code == 200:
            self._log_activity(lead_id, "Calendly booking detected", calendly_event)

        return response.json() if response.status_code == 200 else {}

    def update_email_tracking(self, lead_id: str, email_step: int, email_subject: str):
        """Track email sends"""
        payload = {
            "custom.email_sequence_step": str(email_step),
            "custom.last_email_sent": datetime.utcnow().isoformat(),
            "custom.last_email_subject": email_subject
        }

        response = requests.put(
            f"{self.base_url}/lead/{lead_id}/",
            headers=self.headers,
            json=payload
        )

        if response.status_code == 200:
            self._log_activity(lead_id, f"Sent email: {email_subject}")

        return response.json() if response.status_code == 200 else {}

    def get_lead_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a lead by contact email"""
        params = {
            "_limit": 1,
            "query": f'email:"{email}"'
        }

        response = requests.get(
            f"{self.base_url}/lead/",
            headers=self.headers,
            params=params
        )

        if response.status_code == 200:
            results = response.json().get("data", [])
            return results[0] if results else None
        return None
