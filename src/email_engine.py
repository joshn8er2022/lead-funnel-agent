"""
SendGrid email engine with sequences and personalization
"""
import os
from typing import Dict, Any, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime, timedelta
from jinja2 import Template

class EmailEngine:
    def __init__(self):
        self.sg = SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "josh@humeprograms.com")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "Josh Israel")
        self.reply_to = os.getenv("SENDGRID_REPLY_TO", "josh@myhumehealth.com")

    def send_booked_asset_pack(self, lead_data: Dict[str, Any], calendly_event: Dict[str, Any]) -> bool:
        """Send asset pack to leads who booked a call"""
        subject = f"Looking forward to our call on {self._format_date(calendly_event['start_time'])}"

        # Load template
        with open("templates/emails/booked_assets.html", "r") as f:
            template = Template(f.read())

        html_content = template.render(
            name=lead_data.get("name", "there"),
            company=lead_data.get("company", "your organization"),
            call_time=self._format_date(calendly_event['start_time']),
            call_link=calendly_event.get("location", "")
        )

        return self._send_email(
            to_email=lead_data["email"],
            to_name=lead_data.get("name", ""),
            subject=subject,
            html_content=html_content
        )

    def send_nurture_email(self, lead_data: Dict[str, Any], step: int, report_html: Optional[str] = None) -> bool:
        """Send a nurture sequence email"""
        templates = {
            1: ("nurture_1_welcome.html", "Welcome - Let's transform your practice"),
            2: ("nurture_2_case_study.html", "How {company} achieved results"),
            3: ("nurture_3_report.html", "Custom report: {industry} insights"),
            4: ("nurture_4_social_proof.html", "See what others are saying"),
            5: ("nurture_5_report.html", "Deep dive: Your personalized analysis"),
            6: ("nurture_6_problem_solution.html", "Solving the {industry} challenge"),
            7: ("nurture_7_final_report.html", "Your complete implementation guide"),
            8: ("nurture_8_breakup.html", "Last chance - should we close your file?")
        }

        template_file, subject_template = templates.get(step, templates[1])
        subject = subject_template.format(
            company=lead_data.get("company", "similar organizations"),
            industry=lead_data.get("industry", "your industry")
        )

        # Load template
        try:
            with open(f"templates/emails/{template_file}", "r") as f:
                template = Template(f.read())

            html_content = template.render(
                name=lead_data.get("name", "there"),
                company=lead_data.get("company", "your organization"),
                industry=lead_data.get("industry", "healthcare"),
                goals=lead_data.get("goals", "your goals"),
                lead_type=lead_data.get("leadType", "hume_connect"),
                custom_report=report_html or ""
            )

            return self._send_email(
                to_email=lead_data["email"],
                to_name=lead_data.get("name", ""),
                subject=subject,
                html_content=html_content
            )
        except FileNotFoundError:
            # Template doesn't exist yet, use fallback
            return self._send_fallback_email(lead_data, step, subject)

    def _send_email(self, to_email: str, to_name: str, subject: str, html_content: str) -> bool:
        """Send an email via SendGrid"""
        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email, to_name),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            # Add reply-to
            message.reply_to = Email(self.reply_to)

            # Send
            response = self.sg.send(message)

            return response.status_code in [200, 201, 202]
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    def _send_fallback_email(self, lead_data: Dict[str, Any], step: int, subject: str) -> bool:
        """Fallback email when template doesn't exist"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Hi {lead_data.get('name', 'there')},</h2>
            <p>This is follow-up #{step} from our team at Hume.</p>
            <p>I wanted to check in about your interest in {lead_data.get('goals', 'our solutions')}.</p>
            <p>Would you like to schedule a quick call to discuss how we can help {lead_data.get('company', 'your organization')}?</p>
            <p><a href="https://calendly.com/josh-myhumehealth" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Book a Call</a></p>
            <p>Best regards,<br>{self.from_name}</p>
            <hr>
            <p style="font-size: 12px; color: #666;">
                <a href="{{{{unsubscribe}}}}">Unsubscribe</a>
            </p>
        </body>
        </html>
        """

        return self._send_email(
            to_email=lead_data["email"],
            to_name=lead_data.get("name", ""),
            subject=subject,
            html_content=html_content
        )

    def _format_date(self, iso_date: str) -> str:
        """Format ISO date to human-readable"""
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            return dt.strftime("%A, %B %d at %I:%M %p")
        except:
            return iso_date

    def get_next_email_date(self, step: int, last_sent: Optional[datetime] = None) -> datetime:
        """Calculate when the next email should be sent"""
        schedule = {
            1: 0,   # Immediate
            2: 3,   # Day 3
            3: 7,   # Day 7
            4: 10,  # Day 10
            5: 14,  # Day 14
            6: 17,  # Day 17
            7: 21,  # Day 21
            8: 28   # Day 28
        }

        days_delay = schedule.get(step, 0)

        if last_sent:
            return last_sent + timedelta(days=days_delay)
        else:
            return datetime.utcnow() + timedelta(days=days_delay)

    def should_send_email(self, lead_data: Dict[str, Any], step: int) -> bool:
        """Check if it's time to send the next email"""
        last_sent_str = lead_data.get("custom", {}).get("last_email_sent", "")

        if not last_sent_str:
            # First email, send immediately
            return step == 1

        try:
            last_sent = datetime.fromisoformat(last_sent_str)
            next_send = self.get_next_email_date(step, last_sent)
            return datetime.utcnow() >= next_send
        except:
            return False
