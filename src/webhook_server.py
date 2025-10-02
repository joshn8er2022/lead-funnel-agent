#!/usr/bin/env python3
"""
Webhook Server - Receives webhooks from SendGrid (email replies), Twilio (SMS), and VAPI (call events)
Run this as a separate service or deploy to serverless platform
"""
from flask import Flask, request, jsonify
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import LeadAgent

app = Flask(__name__)
agent = LeadAgent()

@app.route('/webhook/email', methods=['POST'])
def handle_email_webhook():
    """
    SendGrid Inbound Parse webhook
    Configured at: https://app.sendgrid.com/settings/parse
    """
    try:
        # SendGrid sends form data
        payload = {
            "from": request.form.get("from", ""),
            "to": request.form.get("to", ""),
            "subject": request.form.get("subject", ""),
            "text": request.form.get("text", ""),
            "html": request.form.get("html", "")
        }

        print(f"[Webhook] Email received from: {payload['from']}")

        result = agent.email_handler.handle_inbound_email(payload)

        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        print(f"[Webhook] Email error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/sms', methods=['POST'])
def handle_sms_webhook():
    """
    Twilio SMS webhook
    Configured in Twilio console: https://console.twilio.com
    """
    try:
        payload = {
            "From": request.form.get("From", ""),
            "To": request.form.get("To", ""),
            "Body": request.form.get("Body", ""),
            "MessageSid": request.form.get("MessageSid", ""),
            "FromCity": request.form.get("FromCity", ""),
            "FromState": request.form.get("FromState", "")
        }

        print(f"[Webhook] SMS received from: {payload['From']}")

        # Handle with agent
        twiml_response = agent.sms_handler.handle_inbound_sms(payload)

        # Return TwiML
        return twiml_response, 200, {'Content-Type': 'application/xml'}

    except Exception as e:
        print(f"[Webhook] SMS error: {str(e)}")
        return f"<Response><Message>Error processing message</Message></Response>", 500, {'Content-Type': 'application/xml'}

@app.route('/webhook/vapi', methods=['POST'])
def handle_vapi_webhook():
    """
    VAPI webhook for call events
    Configured in VAPI dashboard: https://dashboard.vapi.ai
    """
    try:
        payload = request.json

        event_type = payload.get("type", "")

        print(f"[Webhook] VAPI event: {event_type}")

        if event_type == "call.ended":
            result = agent.vapi_handler.handle_call_ended(payload)
            return jsonify({"status": "success", "result": result}), 200

        # Other VAPI events
        return jsonify({"status": "acknowledged"}), 200

    except Exception as e:
        print(f"[Webhook] VAPI error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/typeform', methods=['POST'])
def handle_typeform_webhook():
    """
    Typeform webhook (alternative to GitHub Actions)
    Direct webhook from Typeform
    """
    try:
        payload = request.json

        print(f"[Webhook] Typeform submission")

        result = agent.process_typeform_submission(payload)

        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        print(f"[Webhook] Typeform error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "lead-funnel-agent"}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Webhook server starting on port {port}")
    print("Endpoints:")
    print(f"  - POST /webhook/email (SendGrid)")
    print(f"  - POST /webhook/sms (Twilio)")
    print(f"  - POST /webhook/vapi (VAPI)")
    print(f"  - POST /webhook/typeform (Typeform)")
    print(f"  - GET  /health")

    app.run(host="0.0.0.0", port=port, debug=False)
