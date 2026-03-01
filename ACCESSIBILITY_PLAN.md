# Accessibility & Mobile Responsiveness Audit - 2026-03-01

## Accessibility Improvements

### Semantic HTML Review
- ✅ All `<main>` landmarks present
- ✅ Navigation via hash routes
- ✅ Form labels properly associated
- [ ] Add ARIA labels to icon-only buttons where introduced later
- [x] Add ARIA descriptions for complex components

### ARIA Enhancements Todo
1. **Public QR Page:**
   - [x] Add `aria-label="Trust light indicator"` to badge light
   - [x] Add `aria-description` for trust metadata grid

2. **Blog/News Pages:**
   - [x] Add `aria-label="Article navigation"` to back links
   - [x] Add `aria-label="Article list"` to lists

3. **Forms (Vehicles, Onboarding, Documents):**
   - [x] Add `aria-required` to required fields
   - [x] Add `aria-invalid` to error fields
   - [x] Add `aria-describedby` linking errors to fields

4. **Auth, Consent, Trust Folders:**
   - [x] Add `aria-required` and field-level error descriptions on OTP and trust-folder forms
   - [x] Group consent checkboxes semantically via `fieldset` and `legend`
   - [x] Add descriptive associations on cookie settings toggles and trust disclaimers

5. **Buttons:**
   - [ ] Add `aria-label` to future icon-only buttons if they are introduced
   - [ ] Add `aria-pressed` to true toggle buttons if they are introduced

### Color Contrast Check
- Review: All text meets WCAG AA (4.5:1) contrast ratio
- Focus indicators bright and visible

### Keyboard Navigation
- Tab order logical across all pages
- [x] Initial focus and focus handoff covered on Auth, Consent, Trust Folders
- Enter/Space activate buttons
- Escape closes modals (if any)

## Mobile Responsiveness

### Breakpoints (CSS)
- [x] 375px (iPhone SE) – lowest
- [x] 768px (iPad) – mid
- [x] 1920px (Desktop) – high

### Tests Needed
- [x] Form layouts responsive (stack on mobile)
- [x] Button groups wrap properly
- [x] Lists have adequate spacing
- [x] Text readable without zoom
- Touch targets >= 44x44px

### CSS Updates
- [x] Add media queries for forms on small screens
- [x] Ensure padding/margin scales
- [x] Check font sizes on 375px
- [x] Add desktop grid/layout rules for 1440px+ and 1920px

## Implementation Order
1. Run accessibility audit (Playwright + accessibility APIs) on newly added routes/components
2. Fix any contrast issues
3. Extend keyboard-navigation checks when new complex widgets enter the UI
4. Add ARIA semantics again when new icon/toggle controls enter the UI
