#!/usr/bin/env python3
"""
Test all integrations to make sure everything is configured correctly
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_env_vars():
    """Check all required environment variables"""
    required = [
        "TYPEFORM_TOKEN",
        "CLOSE_API_KEY",
        "CALENDLY_TOKEN",
        "SENDGRID_API_KEY",
        "ANTHROPIC_API_KEY",
        "SLACK_BOT_TOKEN"
    ]

    print("=" * 60)
    print("CHECKING ENVIRONMENT VARIABLES")
    print("=" * 60)

    missing = []
    for var in required:
        value = os.getenv(var)
        if value:
            # Show first 10 chars only
            preview = value[:10] + "..."
            print(f"✓ {var}: {preview}")
        else:
            print(f"✗ {var}: MISSING")
            missing.append(var)

    if missing:
        print(f"\n❌ Missing variables: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All environment variables set")
        return True

def test_close_connection():
    """Test Close CRM connection"""
    print("\n" + "=" * 60)
    print("TESTING CLOSE CRM CONNECTION")
    print("=" * 60)

    try:
        from close_sync import CloseClient
        close = CloseClient()

        # Try to make a simple API call
        import requests
        response = requests.get(
            f"{close.base_url}/status/",
            headers=close.headers
        )

        if response.status_code == 200:
            print("✅ Close CRM: Connected")
            return True
        else:
            print(f"❌ Close CRM: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Close CRM: Error - {str(e)}")
        return False

def test_calendly_connection():
    """Test Calendly connection"""
    print("\n" + "=" * 60)
    print("TESTING CALENDLY CONNECTION")
    print("=" * 60)

    try:
        from calendly_check import CalendlyChecker
        calendly = CalendlyChecker()

        user_uri = calendly._get_user_uri()

        if user_uri:
            print(f"✅ Calendly: Connected")
            print(f"   User URI: {user_uri}")
            return True
        else:
            print("❌ Calendly: Failed to get user URI")
            return False
    except Exception as e:
        print(f"❌ Calendly: Error - {str(e)}")
        return False

def test_sendgrid_connection():
    """Test SendGrid connection"""
    print("\n" + "=" * 60)
    print("TESTING SENDGRID CONNECTION")
    print("=" * 60)

    try:
        from sendgrid import SendGridAPIClient

        sg = SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))

        # Just check if we can initialize
        print("✅ SendGrid: API key loaded")
        return True
    except Exception as e:
        print(f"❌ SendGrid: Error - {str(e)}")
        return False

def test_anthropic_connection():
    """Test Anthropic API connection"""
    print("\n" + "=" * 60)
    print("TESTING ANTHROPIC API CONNECTION")
    print("=" * 60)

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Make a simple API call
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'Connected'"}]
        )

        if response.content[0].text:
            print("✅ Anthropic API: Connected")
            print(f"   Response: {response.content[0].text[:50]}")
            return True
        else:
            print("❌ Anthropic API: No response")
            return False
    except Exception as e:
        print(f"❌ Anthropic API: Error - {str(e)}")
        return False

def test_slack_connection():
    """Test Slack connection"""
    print("\n" + "=" * 60)
    print("TESTING SLACK CONNECTION")
    print("=" * 60)

    try:
        from slack_sdk import WebClient

        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

        # Test auth
        response = client.auth_test()

        if response["ok"]:
            print("✅ Slack: Connected")
            print(f"   Bot: {response.get('user', 'Unknown')}")
            print(f"   Team: {response.get('team', 'Unknown')}")
            return True
        else:
            print("❌ Slack: Auth failed")
            return False
    except Exception as e:
        print(f"❌ Slack: Error - {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n🔍 INTEGRATION TEST SUITE")
    print("Testing all connections...\n")

    results = []

    results.append(("Environment Variables", test_env_vars()))
    results.append(("Close CRM", test_close_connection()))
    results.append(("Calendly", test_calendly_connection()))
    results.append(("SendGrid", test_sendgrid_connection()))
    results.append(("Anthropic API", test_anthropic_connection()))
    results.append(("Slack", test_slack_connection()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
