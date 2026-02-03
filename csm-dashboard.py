#!/usr/bin/env python3
"""
CSM Dashboard - Complete workflow combining Timeline + Company + Contacts
Ultra-safe READ-ONLY script
"""
import os
import sys
import json
import argparse
import requests
from collections import Counter


def redact_email(email):
    if not email or '@' not in email:
        return email
    user, domain = email.split('@', 1)
    return f"{user[:1]}***@{domain}" if user else f"***@{domain}"


def get_timeline_activities(domain, access_key, user_email, limit=3):
    url = f"{domain.rstrip('/')}/v1/data/objects/query/activity_timeline"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accesskey": access_key,
    }

    query = {
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
            "conditions": [{
                "name": "AuthorId__gr.Email",
                "alias": "A",
                "value": [user_email],
                "operator": "EQ"
            }],
            "expression": "A"
        },
        "orderBy": {"CreatedDate": "desc"},
        "limit": limit,
        "offset": 0
    }

    try:
        print(f"📧 Getting {limit} recent timeline activities for {user_email}...")
        resp = requests.post(url, headers=headers, data=json.dumps(query), timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('result'):
                activities = data.get('data', {}).get('records', [])
                print(f"   ✅ Found {len(activities)} activities")
                return activities
            else:
                print(f"   ❌ API Error: {data.get('errorDesc')}")
                return None
        else:
            print(f"   ❌ HTTP {resp.status_code}: {resp.text[:200]}")
            return None

    except requests.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None


def lookup_company_name(domain, access_key, company_gsid):
    url = f"{domain.rstrip('/')}/v1/data/objects/query/Company"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accesskey": access_key,
    }

    query = {
        "select": ["Gsid", "Name", "Industry"],
        "where": {
            "conditions": [{
                "name": "Gsid",
                "alias": "A",
                "value": [company_gsid],
                "operator": "EQ"
            }],
            "expression": "A"
        },
        "limit": 1,
        "offset": 0
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(query), timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('result'):
                companies = data.get('data', {}).get('records', [])
                if companies:
                    return companies[0]
        return None

    except requests.RequestException:
        return None


def get_company_contacts(domain, access_key, company_gsid, limit=10):
    url = f"{domain.rstrip('/')}/v1/data/objects/query/company_person"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accesskey": access_key,
    }

    query = {
        "select": [
            "Person_ID__gr.FirstName",
            "Person_ID__gr.LastName",
            "Person_ID__gr.Email",
            "Title"
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
        "orderBy": {"Person_ID__gr.LastName": "asc"},
        "limit": limit,
        "offset": 0
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(query), timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('result'):
                records = data.get('data', {}).get('records', [])
                return records
        return []

    except requests.RequestException:
        return []


def extract_email_domains(contacts):
    domains = []

    for contact in contacts:
        email = contact.get('Person_ID__gr.Email', '')
        if email and '@' in email:
            domain = email.split('@')[1].lower()
            domains.append(domain)

    if domains:
        domain_counts = Counter(domains)
        return domain_counts

    return {}


def format_timeline_summary(activities):
    if not activities:
        return "   No activities found"

    output = [f"   📊 Found {len(activities)} recent activities:"]

    for i, activity in enumerate(activities, 1):
        subject = activity.get('Subject', 'No subject')[:50]
        company_id = activity.get('GsCompanyId', 'No company ID')

        if subject:
            subject = subject + "..." if len(subject) == 50 else subject

        output.append(f"   {i}. 📧 {subject}")
        output.append(f"      🏢 Company ID: {company_id}")

    return "
".join(output)


def main():
    parser = argparse.ArgumentParser(description="Run the CSM dashboard workflow (read-only).")
    parser.add_argument("--user-email", dest="user_email", help="User email for timeline filter")
    parser.add_argument("--limit", type=int, default=3, help="Max timeline activities")
    args = parser.parse_args()

    domain = os.environ.get("GAINSIGHT_DOMAIN")
    access_key = os.environ.get("GAINSIGHT_ACCESS_KEY")
    user_email = args.user_email or os.environ.get("GAINSIGHT_USER_EMAIL")
    redact = os.environ.get("GAINSIGHT_REDACT", "1") != "0"

    if not domain or not access_key:
        print("❌ Missing env vars. Set GAINSIGHT_DOMAIN and GAINSIGHT_ACCESS_KEY.")
        sys.exit(1)

    if not user_email:
        print("❌ Missing user email. Provide --user-email or set GAINSIGHT_USER_EMAIL.")
        sys.exit(1)

    print("🎯 CSM Complete Dashboard (READ-ONLY)")
    print(f"🌐 Domain: {domain}")
    print(f"👤 User: {user_email}")
    print("=" * 80)

    print("
🔄 STEP 1: Getting recent timeline activities...")
    activities = get_timeline_activities(domain, access_key, user_email, limit=args.limit)

    if not activities:
        print("❌ Failed to get timeline activities")
        sys.exit(1)

    print(format_timeline_summary(activities))

    print("
🔄 STEP 2: Extracting company GSIDs...")
    company_gsids = []
    for activity in activities:
        gsid = activity.get('GsCompanyId')
        if gsid and gsid not in company_gsids:
            company_gsids.append(gsid)

    print(f"   🏢 Found {len(company_gsids)} unique companies")

    print("
🔄 STEP 3: Processing each company...")
    all_results = []

    for i, company_gsid in enumerate(company_gsids, 1):
        print(f"
   🔍 Processing Company {i}/{len(company_gsids)}: {company_gsid}")

        print(f"      📋 Looking up company name...")
        company_info = lookup_company_name(domain, access_key, company_gsid)

        if company_info:
            company_name = company_info.get('Name', 'Unknown Company')
            industry = company_info.get('Industry') or 'Unknown Industry'
            print(f"      ✅ Company: {company_name} ({industry})")
        else:
            company_name = f"Unknown Company ({company_gsid[:20]}...)"
            industry = "Unknown Industry"
            print(f"      ❌ Could not lookup company name")

        print(f"      👥 Getting top 10 contacts...")
        contacts = get_company_contacts(domain, access_key, company_gsid, limit=10)

        if contacts:
            print(f"      ✅ Found {len(contacts)} contacts")
            domain_counts = extract_email_domains(contacts)
            primary_domain = max(domain_counts.items(), key=lambda x: x[1])[0] if domain_counts else "Unknown"

            all_results.append({
                'gsid': company_gsid,
                'name': company_name,
                'industry': industry,
                'contacts': contacts[:10],
                'domain_counts': domain_counts,
                'primary_domain': primary_domain
            })

        else:
            print(f"      ❌ No contacts found")
            all_results.append({
                'gsid': company_gsid,
                'name': company_name,
                'industry': industry,
                'contacts': [],
                'domain_counts': {},
                'primary_domain': 'Unknown'
            })

    print("
" + "=" * 80)
    print("🎯 FINAL DASHBOARD RESULTS")
    print("=" * 80)

    for i, result in enumerate(all_results, 1):
        print(f"
🏢 COMPANY {i}: {result['name']}")
        print(f"   🆔 GSID: {result['gsid']}")
        print(f"   🏭 Industry: {result['industry']}")

        if result['domain_counts']:
            print(f"   📊 Email Domains:")
            for domain, count in result['domain_counts'].most_common():
                shown_domain = "redacted-domain" if redact else domain
                print(f"      • @{shown_domain} ({count} contacts)")

        print(f"   👥 Top {len(result['contacts'])} Contacts:")
        for j, contact in enumerate(result['contacts'][:10], 1):
            name = f"{contact.get('Person_ID__gr.FirstName', '')} {contact.get('Person_ID__gr.LastName', '')}".strip()
            email = contact.get('Person_ID__gr.Email', 'No email')
            title = contact.get('Title') or 'No title'

            if redact and email != 'No email':
                email = redact_email(email)

            print(f"      {j}. {name}")
            print(f"         📧 {email}")
            if title != 'No title':
                print(f"         💼 {title}")

    print("
" + "=" * 80)
    print("✅ CSM Dashboard completed successfully!")
    print("🛡️  100% READ-ONLY: No data was modified, only viewed")

if __name__ == "__main__":
    main()
