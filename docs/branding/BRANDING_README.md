# Your Training Monkey - Branding System Overview

This directory contains the complete branding framework for **Your Training Monkey** - a comprehensive, production-ready system for maintaining consistent brand identity across all touchpoints.

## Documents in This System

### 1. YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md
**The Complete Strategy & Philosophy**

This is your comprehensive brand bible covering:
- Brand identity and personality
- Visual identity system (colors, typography, imagery)
- Voice & messaging guidelines
- Application standards
- Digital presence strategy
- Quick reference guides

**When to use:** Strategic decisions, understanding brand philosophy, onboarding new team members, major redesigns

**Key sections:**
- Brand essence and promise
- Target audience personas
- Competitive positioning
- Complete color palette with usage rules
- Typography system and hierarchy
- Voice characteristics and messaging framework

---

### 2. BRAND_APPLICATION_GUIDE.md
**Practical Implementation Reference**

This is your developer/designer handbook with:
- Copy-paste ready CSS variables
- Component library with code snippets
- Common UI patterns
- Copy templates
- Responsive breakpoints
- Accessibility helpers

**When to use:** Day-to-day development, implementing new features, styling components, writing copy

**Key sections:**
- CSS variables setup (`:root` configuration)
- Button, card, and form components
- Hero sections, steps, empty states
- Copy templates for common scenarios
- React/Python code examples

---

## Quick Start Guide

### For Developers

1. **Set up CSS variables:**
   - Copy the `:root` section from `BRAND_APPLICATION_GUIDE.md`
   - Add to your main CSS file or create `variables.css`

2. **Use the component library:**
   - Find the component you need (button, card, form)
   - Copy the CSS and HTML from the guide
   - Customize as needed within brand constraints

3. **Reference the color palette:**
   ```css
   /* Always use variables, not hex codes */
   color: var(--ytm-text-primary);     /* ✅ Good */
   color: #1F2937;                     /* ❌ Avoid */
   ```

### For Designers

1. **Study the visual identity:**
   - Review color palette in framework document
   - Understand typography scale
   - Learn logo usage rules

2. **Follow the component patterns:**
   - Use existing card styles before creating new ones
   - Maintain spacing scale (xs, sm, md, lg, xl)
   - Keep one primary CTA per screen

3. **Check accessibility:**
   - Minimum contrast: 4.5:1 for text
   - Test with keyboard navigation
   - Consider reduced motion preferences

### For Content Writers

1. **Understand the voice:**
   - Professional-friendly (not corporate)
   - Technical credibility without jargon
   - Trail-runner authentic

2. **Use the copy templates:**
   - Error messages (no emoji icons)
   - Welcome flows
   - Email subject lines
   - Button copy

3. **Brand name styling:**
   - Preferred: Y, T, M emphasized in sage green (#6B8F7F)
   - Y, T, M slightly larger (1.17em), stronger color/bold weight
   - Acceptable: "YTM" abbreviation
   - Avoid emoji icons in user-facing content

4. **Readability:**
   - Left-justify all text
   - Max-width: 75 characters (75ch)
   - Never center-align body text

---

## Core Brand Principles (Memorize These)

### Visual Identity

**Colors:**
- **Blues/Grays:** Professional navigation and backgrounds
- **Banner Gradient:** `rgba(230,240,255,0.92)` to `rgba(27,46,75,0.92)`
- **Action Orange (#FF5722):** ONE primary CTA per screen only
- **Success Green (#16A34A):** Positive feedback and completions
- **Purple Gradient:** Interactive elements and secondary CTAs
- **Sage Green (#6B8F7F):** Y, T, M emphasis only

**Typography:**
- System font stack (native, performant)
- Scale: Display (40px) → H1 (32px) → H2 (24px) → H3 (20px) → Body (16px)
- Line height: 1.6 for readability
- Text alignment: Left-justified
- Max-width: 75ch for paragraphs

**Logo & Brand Name:**
- Watercolor monkey with compass logo
- Circular text: "Built for Trail Runners / By Trail Runners"
- Minimum size: 72px digital
- Brand name: Y, T, M slightly larger in sage green (#6B8F7F), bold weight
- Never distort, recolor, or remove elements

### Voice & Messaging

**Tagline:** "Prevent Injuries — Train Smarter"

**Value Proposition:** Patent-pending divergence analysis that shows the training imbalance your Garmin can't detect

**Tone Characteristics:**
- Intelligent yet approachable
- Trail-runner authentic
- Proactive & protective
- Scientifically rigorous
- Empowering & supportive

**Do's:**
- Explain the "why" behind recommendations
- Use "we" and "you" to create partnership
- Lead with benefits, follow with features
- Acknowledge complexity, then simplify
- Celebrate sustainable progress

**Don'ts:**
- Use corporate jargon or buzzwords
- Over-promise results
- Shame or guilt users
- Make absolute claims without evidence
- Talk down or assume expertise
- Use emoji icons in user-facing interfaces
- Center-align or justify body text
- Exceed 75 characters per line for readability

---

## Brand Application Checklist

Before launching any new feature, page, or content:

### Visual Check
- [ ] Uses brand color palette (CSS variables)
- [ ] Follows typography scale
- [ ] Logo properly sized and placed
- [ ] Y, T, M slightly larger in sage green (#6B8F7F)
- [ ] Text left-aligned, max-width: 75ch
- [ ] No emoji icons in UI
- [ ] Sufficient white space
- [ ] Mobile responsive
- [ ] Meets accessibility contrast ratios

### Content Check
- [ ] Voice matches brand personality
- [ ] Brand name with Y, T, M emphasis (or YTM acceptable)
- [ ] Clear, action-oriented copy
- [ ] No emoji in user-facing text
- [ ] Left-aligned, max 75ch width
- [ ] No medical claims without disclaimers
- [ ] Trail-running focus maintained

### Functional Check
- [ ] Loading states designed
- [ ] Empty states designed
- [ ] Error states designed with helpful messages
- [ ] Interactive states (hover, focus, active)
- [ ] Keyboard navigation works

### Legal/Compliance Check
- [ ] Strava branding guidelines followed (if applicable)
- [ ] Medical disclaimers present (if health advice)
- [ ] Privacy policy linked
- [ ] No absolute health claims

---

## File Locations

### Brand Assets
```
/app/static/images/
├── YTM_Logo_byandfor_300.webp       (Full logo - primary use)
├── YTM_Logo_byandfor_110.webp       (Small logo)
├── YTM_waterColor_patch800x800_clean.webp  (Square/icon)
└── monkey_700.jpg                   (Mascot only - internal)
```

### Strava Brand Assets
```
/app/Strava_brand/1.2-Strava-API-Logos/
├── Powered by Strava/pwrdBy_strava_orange/
├── Compatible with Strava/cptblWith_strava_orange/
└── btn_strava_connect_with_orange_x2.svg
```

### Reference Implementations
```
/app/templates/landing.html          (Hero, CTA patterns)
/app/templates/welcome_post_strava.html  (Onboarding flow)
/app/static/style.css                (Main stylesheet)
```

---

## Common Scenarios

### "I need to add a new button"
1. Check `BRAND_APPLICATION_GUIDE.md` → Component Library → Buttons
2. Choose appropriate type (primary/success/CTA/secondary)
3. Copy CSS and HTML
4. Remember: Only ONE orange CTA button per screen

### "I need to write an error message"
1. Check `BRAND_APPLICATION_GUIDE.md` → Copy Templates → Error Messages
2. Use the pattern: State problem → Explain why → Offer solution
3. Keep tone helpful, not blaming
4. Include actionable next steps

### "I need to pick a color"
1. Check `YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md` → Color Palette
2. Use CSS variable, not hex code
3. Verify contrast ratio meets accessibility standards
4. When in doubt, use grays for text, blue for interactive

### "I need to write marketing copy"
1. Review `YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md` → Voice & Messaging
2. Check value propositions and key messages
3. Use copy templates as starting point
4. Test against brand personality pillars

### "I need to update the brand"
1. Update `YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md` first (source of truth)
2. Update `BRAND_APPLICATION_GUIDE.md` with new code patterns
3. Update version number and changelog in both documents
4. Communicate changes to team
5. Archive previous versions

---

## Brand Maturity Roadmap

### Phase 1: Foundation (Current)
- ✅ Core brand identity defined
- ✅ Visual system established
- ✅ Component library created
- ✅ Voice guidelines documented

### Phase 2: Expansion (Next 3-6 months)
- [ ] Social media content calendar
- [ ] Email template system
- [ ] User testimonial collection
- [ ] Brand photography guidelines
- [ ] Video content style guide

### Phase 3: Ecosystem (6-12 months)
- [ ] Partner co-branding guidelines
- [ ] Community/user-generated content standards
- [ ] Merchandise design system
- [ ] Event branding toolkit
- [ ] API/developer branding

### Phase 4: Evolution (12+ months)
- [ ] Dark mode implementation
- [ ] Internationalization considerations
- [ ] Sub-brand development (if needed)
- [ ] Brand refresh evaluation

---

## Resources & Tools

### Design Tools
- **Figma:** Component library (to be created)
- **Coolors.co:** Color palette management
- **Google Fonts:** Font pairing (if moving off system fonts)

### Accessibility Tools
- **WebAIM Contrast Checker:** https://webaim.org/resources/contrastchecker/
- **WAVE:** Browser extension for accessibility testing
- **axe DevTools:** Automated accessibility testing

### Reference Sites
- **Strava Brand Guidelines:** Follow for integration branding
- **WCAG 2.1 Guidelines:** Accessibility standards
- **Material Design:** Component behavior patterns (reference, not copying)

---

## Frequently Asked Questions

**Q: Can I create new colors not in the palette?**
A: Only if absolutely necessary and after documenting in the framework. 99% of cases should use existing palette.

**Q: What if the brand name doesn't fit in a headline?**
A: Shorten the headline, or use "YTM" abbreviation if space is extremely limited. Preferred is full name with Y, T, M emphasis.

**Q: Can I use different fonts?**
A: System fonts are intentional (performance, accessibility). If you have a compelling reason, propose in framework update.

**Q: How strictly should I follow the component library?**
A: Very strictly for core components (buttons, forms). More flexibility for page-specific layouts.

**Q: What if I disagree with a brand decision?**
A: Great! Propose a change with rationale. Brand evolves with user feedback and data. Update framework if change is adopted.

**Q: How do I handle brand in third-party integrations?**
A: Maintain core elements (logo, tagline, colors) but adapt to platform norms. See Strava integration as example.

---

## Maintenance

**Review Cycle:** Quarterly (or as needed for major features)

**Ownership:**
- **Brand Framework:** Product/Marketing lead
- **Application Guide:** Lead Developer/Designer
- **Implementation:** Entire team

**Update Process:**
1. Identify need for change (user feedback, new feature, inconsistency)
2. Propose update with rationale
3. Review with team
4. Update framework documents
5. Implement in codebase
6. Communicate to team
7. Archive previous version

---

## Support & Contact

**Questions about brand application?**
- Check this README first
- Review relevant framework document
- Ask in team channel
- Contact brand lead

**Found an inconsistency?**
- Document it (screenshot, link, description)
- Propose fix
- Update framework when resolved

**Need approval for brand deviation?**
- Explain why existing system doesn't work
- Show mockup/example
- Discuss with brand lead
- Document if approved

---

## Version History

**v1.1 - December 8, 2025**
- Updated brand name styling: Y, T, M slightly larger in sage green (#6B8F7F)
- Clarified YTM abbreviation is acceptable
- Added readability guidelines (left-align, 75ch max-width)
- Removed emoji icons from UI guidelines
- Updated banner gradient specification

**v1.0 - December 6, 2025**
- Initial comprehensive brand framework created
- Application guide with component library
- Based on existing implementation analysis

**Next Review:** March 2026 (or when major feature launches)

---

## Final Notes

**This branding system is designed to be:**
- **Comprehensive:** Covers strategy and implementation
- **Practical:** Ready to use today
- **Flexible:** Allows for growth and evolution
- **Accessible:** Clear guidelines for all team members
- **Maintainable:** Easy to update and expand

**Remember:**
Consistency builds trust. The more we reinforce our brand identity across every touchpoint, the more memorable and credible **Your Training Monkey** becomes.

**Train smart. Brand smarter.**

---

*For detailed information, see the full framework documents in this directory.*
