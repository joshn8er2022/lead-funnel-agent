"""
Custom HTML report generator using LLM for personalization
"""
import os
from typing import Dict, Any
from anthropic import Anthropic
from jinja2 import Template

class ReportGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def generate_report(self, lead_data: Dict[str, Any], step: int) -> str:
        """
        Generate a personalized HTML report for a lead
        Steps 3, 5, 7 get custom reports
        """
        lead_type = lead_data.get("leadType", "hume_connect")

        # Map step to report type
        report_types = {
            3: self._get_report_template_1(lead_type),
            5: self._get_report_template_2(lead_type),
            7: self._get_report_template_3(lead_type)
        }

        template_name, template_description = report_types.get(step, (None, None))

        if not template_name:
            return ""

        # Use Claude to generate personalized content
        personalized_content = self._personalize_content(lead_data, template_description)

        # Load HTML template
        html_template = self._load_html_template(template_name, lead_type)

        # Render with personalized content
        template = Template(html_template)
        return template.render(
            name=lead_data.get("name", "there"),
            company=lead_data.get("company", "your organization"),
            industry=lead_data.get("industry", "healthcare"),
            content=personalized_content,
            calendly_link="https://calendly.com/josh-myhumehealth"
        )

    def _get_report_template_1(self, lead_type: str) -> tuple:
        """First report template mapping"""
        templates = {
            "hume_connect": ("hc_roi_analysis", "ROI analysis for remote patient monitoring"),
            "wholesale": ("wholesale_pricing", "Bulk pricing and ROI calculator"),
            "affiliate": ("affiliate_commission", "Affiliate program commission breakdown")
        }
        return templates.get(lead_type, templates["hume_connect"])

    def _get_report_template_2(self, lead_type: str) -> tuple:
        """Second report template mapping"""
        templates = {
            "hume_connect": ("hc_integration", "Integration guide for existing systems"),
            "wholesale": ("wholesale_success", "Reseller success stories"),
            "affiliate": ("affiliate_tracking", "Partner tracking guide")
        }
        return templates.get(lead_type, templates["hume_connect"])

    def _get_report_template_3(self, lead_type: str) -> tuple:
        """Third report template mapping"""
        templates = {
            "hume_connect": ("hc_outcomes", "Clinical outcomes and case studies"),
            "wholesale": ("wholesale_implementation", "Implementation timeline"),
            "affiliate": ("affiliate_onboarding", "Complete onboarding guide")
        }
        return templates.get(lead_type, templates["hume_connect"])

    def _personalize_content(self, lead_data: Dict[str, Any], template_description: str) -> str:
        """Use Claude to generate personalized content"""

        prompt = f"""Generate personalized content for a {template_description} report.

Lead Details:
- Company: {lead_data.get('company', 'Unknown')}
- Industry: {lead_data.get('industry', 'Healthcare')}
- Goals: {lead_data.get('goals', 'Not specified')}
- Lead Type: {lead_data.get('leadType', 'Unknown')}

Create a detailed, professional report section (3-5 paragraphs) that:
1. Addresses their specific industry and goals
2. Includes relevant metrics and case studies
3. Shows clear ROI and value proposition
4. Is personalized to their company size and needs
5. Includes 2-3 specific data points or examples

Format as clean HTML (paragraphs, headings, lists only - no styling).
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _load_html_template(self, template_name: str, lead_type: str) -> str:
        """Load HTML template or return default"""

        default_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Custom Report for {{ company }}</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #007bff; margin-bottom: 10px;">Personalized Report</h1>
            <p style="color: #666; font-size: 14px;">Prepared for {{ company }}</p>
        </div>

        <!-- Content -->
        <div style="line-height: 1.6; color: #333;">
            {{ content | safe }}
        </div>

        <!-- CTA -->
        <div style="text-align: center; margin-top: 40px; padding-top: 30px; border-top: 2px solid #f0f0f0;">
            <p style="font-size: 18px; margin-bottom: 20px;">Ready to get started?</p>
            <a href="{{ calendly_link }}" style="background-color: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Schedule Your Call</a>
        </div>

        <!-- Footer -->
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #f0f0f0;">
            <p style="font-size: 12px; color: #999;">
                This report was generated specifically for {{ company }}<br>
                Have questions? Reply to this email anytime.
            </p>
        </div>
    </div>
</body>
</html>
"""

        # Try to load specific template, fall back to default
        try:
            template_path = f"templates/reports/{lead_type}_{template_name}.html"
            with open(template_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return default_template
