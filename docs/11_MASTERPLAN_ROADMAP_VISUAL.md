# LifeTimeCircle – Finalisierungs-Roadmap (Visual)

## 📅 Timeline Overview (7 Wochen = ~49 Tage)

```
                    P0 (25-33h)     │     P1 (77-101h)     │   P2 (50-65h)
                    Webseite        │    MVP Flows         │  Admin/Polish
    ┌───────────┐                   │                      │
    │ 2026-02-28│ ← TODAY: Design-System ✅ Ready
    │ (Freitag) │
    └───────────┘
        │
        │ (Wochenende + Montag Start)
        │
    ┌───────────────────────────────────────────────────────────────────┐
    │ PHASE P0: Webseite (5-7 Tage, ~28 Std)                           │
    │                                                                     │
    │ Mo 3/1  ████ W1: Landing Page (6-8h)                              │
    │         ████ W2: Entry/Role-Wahl (4-6h)                          │
    │                                                                     │
    │ Di 3/2  ████ W3: Public Nav (3-4h)                                │
    │         ████ W4: FAQ/Impressum (5-6h)                            │
    │                                                                     │
    │ Mi 3/3  ████ W5: Blog/News-List (4-5h)                            │
    │         ████ W6: Design-System Polish (3-4h)                     │
    │                                                                     │
    │ Do 3/4  ✅ P0 COMPLETE + Commit                                   │
    │ (Build greeen, Tests passing)                                     │
    └───────────────────────────────────────────────────────────────────┘
             │
             ↓ (Tests: Landing responsive, Design-Tokens 100%, no warnings)
    ┌───────────────────────────────────────────────────────────────────┐
    │ PHASE P1: MVP Flows (7-10 Tage, ~89 Std)                         │
    │                                                                     │
    │ Do 3/4  ████ P1.1.A1: Auth Page (6-8h)                            │
    │ Fr 3/5  ████ P1.1.A2: Consent Page (5-6h)                        │
    │                                                                     │
    │ Mo 3/8  ████ P1.1.A3: Token Persistence (3-4h)                    │
    │         ████ P1.1.A4: Auth Guards (4-5h)                          │
    │                                                                     │
    │ Di 3/9  ████ P1.2.V1: Vehicles List (6-8h)                        │
    │ Mi 3/10 ████ P1.2.V2: Vehicle Detail (5-7h)                      │
    │         ████ P1.2.V3: Timeline/Entries (6-8h)                    │
    │                                                                     │
    │ Do 3/11 ████ P1.2.V4: Entry-Form (6-8h)                           │
    │ Fr 3/12 ████ P1.2.V5: Documents Tab (4-5h)                       │
    │                                                                     │
    │ Mo 3/15 ████ P1.2.V6: Create Vehicle (5-6h)                      │
    │                                                                     │
    │ Di 3/16 ████ P1.3.D1: Upload UX (6-8h)                            │
    │ Mi 3/17 ████ P1.3.D2-D4: Document Status/List (9-12h)            │
    │                                                                     │
    │ Do 3/18 ████ P1.4.Q1-Q3: Public-QR (12-16h)                      │
    │                                                                     │
    │ Fr 3/19 ✅ P1 COMPLETE + E2E Tests, Mobile responsive             │
    │ (Full user flow: Auth → Vehicles → Documents → QR)               │
    └───────────────────────────────────────────────────────────────────┘
             │
             ↓ (Tests: E2E grün, Mobile OK, Lighthouse >75)
    ┌───────────────────────────────────────────────────────────────────┐
    │ PHASE P2: Admin & Polish (5-7 Tage, ~57 Std)                     │
    │                                                                     │
    │ Mo 3/22 ████ P2.1.AD1-AD3: Admin Pages (15-20h)                   │
    │ Di 3/23 ████ P2.2.T1-T2: Trust/To-Dos (10-13h)                    │
    │                                                                     │
    │ Mi 3/24 ████ P2.3.Q1-Q5: Quality/Polish (25-32h)                 │
    │ (Error handling, Loading states, Perf, E2E expand)               │
    │                                                                     │
    │ Do-Fr   ✅ FINAL QA, Lighthouse >80, build size optimized         │
    │ 3/27-28 ✅ User/UAT Testing (optional)                            │
    │                                                                     │
    │ Mo 3/30 🚀 RELEASE READY (Go/No-Go Decision)                      │
    │ 2026                                                               │
    └───────────────────────────────────────────────────────────────────┘
```

---

## 🔀 Dependency Matrix

```
                    ┌─────────────────┐
                    │  Design System  │
                    │ (DONE ✅)       │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ↓                   ↓                   ↓
    ┌────────────┐    ┌──────────────┐   ┌─────────────┐
    │ Landing    │    │ Auth/Consent │   │ Public Docs │
    │ (5-7h)     │    │ (18-23h)     │   │ (20h)       │
    └────────┬───┘    └──────┬───────┘   └──────┬──────┘
             │                │                 │
             └────────┬───────┴─────────┬───────┘
                      ↓                 ↓
                  ┌─────────────────────────┐
                  │  Route Guards Ready     │
                  │  (Deny-by-Default & 403)│
                  └───────────┬─────────────┘
                              │
         ┌────────────────────┼─────────────────────┐
         ↓                    ↓                     ↓
    ┌──────────────┐   ┌─────────────┐    ┌──────────────┐
    │ Vehicles     │   │ Documents   │    │ Public-QR    │
    │ (32-42h)     │   │ (15-20h)    │    │ (12-16h)     │
    │              │   │             │    │              │
    │ • List       │   │ • Upload    │    │ • Read-Only  │
    │ • Detail     │   │ • Status    │    │ • Print-Ready│
    │ • Timeline   │   │ • Download  │    │              │
    │ • Create     │   │             │    │              │
    └──────┬───────┘   └──────┬──────┘    └──────────────┘
           │                  │
           └──────┬───────────┘
                  ↓
          ┌──────────────────┐
          │ Admin Pages      │
          │ (15-20h)         │
          │                  │
          │ • Rollen         │
          │ • Quarantine     │
          │ • Exports        │
          └──────┬───────────┘
                 ↓
         ┌──────────────────┐
         │ Quality/Polish   │
         │ (25-32h)         │
         │                  │
         │ • Error Handling │
         │ • Loading States │
         │ • Mobile Check   │
         │ • E2E Coverage   │
         │ • Perf & Lighthouse
         └──────────────────┘
```

---

## 📍 Weekly Status Milestones

```
WEEK 1 (Mar 1-5, 2026)
├─ Mo: Landing + Entry-Role → Committed ✓
├─ Tu: Public Nav + FAQ → Committed ✓
├─ We: Blog/News → Ready for E2E
├─ Th: Design Polish → P0 COMPLETE ✔️
└─ Fr: QA P0, Start P1

WEEK 2 (Mar 8-12, 2026)
├─ Mo: Auth + Consent → Committed ✓
├─ Tu-We: Vehicles List/Detail → Preview
├─ Th: Timeline Entries → Committed ✓
├─ Fr: Entry-Form + Create → Preview
└─ Status: P1 40% Complete

WEEK 3 (Mar 15-19, 2026)
├─ Mo: Documents Upload → Committed ✓
├─ Tu: Document Status/Download → Committed ✓
├─ We: Public-QR Page → Committed ✓
├─ Th-Fr: P1 QA + E2E
└─ Status: P1 COMPLETE ✔️

WEEK 4 (Mar 22-26, 2026)
├─ Mo-Tu: Admin Pages (Roles/Quarantine) → Committed ✓
├─ We: Trust/To-Dos → Committed ✓
├─ Th-Fr: Quality Pass (Errors/Loading/Mobile)
└─ Status: P2 40% Complete

WEEK 5 (Mar 29-Apr 2, 2026)
├─ Mo: Final QA, Performance Tune, E2E Expand
├─ Tu-We: UAT (optional)
├─ Th: Go/No-Go Decision
├─ Fr: Release or Hotfix
└─ Status: 🚀 RELEASE READY (or Hotfix Sprint)
```

---

## 🎯 Sprint Planning (Suggested)

### Sprint 1 (Mo-Fr, Mar 1-5)
- **Goal:** P0 Launch Pages Complete
- **Owner:** 1 Dev (Frontend)
- **Daily Standup:** 9:00 CET
- **DoD:** All P0 marked ✅, Build green, no TS errors

### Sprint 2 (Mo-Fr, Mar 8-12)
- **Goal:** Auth + Vehicles Core
- **Owner:** 1 Dev (Frontend) + 1 Dev optional for Backend-Integration
- **Daily Standup:** 9:00 CET
- **DoD:** Auth/Consent/Guards tested, Vehicles CRUD working

### Sprint 3 (Mo-Fr, Mar 15-19)
- **Goal:** Documents + Public-QR + P1 Complete
- **Owner:** 1 Dev (Frontend)
- **Daily Standup:** 9:00 CET
- **DoD:** P1 marked ✅, E2E >70%, Mobile responsive

### Sprint 4 (Mo-Fr, Mar 22-26)
- **Goal:** Admin + Quality Pass, P2 Complete
- **Owner:** 1 Dev (Frontend) + 1 Dev (Backend/Admin APIs)
- **Daily Standup:** 9:00 CET
- **DoD:** P2 marked ✅, Lighthouse >80, E2E >80%

### Sprint 5 (Mo-Th, Mar 29-Apr 1)
- **Goal:** Final QA, Hotfixes, Release
- **Owner:** Full team + QA
- **Daily Standup:** 9:00 CET
- **DoD:** 🚀 Deploy to production-ready environment

---

## 📊 Resource Allocation

### 1-Dev Scenario (24 days, slower)
```
Dev 1: Full-Stack Frontend
├─ P0 (4 days) → Landing, Auth, Navigation
├─ P1 (10 days) → Vehicles, Documents, QR
├─ P2 (7+ days) → Admin, Quality
└─ +3 days: contingency/UAT
```

### 2-Dev Scenario (17 days, faster) ⭐ RECOMMENDED
```
Dev 1: Webseite + MVP Pages (Frontend Lead)
├─ P0+P1 (13 days) → Landing, Auth, Vehicles, Documents

Dev 2: Admin + Integration (Backend/Integration Lead)
├─ P1+P2 (10 days) → API troubleshooting, Admin APIs, QA
└─ Parallel work on P2 while Dev1 finishes P1
```

### 3-Dev Scenario (12 days, luxury)
```
Dev 1: Frontend Pages (Primary)
Dev 2: Admin/Integration
Dev 3: QA/E2E/Performance
└─ All phases run heavily parallelized
```

---

## ⚠️ Risks & Mitigation

| Risk | Likeli. | Impact | Mitigation |
|------|---------|--------|-----------|
| API Breaking Changes | Medium | High | Sync API Contracts beforehand, API versioning |
| Mobile Layout Issues | Medium | Medium | Responsive testing on Week 1, Day 4 |
| Performance Regression | Low | Medium | Lighthouse checks at end of each phase |
| Scope Creep | High | High | Strict P0/P1/P2 prioritization, no "nice-to-haves" |
| Team bandwidth | Medium | High | 2-Dev team recommended, clear task tracking |
| Browser Compatibility | Low | Low | Feature detection, polyfills added as needed |

---

## 🎉 Success Criteria (Go-Live)

✅ **Functional:**
- All P1 pages working (Auth → Vehicles → Documents → QR)
- Admin pages functional (for support team)
- E2E tests >80% covering critical flows
- Zero production blockers (P0 issues only)

✅ **Performance:**
- Lighthouse Score >80 (Performance, Accessibility, Best Practices)
- LCP <2.5s, TTI <3.5s, CLS <0.1
- Bundle size <400KB (gzipped)

✅ **Security:**
- Moderator blocked from app (401/403 tested)
- Consent enforced before product access
- No PII in logs/exports/public pages
- HTTPS/CSP headers configured

✅ **UX:**
- Mobile responsive (375px-1920px tested)
- All error states handeled (no blank screens)
- Loading states visible
- Accessibility (WCAG AA minimum)

---

**Last Updated:** 2026-02-28  
**Next Review:** 2026-03-06 (End of P0)
