#!/usr/bin/env python3
"""
Slack bot event handler - for receiving commands in #ai-test channel
This would typically run as a separate server (Flask/FastAPI)
For GitHub Actions, we'll handle it differently via manual triggers
"""
import os
import sys
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slack_bot import SlackBot

def create_app():
    """Create Slack Bolt app"""
    app = App(
        token=os.getenv("SLACK_BOT_TOKEN"),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET")
    )

    bot = SlackBot()

    # Handle app mentions
    @app.event("app_mention")
    def handle_mention(event, say):
        user = event["user"]
        text = event["text"]

        # Remove mention from text
        text = text.split(">", 1)[-1].strip()

        response = bot.process_command(text, user)
        say(response)

    # Handle direct messages
    @app.event("message")
    def handle_message(event, say):
        # Ignore bot messages
        if event.get("bot_id"):
            return

        user = event["user"]
        text = event["text"]

        response = bot.process_command(text, user)
        say(response)

    return app

def main():
    """Run the Slack bot server"""
    app = create_app()

    print("⚡️ Slack bot is running!")
    app.start(port=int(os.getenv("PORT", 3000)))

if __name__ == "__main__":
    main()
