# Warm Editorial Minimalism: Core Design System

## 1. Philosophy & Tone
"Warm Editorial Minimalism" is a singular, uncompromising design aesthetic. It is a fusion of Japanese spatial restraint, soft brutalism's structural confidence, and the typographic authority of high-end editorial publishing. 

Every interface feels like a beautifully designed product catalog from a Japanese studio that also reads *Wallpaper* magazine and builds premium software. Whether scaling an e-commerce platform like **KIXX** or curating a visual gallery of **Mauryan Heritage** and **Bioluminescent** digital ecologies, the canvas must remain warm, structural, and profoundly calm.

### Absolute Prohibitions (The "Never" List)
- **NO** dark mode as a default.
- **NO** neon, electric, saturated, purple, or magenta colors.
- **NO** glowing gradients, aurora effects, or mesh backgrounds.
- **NO** glassmorphism, backdrop blurs, or heavy drop shadows (`shadow-xl` / glows).
- **NO** pill-shaped (`rounded-full`) primary buttons.
- **NO** emoji-heavy UI. Use crisp SVG line icons.

---

## 2. Core Color System

### Background (The Canvas)
The entire application background MUST be a warm, light beige or off-white. Think high-quality uncoated paper.
*   **Primary Canvas:** `#F7F5F0` (warm off-white, slight yellow undertone) | *Tailwind: `bg-[#F7F5F0]`*
*   **Alternate Canvas:** `#F2F0EA` (slightly warmer, stone-like)

### Accent Color (Primary Actions & Highlights)
Use a single, soft, calm light blue. Used sparingly (1-2 times per screen).
*   **Primary Accent:** `#BFDBFE` (*Tailwind: `blue-200`*) — subtle fills, upload zones.
*   **Action Accent:** `#93C5FD` (*Tailwind: `blue-300`*) — button borders, highlights.
*   **Text on Accent:** `#1E40AF` (*Tailwind: `blue-800`*) — text on light blue fills.
*   **Focused Accent:** `#60A5FA` (*Tailwind: `blue-400`*) — focus rings.

### Typography Colors
*   **Primary Text:** `#1C1917` (*Tailwind: `stone-900`*) — headings, labels.
*   **Secondary Text:** `#78716C` (*Tailwind: `stone-500`*) — descriptions, metadata.
*   **Disabled/Hint:** `#A8A29E` (*Tailwind: `stone-400`*) — inactive text.

### Borders & Dividers
*   **Default Border:** `#E7E5E4` (*Tailwind: `stone-200`*) — card/container borders.
*   **Subtle Divider:** `#F5F5F4` (*Tailwind: `stone-100`*) — internal section separators.
*   **Emphasis Border:** `#000000` @ 10% opacity.
*   **Dashed Border:** `border-dashed border-stone-300` — drop areas.

### Surface Colors
*   **Card Surface:** `#FFFFFF` (Pure white on beige canvas)
*   **Elevated Surface:** `#FAFAF9` (*Tailwind: `stone-50`*)
*   **Input Surface:** `#FFFFFF` or `transparent` (Never grey)

---

## 3. Typography System

Typography does the heavy lifting. Mix weights aggressively to create editorial drama.

### Font Stack
```css
/* Headings — High-impact, editorial geometric sans-serif */
font-family: 'Inter', 'DM Sans', 'Geist', system-ui, sans-serif;

/* Body — Legible, neutral, workhorse sans-serif */
font-family: 'Inter', 'DM Sans', system-ui, sans-serif;

/* Accent / Serif moments — Used sparingly (e.g., gallery titles, quotes) */
font-family: 'Playfair Display', 'DM Serif Display', 'Lora', Georgia, serif;

/* Mono — For code, IDs, technical labels */
font-family: 'JetBrains Mono', 'Fira Code', monospace;
```

### Scale & Rules
*   **Display / Hero:** 56–72px | Weight: 800–900 | Tracking: `-0.03em`
*   **Section Heading:** 28–36px | Weight: 700 | Tracking: `-0.02em`
*   **UI Label:** 12–13px | Weight: 500 | Tracking: `0.05–0.1em` | UPPERCASE
*   **Body Text:** 14–16px | Weight: 400 | Line-height: `1.7` | Max-width: `65ch`
*   *Rule:* No centered body text. Limit serif fonts to one major moment per screen.

---

## 4. Component System

### Buttons
*   **Primary Action:** `bg-stone-900 text-white rounded-sm px-6 py-2.5 text-sm font-medium tracking-wide hover:bg-stone-700`
*   **Secondary:** `bg-transparent border border-stone-300 text-stone-800 rounded-sm hover:bg-stone-100`
*   **Accent:** `bg-blue-100 border border-blue-200 text-blue-800 rounded-sm hover:bg-blue-200`

### Inputs & Forms
*   **Styling:** `bg-white border border-stone-300 rounded-sm px-3 py-2 text-sm placeholder:text-stone-400`
*   **Focus:** `outline-none ring-1 ring-blue-300 border-blue-300`
*   **Labels:** `text-xs font-medium tracking-wider uppercase text-stone-500`

### Cards
*   **Styling:** `bg-white border border-stone-200 shadow-sm rounded-lg p-5`
*   *Note:* Must feel like a sheet of premium paper sitting on the beige canvas.

### Drop Zones / Uploads
*   **Styling:** `bg-blue-50/50 border-2 border-dashed border-stone-300 rounded-lg`
*   **Hover:** `border-blue-300 bg-blue-50`

---

## 5. Layout & Spacing

*   **Width & Padding:** Max width `max-w-6xl` (1152px). Mobile padding `px-6`, Desktop `px-12`.
*   **Whitespace:** Whitespace IS design. Default to left-aligned on an 8px grid. Use asymmetric layouts rather than perfectly centered ones.
*   **Responsive:** Mobile-first, but keep it premium. Single column on mobile, reduce heading scale by 30-40%.

---

## 6. 3D & Animation (Gallery/Showcase Views)

Used for showcasing dynamic imagery.

### 3D Card Stack
```css
/* Container */
perspective: 1200px;
transform-style: preserve-3d;

/* Cards */
transform: translateX(Npx) translateZ(-Npx) rotateY(Ndeg);
transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
```
*   **Shadow:** `box-shadow: 0 4px 16px rgba(0,0,0,0.08)` (soft, realistic).
*   **Motion:** `cubic-bezier(0.4, 0, 0.2, 1)` (smooth, confident, not bouncy). 300–600ms.

---

## 7. Copy & Content Voice

*   **Headings:** Confident, editorial, noun-led. (*"Transform your image."* NOT *"Let's get started!"*)
*   **Descriptions:** Sparse. One sentence maximum per description.
*   **CTAs:** Direct verbs. (*"Upload"*, *"Generate"*, *"Submit"*)
