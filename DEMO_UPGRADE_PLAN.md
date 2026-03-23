# EduLink Product Build Plan (Design-First)

## 1. Goal Reset
- Build EduLink from the user perspective, not as a demo-only surface.
- Design the full screen system first across all primary roles, then connect functions screen by screen.
- Use the PRD as the source of truth for terminology, workflow boundaries, and role responsibilities.

## 2. Product Delivery Principle
- Step 1: Lock the information architecture and screen inventory.
- Step 2: Build the full UI shell and major screens before deep feature work.
- Step 3: Connect workflows in priority order with real or stubbed data.
- Step 4: Replace placeholders with production-ready backend integration.

## 3. User-Centric Product Scope
- Instructor App / Workspace
: onboarding, profile, opportunity discovery, application tracking, session execution, settlement, tax refund, referral network.
- Institution Operations Portal
: staffing request intake, posting management, applicant review, scheduling, attendance oversight, contracts, settlement control.
- District Governance Console
: regional KPI, budget execution, program coverage, instructor supply, compliance reporting, executive briefings.
- Platform Admin Control Tower
: member lifecycle, reward compliance, payout integrity, audit trail, fraud risk, service health.

## 4. Design-First Screen Plan

### Phase A. Platform Structure
- Unified shell: side navigation, header, role switch, page title system, status language.
- Shared components: cards, grid tables, chips, filters, empty states, timeline, detail drawers.
- Responsive rules: mobile-first for instructor, desktop-first for institution/district/admin.

### Phase B. Full Screen Inventory
- Instructor screens
: home, profile, opportunities, application detail, session log, payout statement, tax center, network ledger.
- Institution screens
: dashboard, posting board, applicant review grid, allocation desk, attendance monitor, contract desk, settlement ledger.
- District screens
: regional dashboard, budget monitor, coverage heatmap, instructor pool, compliance report center, steering pack.
- Admin screens
: member governance, reward compliance board, payout control, audit trail, risk radar, service health console.

### Phase C. Functional Hookup Order
- Priority 1
: authentication, role-aware navigation, dashboard summaries, posting list/detail, application state, settlement summary.
- Priority 2
: tax workflow, network compliance, institution operations, district analytics, admin monitoring.
- Priority 3
: automation, alerts, audit depth, advanced reporting, external integrations.

## 5. Current Execution Order
- Step 1
: replace demo-centric planning language with product development language.
- Step 2
: expose the full screen architecture directly in the frontend.
- Step 3
: align each role to a visible workspace canvas before deeper behavior work.
- Step 4
: implement screen-level navigation and visual page states.
- Step 5
: wire backend functions into the already-designed screens.

## 6. Today-to-Next Build Sequence
- Block 1
: information architecture, roadmap board, role-based screen map.
- Block 2
: unified visual system and role workspace canvases.
- Block 3
: actual screen switching and page-state navigation.
- Block 4
: postings, applications, dashboard, settlement and network flows hookup.
- Block 5
: institution, district, and admin workflows hookup.
- Block 6
: QA, terminology pass, interaction polish.

## 7. Definition of Progress
- A role is not considered complete when its story can be narrated.
- A role is complete when the user can see all core screens, understand the navigation model, and execute the main workflow through the UI.
