# EDULINK Tax Workflow (Mock Integration)

## Purpose
This document describes the currently implemented tax workflow API in the Flask backend and how it maps to the expansion plan.

## Implemented Endpoints
- POST /api/tax/onboard
- GET /api/tax/estimate?year=YYYY
- POST /api/tax/submit
- GET /api/tax/status/:submissionId
- GET /api/tax/events?limit=20&event_type=...&claim_code=...
- GET /api/tax/report/:year
- POST /api/cms/charge

## Data Tables
- tax_profiles: instructor tax profile and payout account metadata
- tax_claims: yearly estimate/claim records and fee information
- tax_events: event timeline for auditing workflow actions
- cms_charges: post-refund fee charge records

## Current Calculation Rules
- gross_income: SUM(posting.rate) for approved applications owned by instructor in selected year
- withholding_amount: round(gross_income * 0.033)
- estimated_refund: round(withholding_amount * 0.7)
- service_fee_rate: 0.20 to 0.25 (default 0.22)
- service_fee_amount: round(estimated_refund * service_fee_rate)

## Example Flow
1. Instructor calls POST /api/tax/onboard
2. App calls GET /api/tax/estimate?year=2026
3. User confirms and calls POST /api/tax/submit
4. App polls GET /api/tax/status/:submissionId
5. Refund settlement phase triggers POST /api/cms/charge

## Limitations
- Provider integration is mocked (provider = mock-hometax-sam)
- No external OAuth/certificate flow for HomeTax yet
- Fee charge endpoint marks processed immediately for MVP speed

## Next Integration Targets
- HomeTax connector adapter and token lifecycle
- Samjjeomsam partner handoff and callback status sync
- Monthly batch job for estimate snapshots and reminder push
