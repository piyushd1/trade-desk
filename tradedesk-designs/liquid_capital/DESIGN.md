# Design System Strategy: The Financial Atelier

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Private Bank."** We are moving away from the "fintech-as-a-toy" aesthetic and moving toward a high-end, editorial experience that feels like a bespoke wealth management service. 

To break the "template" look common in investment apps, we utilize **Tonal Architecture**. Instead of rigid grids and harsh lines, we use intentional asymmetry and white space as a structural element. The goal is "Soft Minimalism"—an environment where the interface recedes, allowing the user’s financial data to take center stage with clarity and quiet authority.

## 2. Colors & Surface Philosophy
The palette is built on a foundation of "Optical Whites" and "Atmospheric Grays," punctuated by a precise, high-performance blue.

### The "No-Line" Rule
Traditional 1px borders are strictly prohibited for sectioning content. We define boundaries through **Background Volumetric Shifts**. For example, a `surface-container-low` component should sit on a `surface` background. The transition between these two tones is our "border."

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked, premium paper stocks.
*   **Base Layer:** `surface` (#f8f9fa) — The global canvas.
*   **The Inset Layer:** `surface-container-low` (#f1f4f6) — Used for secondary grouping or "wells."
*   **The Hero Layer:** `surface-container-lowest` (#ffffff) — Reserved for the most important data cards (e.g., Portfolio Balance) to provide maximum "pop" and crispness.

### The "Glass & Gradient" Rule
To add soul to the minimalist aesthetic, use **Glassmorphism** for floating navigation bars or action sheets. Use a semi-transparent `surface` color with a `backdrop-filter: blur(20px)`. 
*   **Signature Textures:** For high-value actions, utilize a subtle linear gradient transitioning from `primary` (#0054d6) to `primary_dim` (#004abd) at a 135-degree angle. This adds a "weighted" feel to buttons that flat colors lack.

## 3. Typography: Editorial Authority
We pair **Manrope** (Display) with **Inter** (Body) to create a sophisticated hierarchy that feels both modern and established.

*   **The Display Scale:** Use `display-lg` and `display-md` (Manrope) for portfolio totals. The tighter kerning and geometric structure of Manrope convey a sense of "Engineered Wealth."
*   **The Narrative Scale:** Use `body-lg` (Inter) for all transactional data. Inter’s high x-height ensures maximum legibility even at small sizes.
*   **Tonal Contrast:** Never use pure black for text. Use `on_surface` (#2b3437) for headlines and `on_surface_variant` (#586064) for secondary labels to maintain a "Soft Minimalist" contrast ratio that reduces eye strain during long sessions.

## 4. Elevation & Depth
In this system, depth is a feeling, not a feature.

*   **Tonal Layering:** Avoid shadows for static elements. A `surface-container-highest` (#dbe4e7) header provides enough contrast against a `surface` background without the "noise" of a shadow.
*   **Ambient Shadows:** For interactive floating elements (like a "Buy" sheet), use a `primary_dim` tinted shadow: `box-shadow: 0 20px 40px rgba(0, 74, 189, 0.06)`. This creates a natural, atmospheric lift that feels integrated into the brand’s blue DNA.
*   **The "Ghost Border":** If a container requires a boundary (e.g., an input field), use `outline_variant` at **15% opacity**. This creates a suggestion of a container rather than a hard cage.

## 5. Components & Primitive Styling

### Buttons (The "Precision Tool")
*   **Primary:** High-pill shape (`rounded-full`). Background: Signature Blue Gradient. Label: `on_primary` (#f8f7ff).
*   **Secondary:** No background. Ghost border (15% `outline`). This keeps the UI light and breathable.
*   **Tertiary:** Text-only with an icon. Used for "View All" or secondary navigation.

### Cards & Data Lists
*   **No Dividers:** Prohibit the use of 1px horizontal lines between assets (e.g., Apple stock vs. Tesla stock). Instead, use `1.5rem` (xl) vertical spacing and subtle `surface-container` shifts to group data.
*   **The "Insight" Card:** Use `primary_container` (#dae1ff) as a background for market alerts or tips to make them feel distinguished from user-owned data.

### Input Fields
*   **State:** Default state should have no background, only a "Ghost Border." On focus, the border transitions to `primary` and the background shifts to `surface_container_lowest` (#ffffff). This mimics a light turning on.

### Chips (Asset Tags)
*   **Style:** Use `secondary_container` (#e4e2e6) with `label-md` typography. Avoid heavy fills; the chips should feel like "light whispers" on the screen.

## 6. Do's and Don'ts

### Do:
*   **Embrace White Space:** Use the `xl` (1.5rem) spacing scale aggressively. High-end design requires room to breathe.
*   **Layer Neutrals:** Use `surface-container-low` to group related information instead of drawing a box around it.
*   **Use Intentional Asymmetry:** Align primary data (Balance) to the left, but place "Growth %" in a floating `surface-container-highest` pill on the right to create visual interest.

### Don't:
*   **Don't use 100% Opaque Borders:** This creates a "boxed-in" feeling that contradicts the minimalist goal.
*   **Don't use Standard Drop Shadows:** Never use `#000000` for shadows. Always tint shadows with the `primary` or `secondary` hue at very low opacities.
*   **Don't use Center-Alignment for Long Lists:** Keep financial data left-aligned (or right-aligned for numbers) to ensure the eye can scan figures with high-speed precision.