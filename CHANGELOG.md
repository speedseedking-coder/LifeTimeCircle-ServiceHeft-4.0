# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-03-01

### Added
- Release candidate branch `wip/add-web-modules-2026-03-01-0900` with full verification.
- Public-facing pages: FAQ, Jobs, Contact, Datenschutz, Blog, News brought to SoT copy.
- Accessibility and mobile/desktop hardening for core workspaces and forms.
- New docs: `99_MASTER_CHECKPOINT.md`, `12_RELEASE_CANDIDATE_2026-03-01.md`,
  `13_GO_LIVE_CHECKLIST.md`, updated `07_START_HERE.md`, `07_WEBSITE_COPY_MASTER_CONTEXT.md`.

### Changed
- Web build and backend tests stabilized; encoding and documentation issues cleaned.
- Adjusted Admin UI to handle declined full-export grants with explicit messaging.
- Documents, Admin, Vehicles, Auth, Consent pages refactored for UX and polish.
- Added e2e tests in `mini-e2e.spec.ts` covering critical flows.
- Updated public site shell routing and labels.

### Fixed
- Drift between Admin UI and Export backend corrected in `adminApi.ts`.
- Various layout and focus/keyboard flow bugs on mobile (375px) and desktop (1920px).
- Encoding and build errors in documentation resolved.

### Documentation
- Comprehensive cleanup and alignment of project documentation with real state.
- Masterplan documents decoupled from old assumptions and calendar entries.
- Readme/start paths updated and release candidate document created.
- Public-copy SoT integrated into site pages.

### Removed
- Legacy or broken document encodings; obsolete masterplan assumptions.

> **Note:** See `docs/12_RELEASE_CANDIDATE_2026-03-01.md` for the full release candidate
> definition and `docs/13_GO_LIVE_CHECKLIST.md` for pre‑live operations.
