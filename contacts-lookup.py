#!/usr/bin/env python3
"""
Company Contacts Lookup - READ-ONLY
Lists active contacts for a company using the company_person custom object.
"""
import os
import sys
import json
import argparse
import requests

def redact_email(email):
    if not email or '@' not in email:
        return email
    user, domain = email.split('@', 1)
    return f"{user[:1]}***@{domain}" if user else f"***@{domain}"

def fetch_contacts_by_company_gsid(domain, access_key, company_gsid):
    url = f"{domain.rstrip('/')}/v1/data/objects/query/company_person"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accesskey": access_key,
    }

    contacts = []
    offset = 0
    limit = 1000

    while True:
        query = {
            "select": [
                "Gsid",
                "Person_ID__gr.Gsid",
                "Person_ID__gr.FirstName",
                "Person_ID__gr.LastName",
                "Person_ID__gr.Email",
                "Role",
                "Title",
                "Active"
            ],
            "where": {
                "conditions": [
                    {
                        "name": "Company_ID",
                        "alias": "A",
                        "operator": "EQ",
                        "value": [company_gsid]
                    },
                    {
                        "name": "Active",
                        "alias": "B",
                        "operator": "EQ",
                        "value": [True]
                    }
                ],
                "expression": "A AND B"
            },
            "orderBy": {
                "Person_ID__gr.LastName": "asc"
            },
            "limit": limit,
            "offset": offset
        }

        try:
            print(f"🔍 Querying contacts (offset: {offset}, limit: {limit})...")
            resp = requests.post(url, headers=headers, data=json.dumps(query), timeout=15)

            if resp.status_code != 200:
                print(f"   ❌ HTTP {resp.status_code}: {resp.text[:300]}")
                return None

            data = resp.json()
            if not data.get('result'):
                print(f"   ❌ API Error: {data.get('errorDesc', 'Unknown error')}")
                return None

            raw_data = data.get('data', [])
            if isinstance(raw_data, dict) and 'records' in raw_data:
                records = raw_data['records']
            elif isinstance(raw_data, list):
                records = raw_data
            else:
                print(f"   ❌ Unexpected data format")
                return None

            contacts.extend(records)
            print(f"   📋 Found {len(records)} contacts in this batch")

            if len(records) < limit:
                break

            offset += limit

        except requests.RequestException as e:
            print(f"   ❌ Request error: {e}")
            return None

    return contacts

def format_contacts_data(contacts, company_name="Unknown Company", redact=True):
    if not contacts:
        return f"   No active contacts found for {company_name}"

    output = [f"   📊 Found {len(contacts)} active contacts for {company_name}:"]
    output.append("   " + "=" * 60)

    for i, contact in enumerate(contacts, 1):
        first_name = contact.get('Person_ID__gr.FirstName') or 'Unknown'
        last_name = contact.get('Person_ID__gr.LastName') or 'Unknown'
        email = contact.get('Person_ID__gr.Email') or 'No email'
        role = contact.get('Role') or 'No role'
        title = contact.get('Title') or 'No title'

        if redact and email != 'No email':
            email = redact_email(email)

        name = f"{first_name} {last_name}".strip()

        output.append(f"   {i}. 👤 {name}")
        output.append(f"      📧 {email}")
        if role != 'No role':
            output.append(f"      🎯 Role: {role}")
        if title != 'No title':
            output.append(f"      💼 Title: {title}")
        output.append("")

    return "
".join(output)

def main():
    parser = argparse.ArgumentParser(description="List active contacts for a company (read-only).")
    parser.add_argument("--company-id", dest="company_id", help="GsCompanyId for the company")
    parser.add_argument("--company-name", dest="company_name", help="Optional display name")
    args = parser.parse_args()

    domain = os.environ.get("GAINSIGHT_DOMAIN")
    access_key = os.environ.get("GAINSIGHT_ACCESS_KEY")
    company_gsid = args.company_id or os.environ.get("GAINSIGHT_COMPANY_ID")
    company_name = args.company_name or os.environ.get("GAINSIGHT_COMPANY_NAME") or "Unknown Company"
    redact = os.environ.get("GAINSIGHT_REDACT", "1") != "0"

    if not domain or not access_key:
        print("❌ Missing env vars. Set GAINSIGHT_DOMAIN and GAINSIGHT_ACCESS_KEY.")
        sys.exit(1)

    if not company_gsid:
        print("❌ Missing company ID. Provide --company-id or set GAINSIGHT_COMPANY_ID.")
        sys.exit(1)

    print("👥 Company Contacts Lookup (READ-ONLY)")
    print(f"🌐 Domain: {domain}")
    print(f"🏢 Company: {company_name} ({company_gsid})")
    print("🔗 Endpoint: v1/data/objects/query/company_person")
    print("=" * 60)

    contacts = fetch_contacts_by_company_gsid(domain, access_key, company_gsid)

    if contacts is not None:
        print("
🎯 Results:")
        formatted = format_contacts_data(contacts, company_name, redact=redact)
        print(formatted)
        print("-" * 40)
        print(f"✅ Contact lookup completed! Total: {len(contacts)} contacts")
    else:
        print("❌ Contact lookup failed")
        print("💡 Possible reasons:")
        print("   • Custom Object API endpoint not accessible")
        print("   • Company GSID doesn't exist")
        print("   • No company_person object access")
        print("   • Wrong domain for Custom Object API")

    print("
🛡️  100% READ-ONLY: No data was modified, only viewed")

if __name__ == "__main__":
    main()
