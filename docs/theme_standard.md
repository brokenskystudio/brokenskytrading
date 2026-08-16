# Broken Sky Studio Theme Standard

This file is the visual source of truth for products created under Broken Sky Studio. Any agent making a branding or theme change must update this file in the same change.

## Brand

- Studio name: `Broken Sky Studio`
- Short brand mark: `BSS`
- Never use `BS` as the brand mark.
- Product family domain: `brokensky.studio`
- Product creator attribution: `Alejandro Restrepo`
- Current product: `Trading Research`
- Product label: `STUDIO / PRODUCT 01`

## Visual Direction

The default visual language is calm, tactile, editorial, and research-oriented. It should feel like a well-designed analog workspace rather than a generic fintech dashboard.

- Use restrained layouts with strong typography and generous whitespace.
- Prefer warm paper, coffee, wood, and slate references over neon colors.
- Use thin borders and small rounded corners.
- Avoid excessive gradients, glassmorphism, oversized decorative illustrations, and generic dashboard decoration.
- Keep data and actions visually clear before adding visual flourish.

## Themes

The application has a persistent light/dark switch. Light mode is the default. Store the selected mode in `localStorage` with the key `trading-research-theme`.

### Light: Coffee Cream

| Token | Value | Usage |
| --- | --- | --- |
| Page background | `#F3E9D8` | Main page canvas |
| Surface | `#E5D4BA` | Cards and panels |
| Border | `#B99B78` | Dividers and outlines |
| Text | `#241A14` | Primary text |
| Muted text | `#634D3B` | Supporting text and labels |
| Accent | `#854719` | Links, active states, primary controls |
| Danger | `#963B2F` | Destructive actions and warnings |
| Button text | `#FFF8ED` | Text on accent buttons |
| Input background | `#FFFDF8` | Input and select fields |
| Input text | `#241A14` | Input content |

### Dark: Coffee + Slate

| Token | Value | Usage |
| --- | --- | --- |
| Page background | `#10151A` | Main page canvas |
| Surface | `#1E252B` | Cards and panels |
| Border | `#3B4A52` | Dividers and outlines |
| Text | `#EEF2F0` | Primary text |
| Muted text | `#A4B0AE` | Supporting text and labels |
| Accent | `#D7A56D` | Links, active states, primary controls |
| Danger | `#E98578` | Destructive actions and warnings |
| Button text | `#241A14` | Text on accent buttons |
| Input background | `#0B1014` | Input and select fields |
| Input text | `#EEF2F0` | Input content |

## Typography

- Use a clean sans-serif system stack unless a product-specific typeface is approved.
- Eyebrows and labels use uppercase lettering with increased tracking.
- Large headings use tight letter spacing and compact line height.
- Supporting text uses muted text color and comfortable line height.
- Never sacrifice text contrast for visual subtlety.

## Shape and Spacing

- Small rounded corners are standard: `8px` for panels and cards, `6px` for controls.
- Inputs must have a visible background distinct from the page and readable text in both themes.
- Use thin borders rather than heavy shadows.
- Keep consistent panel padding around `1.4rem`.
- Use responsive single-column layouts below approximately `780px`.

## Controls

- Primary buttons use the current theme accent and theme-specific button text color.
- Primary button hover uses a noticeable `brightness(1.16)` effect, never a hard-coded color from another theme.
- Disabled controls reduce opacity and show a wait cursor when appropriate.
- Destructive actions use the current theme danger color.
- Buttons must have accessible labels and visible focus states.

## Theme Switch

- The switch is an icon-only button with an accessible `aria-label` and tooltip title.
- Light mode displays a quarter-moon glyph for switching to dark mode.
- Dark mode displays a slightly heavier sun glyph for switching to light mode.
- The quarter moon has a subtle positive angle.
- Do not reintroduce the temporary palette selector unless explicitly requested.

## Branding Placement

- Use the `BSS` mark in the product header.
- The app logo/header should link to the product home page when inside a product workspace.
- Include `Alejandro Restrepo` as the studio owner attribution where appropriate.
- Footer links may include the LinkedIn placeholder and `brokensky.studio`.

## Content and Safety

- Trading Research is an informational research tool.
- Use phrases such as `research candidate`, `review`, and `risk alert`.
- Do not use guaranteed-return language or imply trade execution.
- Keep market-data timestamps and provider limitations visible.

## Change Protocol

When changing the theme:

1. Update the implementation.
2. Update this file with the new token, component, or interaction rule.
3. Verify light and dark contrast.
4. Verify desktop and mobile layouts.
5. Run the frontend production build.
