# CLAUDE.md

Behavioural guidelines to eliminate common LLM coding mistakes and AI-slop design.
Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution and craft over speed.
For trivial tasks, use judgment. For UI work, there are no trivial tasks.

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

---

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- Use simple naming terms, good code practice and human-maintainable code.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: *"Would a senior engineer say this is overcomplicated?"* If yes, simplify.

---

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

---

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## 5. Security Defaults

- Never log credentials, tokens, or PII.
- Validate and sanitise all external inputs at the boundary.
- Return generic errors to clients; log specifics server-side.

---

## 6. Dependencies

- Prefer stdlib or already-present packages over new ones.
- If adding a dependency, state why no existing one suffices.

---

## 7. Design: Anti-Slop Standards

> These apply to every UI task — component, page, product, or prototype.
> The benchmark is Linear, Raycast, Vercel, Notion Calendar, Arc Browser, and modern Apple software.
> If the output wouldn't ship at those companies, it isn't done.

### 7.1 No Generic Defaults — Ever

AI-generated slop has a fingerprint. Never produce it:

| Banned default | Why it's slop | What to do instead |
|---|---|---|
| Inter / Roboto / system-ui as the only font choice | Zero personality, zero decision | Make a typographic decision. Pick a pairing with intent. |
| Purple-to-blue gradients on white | The LLM signature gradient | Earn your gradient. Or don't use one. |
| `rounded-lg` on everything | Cargo-culted from Tailwind demos | Radius is a design decision. Be deliberate. |
| `shadow-md` everywhere | Fake depth without spatial logic | Shadows imply a light source. Make it consistent. |
| Blue `#3B82F6` as the brand colour | Tailwind's default blue | Chose a colour with intent, then derive a system from it. |
| Placeholder grey cards with lorem ipsum | Demonstrates nothing | Use real or realistic content in every mock. |
| 16px base size, `text-sm` / `text-lg` binary scale | No typographic scale | Define a real type scale (e.g. Major Third, Perfect Fourth). |
| Centered hero → features grid → CTA footer | Marketing site template #1 | Break the template. Earn every layout decision. |

If you catch yourself about to produce any of the above, stop and make a real decision.

---

### 7.2 Taste: The Leonxlnx Principle

*Good taste means knowing what to leave out.*

- Restraint is harder than decoration. When in doubt, remove.
- Every visual element must earn its place. If you can't explain why it's there, delete it.
- Similarity creates harmony; sameness creates boredom. Vary weight, size, and rhythm — not colour.
- Reference the best. Before designing a modal, look at how Raycast, Linear, and Apple do it. Then make a considered decision.
- "Clean" is not a style. It is the absence of decisions. Make decisions.

---

### 7.3 Interaction Craft: The Emil Kowalski Principle

*Interactions are the product. Animations aren't decoration — they're communication.*

**Motion rules:**
- Duration: `150ms` for micro (hover, focus), `250ms` for UI transitions, `400ms` for page-level. Never exceed `500ms` unless the motion IS the feature.
- Easing: `ease-out` for elements entering the screen. `ease-in` for elements leaving. `ease-in-out` for elements that stay but transform. Never use `linear` for UI.
- Spring physics over CSS easing when using Framer Motion or react-spring. Springs feel alive; cubic-beziers feel mechanical.
- Stagger: When multiple items animate together, offset by `30–60ms` per item. This is the difference between a list appearing and a list *arriving*.
- Exit animations matter as much as enter animations. A dialog that vanishes without animating out feels broken.

**Interaction states (all of them, always):**
```
default → hover → focus-visible → active → disabled → loading → error → success
```
Never ship a component missing any state it can reach.

**Feedback latency:**
- < 100ms: no indicator needed
- 100ms – 1s: button loading state
- > 1s: skeleton or progress
- > 3s: progress + cancel option

**The Emil test:** Would this interaction feel good on a 120Hz ProMotion display? If the answer is "I don't know," it needs work.

---

### 7.4 Impeccable Design: Detail at Every Scale

*The difference between good and great is what you do at 1px scale.*

**Spacing:**
- Use a 4px base grid. Every margin, padding, and gap should be a multiple of 4.
- Spacing between related elements is smaller than spacing between unrelated elements. If everything has the same gap, nothing has hierarchy.
- Whitespace is a design element, not empty space. Use it to direct attention.

**Typography:**
- Line-height: `1.2–1.3` for headings. `1.5–1.6` for body. `1.4` for UI labels.
- Measure (line length): `55–75ch` for body text. Wider for UI. Narrower for captions.
- Letter-spacing: `-0.02em` to `-0.04em` for large display type. `0` for body. `0.04em` to `0.08em` for ALL-CAPS labels.
- Font-weight: Use weight as a hierarchy signal. Don't use bold for everything important.
- Never set body copy in a weight below 400. Never set large display in a weight above 700 unless intentional.

**Colour:**
- Define a token system before using any colour: `--color-surface`, `--color-surface-raised`, `--color-border`, `--color-text-primary`, `--color-text-secondary`, `--color-text-muted`, `--color-accent`, `--color-accent-subtle`.
- Borders should be subtle. `hsl(var(--hue) 10% 88%)` in light mode. Borders that are too dark create visual noise.
- Avoid pure black (`#000000`) for text. Use `hsl(0 0% 9%)` or similar. Pure black on white has too much contrast and causes eye strain.
- Dark mode is not `background: #000; color: #fff`. Dark mode has depth: multiple surface levels (`#0a0a0a`, `#111`, `#1a1a1a`, `#222`).

**Iconography:**
- One icon library. Consistent stroke weight throughout. Never mix filled and outlined icons in the same context.
- Icons at 16px must be pixel-perfect. If an icon looks fuzzy at 16px, it's wrong.
- Icons are not decoration. If an icon doesn't add meaning, remove it.

**Borders, Radius, and Shadows:**
- Radius should be consistent and intentional. Small components (chips, badges): `4–6px`. Cards: `8–12px`. Modals/sheets: `12–16px`. Full-pill for buttons is a style choice, not a default.
- Shadows have a light source. Pick one (top-centre is standard) and don't deviate. Use layered shadows for realistic depth: one diffuse, one sharp.
- Don't use shadows AND borders together unless creating an inset/pressed effect. Choose one system.

---

### 7.5 Component Standards

Every component must be built to these standards before it's considered done:

**Buttons**
- Minimum tap target: 44×44px (Apple HIG). Visual size can be smaller; hit area must not be.
- Loading state: spinner replaces text, width locked to prevent layout shift.
- Disabled state: reduced opacity, `cursor: not-allowed`, `pointer-events: none`.
- Focus ring: `outline: 2px solid var(--color-accent); outline-offset: 2px`. Never remove focus rings — restyle them.
- Icon buttons need `aria-label`. Always.

**Forms & Inputs**
- Label always visible (never placeholder-as-label).
- Error message below the field, associated via `aria-describedby`.
- Success state for async validation (e.g. username availability).
- Character counts for bounded fields.
- Autofocus only the first field, never programmatically move focus mid-flow.

**Modals & Overlays**
- Trap focus inside the modal. Return focus on close.
- `Escape` key closes. Clicking backdrop closes (with confirmation if destructive).
- Entry: scale from `0.95` + fade in, `250ms ease-out`.
- Exit: scale to `0.95` + fade out, `200ms ease-in`.
- Never full-screen on desktop unless it IS a full-screen feature.

**Lists & Tables**
- Empty states are designed, not an afterthought. An empty state is the first impression for new users.
- Loading state: skeleton rows, same height as real rows.
- Hover state: subtle `background-color` shift, `80–100ms`.
- Selection state: clear visual distinction, not just a checkbox.

**Navigation**
- Active state is always unambiguous.
- Current page link is not a link (no pointer cursor, no hover state).
- Keyboard navigable. Tab order matches visual order.

---

### 7.6 Performance as Design

Perceived performance is part of the design:

- Images: always specify `width` and `height` to prevent layout shift. Use `loading="lazy"` below the fold.
- Fonts: `font-display: swap`. Preload the primary font file.
- Transitions: use `transform` and `opacity` only. Never animate `width`, `height`, `top`, `left`, `margin` — they trigger layout.
- Skeleton screens over spinners for content loading. Spinners for actions.
- Optimistic UI for mutations that are very likely to succeed. Rollback gracefully on error.

---

### 7.7 The Final Check

Before considering any UI work complete, run this checklist:

```
[ ] Does every interactive element have a visible focus state?
[ ] Is the colour contrast ratio ≥ 4.5:1 for body text, ≥ 3:1 for large text?
[ ] Does it work at 320px width and 1440px width?
[ ] Have I used real content (not lorem ipsum) to validate the layout?
[ ] Are all loading, empty, error, and success states designed?
[ ] Does every animation respect prefers-reduced-motion?
[ ] Would I be comfortable showing this to the Linear or Vercel design team?
```

If any box is unchecked, it's not done.

---

### 7.8 Reference Bar

When making any design decision, ask: *what does the best version of this look like?*

- **Menus & command palettes:** Raycast, Linear
- **Data tables & lists:** Linear, Vercel Dashboard
- **Typography & editorial layouts:** Stripe, Vercel
- **Motion & micro-interactions:** Emil Kowalski's work (sonner, vaul, cmdk)
- **Calendar & scheduling UI:** Notion Calendar
- **System UI components:** macOS Ventura/Sonoma, iOS 17/18
- **Onboarding flows:** Arc Browser, Craft
- **Empty states:** Linear, GitHub (post-2022)
- **Dark mode execution:** Raycast, Linear, Vercel

Internalise these. Not to copy them — to understand *why* they work, then make your own decisions at that level.

---

**These guidelines are working if:** diffs are clean and minimal, UI ships without a follow-up "make it look better" pass, and the output could plausibly be mistaken for work from a product company that cares.
