---
name: Tactical Emergency Response
colors:
  surface: '#10141a'
  surface-dim: '#10141a'
  surface-bright: '#353940'
  surface-container-lowest: '#0a0e14'
  surface-container-low: '#181c22'
  surface-container: '#1c2026'
  surface-container-high: '#262a31'
  surface-container-highest: '#31353c'
  on-surface: '#dfe2eb'
  on-surface-variant: '#e5bdb8'
  inverse-surface: '#dfe2eb'
  inverse-on-surface: '#2d3137'
  outline: '#ac8884'
  outline-variant: '#5c403c'
  surface-tint: '#ffb4aa'
  primary: '#ffb4aa'
  on-primary: '#690004'
  primary-container: '#ff5447'
  on-primary-container: '#5c0003'
  inverse-primary: '#bd0e12'
  secondary: '#82deff'
  on-secondary: '#003544'
  secondary-container: '#00c6f3'
  on-secondary-container: '#004e61'
  tertiary: '#ffb868'
  on-tertiary: '#482900'
  tertiary-container: '#ce7f00'
  on-tertiary-container: '#3f2300'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad5'
  primary-fixed-dim: '#ffb4aa'
  on-primary-fixed: '#410001'
  on-primary-fixed-variant: '#930007'
  secondary-fixed: '#b7eaff'
  secondary-fixed-dim: '#50d5ff'
  on-secondary-fixed: '#001f28'
  on-secondary-fixed-variant: '#004d61'
  tertiary-fixed: '#ffddbb'
  tertiary-fixed-dim: '#ffb868'
  on-tertiary-fixed: '#2b1700'
  on-tertiary-fixed-variant: '#673d00'
  background: '#10141a'
  on-background: '#dfe2eb'
  surface-variant: '#31353c'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '800'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '800'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
    letterSpacing: 0em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 18px
    letterSpacing: 0.04em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.08em
  bilingual-cue:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-tablet: 1.5rem
  gutter-desktop: 2rem
  margin: 1rem
  margin-tablet: 1.5rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.25rem
---

## Brand & Style

This design system is engineered for mission-critical disaster coordination during severe cyclone and storm surge events along coastal corridors. Built to operate reliably under extreme physical distress—such as high winds, power grid blackouts, low battery reserves, and rain-slicked glass—the interface prioritizes absolute legibility, immediate triage recognition, and fault-free operation.

The visual style is **High-Contrast Tactical Emergency UI**. It pairs an ultra-dark battery-conserving canvas with high-luminance signal accents, razor-sharp architectural borders, and bilingual information density (English with integrated Telugu cues). The aesthetic rejects decorative softness in favor of deliberate, high-reliability utilitarianism: physical micro-radii, unambiguous status signaling, and explicit tactile framing designed for rapid panic-state response.

## Colors

The color architecture is built around an OLED true-dark foundation to preserve device battery during multi-day grid failure while ensuring maximum luminance separation under harsh ambient conditions.

- **Primary (`#FF453A`) — Emergency SOS / Critical:** Reserved exclusively for immediate life threats, critical trauma, structural failure, and high-urgency alerts.
- **Secondary (`#0AC8F5`) — Marine Inundation / Evacuation Routes:** Dedicated to storm surge alerts, coastal flood lines, watercraft operations, and safe navigation paths.
- **Tertiary (`#FF9F0A`) — Warning / Supplies & Vulnerable:** Denotes structural shelters, food/potable water caches, elderly/child priority flags, and urgent advisory states.
- **Signal Emerald (`#30D158`):** Indicates verified safe status, active peer-to-peer sync, confirmed battery check-ins, and resolved triage tasks.
- **Neutral Stack:**
  - Base Canvas (`#0A0E14`): Deep slate-charcoal black optimized for OLED power conservation.
  - Surface Tier 1 (`#121824`): Structural card containers, map controls, and action bars.
  - Surface Tier 2 (`#1B2433`): Floating overlays, input containers, and active drawers.
  - Stroke/Border Surface (`#2C384E`): High-definition perimeter outlines for tactile segregation.
  - Text High-Emphasized (`#FFFFFF`): Maximum legibility headers, SOS coordinates, and telemetry readings.
  - Text Medium-Emphasized (`#9EABBF`): Bilingual Telugu secondary strings, timestamps, and descriptive metadata.

## Typography

Typography relies on `Inter` across all structural levels, configured with generous open counters, distinct glyph differentiation, and robust vertical metric balancing. This ensures rapid scanning when the device screen is obscured by water drops or operating at minimum display brightness.

- **Scale & Hierarchy:** Critical emergency headlines enforce tight tracking with maximum weight (`800` / `700`) to guarantee legibility from arm’s length. Numerical coordinates and grid references utilize tabular figures (`tnum`).
- **Bilingual Typographic Hierarchy:** English serves as the operational anchor, paired alongside or stacked directly above Telugu secondary labels (e.g., `ఆపద SOS / Emergency` or `రక్షణ శిబిరం / Shelter`). Telugu companion strings are styled using `bilingual-cue` or `body-sm` with a secondary opacity (`#9EABBF`) to preserve direct hierarchy while ensuring native-language comprehension.

## Layout & Spacing

Layout execution utilizes a responsive fluid grid optimized for high-urgency touch interaction.
- **Columns & Breakpoints:** 4 columns on mobile viewports (<600px), 8 columns on tactical tablets (600px–1024px), and 12 columns on command consoles (>1024px).
- **Physical Touch Target Threshold:** All actionable UI items mandate an absolute physical touch envelope of at least 48px × 48px, expanding to 56px for primary triage buttons, preventing input error during manual tremors or active rainfall.
- **Rhythm & Safe Insets:** Component internal density is locked to strict multiples of 4px and 8px. Top and bottom mobile edges incorporate reinforced safe areas to isolate operational triggers from hardware gesture navigation zones.

## Elevation & Depth

To maximize battery endurance on OLED panels and guarantee visual clarity in wet environments, this design system avoids multi-layer ambient blur, diffuse colored glows, and drop shadows. 

Depth is structured entirely through **Tonal Stacking and Crisp Boundary Definition**:
- **Elevation 0 (Canvas):** Pure `#0A0E14` base screen plane.
- **Elevation 1 (Card/List Containers):** `#121824` fill enclosed by a solid 1px `#2C384E` stroke.
- **Elevation 2 (Active/Selected Panels):** `#1B2433` fill framed by a 1.5px high-contrast structural boundary.
- **Elevation 3 (Floating Emergency Actions/Drawers):** `#1B2433` overlay pinned by an active status edge-indicator (e.g., 2px solid `#FF453A` or `#0AC8F5`).

This structured framework eliminates rendering overhead, avoids battery drain, and maintains immediate visual edge detection.

## Shapes

The design system enforces a controlled micro-radius (`roundedness: 1`), implementing an architectural `0.25rem` (4px) corner radius across standard buttons, status modules, input elements, and cards. Larger containers or bottom sheets scale to `rounded-lg` (0.5rem / 8px).

This tight, mechanical geometry maximizes the usable interior display area, reinforces a tactical instrumentation aesthetic, and establishes clear visual boundaries between adjacent action tiles. Fully round pill shapes are reserved exclusively for live connectivity badges to visually distinguish static infrastructure cards from dynamic telemetry data.

## Components

### Buttons
- **Critical Action (SOS / Trauma):** Full-bleed or full-width container, 56px height. Background `#FF453A`, text `#FFFFFF` (`label-lg`, uppercase), 4px border radius. Displays both primary and vernacular triggers (e.g., "ఆపద పంపండి • TRANSMIT SOS"). Active state: `#D63329`.
- **Secondary Action (Inundation Route / Safe Path):** 48px height minimum. Border 1.5px `#0AC8F5`, surface `#121824`, text `#0AC8F5`.
- **Utility / Tactical Ghost:** Surface `#1B2433`, border 1px `#2C384E`, text `#FFFFFF`.

### Connectivity Status Pills
- Micro-pill badges (height 28px, padding 4px 12px, border-radius 9999px) positioned in the persistent telemetry bar to indicate network transport layer:
  - **Zero Data / Offline:** `#1B2433` surface, 1px `#FF453A` border, `#FF453A` text with blinking offline marker.
  - **SMS Fallback:** `#1B2433` surface, 1px `#FF9F0A` border, `#FF9F0A` text, labeled `SMS BRIDGE / సెల్ మెసేజ్`.
  - **Cached Local SQLite:** `#1B2433` surface, 1px `#0AC8F5` border, `#0AC8F5` text, labeled `LOCAL DB / లోకల్ స్టోరేజ్`.
  - **Mesh / Synced:** `#1B2433` surface, 1px `#30D158` border, `#30D158` text.

### Cards
- Constructed with `#121824` background and 1px `#2C384E` solid perimeter border.
- Cards feature an optional 4px solid left indicator bar tinted to the respective triage classification (Emergency Red, Marine Cyan, Warning Amber, or Signal Emerald).
- Internal content maintains `space-md` (16px) padding with primary English title paired with Telugu subtitle metadata.

### Input Fields & Controls
- Form elements use 52px height for high touch accuracy.
- Surface `#0A0E14` surrounded by 1.5px `#2C384E` border. Focus state shifts border directly to `#0AC8F5` or `#FF453A`.
- Native placeholder text set in `#9EABBF` body font with bilingual assistance cues directly underneath.

### Checkboxes & Segmented Toggles
- High-contrast square geometries (24px × 24px) with 2px solid `#2C384E` borders. Active state renders `#30D158` or `#FF453A` solid core with high-contrast icon overlay.
- Segmented switches leverage structural `#121824` trays with inset 4px active toggles framed by crisp tactical borders.