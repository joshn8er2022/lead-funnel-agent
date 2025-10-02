"""
Calendly booking checker - detect if a lead has booked a call
"""
import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class CalendlyChecker:
    def __init__(self):
        self.token = os.getenv("CALENDLY_TOKEN")
        self.org = os.getenv("CALENDLY_ORG", "josh-myhumehealth")
        self.base_url = "https://api.calendly.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def check_booking(self, email: str, since_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Check if a lead has booked a call
        Looks for bookings within 24 hours of submission (or custom date)
        """
        if not since_date:
            since_date = datetime.utcnow() - timedelta(hours=24)

        # Get user URI first
        user_uri = self._get_user_uri()
        if not user_uri:
            raise Exception("Could not fetch Calendly user URI")

        # Get scheduled events
        events = self._get_scheduled_events(user_uri, since_date)

        # Check if any event has an invitee with this email
        for event in events:
            invitees = self._get_event_invitees(event["uri"])
            for invitee in invitees:
                if invitee.get("email", "").lower() == email.lower():
                    return {
                        "uri": event["uri"],
                        "name": event["name"],
                        "start_time": event["start_time"],
                        "end_time": event["end_time"],
                        "status": event["status"],
                        "location": event.get("location", {}).get("location", "Not specified"),
                        "invitee_uri": invitee["uri"],
                        "invitee_email": invitee["email"],
                        "invitee_name": invitee["name"]
                    }

        return None

    def _get_user_uri(self) -> Optional[str]:
        """Get the current user's URI"""
        response = requests.get(
            f"{self.base_url}/users/me",
            headers=self.headers
        )

        if response.status_code == 200:
            return response.json()["resource"]["uri"]
        return None

    def _get_scheduled_events(self, user_uri: str, since_date: datetime) -> list:
        """Get scheduled events for a user"""
        params = {
            "user": user_uri,
            "min_start_time": since_date.isoformat() + "Z",
            "status": "active",
            "count": 100  # Check last 100 events
        }

        response = requests.get(
            f"{self.base_url}/scheduled_events",
            headers=self.headers,
            params=params
        )

        if response.status_code == 200:
            return response.json().get("collection", [])
        return []

    def _get_event_invitees(self, event_uri: str) -> list:
        """Get invitees for a specific event"""
        response = requests.get(
            f"{self.base_url}/scheduled_events/{event_uri.split('/')[-1]}/invitees",
            headers=self.headers
        )

        if response.status_code == 200:
            return response.json().get("collection", [])
        return []

    def get_upcoming_calls(self, email: str) -> list:
        """Get all upcoming calls for a lead"""
        user_uri = self._get_user_uri()
        if not user_uri:
            return []

        # Get future events
        now = datetime.utcnow()
        events = self._get_scheduled_events(user_uri, now)

        upcoming = []
        for event in events:
            invitees = self._get_event_invitees(event["uri"])
            for invitee in invitees:
                if invitee.get("email", "").lower() == email.lower():
                    upcoming.append({
                        "name": event["name"],
                        "start_time": event["start_time"],
                        "end_time": event["end_time"],
                        "status": event["status"]
                    })

        return upcoming
