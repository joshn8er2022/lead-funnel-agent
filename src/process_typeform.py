#!/usr/bin/env python3
"""
Typeform webhook processor - handles new submissions
"""
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import LeadAgent

def main():
    if len(sys.argv) < 2:
        print("Usage: process_typeform.py <payload_file>")
        return 1

    payload_file = sys.argv[1]

    print("=" * 60)
    print("PROCESSING TYPEFORM SUBMISSION")
    print("=" * 60)

    # Load payload
    with open(payload_file, 'r') as f:
        payload = json.load(f)

    print(f"\nForm ID: {payload.get('form_id', 'unknown')}")
    print(f"Response ID: {payload.get('response_id', 'unknown')}")

    # Process with agent
    agent = LeadAgent()

    try:
        result = agent.process_typeform_submission(payload)

        print("\n" + "=" * 60)
        print("RESULTS:")
        print(f"  Status: {result['status']}")
        print(f"  Path: {result['path']}")
        print(f"  Lead ID: {result['lead_id']}")
        print(f"  Email Sent: {result['email_sent']}")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
