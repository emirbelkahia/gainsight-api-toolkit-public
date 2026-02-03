# Gainsight API Toolkit

> **Disclaimer**: This is an independent, personal project and is **not** an official Gainsight product.

## Personal branding
If this toolkit helped you or inspired a workflow, feel free to mention or credit me on GitHub.
A practical **Python toolkit** for exploring the Gainsight NXT APIs and building read-only CSM workflows (timeline → company → contacts → domain insights).

> This repository is designed to be **safe-by-default**: all scripts are read-only and use small limits.

## Why this exists
- Reduce the friction of working with Gainsight APIs.
- Provide ready‑to‑run examples for common CSM workflows.
- Keep everything simple, observable, and safe (read‑only).

## What it does
- **Timeline viewer**: fetch recent activities for a user.
- **Company lookup**: resolve a `GsCompanyId` to a readable company name.
- **Contacts lookup**: list active contacts for a company.
- **CSM dashboard**: combine timeline → company → contacts → domain analysis in one flow.
- **Hello world**: validate credentials + connectivity.

## Quick start
```bash
# Environment variables
export GAINSIGHT_DOMAIN="https://yourcompany.gainsightcloud.com"
export GAINSIGHT_ACCESS_KEY="your-access-key"

# (Optional) reduce output sensitivity
export GAINSIGHT_REDACT=1

# Timeline activities
python3 timeline-viewer.py --user-email "you@company.com" --limit 3

# Lookup a company by GSID
python3 company-lookup.py --company-id "YOUR_COMPANY_GSID"

# List contacts for a company
python3 contacts-lookup.py --company-id "YOUR_COMPANY_GSID" --company-name "Acme"

# Full workflow
python3 csm-dashboard.py --user-email "you@company.com" --limit 3
```

## Scripts
| Script | Purpose |
| --- | --- |
| `gainsight-api-hello-world.py` | Connectivity test (read-only) |
| `timeline-viewer.py` | Timeline activities for a user |
| `company-lookup.py` | Resolve company name from GSID |
| `contacts-lookup.py` | List active contacts for a company |
| `csm-dashboard.py` | End‑to‑end CSM workflow |

## Environment variables
- `GAINSIGHT_DOMAIN` – e.g. `https://yourcompany.gainsightcloud.com`
- `GAINSIGHT_ACCESS_KEY` – Gainsight access key
- `GAINSIGHT_REDACT` – `1` (default) masks emails in console output (example: `e***@company.com`). Set to `0` to disable masking.

## Safety & privacy
- **Read‑only**: no create/update/delete operations.
- **Small limits**: defaults are conservative.
- **Redaction**: output can be redacted to avoid exposing sensitive data.

> Note: Gainsight data can contain PII (names, emails). Use responsibly.

## Requirements
- Python 3.7+
- `requests`

## Status
Maintained for personal use; contributions welcome.
