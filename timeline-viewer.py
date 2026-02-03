#!/usr/bin/env python3
"""
Timeline Viewer - READ-ONLY
Shows recent timeline activities with minimal data.
"""
import os
import sys
import json
import argparse
import requests
from datetime import datetime

def safe_timeline_query(domain, access_key, user_email, limit=3):
    url = f"{domain.rstrip('/')}/v1/data/objects/query/activity_timeline"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accesskey": access_key,
    }

    safe_query = {
        "select": [
            "Gsid",
            "CreatedDate",
            "Subject",
            "Notes",
            "ActivityDate",
            "contextname",
            "AuthorId",
            "GsCompanyId",
            "GsRelationshipId"
        ],
        "where": {
            "conditions": [
                {
                    "name": "AuthorId__gr.Email",
                    "alias": "A",
                    "value": [user_email],
                    "operator": "EQ"
                }
            ],
            "expression": "A"
        },
        "orderBy": {
            "CreatedDate": "desc"
        },
        "limit": limit,
        "offset": 0
    }

    try:
        print(f"🔍 Querying Timeline activities for {user_email} (limit: {limit})...")
        resp = requests.post(url, headers=headers, data=json.dumps(safe_query), timeout=15)

        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"   ❌ HTTP {resp.status_code}: {resp.text[:200]}")
            return None

    except requests.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None

def format_timeline_data(data):
    if not data or not data.get('result'):
        return "   No Timeline data available"

    records = data.get('data', {})
    if isinstance(records, dict) and 'records' in records:
        activities = records['records']
    elif isinstance(records, list):
        activities = records
    else:
        return "   Unexpected data format from Timeline API"

    if not activities:
        return "   No activities found in Timeline"

    output = [f"   📊 Found {len(activities)} Timeline activities:"]

    for i, activity in enumerate(activities, 1):
        date_str = "Unknown date"
        for date_field in ['ActivityDate', 'CreatedDate']:
            if date_field in activity and activity[date_field]:
                try:
                    date_obj = datetime.fromisoformat(activity[date_field].replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                    break
                except Exception:
                    pass

        context = activity.get('contextname', 'Unknown')
        subject = activity.get('Subject', 'No subject')
        if subject and len(subject) > 50:
            subject = subject[:50] + "..."

        gsid = activity.get('Gsid', 'Unknown')[:10] + "..."

        output.append(f"   {i}. [{date_str}] {context} context")
        if subject and subject != 'No subject':
            output.append(f"      📧 {subject}")
        output.append(f"      🆔 {gsid}")

    return "
".join(output)

def main():
    parser = argparse.ArgumentParser(description="View recent timeline activities (read-only).")
    parser.add_argument("--user-email", dest="user_email", help="User email for timeline filter")
    parser.add_argument("--limit", type=int, default=3, help="Max activities to fetch")
    parser.add_argument("--debug", action="store_true", help="Print raw JSON payload")
    args = parser.parse_args()

    domain = os.environ.get("GAINSIGHT_DOMAIN")
    access_key = os.environ.get("GAINSIGHT_ACCESS_KEY")
    user_email = args.user_email or os.environ.get("GAINSIGHT_USER_EMAIL")

    if not domain or not access_key:
        print("❌ Missing env vars. Set GAINSIGHT_DOMAIN and GAINSIGHT_ACCESS_KEY.")
        sys.exit(1)

    if not user_email:
        print("❌ Missing user email. Provide --user-email or set GAINSIGHT_USER_EMAIL.")
        sys.exit(1)

    print("👤 Timeline Activity Viewer (READ-ONLY)")
    print(f"🌐 Domain: {domain}")
    print(f"🧑 User: {user_email}")
    print("=" * 60)

    data = safe_timeline_query(domain, access_key, user_email, limit=args.limit)

    if data:
        if args.debug:
            print("📝 Raw JSON:")
            print(json.dumps(data, indent=2))
            print("
" + "=" * 80)
        formatted = format_timeline_data(data)
        print(formatted)
        print("-" * 40)
        print("✅ Successfully accessed Timeline API!")
    else:
        print("❌ Timeline API not accessible")
        print("💡 Possible reasons:")
        print("   • Timeline features not enabled on your instance")
        print("   • API key lacks Timeline read permissions")
        print("   • No Timeline activities in the system")

    print("
🛡️  100% READ-ONLY: No data was modified, only viewed")

if __name__ == "__main__":
    main()
