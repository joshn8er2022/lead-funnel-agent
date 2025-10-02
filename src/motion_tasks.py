"""
Motion API integration - auto-create tasks for lead follow-ups
"""
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class MotionClient:
    def __init__(self):
        self.api_key = os.getenv("MOTION_API_KEY")
        self.base_url = "https://api.usemotion.com/v1"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        self.workspace_id = os.getenv("MOTION_WORKSPACE_ID")
        self.project_id = os.getenv("MOTION_PROJECT_ID")  # Lead Funnel Automation project

    def create_lead_follow_up_task(self, lead_data: Dict[str, Any], priority: str = "MEDIUM") -> Dict[str, Any]:
        """Create a follow-up task for a new lead"""

        task_name = f"Follow up: {lead_data.get('name', 'Unknown')} - {lead_data.get('company', 'No Company')}"

        description = f"""Lead Type: {lead_data.get('leadType', 'Unknown')}
Email: {lead_data.get('email', 'N/A')}
Phone: {lead_data.get('phone', 'N/A')}
Goals: {lead_data.get('goals', 'Not specified')}
Source: Typeform

Action: Monitor lead progress and intervene if needed
"""

        payload = {
            "name": task_name,
            "description": description,
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "priority": priority,
            "dueDate": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            "duration": 15,  # 15 minutes
            "labels": [lead_data.get('leadType', 'unknown'), "lead-follow-up"]
        }

        response = requests.post(
            f"{self.base_url}/tasks",
            headers=self.headers,
            json=payload
        )

        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create Motion task: {response.text}")

    def create_call_prep_task(self, lead_data: Dict[str, Any], call_time: str) -> Dict[str, Any]:
        """Create a call prep task when Calendly booking detected"""

        task_name = f"📞 Call prep: {lead_data.get('name', 'Unknown')} - {lead_data.get('company', 'No Company')}"

        description = f"""CALL SCHEDULED for {call_time}

Lead Details:
- Type: {lead_data.get('leadType', 'Unknown')}
- Email: {lead_data.get('email', 'N/A')}
- Phone: {lead_data.get('phone', 'N/A')}
- Company: {lead_data.get('company', 'N/A')}
- Industry: {lead_data.get('industry', 'N/A')}
- Goals: {lead_data.get('goals', 'Not specified')}

Prep Tasks:
□ Review lead submission details
□ Research company/industry
□ Prepare customized demo
□ Have pricing sheet ready
□ Calendar blocked
"""

        # Parse call time to set due date 1 hour before
        try:
            call_dt = datetime.fromisoformat(call_time.replace("Z", "+00:00"))
            due_date = call_dt - timedelta(hours=1)
        except:
            due_date = datetime.utcnow() + timedelta(hours=1)

        payload = {
            "name": task_name,
            "description": description,
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "priority": "ASAP",
            "dueDate": due_date.isoformat(),
            "duration": 30,  # 30 minutes prep time
            "labels": [lead_data.get('leadType', 'unknown'), "call-prep", "booked"]
        }

        response = requests.post(
            f"{self.base_url}/tasks",
            headers=self.headers,
            json=payload
        )

        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create call prep task: {response.text}")

    def create_escalation_task(self, lead_data: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Create an escalation task when agent needs human intervention"""

        task_name = f"⚠️ Escalation: {lead_data.get('name', 'Unknown')} - {reason}"

        description = f"""Agent needs help with this lead.

Reason: {reason}

Lead Details:
- Type: {lead_data.get('leadType', 'Unknown')}
- Email: {lead_data.get('email', 'N/A')}
- Phone: {lead_data.get('phone', 'N/A')}
- Company: {lead_data.get('company', 'N/A')}
- Current State: {lead_data.get('custom', {}).get('agent_state', 'Unknown')}
- Emails Sent: {lead_data.get('custom', {}).get('email_sequence_step', '0')}

Action Required:
Review lead and decide next steps
"""

        payload = {
            "name": task_name,
            "description": description,
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "priority": "HIGH",
            "dueDate": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "duration": 20,
            "labels": [lead_data.get('leadType', 'unknown'), "escalation", "needs-attention"]
        }

        response = requests.post(
            f"{self.base_url}/tasks",
            headers=self.headers,
            json=payload
        )

        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create escalation task: {response.text}")

    def create_reminder_task(self, lead_data: Dict[str, Any], days_ahead: int, message: str) -> Dict[str, Any]:
        """Create a reminder task for future follow-up"""

        task_name = f"⏰ Reminder: {lead_data.get('name', 'Unknown')} - {message}"

        payload = {
            "name": task_name,
            "description": f"Follow up reminder\n\nLead: {lead_data.get('email', 'N/A')}\nMessage: {message}",
            "workspaceId": self.workspace_id,
            "projectId": self.project_id,
            "priority": "LOW",
            "dueDate": (datetime.utcnow() + timedelta(days=days_ahead)).isoformat(),
            "duration": 10,
            "labels": [lead_data.get('leadType', 'unknown'), "reminder"]
        }

        response = requests.post(
            f"{self.base_url}/tasks",
            headers=self.headers,
            json=payload
        )

        if response.status_code in [200, 201]:
            return response.json()
        else:
            # Don't fail on reminder tasks
            print(f"Warning: Failed to create reminder task: {response.text}")
            return {}

    def create_no_reply_escalation(self, lead_data: Dict[str, Any], emails_sent: int) -> Dict[str, Any]:
        """Escalate when lead hasn't replied after multiple emails"""

        return self.create_escalation_task(
            lead_data,
            f"No reply after {emails_sent} emails - consider closing or changing approach"
        )
