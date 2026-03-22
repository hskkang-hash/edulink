# EDULINK Network Compliance (MVP)

## Goal
Support MLM-style sponsor bonus calculations while enforcing the legal cap:
- C <= 0.35 * Gamma

Where:
- Gamma: sales price aggregate
- C: sponsor bonus aggregate

## Implemented APIs
- POST /api/network/link
- POST /api/network/sales
- GET /api/network/compliance?period=YYYY-MM
- GET /api/network/bonuses?period=YYYY-MM
- GET /api/network/admin/summary?period=YYYY-MM
- GET /api/network/admin/top-sponsors?period=YYYY-MM&limit=10
- GET /api/network/admin/sponsor-trend?user_id=1&months=6
- GET /api/network/admin/rules
- PUT /api/network/admin/rules
- GET /api/network/admin/rules/audits?limit=20
- POST /api/network/admin/rules/simulate
   - Returns ratio/cost preview plus `sponsor_deltas` (top 10 impacted sponsors)

## Current Algorithm
1. Seller records a sale with base_price, pv, bv.
2. Backend resolves up to 3 sponsor levels from network_links.
3. Each sponsor rate is selected by monthly PV rank:
   - >= 10,000,000 PV: 21%
   - >= 5,000,000 PV: 6%
   - >= 200,000 PV: 3%
   - otherwise: 0%
4. Raw bonus total C_raw is compared to 35% cap.
5. If C_raw exceeds cap, all payouts are scaled by factor cap / C_raw.
6. Paid allocations are saved in network_bonus_allocations.

## Data Tables
- network_links
- network_sales
- network_bonus_allocations

## Notes
- This is an MVP-safe implementation focused on deterministic payout + cap enforcement.
- Sponsorship graph depth is currently limited to 3.
- Monthly period format uses YYYY-MM.
- Admin aggregate endpoints are enabled for admin/instructor roles in this MVP.
- Admin aggregate/rule endpoints are restricted to admin/super_admin roles.
- Risk interpretation in dashboard:
   - ratio < 30%: Low Risk
   - 30% <= ratio <= 35%: Warning
   - ratio > 35%: High Risk
- Bonus rate rules are now DB-backed (`network_bonus_rules`) and can be updated via admin API.
