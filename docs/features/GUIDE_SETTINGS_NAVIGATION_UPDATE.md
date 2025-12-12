# Guide and Settings Navigation Update Summary

## Overview
Updated the Guide and Settings pages to match the Dashboard's navigation bar styling and replaced the monkey mascot image with the YTM (Your Training Monkey) cap version.

## Changes Made

### 1. Image Update
**File Used:**
- `app/static/images/YTM_waterColor_patch800x800.webp`

**Image Features:**
- Official YTM watercolor patch logo
- Circular badge design with navy blue border
- Monkey wearing YTM cap and goggles
- Includes compass rose and "YourTrainingMonkey.com" branding
- Professional watercolor artistic style
- Perfect for brand consistency across the application

### 2. Guide Page Updates (`app/templates/base_getting_started.html`)

**Navigation Changes:**
- Added dashboard-style tab navigation at the top
- Includes all 6 tabs: Dashboard, Activities, Journal, Coach, Guide, Settings
- Tabs use the same styling as the React dashboard (file folder tab design)
- Added "Your Training Monkey" branding in upper right corner of tab bar
- Branding uses YTM styling with green highlighted letters

**Mascot Changes:**
- Updated image source from `monkey_700.jpg` to `YTM_waterColor_patch800x800.webp`
- Using official YTM branded watercolor patch logo
- Circular badge design with navy border
- Includes YTM cap, goggles, and compass rose details
- Size: 150px × 150px
- No border-radius needed (image already has circular design)
- Clean, professional appearance with drop shadow

**Visual Consistency:**
- Top navigation now matches React dashboard exactly
- Consistent spacing and alignment
- Same color scheme (#f1f5f9 background, #e2e8f0 inactive tabs, white active tabs)
- Matching transition effects and shadows

### 3. Settings Pages Updates (`app/templates/base_settings.html`)

**Navigation Changes:**
- Replaced vertical left sidebar navigation with horizontal tab navigation at top
- Added dashboard-style tab navigation matching Guide page
- Includes all 6 main tabs: Dashboard, Activities, Journal, Coach, Guide, Settings
- Added "Your Training Monkey" branding in upper right corner of tab bar
- Settings tab is always active on settings pages

**Mascot Changes:**
- Updated image source from `monkey_700.jpg` to `YTM_waterColor_patch800x800.webp`
- Using official YTM branded watercolor patch logo
- Circular badge design with navy border
- Size: 150px × 150px
- No border-radius needed (image already has circular design)
- Clean, professional appearance

**Layout Changes:**
- Removed fixed left sidebar navigation
- Removed `margin-left: 200px` adjustments throughout
- Settings sub-navigation remains below header for category-specific navigation
- Cleaner, more spacious layout without sidebar

**Settings Sub-Navigation:**
- Kept the secondary navigation bar for settings categories (Profile, HR Zones, Training, Coaching, ACWR)
- Maintained the "Settings:" label prefix
- Preserved gradient background and styling
- Still uses pills/buttons style for settings categories

### 4. CSS Styling Updates

**New Tab Styling (Both Templates):**
```css
.dashboard-tabs-container {
    background-color: #f1f5f9;
    padding-top: 4px;
}

.dashboard-tab {
    padding: 6px 16px 7px 16px;
    background-color: #e2e8f0;  /* Inactive */
    border-top-right-radius: 8px;
    min-width: 120px;
}

.dashboard-tab.active {
    background-color: white;
    box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
}
```

**App Branding Styling:**
```css
.app-branding h1 {
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    font-variant: small-caps;
    font-family: "Arial Black", "Arial Bold", sans-serif;
}

.app-branding .highlight {
    font-size: 1.8rem;
    color: #7a9b76;  /* Green for Y, T, M */
}
```

**Mascot Styling:**
```css
.monkey-mascot {
    width: 150px;
    height: 150px;
    filter: drop-shadow(2px 4px 8px rgba(0,0,0,0.3));
}

.monkey-mascot img {
    object-fit: contain;  /* No border-radius - image is pre-styled */
}
```

## Benefits

1. **Visual Consistency**: All pages now have the same navigation style and branding
2. **Professional Branding**: Official YTM watercolor patch logo reinforces brand identity
3. **Improved UX**: Consistent navigation makes the app easier to use
4. **Modern Look**: Tab-based navigation is cleaner and more modern than mixed styles
5. **Mobile Friendly**: Tab design adapts better to different screen sizes
6. **Clear Hierarchy**: Main navigation at top, category navigation below (for settings)
7. **Brand Recognition**: YTM logo with cap and goggles creates memorable brand identity

## Files Modified

1. `app/templates/base_getting_started.html`
2. `app/templates/base_settings.html`

**Note:** Using existing branded image from `app/static/images/YTM_waterColor_patch800x800.webp`

## Testing Checklist

- [ ] Guide page loads correctly
- [ ] Settings pages load correctly
- [ ] Navigation tabs work on all pages
- [ ] Active tab is highlighted correctly
- [ ] YTM cap image displays properly
- [ ] Branding text displays in upper right
- [ ] Responsive design works on mobile
- [ ] Settings sub-navigation still works
- [ ] All links navigate to correct pages
- [ ] Hover effects work on tabs

## Notes

- The YTM cap image is significantly more engaging and brand-appropriate
- Navigation now matches the React dashboard exactly for consistency
- Settings pages retain their secondary navigation for category switching
- All pages maintain their specific content and functionality
- Changes are purely visual/navigation improvements

## Deployment

Follow standard deployment process as documented in `scripts/Deployment_script.txt`:
1. User should test locally first
2. When ready, run `app/deploy_strava_simple.bat`
3. Verify all pages load correctly in production
4. Check navigation works across all pages

