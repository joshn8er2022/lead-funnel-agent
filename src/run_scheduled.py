#!/usr/bin/env python3
"""
Scheduled runner - processes all leads in nurture sequence
Called by GitHub Actions twice daily
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import LeadAgent

def main():
    print("=" * 60)
    print("SCHEDULED LEAD PROCESSING")
    print("=" * 60)

    agent = LeadAgent()

    try:
        results = agent.run_scheduled_tasks()

        print("\n" + "=" * 60)
        print("RESULTS:")
        print(f"  Leads Processed: {results['leads_processed']}")
        print(f"  Emails Sent: {results['emails_sent']}")
        print(f"  Bookings Detected: {results['bookings_detected']}")
        print(f"  Escalations: {results['escalations']}")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
