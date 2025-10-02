"""
Lead classification engine using rules + LLM fallback
"""
import os
from typing import Dict, Any, Literal
from anthropic import Anthropic

LeadType = Literal["hume_connect", "wholesale", "affiliate"]

class LeadClassifier:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.hc_form_id = os.getenv("TYPEFORM_HC_FORM_ID", "F7whHyXK")
        self.hw_form_id = os.getenv("TYPEFORM_HW_FORM_ID", "wR9Ufu8Z")

    def classify(self, typeform_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a lead from Typeform submission
        Returns: {leadType, intent, priority, industry, company, goals}
        """
        form_id = typeform_payload.get("form_id", "")
        answers = typeform_payload.get("answers", [])

        # Rule-based classification first
        if form_id == self.hc_form_id:
            return self._classify_hume_connect(typeform_payload)
        elif form_id == self.hw_form_id:
            return self._classify_wholesale(typeform_payload)
        else:
            # Fallback to LLM for ambiguous cases
            return self._classify_with_llm(typeform_payload)

    def _classify_hume_connect(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Hume Connect leads - patient monitoring solutions"""
        answers = payload.get("answers", [])

        # Extract key information
        extracted = self._extract_answers(answers)

        return {
            "leadType": "hume_connect",
            "intent": "body_composition_tracking",
            "priority": self._calculate_priority(extracted),
            "industry": extracted.get("industry", "healthcare"),
            "company": extracted.get("company", "Unknown"),
            "goals": extracted.get("goals", "Patient monitoring"),
            "email": extracted.get("email", ""),
            "name": extracted.get("name", ""),
            "phone": extracted.get("phone", "")
        }

    def _classify_wholesale(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Wholesale leads - bulk BodyPod purchases"""
        answers = payload.get("answers", [])
        extracted = self._extract_answers(answers)

        return {
            "leadType": "wholesale",
            "intent": "bulk_purchase",
            "priority": self._calculate_priority(extracted, is_wholesale=True),
            "industry": extracted.get("industry", "fitness"),
            "company": extracted.get("company", "Unknown"),
            "goals": extracted.get("goals", "Bulk equipment purchase"),
            "email": extracted.get("email", ""),
            "name": extracted.get("name", ""),
            "phone": extracted.get("phone", "")
        }

    def _classify_with_llm(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Use Claude to classify ambiguous leads"""
        answers = payload.get("answers", [])
        answers_text = "\n".join([
            f"Q: {a.get('field', {}).get('title', 'Unknown')}\nA: {a.get('text', a.get('choice', 'N/A'))}"
            for a in answers
        ])

        prompt = f"""Analyze this Typeform submission and classify the lead.

Submission:
{answers_text}

Classify as one of:
1. hume_connect - Interested in patient monitoring, body composition tracking, healthcare solutions
2. wholesale - Interested in bulk purchases of BodyPod equipment, reseller inquiries
3. affiliate - Partnership, referral programs, affiliate marketing

Return JSON with:
{{
  "leadType": "hume_connect" | "wholesale" | "affiliate",
  "intent": "brief description of what they want",
  "priority": "high" | "medium" | "low",
  "industry": "their industry",
  "company": "company name",
  "goals": "their stated goals",
  "email": "email address",
  "name": "contact name",
  "phone": "phone number if provided"
}}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        result = json.loads(response.content[0].text)
        return result

    def _extract_answers(self, answers: list) -> Dict[str, str]:
        """Extract common fields from Typeform answers"""
        extracted = {}

        for answer in answers:
            field_title = answer.get("field", {}).get("title", "").lower()
            value = answer.get("text") or answer.get("email") or answer.get("phone_number") or answer.get("choice", {}).get("label", "")

            # Map common field types
            if "email" in field_title:
                extracted["email"] = value
            elif "name" in field_title:
                extracted["name"] = value
            elif "phone" in field_title:
                extracted["phone"] = value
            elif "company" in field_title or "organization" in field_title:
                extracted["company"] = value
            elif "industry" in field_title:
                extracted["industry"] = value
            elif "goal" in field_title or "looking for" in field_title:
                extracted["goals"] = value

        return extracted

    def _calculate_priority(self, extracted: Dict[str, str], is_wholesale: bool = False) -> str:
        """Calculate lead priority based on signals"""
        priority_signals = 0

        # Wholesale leads are higher priority
        if is_wholesale:
            priority_signals += 2

        # Has phone number
        if extracted.get("phone"):
            priority_signals += 1

        # Company name provided
        if extracted.get("company") and extracted["company"] != "Unknown":
            priority_signals += 1

        # Specific goals mentioned
        if extracted.get("goals") and len(extracted["goals"]) > 20:
            priority_signals += 1

        if priority_signals >= 4:
            return "high"
        elif priority_signals >= 2:
            return "medium"
        else:
            return "low"
