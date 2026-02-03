#!/usr/bin/env python3
"""
Company Name Lookup - READ-ONLY
Lookup a company name by GsCompanyId using the Company query endpoint.
"""
import os
import sys
import json
import argparse
import requests

def lookup_company_by_id(domain, access_key, company_id):
    """Lookup company name by GsCompanyId using Company query endpoint"""
    url = f"{domain.rstrip('/')}/v1/data/objects/query/Company"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accesskey": access_key,
    }

    query = {
        "select": ["Gsid", "Name", "Industry", "ModifiedDate"],
        "where": {
            "conditions": [
                {
                    "name": "Gsid",
                    "alias": "A",
                    "value": [company_id],
                    "operator": "EQ"
                }
            ],
            "expression": "A"
        },
        "limit": 1,
        "offset": 0
    }

    try:
        print(f"🔍 Looking up company with ID: {company_id}")
        resp = requests.post(url, headers=headers, data=json.dumps(query), timeout=15)

        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"   ❌ HTTP {resp.status_code}: {resp.text[:300]}")
            return None

    except requests.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None

def format_company_data(data):
    """Format company data for display"""
    if not data or not data.get('result'):
        return "   No company data available"

    data_section = data.get('data', {})
    companies = data_section.get('records', [])

    if not companies:
        return "   No company found with that ID"

    company = companies[0]

    name = company.get('Name', 'Unknown Company')
    industry = company.get('Industry', 'No industry')
    gsid = company.get('Gsid', 'Unknown ID')

    return f"""   ✅ Company found:
   📊 Name: {name}
   🏭 Industry: {industry}
   🆔 Gsid: {gsid}"""

def main():
    parser = argparse.ArgumentParser(description="Lookup company name by GSID (read-only).")
    parser.add_argument("--company-id", dest="company_id", help="GsCompanyId to lookup")
    args = parser.parse_args()

    domain = os.environ.get("GAINSIGHT_DOMAIN")
    access_key = os.environ.get("GAINSIGHT_ACCESS_KEY")
    company_id = args.company_id or os.environ.get("GAINSIGHT_COMPANY_ID")

    if not domain or not access_key:
        print("❌ Missing env vars. Set GAINSIGHT_DOMAIN and GAINSIGHT_ACCESS_KEY.")
        sys.exit(1)

    if not company_id:
        print("❌ Missing company ID. Provide --company-id or set GAINSIGHT_COMPANY_ID.")
        sys.exit(1)

    print("🏢 Company Name Lookup (READ-ONLY)")
    print(f"🌐 Domain: {domain}")
    print(f"🆔 Target Company ID: {company_id}")
    print("📖 Endpoint: v1/data/objects/query/Company")
    print("=" * 60)

    data = lookup_company_by_id(domain, access_key, company_id)

    if data:
        print("🎯 Result:")
        formatted = format_company_data(data)
        print(formatted)
        print("-" * 40)
        print("✅ Company lookup completed!")
    else:
        print("❌ Company lookup failed")
        print("💡 Possible reasons:")
        print("   • Company ID doesn't exist")
        print("   • API key lacks Company read permissions")
        print("   • Company object not accessible")

    print("
🛡️  100% READ-ONLY: No data was modified, only viewed")

if __name__ == "__main__":
    main()
