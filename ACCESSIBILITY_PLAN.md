# Accessibility & Mobile Responsiveness Audit - 2026-03-01

## Accessibility Improvements

### Semantic HTML Review
- ✅ All `<main>` landmarks present
- ✅ Navigation via hash routes
- ✅ Form labels properly associated
- [ ] Add ARIA labels to icon buttons
- [ ] Add ARIA descriptions for complex components

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

4. **Buttons:**
   - Add `aria-label` to all icon-only buttons
   - Add `aria-pressed` to toggle buttons

### Color Contrast Check
- Review: All text meets WCAG AA (4.5:1) contrast ratio
- Focus indicators bright and visible

### Keyboard Navigation
- Tab order logical across all pages
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
1. Add ARIA labels to existing components
2. Run accessibility audit (Playwright + accessibility APIs)
3. Mobile responsive testing on 375px
4. Fix any contrast issues
5. Verify keyboard navigation
